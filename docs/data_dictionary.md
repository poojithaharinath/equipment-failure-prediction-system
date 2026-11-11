# Data Dictionary — AI-Based Predictive Maintenance System

This document outlines all database entities, attributes, primary/foreign keys, physical units, data types, and permitted values.

---

## 1. Plants (`plants`)
Industrial facilities housing multiple production lines.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(32) | NO | PK | Plant identifier | `PLT-001` |
| `name` | VARCHAR(128) | NO | | Facility display name | `Detroit Advanced Manufacturing Hub` |
| `code` | VARCHAR(32) | NO | UNIQUE | Unique site identifier | `DAM-01` |
| `location` | VARCHAR(255) | NO | | City, region, country | `Detroit, MI, USA` |
| `capacity_mw` | NUMERIC(10,2) | NO | Default 0.00 | Total electrical capacity (MW) | `45.00` |
| `commissioning_date` | DATE | NO | | Operational start date | `2021-03-15` |
| `status` | VARCHAR(32) | NO | Default 'ACTIVE' | Operational status (`ACTIVE`, `INACTIVE`, `MAINTENANCE`) | `ACTIVE` |
| `created_at` | TIMESTAMP | NO | Default CURRENT | Record timestamp | `2026-08-12 00:00:00` |
| `updated_at` | TIMESTAMP | NO | Default CURRENT | Last modification timestamp | `2026-11-10 23:59:59` |

---

## 2. Production Lines (`production_lines`)
Manufacturing segments within a plant.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(64) | NO | PK | Line identifier | `LINE-PLT-001-001` |
| `plant_id` | VARCHAR(32) | NO | FK (`plants.id`) | Owning plant ID | `PLT-001` |
| `name` | VARCHAR(128) | NO | | Production line name | `Detroit Line 1 - Machining` |
| `line_number` | INTEGER | NO | UNIQUE (`plant_id`, `line_number`) | Line sequence index | `1` |
| `line_type` | VARCHAR(64) | NO | | Process classification (`MACHINING`, `ASSEMBLY`, `HYDRAULIC_PRESSING`, `PACKAGING`) | `MACHINING` |
| `target_units_per_hour` | INTEGER | NO | Default 100 | Rated hourly output | `120` |
| `status` | VARCHAR(32) | NO | Default 'OPERATIONAL' | Operating state (`OPERATIONAL`, `DEGRADED`, `STOPPED`) | `OPERATIONAL` |
| `created_at` | TIMESTAMP | NO | | Creation timestamp | `2026-08-12 00:00:00` |
| `updated_at` | TIMESTAMP | NO | | Modification timestamp | `2026-11-10 23:59:59` |

---

## 3. Machines (`machines`)
Industrial equipment and assets being monitored.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(96) | NO | PK | Asset identifier | `MCH-LINE-PLT-001-001-001` |
| `line_id` | VARCHAR(64) | NO | FK (`production_lines.id`) | Assigned line ID | `LINE-PLT-001-001` |
| `name` | VARCHAR(128) | NO | | Machine title | `CNC Milling #001` |
| `machine_type` | VARCHAR(64) | NO | | Equipment category (`CNC_MILLING`, `HYDRAULIC_PRESS`, `ROBOTIC_ARM`, `COMPRESSOR`, `CONVEYOR`, `TURBINE`) | `CNC_MILLING` |
| `model_number` | VARCHAR(64) | NO | | OEM model designator | `MDL-CNC-482` |
| `serial_number` | VARCHAR(64) | NO | UNIQUE | Factory serial number | `SN-84918204` |
| `installation_date` | DATE | NO | | Commissioning date | `2023-05-18` |
| `criticality` | VARCHAR(32) | NO | Default 'MEDIUM' | Impact priority (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) | `CRITICAL` |
| `health_score` | NUMERIC(5,2) | NO | Default 100.00 | Real-time health (0.00 - 100.00) | `94.50` |
| `status` | VARCHAR(32) | NO | Default 'OPERATIONAL' | Asset condition (`OPERATIONAL`, `DEGRADED`, `MAINTENANCE`, `FAILED`, `OFFLINE`) | `OPERATIONAL` |
| `operating_hours` | NUMERIC(10,2) | NO | Default 0.00 | Accumulated operational run hours | `6420.50` |
| `created_at` | TIMESTAMP | NO | | Creation timestamp | `2026-08-12 00:00:00` |
| `updated_at` | TIMESTAMP | NO | | Modification timestamp | `2026-11-10 23:59:59` |

---

