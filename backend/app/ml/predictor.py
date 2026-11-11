import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import joblib
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.config import settings
from backend.app.models.machine import Machine
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.audit import FailurePredictionLog, MachineHealthAuditTrail
from backend.app.ml.feature_engineering import FeatureExtractor, FEATURE_COLUMNS

logger = logging.getLogger(__name__)


class ModelNotAvailableError(RuntimeError):
    """Raised when the trained model bundle is missing or cannot be loaded."""


def load_model_bundle(model_path: Optional[str] = None) -> Dict[str, Any]:
    path = model_path or settings.model_file
    if not os.path.exists(path):
        raise ModelNotAvailableError(
            f"Trained model not found at {path}. Run `python -m backend.app.ml.train` to create it."
        )
    try:
        bundle = joblib.load(path)
    except Exception as e:
        raise ModelNotAvailableError(f"Could not load trained model from {path}: {e}") from e
    if not isinstance(bundle, dict) or bundle.get("model") is None:
        raise ModelNotAvailableError(f"Model file {path} does not contain a trained model bundle.")
    return bundle


def get_model_status() -> Dict[str, Any]:
    try:
        bundle = load_model_bundle()
    except ModelNotAvailableError as e:
        return {"status": "UNAVAILABLE", "path": settings.model_file, "error": str(e)}
    return {
        "status": "LOADED",
        "path": settings.model_file,
        "model_type": type(bundle["model"]).__name__,
        "trained_at": bundle.get("trained_at"),
    }


