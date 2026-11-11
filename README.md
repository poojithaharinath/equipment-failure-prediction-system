# AI-Based Industrial Predictive Maintenance System

A production-grade, end-to-end **AI-Based Predictive Maintenance System** engineered to forecast industrial equipment failures using machine telemetry, operating conditions, and maintenance histories.

Built with a clean architectural separation among Frontend, Backend, Database, Data Science, and Documentation tiers.

---

## 1. System Capabilities & Highlights

- **Multi-Facility Topology**: 3 Industrial Plants, 12 Production Lines, 100 Monitored Machines, and 500 Active IoT Sensors.
- **Physical Sensor Domains**: High-frequency monitoring of **Temperature** (°C), **Vibration** (mm/s), **Pressure** (Bar), **Motor Current** (A), and **Rotational Speed** (RPM).
- **Advanced Machine Learning**: Supervised Random Forest Classifier (Champion) evaluated against Logistic Regression (Baseline) predicting equipment failure probability within the **next 24 hours**.
- **Explainable AI (XAI)**: Deconstructs failure risk scores into human-understandable engineering factors (e.g. vibration ramp rate deviation, thermal spikes, current instability) with targeted corrective recommendations.
- **Data Quality & Edge Cases**: Explicit detection, logging, and resolution tracking for all 5 required industrial edge cases without silent data deletion.
- **Maintenance Lifecycle**: Automated and manual work orders, technician assignments, replacement parts stock allocation, and machine downtime tracking.
- **Modern Responsive Dashboard**: Industrial monitoring UI with 9 dedicated pages built with React, Vite, Tailwind CSS, Recharts, and Lucide icons.

---

## 2. Technology Stack

### Frontend
- **Framework**: React.js 18
- **Build Tool**: Vite 6
- **Styling**: Tailwind CSS
- **Visualizations**: Recharts (Multi-sensor charts, distribution bar charts, breakdown pie charts)
- **Icons**: Lucide React
- **API Client**: Axios

### Backend
- **Language**: Python 3.11+ (Dockerfile uses 3.11; verified locally on 3.13)
- **Framework**: FastAPI (Asynchronous REST API)
- **Validation**: Pydantic v2 & Pydantic-Settings
- **ORM & Database**: SQLAlchemy 2.0 on PostgreSQL
- **Machine Learning**: Scikit-learn, NumPy, Pandas, Joblib
- **API Documentation**: OpenAPI / Swagger (`/docs`) & ReDoc (`/redoc`)

### Database & Migrations
- **Primary Database**: PostgreSQL 15
- **Migration Framework**: Alembic (single source of the schema; `database/schema.sql` is a readable reference copy)

### DevOps & Testing
- **Containerization**: Docker & Docker Compose (optional; local PostgreSQL is enough)
- **Testing**: Pytest & FastAPI TestClient (independent throwaway database per run)

---

## 3. Project Directory Structure

```text
<repo>/
├── backend/
│   ├── app/
│   │   ├── api/                 # 14 REST API routers
│   │   ├── core/                # config.py (settings, path resolution), database.py (engine, health check, migrations)
│   │   ├── data_generation/
│   │   │   └── generator.py     # Deterministic synthetic data generator (seed 20261022)
│   │   ├── ml/
│   │   │   ├── feature_engineering.py
│   │   │   ├── train.py         # Random Forest (champion) vs Logistic Regression (baseline)
│   │   │   ├── predictor.py     # Inference + explainability
│   │   │   └── saved_models/
│   │   │       └── failure_prediction_rf.joblib   # Trained model (committed)
│   │   ├── models/              # 15 SQLAlchemy models
│   │   ├── schemas/             # Pydantic v2 request/response schemas
│   │   ├── services/            # machine_service.py, maintenance_service.py
│   │   ├── validation/
│   │   │   └── validator.py     # Data validation / five edge cases
│   │   ├── bootstrap.py         # Migrate + generate data if empty + train model if missing
│   │   └── main.py              # FastAPI entrypoint (/health, CORS, routers)
│   ├── tests/
│   │   ├── conftest.py          # Creates an independent test database per run
│   │   ├── test_api.py
│   │   ├── test_ml.py
│   │   ├── test_reproducibility.py
│   │   └── test_validation.py
│   ├── requirements.txt         # Pinned versions (scikit-learn must match the saved model)
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # MetricCard.jsx, StatusBadge.jsx
│   │   ├── hooks/               # useApi.js
│   │   ├── layouts/             # AppLayout.jsx (sidebar & navigation)
│   │   ├── pages/               # 9 pages: Dashboard, Plants, MachineMonitoring, Predictions, Alerts,
│   │   │                        #          Maintenance, FailureHistory, ModelEvaluation, DataQuality
│   │   ├── services/api.js      # Axios API client
│   │   ├── utils/formatters.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json / package-lock.json
│   ├── vite.config.js           # Dev proxy /api -> http://localhost:8000
│   ├── tailwind.config.js, postcss.config.js
│   ├── nginx.conf
│   └── Dockerfile
├── database/
│   ├── migrations/              # Alembic (applied schema)
│   │   ├── env.py
│   │   └── versions/001_initial_schema.py
│   ├── seed_data/01_seed_reference_data.sql
│   ├── schema.sql               # PostgreSQL DDL reference (schema is applied by Alembic)
│   └── README.md
├── data/
│   ├── ground_truth/ground_truth.csv
│   └── reports/                 # model_evaluation_report.json, validation_report.json
├── docs/
│   ├── API_documentation.md
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── database_design.md
│   ├── data_generation_instructions.md
│   └── model_training_instructions.md
├── alembic.ini
├── docker-compose.yml           # Optional: PostgreSQL + backend + frontend
├── .gitattributes               # LF line endings on every OS
├── .gitignore
├── .dockerignore
└── README.md
```

