from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.failure import FailureEvent
from backend.app.models.machine import Machine
from backend.app.schemas.entities import FailureEventResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.services.machine_service import get_failure_summary

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
    return get_failure_summary(db)

