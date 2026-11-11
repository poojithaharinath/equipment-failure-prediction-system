# REST API Documentation — Predictive Maintenance System

## Base URL & Interactive Docs
- **Base URL**: `http://localhost:8000/api`
- **Swagger Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **ReDoc Interactive Documentation**: `http://localhost:8000/redoc`

---

## 1. System & Health Endpoints

### `GET /health`
Runs `SELECT 1` against the configured database and loads the model artifact. Returns `200` when both succeed, otherwise `503` with `"status": "UNHEALTHY"` and an `error` on the failing component.
```json
{
  "status": "HEALTHY",
  "database": {"backend": "postgresql", "status": "CONNECTED"},
  "model": {"status": "LOADED", "path": "/app/backend/app/ml/saved_models/failure_prediction_rf.joblib", "model_type": "RandomForestClassifier", "trained_at": "..."},
  "version": "1.0.0"
}
```

Prediction endpoints return `503` with `"error": "MODEL_NOT_AVAILABLE"` when the model artifact is missing; there is no heuristic fallback.

---

## 2. Dashboard Analytics

### `GET /api/dashboard/stats`
Returns aggregated operational metrics across all plants, machines, health distribution, recent alerts, and machines requiring immediate attention.

**Response (200 OK):**
```json
{
  "total_plants": 3,
  "total_production_lines": 12,
  "total_machines": 100,
  "healthy_machines": 86,
  "medium_risk_machines": 50,
  "high_risk_machines": 12,
  "failed_machines": 2,
  "average_machine_health": 88.4,
  "health_distribution": [
    { "range": "0-20%", "count": 2 },
    { "range": "21-40%", "count": 4 },
    { "range": "41-60%", "count": 8 },
    { "range": "61-80%", "count": 18 },
    { "range": "81-100%", "count": 68 }
  ],
  "recent_alerts": [...],
  "machines_requiring_attention": [...]
}
```

---

## 3. Plants & Production Lines

### `GET /api/plants`
List all 3 industrial facilities.

### `GET /api/plants/{plant_id}/lines`
List production lines within a plant.

### `GET /api/production-lines/{line_id}/machines`
List machines installed along a specific production line.

---

## 4. Machines & Telemetry

