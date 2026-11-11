from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.validation import DataValidationException
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.machine import Machine
from backend.app.schemas.entities import ValidationExceptionResponse, ExceptionResolutionUpdate

router = APIRouter(prefix="/alerts", tags=["Alerts & Exceptions"])

@router.get("", response_model=List[ValidationExceptionResponse])
def get_alerts(
    severity: Optional[str] = Query(None, description="CRITICAL, HIGH, MEDIUM, LOW"),
    resolution_status: Optional[str] = Query(None, description="UNRESOLVED, UNDER_REVIEW, RESOLVED, DISMISSED"),
    issue_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(DataValidationException)
    if severity:
        query = query.filter(DataValidationException.severity == severity)
    if resolution_status:
        query = query.filter(DataValidationException.resolution_status == resolution_status)
    if issue_type:
        query = query.filter(DataValidationException.issue_type == issue_type)

    return query.order_by(DataValidationException.timestamp.desc()).limit(limit).all()

@router.patch("/{issue_id}", response_model=ValidationExceptionResponse)
def update_alert_resolution(
    issue_id: str,
    payload: ExceptionResolutionUpdate,
    db: Session = Depends(get_db)
):
    exc = db.query(DataValidationException).filter(DataValidationException.issue_id == issue_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Alert / Exception not found")

    exc.resolution_status = payload.resolution_status
    db.commit()
    db.refresh(exc)
    return exc

@router.get("/metrics")
def get_alert_metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(DataValidationException.issue_id)).scalar() or 0
    unresolved = db.query(func.count(DataValidationException.issue_id)).filter(
        DataValidationException.resolution_status == "UNRESOLVED"
    ).scalar() or 0
    critical = db.query(func.count(DataValidationException.issue_id)).filter(
        DataValidationException.severity == "CRITICAL",
        DataValidationException.resolution_status == "UNRESOLVED"
    ).scalar() or 0

    by_type = dict(
        db.query(DataValidationException.issue_type, func.count(DataValidationException.issue_id))
        .group_by(DataValidationException.issue_type).all()
    )
    by_severity = dict(
        db.query(DataValidationException.severity, func.count(DataValidationException.issue_id))
        .group_by(DataValidationException.severity).all()
    )

    return {
        "total_alerts": total,
        "unresolved_alerts": unresolved,
        "critical_unresolved": critical,
        "by_type": by_type,
        "by_severity": by_severity
    }
