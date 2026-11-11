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
```bash
# 1. Start PostgreSQL container:
docker-compose up -d db

# 2. Apply PostgreSQL schema directly:
docker exec -i postgres_pm psql -U postgres -d predictive_maintenance < database/schema.sql

# 3. Or apply via Alembic:
cd backend
alembic upgrade head
```

### Flexible Development:
The application dynamically checks `DATABASE_URL`. If a PostgreSQL database is reachable, it uses PostgreSQL. If not, it defaults to the SQLite database `backend/predictive_maintenance.db` so the entire pipeline runs immediately on any local machine.
