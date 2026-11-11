# Data Generation Instructions

## Overview

`backend/app/data_generation/generator.py` builds a deterministic industrial dataset and writes it to the application database, `data/ground_truth/ground_truth.csv`, and `data/reports/validation_report.json`.

The generator class is `SyntheticDataGenerator`. The command-line entry point is:

```bash
python -m backend.app.data_generation.generator --mode starter --seed 20261022
```

Run that command from the project root after the schema exists (`python -m alembic upgrade head`). `--mode` accepts `starter` or `full`. `--seed` defaults to `20261022`, the same value as `settings.RANDOM_SEED`.

Each run calls `clean_existing_data()`, which deletes rows from all 15 tables in reverse dependency order, then inserts a new dataset and runs `DataValidator.run_all_validations()`.

## What the two modes change

Both modes use the same plant, machine, failure, and edge-case logic. Only `generate_telemetry()` changes the number of regular timestamps:

| Mode | `time_steps` | Regular grid |
|---|---|---|
| `starter` | 90 | 90 points spread across the 90-day window |
| `full` | 2500 | 2,500 points spread across the same window |

For every failure whose `pre_warning_lead_time_hours` is greater than 0, the generator also appends timestamps 24, 18, 12, 6, 4, 2, and 1 hours before that failure. Each timestamp is written once per sensor. A starter run is therefore larger than `90 × 100 machines × 5 sensors` because of those extra pre-failure points. A full run starts from `2,500 × 100 × 5` and adds the same pre-failure points.

## Fixed topology

`generate_plants()`, `generate_production_lines()`, `generate_machines()`, and `generate_sensors()` always create:

| Entity | Count | ID pattern |
|---|---|---|
| Plants | 3 | `PLT-001`, `PLT-002`, `PLT-003` |
| Production lines | 12 (4 per plant) | `LINE-<plant_id>-001` … `004` |
| Machines | 100 | `MCH-<line_id>-001` … |
| Sensors | 500 (5 per machine) | `SNS-<machine_id>-TEMP-01`, `VIB-01`, `PRESS-01`, `CURR-01`, `RPM-01` |
| Technicians | 15 | `TECH-001` … `TECH-015` |
| Parts | 20 | `PRT-0001` … `PRT-0020` |

Line types cycle through `MACHINING`, `ASSEMBLY`, `HYDRAULIC_PRESSING`, and `PACKAGING`. Machine counts per line are `[8, 8, 8, 9, 8, 8, 8, 9, 8, 8, 9, 9]`. Machine types cycle through `CNC_MILLING`, `HYDRAULIC_PRESS`, `ROBOTIC_ARM`, `COMPRESSOR`, `CONVEYOR`, and `TURBINE`.

The timeline ends at `2026-11-10 23:59:59` and starts 90 days earlier. `created_at` / `updated_at` on master rows use that window, not the wall clock.

Operating shifts are sampled every 7 days. Each sampled day writes Morning (`SHF-MORN`, 06:00–14:00), Afternoon (`SHF-AFTN`, 14:00–22:00), and Night (`SHF-NGHT`, 22:00–06:00 next day) for every plant. Shift IDs look like `SHF-PLT-001-20260812-MORN`.

## Failures and work orders

`generate_failures_and_work_orders()` draws `random.randint(120, 145)` failures. With seed `20261022` that count is stable across runs. Each failure gets one completed work order (`WO-2026-NNNNNN`), one failure row (`FAIL-2026-NNNNNN`), one to three part rows, and one technician assignment.

Failure types and their nominal lead times:

| Type | Nominal lead hours |
|---|---|
| `BEARING_WEAR` | 36 |
| `OVERHEATING` | 24 |
| `HYDRAULIC_LEAK` | 18 |
| `MOTOR_BURNOUT` | 12 |
| `SENSOR_DRIFT` | 48 |
| `MECHANICAL_JAM` | 0 |

