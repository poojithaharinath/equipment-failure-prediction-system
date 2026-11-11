from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.app.core.database import get_db
from backend.app.models.machine import Machine
from backend.app.models.production_line import ProductionLine
from backend.app.models.sensor import Sensor
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.audit import FailurePredictionLog, MachineHealthAuditTrail
from backend.app.schemas.entities import MachineResponse, MachineUpdate, SensorResponse
from backend.app.schemas.common import PaginatedResponse

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
    query = db.query(Machine)

    if plant_id:
        query = query.join(ProductionLine, Machine.line_id == ProductionLine.id).filter(ProductionLine.plant_id == plant_id)
    if line_id:
        query = query.filter(Machine.line_id == line_id)
    if status:
        query = query.filter(Machine.status == status)
    if criticality:
        query = query.filter(Machine.criticality == criticality)
    if search:
        s = f"%{search}%"
        query = query.filter(or_(Machine.name.ilike(s), Machine.serial_number.ilike(s), Machine.model_number.ilike(s)))

    total = query.count()
    machines = query.order_by(Machine.id).offset((page - 1) * page_size).limit(page_size).all()

    # Get latest prediction logs for risk category display
    items = []
    for m in machines:
        latest_pred = db.query(FailurePredictionLog).filter(
            FailurePredictionLog.machine_id == m.id
        ).order_by(FailurePredictionLog.prediction_timestamp.desc()).first()

        m_dict = {
            "id": m.id,
            "line_id": m.line_id,
            "name": m.name,
            "machine_type": m.machine_type,
            "model_number": m.model_number,
            "serial_number": m.serial_number,
            "installation_date": m.installation_date,
            "criticality": m.criticality,
            "health_score": m.health_score,
            "status": m.status,
            "operating_hours": m.operating_hours,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
            "sensor_count": 5,
            "failure_probability_pct": round(latest_pred.failure_probability * 100, 2) if latest_pred else 12.5,
            "risk_category": latest_pred.risk_category if latest_pred else "Low Risk"
        }

        if risk_category and m_dict["risk_category"] != risk_category:
            continue
        items.append(m_dict)

    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")

    latest_pred = db.query(FailurePredictionLog).filter(
        FailurePredictionLog.machine_id == m.id
    ).order_by(FailurePredictionLog.prediction_timestamp.desc()).first()

    return {
        "id": m.id,
        "line_id": m.line_id,
        "name": m.name,
        "machine_type": m.machine_type,
        "model_number": m.model_number,
        "serial_number": m.serial_number,
        "installation_date": m.installation_date,
        "criticality": m.criticality,
        "health_score": m.health_score,
        "status": m.status,
        "operating_hours": m.operating_hours,
        "created_at": m.created_at,
        "updated_at": m.updated_at,
        "sensor_count": 5,
        "failure_probability_pct": round(latest_pred.failure_probability * 100, 2) if latest_pred else 10.0,
        "risk_category": latest_pred.risk_category if latest_pred else "Low Risk"
    }

@router.get("/{machine_id}/sensors", response_model=List[SensorResponse])
def get_machine_sensors(machine_id: str, db: Session = Depends(get_db)):
    sensors = db.query(Sensor).filter(Sensor.machine_id == machine_id).all()
    res = []
    for s in sensors:
        latest_event = db.query(TelemetryEvent).filter(
            TelemetryEvent.sensor_id == s.id
        ).order_by(TelemetryEvent.timestamp.desc()).first()

        res.append({
            "id": s.id,
            "machine_id": s.machine_id,
            "name": s.name,
            "sensor_type": s.sensor_type,
            "unit": s.unit,
            "sampling_frequency_hz": s.sampling_frequency_hz,
            "min_threshold": s.min_threshold,
            "max_threshold": s.max_threshold,
            "status": s.status,
            "last_calibrated_at": s.last_calibrated_at,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "latest_reading": latest_event.value if latest_event else None,
            "latest_reading_time": latest_event.timestamp if latest_event else None,
        })
    return res

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
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")

    prev_status = m.status
    prev_health = m.health_score

    if payload.name is not None:
        m.name = payload.name
    if payload.criticality is not None:
        m.criticality = payload.criticality
    if payload.health_score is not None:
        m.health_score = payload.health_score
    if payload.status is not None:
        m.status = payload.status
    if payload.operating_hours is not None:
        m.operating_hours = payload.operating_hours

    # Record health audit if status or score changed
    if payload.status is not None or payload.health_score is not None:
        audit = MachineHealthAuditTrail(
            machine_id=m.id,
            previous_status=prev_status,
            new_status=m.status,
            previous_health_score=prev_health,
            new_health_score=m.health_score,
            trigger_event="MANUAL_OPERATOR_UPDATE"
        )
        db.add(audit)

    db.commit()
    db.refresh(m)
    return get_machine(machine_id, db)