---

## 4. Database Entities & Conventions

The database defines **10 primary entities** and **5 bridge/audit tables**:

1. **`plants`**: ID: `PLT-001`
2. **`production_lines`**: ID: `LINE-PLT-001-001`
3. **`machines`**: ID: `MCH-LINE-PLT-001-001-001`
4. **`sensors`**: ID: `SNS-MACHINE-ID-TEMP-01`
5. **`telemetry_events`**: ID: `TEL-SENSOR-ID-TIMESTAMP`
6. **`operating_shifts`**: ID: `SHF-PLT-001-20261022-MORN`
7. **`technicians`**: ID: `TECH-001`
8. **`parts`**: ID: `PRT-0001`
9. **`maintenance_work_orders`**: ID: `WO-2026-000001`
10. **`failure_events`**: ID: `FAIL-2026-000001`
11. **`work_order_parts`**: Many-to-many bridge linking work orders to parts and unit costs.
12. **`work_order_technicians`**: Many-to-many bridge tracking labor hours per technician.
13. **`data_validation_exceptions`**: Storage for edge cases (`VAL-TYPE-TIMESTAMP-COUNTER`).
14. **`machine_health_audit_trail`**: Complete history of machine status and health transitions.
15. **`failure_prediction_logs`**: Historical prediction log with JSON explanatory factor weights.

---

## 5. Synthetic Data Generator

- **Fixed Random Seed**: `20261022` (guarantees 100% deterministic reproducibility).
- **Scale**:
  - 3 Plants (Detroit, Stuttgart, Yokohama)
  - 12 Production Lines (Machining, Assembly, Hydraulic Pressing, Packaging)
  - 100 Industrial Machines (CNC Milling, Hydraulic Press, Robotic Arm, Compressor, Conveyor, Turbine)
  - 500 Active Sensors (5 per machine: Temperature, Vibration, Pressure, Current, RPM)
  - 90 Days of Historical Telemetry Timeline
  - 139 Labelled Machine Breakdowns & Associated Maintenance Work Orders
- **Modes**:
  - `starter`: Generates ~49,025 representative telemetry events for fast development, instant queries, and responsive UI.
  - `full`: Generates 1 to 3 million high-frequency telemetry events using the exact same generation logic.

---

## 6. The Five Negative Scenarios & Data Validation

The system does not silently ignore or delete invalid data. All anomalies are flagged, recorded in `data_validation_exceptions`, and made actionable via the dashboard:

1. **Unknown Sensor Telemetry**: Sensor ID referenced in telemetry has no record in the `sensors` table (`UNKNOWN_SENSOR`).
2. **Impossible Sensor Readings & Invalid Units**: Temperature = 999°C, Vibration = -22.5 mm/s, Unit = "Fahrenheit" for electrical current (`OUT_OF_RANGE_READING`, `INVALID_UNIT`).
3. **Failure Without Warning**: Mechanical jam or sudden spindle seizure occurring with 0.0 hours warning lead time (`FAILURE_WITHOUT_WARNING`).
4. **Inverted Maintenance Timestamps**: Maintenance work order where `actual_end_time < actual_start_time` (`INVALID_MAINTENANCE_TIME`).
5. **Missing Telemetry Masked as Zero**: Sensor drop/disconnects represented incorrectly as exact `0.000` (`ZERO_INSTEAD_OF_MISSING`).

---

## 7. Machine Learning & Explainable AI

- **Target**: Predict whether an industrial machine will experience failure within the **next 24 hours**.
- **No Data Leakage**: Chronological split (75% early train, 25% holdout test). Ground truth labels are stored in `data/ground_truth/ground_truth.csv` and never leaked into feature extraction.
- **Engineered Features**:
  1. `avg_temperature_24h`
  2. `max_temperature_24h`
  3. `avg_vibration_24h`
  4. `vibration_trend` (6h to 24h ratio)
  5. `pressure_fluctuation_24h` (std dev)
  6. `current_fluctuation_24h` (std dev)
  7. `avg_rpm_24h`
  8. `operating_hours`
  9. `missing_sensor_count`
  10. `previous_failure_count`
  11. `previous_maintenance_count`