### `GET /api/machines`
List machines with pagination and filtering.
- Query parameters:
  - `page`: int (default 1)
  - `page_size`: int (default 20)
  - `search`: string
  - `plant_id`: string
  - `line_id`: string
  - `status`: string (`OPERATIONAL`, `DEGRADED`, `MAINTENANCE`, `FAILED`)
  - `criticality`: string (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
  - `risk_category`: string (`High Risk`, `Medium Risk`, `Low Risk`)

### `GET /api/machines/{machine_id}`
Returns machine asset details, health score, operating hours, and active risk score.

### `GET /api/machines/{machine_id}/sensors`
Returns list of all 5 sensors mounted on the machine along with threshold parameters and latest reading.

### `GET /api/telemetry/machine/{machine_id}/chart-data`
Returns time-series telemetry points for multi-sensor visualization.
- Query parameters:
  - `limit`: int (default 60)

**Response (200 OK):**
```json
{
  "machine_id": "MCH-LINE-PLT-001-001-001",
  "points": [
    {
      "timestamp": "2026-11-10T22:00:00",
      "formatted_time": "11/10 22:00",
      "temperature": 68.4,
      "vibration": 1.95,
      "pressure": 22.4,
      "current": 24.8,
      "rpm": 1645.0,
      "is_anomaly": false
    }
  ],
  "thresholds": {
    "temperature": { "min": 20.0, "max": 95.0, "unit": "Celsius" },
    "vibration": { "min": 0.0, "max": 6.0, "unit": "mm/s" },
    "pressure": { "min": 8.0, "max": 40.0, "unit": "Bar" },
    "current": { "min": 10.0, "max": 50.0, "unit": "Amperes" },
    "rpm": { "min": 1000.0, "max": 2200.0, "unit": "RPM" }
  }
}
```

---

## 5. Failure Predictions

### `GET /api/predictions`
List machine-wise failure probabilities.
- Parameters: `risk_category`, `sort_by` (`probability_desc`, `health_asc`), `limit`.

### `GET /api/predictions/machine/{machine_id}`
Returns 24-hour failure prediction, risk category, and explainable AI contributing factors.

**Response (200 OK):**
```json
{
  "machine_id": "MCH-LINE-PLT-001-001-001",
  "machine_name": "CNC Milling #001",
  "failure_probability_pct": 82.5,
  "risk_category": "High Risk",
  "health_score": 29.8,
  "contributing_factors": [
    {
      "factor": "Vibration ramp rate",
      "feature": "vibration_trend",
      "current_value": 2.15,
      "baseline_value": 1.0,
      "unit": "x",
      "severity_impact_pct": 42.0,
      "detail": "Vibration ramp rate is 2.15x (vs normal 1.0x, +115.0% deviation)"
    }
  ],
  "recommendation": "CRITICAL: Immediate spindle bearing inspection required."
}
```

### `POST /api/predictions/batch-predict`
Re-runs failure probability inferences across all 100 machines.

---

## 6. Maintenance Work Orders

### `GET /api/work-orders`
List work orders with pagination and filtering by `status`, `priority`, `machine_id`.

### `POST /api/work-orders`
Creates a new work order and allocates parts from inventory.
**Request Body:**
```json
{
  "machine_id": "MCH-LINE-PLT-001-001-001",
  "priority": "CRITICAL",
  "work_order_type": "CORRECTIVE",
  "description": "Emergency spindle bearing replacement",
  "scheduled_start_time": "2026-11-11T14:00:00",
  "lead_technician_id": "TECH-001",
  "parts_to_use": [
    { "part_id": "PRT-0001", "quantity": 1 }
  ]
}
```

### `PATCH /api/work-orders/{wo_id}`
Updates status (`COMPLETED`, `IN_PROGRESS`), records downtime minutes and total cost.

---

## 7. Data Quality & Edge Case Validation

### `POST /api/validation/run`
Executes automated integrity suite and tests all 5 negative scenarios.

### `GET /api/validation/report`
Returns data quality report summary.

### `GET /api/alerts`
Returns a paginated list of validation exceptions (unknown sensor events, out-of-range readings, etc.), newest first.
- Parameters: `severity`, `resolution_status`, `issue_type`, `page` (default 1), `page_size` (default 50, max 200).
- Response: `{"items": [...], "total", "page", "page_size", "total_pages"}`, the same shape as `GET /api/validation/exceptions`.

### `PATCH /api/alerts/{issue_id}`
Updates resolution status (`RESOLVED`, `UNDER_REVIEW`, `DISMISSED`).

---

## 8. Machine Learning Model Evaluation

### `GET /api/model-evaluation`
Returns accuracy, precision, recall, F1-score, ROC-AUC, confusion matrix, and feature importances.

### `POST /api/model-evaluation/train`
Triggers full chronological retraining of Random Forest Champion and Logistic Regression Baseline.

---

## 9. Additional Endpoints

| Method | Path | Notes |
|---|---|---|
| GET | `/api/sensors`, `/api/sensors/{sensor_id}` | Sensor catalog |
| GET | `/api/technicians` | Technician list (filter: specialization, status) |
| GET | `/api/parts` | Parts inventory (filter: category, low_stock_only) |
| GET | `/api/failure-events` | Paginated failure history |
| GET | `/api/failure-events/summary` | Failure-mode aggregates |
| GET | `/api/alerts/metrics` | Alert counts by type/severity |
| GET | `/api/machines/{id}/health-history` | Status/health audit trail (`limit`) |
| PATCH | `/api/machines/{id}` | Update machine fields / restore |
| GET | `/api/telemetry` | Paginated telemetry |
| GET | `/api/telemetry/machine/{id}/latest` | Latest reading per sensor |
| POST | `/api/telemetry` | Ingest a telemetry event |
| GET | `/api/validation/exceptions` | Paginated validation exceptions |
| PATCH | `/api/validation/exceptions/{id}` | Resolve an exception |
| GET | `/api/production-lines` | Production line list |
| GET | `/api/plants/{id}`, `/api/production-lines/{id}` | Detail GETs |

