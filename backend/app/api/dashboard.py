from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.plant import Plant
from backend.app.models.production_line import ProductionLine
from backend.app.models.machine import Machine
from backend.app.models.audit import FailurePredictionLog
from backend.app.models.validation import DataValidationException
from backend.app.models.failure import FailureEvent
from backend.app.models.work_order import MaintenanceWorkOrder

router = APIRouter(prefix="/dashboard", tags=["Dashboard Analytics"])

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_plants = db.query(func.count(Plant.id)).scalar() or 0
    total_lines = db.query(func.count(ProductionLine.id)).scalar() or 0
    total_machines = db.query(func.count(Machine.id)).scalar() or 0

    failed_machines = db.query(func.count(Machine.id)).filter(Machine.status == "FAILED").scalar() or 0
    healthy_machines = db.query(func.count(Machine.id)).filter(Machine.health_score >= 80.0, Machine.status != "FAILED").scalar() or 0

    # Get latest predictions for each machine to tally High and Medium risk
    machines = db.query(Machine).all()
    high_risk_machines = []
    med_risk_count = 0
    high_risk_count = 0
    low_risk_count = 0

    # Health distribution buckets
    health_distribution = {
        "0-20%": 0,
        "21-40%": 0,
        "41-60%": 0,
        "61-80%": 0,
        "81-100%": 0
    }

    for m in machines:
        score = m.health_score
        if score <= 20:
            health_distribution["0-20%"] += 1
        elif score <= 40:
            health_distribution["21-40%"] += 1
        elif score <= 60:
            health_distribution["41-60%"] += 1
        elif score <= 80:
            health_distribution["61-80%"] += 1
        else:
            health_distribution["81-100%"] += 1

        pred = db.query(FailurePredictionLog).filter(
            FailurePredictionLog.machine_id == m.id
        ).order_by(FailurePredictionLog.prediction_timestamp.desc()).first()

        risk = pred.risk_category if pred else ("High Risk" if m.health_score < 40 else "Medium Risk" if m.health_score < 75 else "Low Risk")
        prob = round(pred.failure_probability * 100, 1) if pred else round(100.0 - m.health_score, 1)

        if risk == "High Risk":
            high_risk_count += 1
            high_risk_machines.append({
                "machine_id": m.id,
                "machine_name": m.name,
                "machine_type": m.machine_type,
                "line_id": m.line_id,
                "health_score": m.health_score,
                "failure_probability_pct": prob,
                "status": m.status,
                "criticality": m.criticality,
                "recommendation": pred.recommendations if pred else "Emergency inspection needed."
            })
        elif risk == "Medium Risk":
            med_risk_count += 1
        else:
            low_risk_count += 1

    # Sort high risk machines by failure probability descending
    high_risk_machines.sort(key=lambda x: x["failure_probability_pct"], reverse=True)

    # Recent alerts
    recent_alerts = db.query(DataValidationException).order_by(
        DataValidationException.timestamp.desc()
    ).limit(8).all()
    alerts_data = [
        {
            "issue_id": a.issue_id,
            "issue_type": a.issue_type,
            "related_entity_id": a.related_entity_id,
            "description": a.description,
            "timestamp": a.timestamp.isoformat(),
            "severity": a.severity,
            "resolution_status": a.resolution_status
        }
        for a in recent_alerts
    ]

    # Additional operational summary
    active_work_orders = db.query(func.count(MaintenanceWorkOrder.id)).filter(
        MaintenanceWorkOrder.status.in_(["PENDING", "IN_PROGRESS"])
    ).scalar() or 0
    total_failures = db.query(func.count(FailureEvent.id)).scalar() or 0
    avg_health = round(float(db.query(func.avg(Machine.health_score)).scalar() or 85.0), 1)

    return {
        "total_plants": total_plants,
        "total_production_lines": total_lines,
        "total_machines": total_machines,
        "healthy_machines": healthy_machines,
        "medium_risk_machines": med_risk_count,
        "high_risk_machines": high_risk_count,
        "low_risk_machines": low_risk_count,
        "failed_machines": failed_machines,
        "average_machine_health": avg_health,
        "active_work_orders": active_work_orders,
        "total_failures_recorded": total_failures,
        "health_distribution": [
            {"range": k, "count": v} for k, v in health_distribution.items()
        ],
        "recent_alerts": alerts_data,
        "machines_requiring_attention": high_risk_machines[:6]
    }
