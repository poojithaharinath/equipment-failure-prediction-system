from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.failure import FailureEvent
from backend.app.models.machine import Machine
from backend.app.schemas.entities import FailureEventResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/failure-events", tags=["Failure Events"])

@router.get("", response_model=PaginatedResponse[FailureEventResponse])
def get_failure_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    machine_id: Optional[str] = Query(None),
    failure_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(FailureEvent)
    if machine_id:
        query = query.filter(FailureEvent.machine_id == machine_id)
    if failure_type:
        query = query.filter(FailureEvent.failure_type == failure_type)
    if severity:
        query = query.filter(FailureEvent.severity == severity)

    total = query.count()
    failures = query.order_by(FailureEvent.failure_timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for f in failures:
        m = db.query(Machine).filter(Machine.id == f.machine_id).first()
        items.append({
            "id": f.id,
            "machine_id": f.machine_id,
            "machine_name": m.name if m else None,
            "failure_timestamp": f.failure_timestamp,
            "failure_type": f.failure_type,
            "severity": f.severity,
            "pre_warning_lead_time_hours": f.pre_warning_lead_time_hours,
            "root_cause": f.root_cause,
            "downtime_hours": f.downtime_hours,
            "work_order_id": f.work_order_id,
            "created_at": f.created_at
        })

    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/summary")
def get_failures_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(FailureEvent.id)).scalar() or 0
    total_downtime = db.query(func.sum(FailureEvent.downtime_hours)).scalar() or 0.0
    avg_downtime = db.query(func.avg(FailureEvent.downtime_hours)).scalar() or 0.0
    avg_lead = db.query(func.avg(FailureEvent.pre_warning_lead_time_hours)).scalar() or 0.0

    by_type = dict(
        db.query(FailureEvent.failure_type, func.count(FailureEvent.id))
        .group_by(FailureEvent.failure_type).all()
    )
    by_severity = dict(
        db.query(FailureEvent.severity, func.count(FailureEvent.id))
        .group_by(FailureEvent.severity).all()
    )

    return {
        "total_failures": total,
        "total_downtime_hours": round(float(total_downtime), 1),
        "average_downtime_hours": round(float(avg_downtime), 1),
        "average_lead_time_hours": round(float(avg_lead), 1),
        "failures_by_type": by_type,
        "failures_by_severity": by_severity
    }
