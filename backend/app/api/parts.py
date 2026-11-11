from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.part import Part
from backend.app.schemas.entities import PartResponse

router = APIRouter(prefix="/parts", tags=["Parts"])

@router.get("", response_model=List[PartResponse])
def get_parts(
    category: Optional[str] = Query(None),
    low_stock_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    query = db.query(Part)
    if category:
        query = query.filter(Part.category == category)
    if low_stock_only:
        query = query.filter(Part.stock_quantity <= Part.minimum_reorder_level)
    return query.order_by(Part.name).all()