`MECHANICAL_JAM`, and also the failure at index 12, are stored with `pre_warning_lead_time_hours = 0`. Every other failure uses `max(2.0, nominal_lead + uniform(-6, 6))`.

Work order index 7 is the inverted-timestamp case: `actual_end_time = actual_start_time - 2.5 hours`. The comment in the generator mentions two work orders; the code injects this once, at `idx == 7`.

## Telemetry values

Nominal readings are normal distributions:

| Sensor | Mean | Std | Unit |
|---|---|---|---|
| Temperature | 65.0 | 3.5 | Celsius |
| Vibration | 1.8 | 0.4 | mm/s |
| Pressure | 22.0 | 2.0 | Bar |
| Current | 25.0 | 2.5 | Amperes |
| RPM | 1650.0 | 45.0 | RPM |

Inside a pre-failure window, `severity_factor = max(0, 1 - hours_to_failure / 24)` scales these drifts:

| Failure type | Drift |
|---|---|
| `BEARING_WEAR` | Vibration `+ 5.5 * factor`; temperature `+ 18 * factor` |
| `OVERHEATING` | Temperature `+ 28 * factor`; current `+ 16 * factor` |
| `HYDRAULIC_LEAK` | Pressure `- 15 * factor` |
| `MOTOR_BURNOUT` | Current `+ 26 * factor` |
| `MECHANICAL_JAM` | When `hours_to_failure <= 1`: RPM set to `0.0`, current `+ 35` |
| `SENSOR_DRIFT` | No extra sensor drift is applied. The type is only a failure label. |

## Edge cases the generator inserts

| Case | Code condition | Stored as |
|---|---|---|
| Unknown sensor | Machine index 3, temperature, timestamp index 10 | `sensor_id = SNS-UNKNOWN-999-TEMP-01` |
| Impossible temperature | Machine index 5, temperature, timestamp index 15 | value `999.0` |
| Negative vibration | Machine index 6, vibration, timestamp index 20 | value `-22.5` |
| Invalid unit | Machine index 7, current, timestamp index 25 | unit `Fahrenheit` |
| Zero warning | `MECHANICAL_JAM` or failure index 12 | `lead_time_hours = 0` |
| Inverted maintenance time | Work-order loop index 7 | end before start |
| Zero masked as missing | Machine index 9, RPM, timestamp index 30 | value `0.0` |

After insert, `DataValidator` records exceptions. It does not delete the bad rows. `ZERO_INSTEAD_OF_MISSING` matches every temperature, RPM, or pressure reading whose raw value is exactly `0.0`, so mechanical-jam RPM zeros are counted in addition to the single explicit injection. The checked-in starter report at `data/reports/validation_report.json` records 33 exceptions for seed `20261022`: 24 `FAILURE_WITHOUT_WARNING`, 1 `INVALID_MAINTENANCE_TIME`, 1 `INVALID_UNIT`, 2 `OUT_OF_RANGE_READING`, 1 `UNKNOWN_SENSOR`, and 4 `ZERO_INSTEAD_OF_MISSING`.

## Ground truth file

`save_ground_truth()` writes `data/ground_truth/ground_truth.csv` with one row per failure:

`failure_id`, `machine_id`, `failure_timestamp`, `failure_type`, `severity`, `lead_time_hours`, `downtime_hours`, `work_order_id`, `is_zero_warning_anomaly`.

`backend/app/ml/feature_engineering.py` does not read this file. Labels used in training come from `failure_events.failure_timestamp`.

## Reproducibility

`set_seed()` resets both `random.Random(seed)` and `numpy.random.seed(seed)` before generation. Repeating the same `--mode` and `--seed` replaces the database and rewrites the ground-truth file with the same contents.

```bash
python -m backend.app.data_generation.generator --mode starter --seed 20261022
python -m pytest backend/tests/test_reproducibility.py -v
```

A smaller PostgreSQL reference load that does not generate telemetry lives in `database/seed_data/01_seed_reference_data.sql`. Use the Python generator when you need the full labelled dataset.
