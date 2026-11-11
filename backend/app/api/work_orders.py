from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.work_order import MaintenanceWorkOrder, WorkOrderPart, WorkOrderTechnician
from backend.app.models.machine import Machine
from backend.app.models.technician import Technician
from backend.app.models.part import Part
from backend.app.schemas.entities import WorkOrderCreate, WorkOrderStatusUpdate, WorkOrderResponse
from backend.app.schemas.common import PaginatedResponse

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
    query = db.query(MaintenanceWorkOrder)
    if machine_id:
        query = query.filter(MaintenanceWorkOrder.machine_id == machine_id)
    if status:
        query = query.filter(MaintenanceWorkOrder.status == status)
    if priority:
        query = query.filter(MaintenanceWorkOrder.priority == priority)
    if work_order_type:
        query = query.filter(MaintenanceWorkOrder.work_order_type == work_order_type)

    total = query.count()
    wos = query.order_by(MaintenanceWorkOrder.scheduled_start_time.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for wo in wos:
        m = db.query(Machine).filter(Machine.id == wo.machine_id).first()
        t = db.query(Technician).filter(Technician.id == wo.lead_technician_id).first() if wo.lead_technician_id else None

        items.append({
            "id": wo.id,
            "machine_id": wo.machine_id,
            "machine_name": m.name if m else None,
            "priority": wo.priority,
            "work_order_type": wo.work_order_type,
            "status": wo.status,
            "description": wo.description,
            "root_cause": wo.root_cause,
            "scheduled_start_time": wo.scheduled_start_time,
            "actual_start_time": wo.actual_start_time,
            "actual_end_time": wo.actual_end_time,
            "lead_technician_id": wo.lead_technician_id,
            "lead_technician_name": f"{t.first_name} {t.last_name}" if t else None,
            "downtime_minutes": wo.downtime_minutes,
            "cost": wo.cost,
            "created_at": wo.created_at,
            "updated_at": wo.updated_at
        })

    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/{wo_id}", response_model=WorkOrderResponse)
def get_work_order(wo_id: str, db: Session = Depends(get_db)):
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")

    m = db.query(Machine).filter(Machine.id == wo.machine_id).first()
    t = db.query(Technician).filter(Technician.id == wo.lead_technician_id).first() if wo.lead_technician_id else None

    # Parts used
    parts_query = db.query(WorkOrderPart, Part).join(Part, WorkOrderPart.part_id == Part.id).filter(
        WorkOrderPart.work_order_id == wo.id
    ).all()
    parts_list = [
        {
            "part_id": p.id,
            "part_name": p.name,
            "part_number": p.part_number,
            "quantity_used": wop.quantity_used,
            "unit_cost": wop.unit_cost_at_time
        }
        for wop, p in parts_query
    ]

    return {
        "id": wo.id,
        "machine_id": wo.machine_id,
        "machine_name": m.name if m else None,
        "priority": wo.priority,
        "work_order_type": wo.work_order_type,
        "status": wo.status,
        "description": wo.description,
        "root_cause": wo.root_cause,
        "scheduled_start_time": wo.scheduled_start_time,
        "actual_start_time": wo.actual_start_time,
        "actual_end_time": wo.actual_end_time,
        "lead_technician_id": wo.lead_technician_id,
        "lead_technician_name": f"{t.first_name} {t.last_name}" if t else None,
        "downtime_minutes": wo.downtime_minutes,
        "cost": wo.cost,
        "created_at": wo.created_at,
        "updated_at": wo.updated_at,
        "parts_used": parts_list
    }

@router.post("", response_model=WorkOrderResponse)
def create_work_order(payload: WorkOrderCreate, db: Session = Depends(get_db)):
    m = db.query(Machine).filter(Machine.id == payload.machine_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")

    # Generate sequential work order ID
    count = db.query(func.count(MaintenanceWorkOrder.id)).scalar() or 0
    now = datetime.utcnow()
    wo_id = f"WO-{now.year}-{count + 1:06d}"

    wo = MaintenanceWorkOrder(
        id=wo_id,
        machine_id=payload.machine_id,
        priority=payload.priority,
        work_order_type=payload.work_order_type,
        status="PENDING",
        description=payload.description,
        root_cause=payload.root_cause,
        scheduled_start_time=payload.scheduled_start_time,
        lead_technician_id=payload.lead_technician_id,
        cost=150.0, # Base labor cost
        created_at=now,
        updated_at=now
    )
    db.add(wo)

    # Attach parts if specified
    if payload.parts_to_use:
        for p_item in payload.parts_to_use:
            part = db.query(Part).filter(Part.id == p_item.part_id).first()
            if part:
                wop = WorkOrderPart(
                    work_order_id=wo_id,
                    part_id=part.id,
                    quantity_used=p_item.quantity,
                    unit_cost_at_time=part.unit_cost,
                    created_at=now
                )
                db.add(wop)
                part.stock_quantity = max(0, part.stock_quantity - p_item.quantity)
                wo.cost += part.unit_cost * p_item.quantity

    db.commit()
    db.refresh(wo)
    return get_work_order(wo_id, db)

@router.patch("/{wo_id}", response_model=WorkOrderResponse)
def update_work_order_status(wo_id: str, payload: WorkOrderStatusUpdate, db: Session = Depends(get_db)):
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == wo_id).first()
    if not wo:
        raise HTTPException(status_code=404, detail="Work Order not found")

    wo.status = payload.status
    if payload.actual_start_time is not None:
        wo.actual_start_time = payload.actual_start_time
    if payload.actual_end_time is not None:
        wo.actual_end_time = payload.actual_end_time
    if payload.downtime_minutes is not None:
        wo.downtime_minutes = payload.downtime_minutes
    if payload.cost is not None:
        wo.cost = payload.cost
    if payload.root_cause is not None:
        wo.root_cause = payload.root_cause

    # If completed, restore machine status to OPERATIONAL and reset health score to high
    if payload.status == "COMPLETED":
        m = db.query(Machine).filter(Machine.id == wo.machine_id).first()
        if m:
            m.status = "OPERATIONAL"
            m.health_score = 98.0

    wo.updated_at = datetime.utcnow()
    db.commit()
    return get_work_order(wo_id, db)