- **Performance**:
  - **Random Forest (Champion)**: Accuracy **93.72%**, Precision **94.20%**, Recall **76.47%**, F1-Score **84.42%**, ROC-AUC **93.68%**.
  - **Logistic Regression (Baseline)**: Accuracy **94.63%**, F1-Score **87.07%**.
- **Risk Classification**:
  - **Low Risk**: Failure probability < 35%
  - **Medium Risk**: Failure probability 35% – 70%
  - **High Risk**: Failure probability > 70%
- **Explainability**: Every prediction produces weighted contributing factors (e.g., *Current fluctuation +31.2% impact*, *Vibration ramp +11.8% impact*) with specific engineering recommendations.

---

## 8. Dashboard Pages

1. **Executive Dashboard**: KPI summary, health score distribution bar chart, recent alerts stream, and immediate attention machine callouts.
2. **Plant & Production Line Management**: Plant topology, capacity MW, line types, and machine lists.
3. **Machine Monitoring**: Live sensor cards with bounds indicators, historical multi-sensor chart with anomaly dots, and status transition audit history.
4. **Failure Prediction**: Machine risk ranking, 24h failure probability percentage, explainable factor weights, and on-demand batch inference.
5. **Alerts & Exceptions**: Filterable exceptions table for all 5 negative scenarios with inline resolution actions.
6. **Maintenance Management**: Work orders tracking, interactive modal to create work orders, allocate replacement parts, and record repair downtime.
7. **Failure History**: Historical breakdowns log, failure mode pie chart, and downtime analytics.
8. **Model Performance**: ML metrics cards, 2x2 confusion matrix grid, model comparison table, and feature importances chart.
9. **Data Quality**: Automated validation engine report and live validation suite runner.

---

## 9. Quickstart & Execution Instructions

The repository is self-contained: it ships the Alembic migration, the deterministic data generator, reference seed SQL, and the trained model (`backend/app/ml/saved_models/failure_prediction_rf.joblib`). No pre-existing database is needed.

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### Option A: Local Setup with PostgreSQL (Python 3.11–3.13, Node 20+, PostgreSQL 15+)

All commands run from the project root.

```bash
# 1. Create an empty PostgreSQL database
createdb -U postgres predictive_maintenance

# 2. Configuration (edit DATABASE_URL if your credentials differ)
cp backend/.env.example backend/.env        # PowerShell: Copy-Item backend/.env.example backend/.env

# 3. Backend dependencies (a virtual environment is recommended)
pip install -r backend/requirements.txt

# 4. Apply the migration, generate the seeded dataset, and ensure the model exists
python -m backend.app.bootstrap

# 5. Start the API (http://localhost:8000/docs, health: http://localhost:8000/health)
python -m uvicorn backend.app.main:app --port 8000
```

In a second terminal:
```bash
cd frontend
npm ci
npm run dev                                  # http://localhost:5173 (proxies /api to :8000)
```

### Option B (optional): Docker Compose

Docker is not required; it is a one-command alternative that also provides PostgreSQL.

```bash
docker compose up --build -d
docker compose ps          # wait until backend_pm is "healthy" (first start generates data, ~1-2 min)
```

The backend container runs `python -m backend.app.bootstrap` before starting the API. Frontend: `http://localhost:5173`, API: `http://localhost:8000/docs`, PostgreSQL: `localhost:5432` (`postgres` / `postgres`, database `predictive_maintenance`). Reset with `docker compose down -v`.

### Tests

```bash
python -m pytest backend/tests -v
```

Tests never use the application database. Each run creates a throwaway SQLite database in a temp directory, migrates it, and generates the seeded dataset (about 30 seconds). To run them against PostgreSQL instead, point `TEST_DATABASE_URL` at a separate, dedicated database:

```bash
createdb -U postgres predictive_maintenance_test
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/predictive_maintenance_test python -m pytest backend/tests -v
```

### Individual Steps

| Task | Command |
|---|---|
| Apply migrations | `python -m alembic upgrade head` |
| Regenerate data (wipes and refills tables) | `python -m backend.app.data_generation.generator --seed 20261022` |
| Retrain the model and rewrite the evaluation report | `python -m backend.app.ml.train` |
| Load the small reference seed instead of generated data | `psql -U postgres -d predictive_maintenance -f database/seed_data/01_seed_reference_data.sql` |
| Production build of the frontend | `cd frontend && npm run build` |

The application uses exactly the database in `DATABASE_URL`; there is no automatic fallback. A SQLite URL (`sqlite:///./predictive_maintenance.db`) also works for a quick look but is not required.

---

## 10. Reproducibility Verification

The generator is deterministic for seed `20261022` and writes the ground truth with LF line endings on every OS. Its SHA-256 is:

```
3372bf6731afd02e205e4d15aec385d3b0333bd2f2771531f0ed862a9aa5b704
```

`python -m pytest backend/tests/test_reproducibility.py -v` regenerates the dataset into a temp directory and checks that it is byte-for-byte identical to the committed `data/ground_truth/ground_truth.csv`.
