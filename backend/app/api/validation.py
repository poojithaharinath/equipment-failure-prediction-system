import os
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.validation import DataValidationException
from backend.app.validation.validator import DataValidator
from backend.app.schemas.entities import ValidationExceptionResponse, ExceptionResolutionUpdate
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/validation", tags=["Data Quality & Validation"])

@router.post("/run")
def trigger_validation(db: Session = Depends(get_db)):
    validator = DataValidator(db)
    report = validator.run_all_validations()

    os.makedirs("data/reports", exist_ok=True)
    report_path = "data/reports/validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report

@router.get("/report")
def get_validation_report(db: Session = Depends(get_db)):
    report_path = "data/reports/validation_report.json"
    if os.path.exists(report_path):
        try:
            with open(report_path, "r") as f:
                return json.load(f)
        except Exception:
            pass

    # Fallback to dynamic execution
    validator = DataValidator(db)
    return validator.run_all_validations()

@router.get("/exceptions", response_model=PaginatedResponse[ValidationExceptionResponse])
def get_validation_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    issue_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    resolution_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(DataValidationException)
    if issue_type:
        query = query.filter(DataValidationException.issue_type == issue_type)
    if severity:
        query = query.filter(DataValidationException.severity == severity)
    if resolution_status:
        query = query.filter(DataValidationException.resolution_status == resolution_status)

    total = query.count()
    items = query.order_by(DataValidationException.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.patch("/exceptions/{issue_id}", response_model=ValidationExceptionResponse)
def resolve_exception(
    issue_id: str,
    payload: ExceptionResolutionUpdate,
    db: Session = Depends(get_db)
):
    exc = db.query(DataValidationException).filter(DataValidationException.issue_id == issue_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception record not found")

    exc.resolution_status = payload.resolution_status
    db.commit()
    db.refresh(exc)
    return exc
