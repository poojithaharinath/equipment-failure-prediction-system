from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.production_line import ProductionLine
from backend.app.models.machine import Machine
from backend.app.schemas.entities import ProductionLineResponse, MachineResponse

router = APIRouter(prefix="/production-lines", tags=["Production Lines"])

@router.get("", response_model=List[ProductionLineResponse])
def get_production_lines(
    plant_id: Optional[str] = Query(None, description="Filter lines by plant"),
    status: Optional[str] = Query(None, description="Filter lines by status"),
    db: Session = Depends(get_db)
):
    query = db.query(ProductionLine)
    if plant_id:
        query = query.filter(ProductionLine.plant_id == plant_id)
    if status:
        query = query.filter(ProductionLine.status == status)

    lines = query.all()
    res = []
    for l in lines:
        mch_cnt = db.query(func.count(Machine.id)).filter(Machine.line_id == l.id).scalar() or 0
        l_dict = {
            "id": l.id,
            "plant_id": l.plant_id,
            "name": l.name,
            "line_number": l.line_number,
            "line_type": l.line_type,
            "target_units_per_hour": l.target_units_per_hour,
            "status": l.status,
            "created_at": l.created_at,
            "updated_at": l.updated_at,
            "machine_count": mch_cnt
        }
        res.append(l_dict)
    return res

@router.get("/{line_id}", response_model=ProductionLineResponse)
def get_production_line(line_id: str, db: Session = Depends(get_db)):
    l = db.query(ProductionLine).filter(ProductionLine.id == line_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Production Line not found")

    mch_cnt = db.query(func.count(Machine.id)).filter(Machine.line_id == l.id).scalar() or 0
    return {
        "id": l.id,
        "plant_id": l.plant_id,
        "name": l.name,
        "line_number": l.line_number,
        "line_type": l.line_type,
        "target_units_per_hour": l.target_units_per_hour,
        "status": l.status,
        "created_at": l.created_at,
        "updated_at": l.updated_at,
        "machine_count": mch_cnt
    }

@router.get("/{line_id}/machines", response_model=List[MachineResponse])
def get_line_machines(line_id: str, db: Session = Depends(get_db)):
    machines = db.query(Machine).filter(Machine.line_id == line_id).all()
    res = []
    for m in machines:
        res.append({
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
            "sensor_count": 5
        })
    return res