## 4. Sensors (`sensors`)
IoT measurement devices mounted on machines.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(128) | NO | PK | Sensor identifier | `SNS-MCH-LINE-PLT-001-001-001-TEMP-01` |
| `machine_id` | VARCHAR(96) | NO | FK (`machines.id`) | Host machine ID | `MCH-LINE-PLT-001-001-001` |
| `name` | VARCHAR(128) | NO | | Sensor label | `CNC Milling #001 Bearing Temperature Sensor` |
| `sensor_type` | VARCHAR(32) | NO | | Physical domain (`TEMPERATURE`, `VIBRATION`, `PRESSURE`, `CURRENT`, `RPM`) | `TEMPERATURE` |
| `unit` | VARCHAR(32) | NO | | Engineering unit (`Celsius`, `mm/s`, `Bar`, `Amperes`, `RPM`) | `Celsius` |
| `sampling_frequency_hz` | NUMERIC(6,2) | NO | Default 1.00 | Sampling frequency in Hertz | `1.00` |
| `min_threshold` | NUMERIC(10,2) | NO | | Lower operational tolerance | `20.00` |
| `max_threshold` | NUMERIC(10,2) | NO | | Upper operational threshold | `95.00` |
| `status` | VARCHAR(32) | NO | Default 'ACTIVE' | Sensor state (`ACTIVE`, `FAULTY`, `CALIBRATING`, `OFFLINE`) | `ACTIVE` |
| `last_calibrated_at` | TIMESTAMP | YES | | Calibration timestamp | `2026-09-14 10:00:00` |

---

## 5. Telemetry Events (`telemetry_events`)
Time-series sensor telemetry data.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(160) | NO | PK | Telemetry event ID | `TEL-SNS-...-20261022143000` |
| `sensor_id` | VARCHAR(128) | NO | FK (`sensors.id`) | Emitting sensor ID | `SNS-MCH-...-TEMP-01` |
| `machine_id` | VARCHAR(96) | NO | FK (`machines.id`) | Host machine ID | `MCH-...` |
| `timestamp` | TIMESTAMP | NO | Indexed | Time of measurement | `2026-10-22 14:30:00` |
| `value` | NUMERIC(12,4) | NO | | Calibrated reading | `74.8000` |
| `raw_value` | NUMERIC(12,4) | NO | | Unfiltered sensor reading | `74.8000` |
| `unit` | VARCHAR(32) | NO | | Measurement unit | `Celsius` |
| `is_anomaly` | BOOLEAN | NO | Default FALSE | Out of threshold / anomaly indicator | `FALSE` |
| `anomaly_score` | NUMERIC(6,4) | NO | Default 0.0000 | Deviation intensity (0.0000 - 1.0000) | `0.0000` |

---

## 6. Operating Shifts (`operating_shifts`)
Shift operations schedule and supervisors.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(64) | NO | PK | Shift identifier | `SHF-PLT-001-20261022-MORN` |
| `plant_id` | VARCHAR(32) | NO | FK (`plants.id`) | Plant ID | `PLT-001` |
| `shift_name` | VARCHAR(64) | NO | | Shift name | `Morning Shift` |
| `shift_code` | VARCHAR(32) | NO | | Code (`SHF-MORN`, `SHF-AFTN`, `SHF-NGHT`) | `SHF-MORN` |
| `start_time` | TIMESTAMP | NO | | Shift start | `2026-10-22 06:00:00` |
| `end_time` | TIMESTAMP | NO | | Shift end | `2026-10-22 14:00:00` |
| `shift_supervisor` | VARCHAR(128) | NO | | Shift supervisor in charge | `John Davis` |
| `operating_mode` | VARCHAR(32) | NO | Default 'FULL_CAPACITY' | Facility operating mode | `FULL_CAPACITY` |

---

## 7. Technicians (`technicians`)
Maintenance staff details and skills.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(32) | NO | PK | Technician identifier | `TECH-001` |
| `first_name` | VARCHAR(64) | NO | | First name | `Marcus` |
| `last_name` | VARCHAR(64) | NO | | Last name | `Vance` |
| `employee_code` | VARCHAR(32) | NO | UNIQUE | Corporate staff badge ID | `EMP-2026-0001` |
| `email` | VARCHAR(128) | NO | UNIQUE | Email address | `marcus.vance@industrial-pm.com` |
| `phone` | VARCHAR(32) | NO | | Contact phone | `+1-555-482-1984` |
| `specialization` | VARCHAR(64) | NO | | Skill domain (`MECHANICAL`, `ELECTRICAL`, `HYDRAULIC`, `SENSOR_CALIBRATION`, `AUTOMATION`) | `MECHANICAL` |
| `skill_level` | VARCHAR(32) | NO | Default 'SENIOR' | Competency level (`EXPERT`, `SENIOR`, `JUNIOR`) | `EXPERT` |
| `status` | VARCHAR(32) | NO | Default 'AVAILABLE' | Availability (`AVAILABLE`, `ASSIGNED`, `ON_LEAVE`) | `AVAILABLE` |

---

