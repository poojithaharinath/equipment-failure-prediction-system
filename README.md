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
- **Language**: Python 3.11 / 3.13
- **Framework**: FastAPI (Asynchronous REST API)
- **Validation**: Pydantic v2 & Pydantic-Settings
- **ORM & Database**: SQLAlchemy 2.0 (PostgreSQL engine with automatic SQLite fallback)
- **Machine Learning**: Scikit-learn, NumPy, Pandas, Joblib
- **API Documentation**: OpenAPI / Swagger (`/docs`) & ReDoc (`/redoc`)

### Database & Migrations
- **Primary Database**: PostgreSQL 15
- **Migration Framework**: Alembic (version-controlled migration scripts)
- **Testing Database**: Seamless SQLite support for standalone zero-dependency local runs

### DevOps & Testing
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest & FastAPI TestClient

---

## 3. Project Directory Structure

```text
predictive-maintenance-system/
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/               # 9 Dedicated Views
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── PlantsPage.jsx
│   │   │   ├── MachineMonitoringPage.jsx
│   │   │   ├── PredictionsPage.jsx
│   │   │   ├── AlertsPage.jsx
│   │   │   ├── MaintenancePage.jsx
│   │   │   ├── FailureHistoryPage.jsx
│   │   │   ├── ModelEvaluationPage.jsx
│   │   │   └── DataQualityPage.jsx
│   │   ├── layouts/
│   │   │   └── AppLayout.jsx    # Sidebar and navigation
│   │   ├── services/
│   │   │   └── api.js           # Centralized Axios API client
│   │   ├── hooks/
│   │   ├── assets/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── backend/
│   ├── app/
│   │   ├── api/                 # 14 REST API Routers
│   │   ├── models/              # 15 SQLAlchemy Declarative Models
│   │   ├── schemas/             # Pydantic v2 Request/Response Schemas
│   │   ├── services/            # Business & operational logic
│   │   ├── ml/                  # ML Training, Feature Engineering & Predictor
│   │   │   ├── feature_engineering.py
│   │   │   ├── train.py
│   │   │   ├── predictor.py
│   │   │   └── saved_models/
│   │   ├── data_generation/     # Deterministic Synthetic Data Generator
│   │   │   └── generator.py
│   │   ├── validation/          # Automated Data Validation Engine
│   │   │   └── validator.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   └── main.py              # FastAPI Application Entrypoint
│   ├── tests/
│   │   └── test_api.py          # Pytest API Test Suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── database/
│   ├── migrations/              # Alembic Database Migrations
│   │   └── versions/
│   │       └── 001_initial_schema.py
│   ├── schema.sql               # Pure PostgreSQL DDL & Indices
│   ├── seed_data/
│   └── README.md
│
├── data/
│   ├── input/
│   ├── processed/               # Extracted feature matrices
│   ├── ground_truth/            # Isolated ground_truth.csv
│   └── reports/                 # validation_report.json & model_evaluation_report.json
│
├── docs/
│   ├── data_dictionary.md       # Comprehensive entity & field dictionary
│   ├── database_design.md       # ER diagrams, cardinalities & indexes
│   ├── architecture.md          # 3-tier system architecture & data flow
│   └── API_documentation.md     # Complete REST endpoints documentation
│
├── docker-compose.yml           # Multi-container orchestration
├── README.md
└── .gitignore
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

### Option A: Local Direct Execution (Recommended for Fast Testing)

#### 1. Setup Backend & Generate Data
```bash
# 1. Run database migration (Alembic)
python -m alembic upgrade head

# 2. Run deterministic synthetic data generator
python -m backend.app.data_generation.generator

# 3. Train Machine Learning Models
python -m backend.app.ml.train

# 4. Start FastAPI Backend Server
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API and Swagger docs will be live at `http://localhost:8000/docs`.

#### 2. Setup & Run React Frontend
```bash
cd frontend
npm install
npm run dev
```
The frontend dashboard will be live at `http://localhost:5173`.

#### 3. Run Automated Tests
```bash
python -m pytest backend/tests/test_api.py -v
```

---

### Option B: Full Docker Compose Execution (PostgreSQL + Backend + Frontend)

```bash
# Start all three services (PostgreSQL 15, FastAPI, React Nginx)
docker-compose up --build -d

# Check running services
docker-compose ps
```
- Frontend Dashboard: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/docs`
- PostgreSQL: Port `5432`

---

## 10. Reproducibility Verification

To verify that the synthetic data generator is strictly reproducible:

```bash
# Run the generator
python -m backend.app.data_generation.generator

# Verify SHA-256 Checksum of Ground Truth
python -c "import hashlib; print(hashlib.sha256(open('data/ground_truth/ground_truth.csv', 'rb').read()).hexdigest())"
```
The resulting dataset checksum will match identically across repeated executions with seed `20261022`.
