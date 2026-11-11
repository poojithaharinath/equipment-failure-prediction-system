import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "OPERATIONAL"

def test_get_dashboard_stats():
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total_plants"] == 3
    assert data["total_production_lines"] == 12
    assert data["total_machines"] == 100
    assert len(data["health_distribution"]) == 5

def test_get_plants():
    response = client.get("/api/plants")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["code"] in ["DAM-01", "SPE-02", "YSR-03"]

def test_get_machines_pagination():
    response = client.get("/api/machines?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 100
    assert len(data["items"]) == 10

def test_get_machine_sensors():
    response = client.get("/api/machines/MCH-LINE-PLT-001-001-001/sensors")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    types = {s["sensor_type"] for s in data}
    assert types == {"TEMPERATURE", "VIBRATION", "PRESSURE", "CURRENT", "RPM"}

def test_get_telemetry_chart_data():
    response = client.get("/api/telemetry/machine/MCH-LINE-PLT-001-001-001/chart-data")
    assert response.status_code == 200
    data = response.json()
    assert "points" in data
    assert "thresholds" in data

def test_predictions_api():
    response = client.get("/api/predictions?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "failure_probability_pct" in data[0]
    assert data[0]["risk_category"] in ["Low Risk", "Medium Risk", "High Risk"]

def test_work_orders_api():
    response = client.get("/api/work-orders?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0

def test_model_evaluation_report():
    response = client.get("/api/model-evaluation")
    assert response.status_code == 200
    data = response.json()
    assert "champion_model" in data
    assert "accuracy" in data["champion_model"]

def test_validation_report():
    response = client.get("/api/validation/report")
    assert response.status_code == 200
    data = response.json()
    assert "breakdown_by_category" in data
