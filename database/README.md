# Database Documentation

## Overview
This database stores telemetry, operating shifts, maintenance work orders, machine failures, sensor configurations, and audit trails for the AI-Based Predictive Maintenance System.

## Main Entities (10 Primary Entities + 5 Bridge & Audit Tables)
1. **`plants`**: Industrial facility records (`PLT-001`, etc.)
2. **`production_lines`**: Assembly & machining lines (`LINE-PLT-001-001`)
3. **`machines`**: Industrial equipment assets (`MCH-LINE-PLT-001-001-001`)
4. **`sensors`**: Temperature, Vibration, Pressure, Current, and RPM sensors (`SNS-MCH-...-TEMP-01`)
5. **`telemetry_events`**: High-frequency time-series sensor events (`TEL-SNS-...-TIMESTAMP`)
6. **`operating_shifts`**: Shift schedules and operational states (`SHF-PLT-001-20261022-1`)
7. **`technicians`**: Maintenance engineering staff (`TECH-001`)
8. **`parts`**: Spare parts inventory and unit costs (`PRT-0001`)
9. **`maintenance_work_orders`**: Scheduled, corrective, and emergency work orders (`WO-2026-000001`)
10. **`failure_events`**: Ground truth machine failure events with root causes (`FAIL-2026-000001`)

### Additional Tables:
11. **`work_order_parts`**: Bridge table tracking parts and unit cost per work order.
12. **`work_order_technicians`**: Bridge table tracking labor hours per technician.
13. **`data_validation_exceptions`**: Stores data quality issues and edge cases (`VAL-20261022-0001`).
14. **`machine_health_audit_trail`**: Complete history of health score changes and status transitions.
15. **`failure_prediction_logs`**: Historical machine failure predictions and explanatory factors.

## Running Migrations and Loading Schema
### PostgreSQL via Docker or Local Instance:
The Alembic migration in `database/migrations/versions/` is the single source of the schema. `database/schema.sql` is a readable PostgreSQL reference copy of the same tables and is not executed by any setup step.

Note: `telemetry_events.sensor_id` is intentionally **not** a foreign key. That lets the generator persist the required `UNKNOWN_SENSOR` edge-case row under PostgreSQL; `machine_id` remains a hard FK.

```bash
# 1. Start PostgreSQL (or use a local instance):
docker compose up -d db

# 2. From the project root, apply the migration:
python -m alembic upgrade head

# Or migrate + generate data + ensure the model in one step:
python -m backend.app.bootstrap
```

### Connection
The application uses exactly the database in `DATABASE_URL` (default `postgresql://postgres:postgres@localhost:5432/predictive_maintenance`); there is no automatic fallback. If the database is unreachable, `/health` returns `503` and `python -m backend.app.bootstrap` exits non-zero. A SQLite URL also works for a quick local look but is not required.

## Reference Seed Data
`seed_data/01_seed_reference_data.sql` loads a deterministic PostgreSQL baseline: 3 plants, 12 production lines, 10 machines, 50 sensors, 15 technicians, and 20 spare parts. Inserts use `ON CONFLICT (id) DO NOTHING`, so the script can be applied more than once.

Plant names, line IDs, technician names, and part numbers follow `backend/app/data_generation/generator.py`. Sensor IDs use the generator convention `SNS-<machine_id>-<TYPE>-01`. The 10 machines are a stable reference subset, not a replay of the generator's random serial numbers or health scores. Telemetry, failures, and work orders are not included.

```bash
psql -U postgres -d predictive_maintenance -f database/seed_data/01_seed_reference_data.sql
```

The full 100-machine dataset, including telemetry and labelled failures, still comes from:

```bash
python -m backend.app.data_generation.generator --mode starter --seed 20261022
```

