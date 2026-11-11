import pytest
from datetime import datetime
from backend.app.core.database import SessionLocal
from backend.app.models.machine import Machine
from backend.app.ml.feature_engineering import FeatureExtractor, FEATURE_COLUMNS
from backend.app.ml.predictor import FailurePredictor

def test_feature_extraction():
    db = SessionLocal()
    try:
        extractor = FeatureExtractor(db)
        machine = db.query(Machine).first()
        assert machine is not None

        features = extractor.extract_features_for_machine_at_time(machine, datetime.utcnow())
        for col in FEATURE_COLUMNS:
            assert col in features, f"Feature column {col} missing from extraction"
            assert isinstance(features[col], (int, float))
    finally:
        db.close()

def test_failure_predictor_inference():
    db = SessionLocal()
    try:
        predictor = FailurePredictor(db)
        machine = db.query(Machine).first()
        assert machine is not None

        res = predictor.predict_for_machine(machine.id)
        assert "failure_probability_pct" in res
        assert 0.0 <= res["failure_probability_pct"] <= 100.0
        assert res["risk_category"] in ["Low Risk", "Medium Risk", "High Risk"]
        assert "contributing_factors" in res
        assert isinstance(res["contributing_factors"], list)
        assert "recommendation" in res
        assert len(res["recommendation"]) > 0
    finally:
        db.close()

