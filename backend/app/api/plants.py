from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.plant import Plant
from backend.app.models.production_line import ProductionLine
from backend.app.models.machine import Machine
from backend.app.schemas.entities import PlantResponse, ProductionLineResponse

router = APIRouter(prefix="/plants", tags=["Plants"])

@router.get("", response_model=List[PlantResponse])
def get_plants(db: Session = Depends(get_db)):
    plants = db.query(Plant).all()
    res = []
    for p in plants:
        line_cnt = db.query(func.count(ProductionLine.id)).filter(ProductionLine.plant_id == p.id).scalar() or 0
        mch_cnt = db.query(func.count(Machine.id)).join(
            ProductionLine, Machine.line_id == ProductionLine.id
        ).filter(ProductionLine.plant_id == p.id).scalar() or 0

        p_dict = {
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "location": p.location,
            "capacity_mw": p.capacity_mw,
            "commissioning_date": p.commissioning_date,
            "status": p.status,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "line_count": line_cnt,
            "machine_count": mch_cnt
        }
        res.append(p_dict)
    return res

@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(plant_id: str, db: Session = Depends(get_db)):
    p = db.query(Plant).filter(Plant.id == plant_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Plant not found")

    line_cnt = db.query(func.count(ProductionLine.id)).filter(ProductionLine.plant_id == p.id).scalar() or 0
    mch_cnt = db.query(func.count(Machine.id)).join(
        ProductionLine, Machine.line_id == ProductionLine.id
    ).filter(ProductionLine.plant_id == p.id).scalar() or 0

    return {
        "id": p.id,
        "name": p.name,
        "code": p.code,
        "location": p.location,
        "capacity_mw": p.capacity_mw,
        "commissioning_date": p.commissioning_date,
        "status": p.status,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
        "line_count": line_cnt,
        "machine_count": mch_cnt
    }

@router.get("/{plant_id}/lines", response_model=List[ProductionLineResponse])
def get_plant_lines(plant_id: str, db: Session = Depends(get_db)):
    lines = db.query(ProductionLine).filter(ProductionLine.plant_id == plant_id).all()
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
