from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.audit import MachineHealthAuditTrail
from backend.app.schemas.entities import MachineResponse, MachineUpdate, SensorResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.services import machine_service

router = APIRouter(prefix="/machines", tags=["Machines"])


@router.get("", response_model=PaginatedResponse[MachineResponse])
def get_machines(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search name, serial, or model"),
    line_id: Optional[str] = Query(None),
    plant_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    risk_category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return machine_service.query_machines(
        db,
        page=page,
        page_size=page_size,
        search=search,
        line_id=line_id,
        plant_id=plant_id,
        status=status,
        criticality=criticality,
        risk_category=risk_category,
    )


@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    try:
        machine = machine_service.get_machine_or_404(db, machine_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine_service.enrich_machine_with_prediction(
        db, machine, default_probability_pct=10.0
    )


@router.get("/{machine_id}/sensors", response_model=List[SensorResponse])
def get_machine_sensors(machine_id: str, db: Session = Depends(get_db)):
    return machine_service.get_sensor_summary(db, machine_id)


@router.get("/{machine_id}/health-history")
def get_machine_health_history(machine_id: str, limit: int = 50, db: Session = Depends(get_db)):
    audits = db.query(MachineHealthAuditTrail).filter(
        MachineHealthAuditTrail.machine_id == machine_id
    ).order_by(MachineHealthAuditTrail.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": a.id,
            "previous_status": a.previous_status,
            "new_status": a.new_status,
            "previous_health_score": a.previous_health_score,
            "new_health_score": a.new_health_score,
            "failure_probability": a.failure_probability,
            "risk_category": a.risk_category,
            "trigger_event": a.trigger_event,
            "timestamp": a.timestamp.isoformat()
        }
        for a in audits
    ]


@router.patch("/{machine_id}", response_model=MachineResponse)
def update_machine(machine_id: str, payload: MachineUpdate, db: Session = Depends(get_db)):
    try:
        machine = machine_service.get_machine_or_404(db, machine_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Machine not found")

    machine_service.update_machine_fields(
        db,
        machine,
        name=payload.name,
        criticality=payload.criticality,
        health_score=payload.health_score,
        status=payload.status,
        operating_hours=payload.operating_hours,
    )
    return machine_service.enrich_machine_with_prediction(
        db, machine, default_probability_pct=10.0
    )