class FailurePredictor:
    """
    Inference and Explainable AI Service for Equipment Failure Prediction.
    Raises ModelNotAvailableError when no trained model can be loaded.
    """

    def __init__(self, db: Session, model_path: Optional[str] = None):
        self.db = db
        self.model_path = model_path or settings.model_file
        self.bundle = load_model_bundle(self.model_path)
        self.model = self.bundle["model"]
        self.feature_columns = self.bundle.get("feature_columns", FEATURE_COLUMNS)
        self.threshold_low = self.bundle.get("threshold_low", settings.RISK_THRESHOLD_LOW)
        self.threshold_high = self.bundle.get("threshold_high", settings.RISK_THRESHOLD_HIGH)
        logger.info(f"Loaded trained ML model from {self.model_path}")

    def explain_prediction(self, features: Dict[str, float], prob: float) -> Tuple[List[Dict[str, Any]], str]:
        contributing_factors = []

        # Baseline healthy references
        refs = {
            "avg_temperature_24h": (65.0, "Bearing temperature", "°C"),
            "max_temperature_24h": (68.0, "Peak temperature", "°C"),
            "avg_vibration_24h": (1.8, "Vibration level", "mm/s"),
            "vibration_trend": (1.0, "Vibration ramp rate", "x"),
            "pressure_fluctuation_24h": (1.5, "Pressure instability", "Bar"),
            "current_fluctuation_24h": (2.0, "Motor current fluctuations", "A"),
            "operating_hours": (5000.0, "Operating hours", "hrs"),
            "missing_sensor_count": (0.0, "Missing telemetry channels", "sensors"),
            "previous_failure_count": (0.0, "Prior failure events", "events"),
        }

        # Calculate deviations
        deviations = []
        for feat, val in features.items():
            if feat in refs:
                normal_val, label, unit = refs[feat]
                if feat in ["vibration_trend", "avg_vibration_24h", "avg_temperature_24h", "max_temperature_24h", "current_fluctuation_24h"]:
                    delta = (val - normal_val) / max(0.1, normal_val)
                    if delta > 0.15: # Significant upward anomaly
                        deviations.append((feat, label, val, normal_val, delta, unit))
                elif feat == "missing_sensor_count" and val > 0:
                    deviations.append((feat, label, val, 0, 1.0, unit))
                elif feat == "previous_failure_count" and val > 1:
                    deviations.append((feat, label, val, 0, 0.5, unit))

        # Sort deviations descending
        deviations.sort(key=lambda x: x[4], reverse=True)
        total_delta = sum(d[4] for d in deviations) if deviations else 1.0

        for feat, label, val, normal_val, delta, unit in deviations[:4]:
            weight_pct = round((delta / total_delta) * 100, 1) if total_delta > 0 else 25.0
            contributing_factors.append({
                "factor": label,
                "feature": feat,
                "current_value": val,
                "baseline_value": normal_val,
                "unit": unit,
                "severity_impact_pct": weight_pct,
                "detail": f"{label} is {round(val, 2)} {unit} (vs normal {normal_val} {unit}, +{round(delta*100, 1)}% deviation)"
            })

        # Recommendations based on highest contributing factors & risk
        if prob > self.threshold_high:
            if any(f["feature"] == "vibration_trend" or f["feature"] == "avg_vibration_24h" for f in contributing_factors):
                rec = "CRITICAL: Immediate spindle bearing inspection required. Reduce feed rate or shut down machine to prevent catastrophic bearing seizure."
            elif any("temperature" in f["feature"] for f in contributing_factors):
                rec = "CRITICAL: Urgent thermal investigation required. Inspect coolant circulation, heat exchanger, and motor winding temperature immediately."
            else:
                rec = "CRITICAL: High failure probability detected within next 24 hours. Dispatch emergency maintenance crew and prepare replacement parts."
        elif prob >= self.threshold_low:
            rec = "WARNING: Elevated risk parameters detected. Schedule preventive inspection at end of current shift and monitor telemetry closely."
        else:
            rec = "NORMAL: Machine telemetry within acceptable operational thresholds. Continue standard automated monitoring."

        return contributing_factors, rec

    def predict_for_machine(self, machine_id: str, as_of_time: Optional[datetime] = None) -> Dict[str, Any]:
        machine = self.db.query(Machine).filter(Machine.id == machine_id).first()
        if not machine:
            raise ValueError(f"Machine {machine_id} not found.")

        if not as_of_time:
            # Default to the most recent telemetry event timestamp in the database
            latest_tel_ts = self.db.query(func.max(TelemetryEvent.timestamp)).filter(
                TelemetryEvent.machine_id == machine_id
            ).scalar()
            as_of = latest_tel_ts or datetime.utcnow()
        else:
            as_of = as_of_time
        extractor = FeatureExtractor(self.db)
        feats = extractor.extract_features_for_machine_at_time(machine, as_of)

        X_df = pd.DataFrame([feats])[self.feature_columns]
        prob = float(self.model.predict_proba(X_df)[0][1])
        prob = min(0.9999, max(0.0001, prob))
        prob_pct = round(prob * 100.0, 2)

        if prob >= self.threshold_high:
            risk_category = "High Risk"
        elif prob >= self.threshold_low:
            risk_category = "Medium Risk"
        else:
            risk_category = "Low Risk"

        factors, recommendation = self.explain_prediction(feats, prob)

        # Log prediction to database
        log_entry = FailurePredictionLog(
            machine_id=machine.id,
            prediction_timestamp=as_of,
            target_horizon_hours=settings.PREDICTION_HORIZON_HOURS,
            failure_probability=round(prob, 4),
            risk_category=risk_category,
            contributing_factors=json.dumps(factors),
            recommendations=recommendation,
            created_at=datetime.utcnow()
        )
        self.db.add(log_entry)

        # Update machine health score dynamically
        new_health_score = round(max(5.0, 100.0 - (prob * 85.0)), 1)
        prev_health = machine.health_score
        prev_status = machine.status

        machine.health_score = new_health_score
        if risk_category == "High Risk" and machine.status == "OPERATIONAL":
            machine.status = "DEGRADED"

        # Record health audit if status or score changed significantly
        if abs(prev_health - new_health_score) >= 5.0 or prev_status != machine.status:
            audit = MachineHealthAuditTrail(
                machine_id=machine.id,
                previous_status=prev_status,
                new_status=machine.status,
                previous_health_score=prev_health,
                new_health_score=new_health_score,
                failure_probability=round(prob, 4),
                risk_category=risk_category,
                trigger_event="ML_PREDICTION_INFERENCE",
                timestamp=as_of,
                created_at=datetime.utcnow()
            )
            self.db.add(audit)

        self.db.commit()

        return {
            "machine_id": machine.id,
            "machine_name": machine.name,
            "machine_type": machine.machine_type,
            "line_id": machine.line_id,
            "prediction_timestamp": as_of.isoformat(),
            "target_horizon_hours": settings.PREDICTION_HORIZON_HOURS,
            "failure_probability_pct": prob_pct,
            "risk_category": risk_category,
            "health_score": new_health_score,
            "status": machine.status,
            "features": feats,
            "contributing_factors": factors,
            "recommendation": recommendation,
        }

    def batch_predict_all(self, as_of_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        machines = self.db.query(Machine).all()
        results = []
        for m in machines:
            res = self.predict_for_machine(m.id, as_of_time=as_of_time)
            results.append(res)
        return results
