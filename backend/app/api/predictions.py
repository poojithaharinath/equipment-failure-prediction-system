from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.machine import Machine
from backend.app.models.audit import FailurePredictionLog
from backend.app.ml.predictor import FailurePredictor
from backend.app.schemas.entities import MachinePredictionResponse

router = APIRouter(prefix="/predictions", tags=["Failure Predictions"])

@router.get("", response_model=List[MachinePredictionResponse])
def get_all_predictions(
    risk_category: Optional[str] = Query(None, description="Filter by 'High Risk', 'Medium Risk', or 'Low Risk'"),
    sort_by: str = Query("probability_desc", description="probability_desc or health_asc"),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    predictor = None
    machines = db.query(Machine).all()
    results = []

    for m in machines:
        latest = db.query(FailurePredictionLog).filter(
            FailurePredictionLog.machine_id == m.id
        ).order_by(FailurePredictionLog.prediction_timestamp.desc()).first()

        if latest:
            import json
            factors = json.loads(latest.contributing_factors) if latest.contributing_factors else []
            res = {
                "machine_id": m.id,
                "machine_name": m.name,
                "machine_type": m.machine_type,
                "line_id": m.line_id,
                "prediction_timestamp": latest.prediction_timestamp,
                "target_horizon_hours": latest.target_horizon_hours,
                "failure_probability_pct": round(latest.failure_probability * 100.0, 2),
                "risk_category": latest.risk_category,
                "health_score": m.health_score,
                "status": m.status,
                "features": {},
                "contributing_factors": factors,
                "recommendation": latest.recommendations or "Maintain continuous telemetry monitoring."
            }
        else:
            if predictor is None:
                predictor = FailurePredictor(db)
            res = predictor.predict_for_machine(m.id)

        if risk_category and res["risk_category"] != risk_category:
            continue
        results.append(res)

    if sort_by == "probability_desc":
        results.sort(key=lambda x: x["failure_probability_pct"], reverse=True)
    elif sort_by == "health_asc":
        results.sort(key=lambda x: x["health_score"])

    return results[:limit]

@router.get("/machine/{machine_id}", response_model=MachinePredictionResponse)
def get_machine_prediction(machine_id: str, refresh: bool = False, db: Session = Depends(get_db)):
    if not db.query(Machine.id).filter(Machine.id == machine_id).first():
        raise HTTPException(status_code=404, detail=f"Machine {machine_id} not found")
    if refresh:
        return FailurePredictor(db).predict_for_machine(machine_id)

    # Check cached prediction log
    latest = db.query(FailurePredictionLog).filter(
        FailurePredictionLog.machine_id == machine_id
    ).order_by(FailurePredictionLog.prediction_timestamp.desc()).first()

    if latest:
        import json
        m = db.query(Machine).filter(Machine.id == machine_id).first()
        factors = json.loads(latest.contributing_factors) if latest.contributing_factors else []
        return {
            "machine_id": m.id,
            "machine_name": m.name,
            "machine_type": m.machine_type,
            "line_id": m.line_id,
            "prediction_timestamp": latest.prediction_timestamp,
            "target_horizon_hours": latest.target_horizon_hours,
            "failure_probability_pct": round(latest.failure_probability * 100.0, 2),
            "risk_category": latest.risk_category,
            "health_score": m.health_score,
            "status": m.status,
            "features": {},
            "contributing_factors": factors,
            "recommendation": latest.recommendations or "Continue standard monitoring."
        }
    else:
        return FailurePredictor(db).predict_for_machine(machine_id)

@router.post("/batch-predict")
def run_batch_predictions(db: Session = Depends(get_db)):
    predictor = FailurePredictor(db)
    results = predictor.batch_predict_all()
    high = sum(1 for r in results if r["risk_category"] == "High Risk")
    med = sum(1 for r in results if r["risk_category"] == "Medium Risk")
    low = sum(1 for r in results if r["risk_category"] == "Low Risk")

    return {
        "message": f"Evaluated predictions for {len(results)} machines successfully.",
        "machines_evaluated": len(results),
        "high_risk_count": high,
        "medium_risk_count": med,
        "low_risk_count": low
    }