## 8. Parts (`parts`)
Spare components inventory.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(32) | NO | PK | Part identifier | `PRT-0001` |
| `part_number` | VARCHAR(64) | NO | UNIQUE | Manufacturer part number | `SKF-6205-2RSH` |
| `name` | VARCHAR(128) | NO | | Description | `Deep Groove Ball Bearing 25x52x15mm` |
| `category` | VARCHAR(64) | NO | | Part category (`BEARING`, `SEAL`, `MOTOR`, `SENSOR`, `FILTER`, `VALVE`) | `BEARING` |
| `unit_cost` | NUMERIC(10,2) | NO | | Unit cost in USD | `45.00` |
| `stock_quantity` | INTEGER | NO | Default 0 | In-stock quantity | `40` |
| `minimum_reorder_level`| INTEGER | NO | Default 5 | Restock trigger threshold | `10` |
| `manufacturer` | VARCHAR(128) | NO | | Supplier / OEM | `SKF Industrial` |
| `lead_time_days` | INTEGER | NO | Default 7 | Procurement lead time in days | `5` |

---

## 9. Maintenance Work Orders (`maintenance_work_orders`)
Work orders scheduled or executed on machinery.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(32) | NO | PK | Work Order ID | `WO-2026-000001` |
| `machine_id` | VARCHAR(96) | NO | FK (`machines.id`) | Machine target | `MCH-...` |
| `priority` | VARCHAR(32) | NO | Default 'MEDIUM' | Priority (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) | `CRITICAL` |
| `work_order_type` | VARCHAR(32) | NO | | Type (`PREVENTIVE`, `CORRECTIVE`, `EMERGENCY`, `INSPECTION`) | `CORRECTIVE` |
| `status` | VARCHAR(32) | NO | Default 'PENDING' | Status (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`) | `COMPLETED` |
| `description` | TEXT | NO | | Description of repair task | `Replace spalled ball bearing` |
| `root_cause` | TEXT | YES | | Diagnostic findings | `Bearing fatigue spalling` |
| `scheduled_start_time` | TIMESTAMP | NO | | Scheduled time | `2026-10-14 10:00:00` |
| `actual_start_time` | TIMESTAMP | YES | | Actual work start | `2026-10-14 10:15:00` |
| `actual_end_time` | TIMESTAMP | YES | | Actual work completion | `2026-10-14 14:45:00` |
| `lead_technician_id` | VARCHAR(32) | YES | FK (`technicians.id`) | Lead engineer | `TECH-001` |
| `downtime_minutes` | INTEGER | NO | Default 0 | Total machine downtime | `270` |
| `cost` | NUMERIC(12,2) | NO | Default 0.00 | Total repair cost in USD | `625.00` |

---

## 10. Failure Events (`failure_events`)
Ground truth confirmed equipment breakdown events.

| Column | Type | Nullable | Key / Constraint | Description | Example |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | VARCHAR(32) | NO | PK | Failure record ID | `FAIL-2026-000001` |
| `machine_id` | VARCHAR(96) | NO | FK (`machines.id`) | Machine identifier | `MCH-...` |
| `failure_timestamp` | TIMESTAMP | NO | Indexed | Moment of failure | `2026-10-14 09:30:00` |
| `failure_type` | VARCHAR(64) | NO | Indexed | Failure mode (`BEARING_WEAR`, `OVERHEATING`, `HYDRAULIC_LEAK`, `MOTOR_BURNOUT`, `SENSOR_DRIFT`, `MECHANICAL_JAM`) | `BEARING_WEAR` |
| `severity` | VARCHAR(32) | NO | Default 'CRITICAL' | Failure impact (`CRITICAL`, `SEVERE`, `MODERATE`) | `CRITICAL` |
| `pre_warning_lead_time_hours` | NUMERIC(6,2) | NO | Default 0.00 | Hours telemetry showed anomaly prior to trip | `36.00` |
| `root_cause` | TEXT | NO | | Root cause analysis | `Inner raceway fatigue` |
| `downtime_hours` | NUMERIC(6,2) | NO | Default 0.00 | Operational hours lost | `5.50` |
| `work_order_id` | VARCHAR(32) | YES | FK (`maintenance_work_orders.id`) | Associated repair order | `WO-2026-000001` |

---

## 11. Additional Audit & Quality Tables
- **`data_validation_exceptions`**: Stores invalid records and edge cases with issue type, severity, entity ID, and resolution status.
- **`machine_health_audit_trail`**: Complete chronological audit log of all health score and status changes per machine.
- **`failure_prediction_logs`**: Historical machine failure predictions, risk categories, and JSON-encoded explanatory factor weights.
- **`work_order_parts`**: Many-to-many bridge linking work orders to parts and recording unit cost at time of repair.
- **`work_order_technicians`**: Many-to-many bridge recording labor hours spent by technicians on each work order.
