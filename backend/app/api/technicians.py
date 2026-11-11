from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.technician import Technician
from backend.app.schemas.entities import TechnicianResponse

router = APIRouter(prefix="/technicians", tags=["Technicians"])

@router.get("", response_model=List[TechnicianResponse])
def get_technicians(
    specialization: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Technician)
    if specialization:
        query = query.filter(Technician.specialization == specialization)
    if status:
        query = query.filter(Technician.status == status)
    return query.order_by(Technician.first_name).all()
