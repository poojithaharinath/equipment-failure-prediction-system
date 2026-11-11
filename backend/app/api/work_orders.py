from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.entities import WorkOrderCreate, WorkOrderStatusUpdate, WorkOrderResponse
from backend.app.schemas.common import PaginatedResponse
from backend.app.services import maintenance_service

router = APIRouter(prefix="/work-orders", tags=["Maintenance Work Orders"])


@router.get("", response_model=PaginatedResponse[WorkOrderResponse])
def get_work_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    machine_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    work_order_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    return maintenance_service.list_work_orders(
        db,
        page=page,
        page_size=page_size,
        machine_id=machine_id,
        status=status,
        priority=priority,
        work_order_type=work_order_type,
    )


@router.get("/{wo_id}", response_model=WorkOrderResponse)
def get_work_order(wo_id: str, db: Session = Depends(get_db)):
    try:
        return maintenance_service.get_work_order_response(db, wo_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Work Order not found")


@router.post("", response_model=WorkOrderResponse)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)):
    parts = None
    if payload.parts_to_use:
        parts = [
            {"part_id": item.part_id, "quantity": item.quantity}
            for item in payload.parts_to_use
        ]
    try:
        return maintenance_service.create_work_order(
            db,
            machine_id=payload.machine_id,
            priority=payload.priority,
            work_order_type=payload.work_order_type,
            description=payload.description,
            scheduled_start_time=payload.scheduled_start_time,
            root_cause=payload.root_cause,
            lead_technician_id=payload.lead_technician_id,
            parts_to_use=parts,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Machine not found")


@router.patch("/{wo_id}", response_model=WorkOrderResponse)
def update_work_order_status(wo_id: str, payload: WorkOrderStatusUpdate, db: Session = Depends(get_db)):
    try:
        return maintenance_service.update_work_order_status(
            db,
            wo_id,
            status=payload.status,
            actual_start_time=payload.actual_start_time,
            actual_end_time=payload.actual_end_time,
            downtime_minutes=payload.downtime_minutes,
            cost=payload.cost,
            root_cause=payload.root_cause,
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Work Order not found")
