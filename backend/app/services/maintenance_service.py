"""
maintenance_service.py
Service layer for Maintenance Work Order business logic.

Centralises WO creation, status transitions, parts/technician
assignment and cost calculation so the API routers stay thin.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.work_order import MaintenanceWorkOrder, WorkOrderPart, WorkOrderTechnician
from backend.app.models.machine import Machine
from backend.app.models.technician import Technician
from backend.app.models.part import Part

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def next_work_order_id(db: Session) -> str:
    """Generate the next sequential work-order ID: WO-YYYY-NNNNNN."""
    count = db.query(func.count(MaintenanceWorkOrder.id)).scalar() or 0
    return f"WO-{datetime.utcnow().year}-{count + 1:06d}"


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def _build_wo_response(
    db: Session,
    wo: MaintenanceWorkOrder,
    include_parts: bool = False,
) -> Dict[str, Any]:
    """Build a work-order response dict. Parts are loaded only for detail responses."""
    m = db.query(Machine).filter(Machine.id == wo.machine_id).first()
    t = (
        db.query(Technician).filter(Technician.id == wo.lead_technician_id).first()
        if wo.lead_technician_id
        else None
    )
    parts_list = None
    if include_parts:
        parts_rows = (
            db.query(WorkOrderPart, Part)
            .join(Part, WorkOrderPart.part_id == Part.id)
            .filter(WorkOrderPart.work_order_id == wo.id)
            .all()
        )
        parts_list = [
            {
                "part_id": p.id,
                "part_name": p.name,
                "part_number": p.part_number,
                "quantity_used": wop.quantity_used,
                "unit_cost": wop.unit_cost_at_time,
            }
            for wop, p in parts_rows
        ]

    payload = {
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
    }
    if include_parts:
        payload["parts_used"] = parts_list
    return payload


def get_work_order_response(db: Session, wo_id: str) -> Dict[str, Any]:
    """Return a full work-order response dict or raise ValueError."""
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == wo_id).first()
    if not wo:
        raise ValueError(f"Work Order '{wo_id}' not found.")
    return _build_wo_response(db, wo, include_parts=True)


def list_work_orders(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    machine_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    work_order_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Paginated, filtered work-order list."""
    q = db.query(MaintenanceWorkOrder)
    if machine_id:
        q = q.filter(MaintenanceWorkOrder.machine_id == machine_id)
    if status:
        q = q.filter(MaintenanceWorkOrder.status == status)
    if priority:
        q = q.filter(MaintenanceWorkOrder.priority == priority)
    if work_order_type:
        q = q.filter(MaintenanceWorkOrder.work_order_type == work_order_type)

    total = q.count()
    wos = (
        q.order_by(MaintenanceWorkOrder.scheduled_start_time.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_build_wo_response(db, wo, include_parts=False) for wo in wos]
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def create_work_order(
    db: Session,
    machine_id: str,
    priority: str,
    work_order_type: str,
    description: str,
    scheduled_start_time: datetime,
    root_cause: Optional[str] = None,
    lead_technician_id: Optional[str] = None,
    parts_to_use: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Create a new MaintenanceWorkOrder, attach parts (deducting stock),
    and return the full response dict.

    Business rules:
    - Base labour cost: $150.00
    - Each part item adds (unit_cost × quantity) to WO cost
    - Stock is decremented to 0 minimum (never negative)
    """
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise ValueError(f"Machine '{machine_id}' not found.")

    wo_id = next_work_order_id(db)
    now = datetime.utcnow()
    base_cost = 150.0

    wo = MaintenanceWorkOrder(
        id=wo_id,
        machine_id=machine_id,
        priority=priority,
        work_order_type=work_order_type,
        status="PENDING",
        description=description,
        root_cause=root_cause,
        scheduled_start_time=scheduled_start_time,
        lead_technician_id=lead_technician_id,
        cost=base_cost,
        created_at=now,
        updated_at=now,
    )
    db.add(wo)

    if parts_to_use:
        for item in parts_to_use:
            part = db.query(Part).filter(Part.id == item["part_id"]).first()
            if not part:
                logger.warning(f"Part '{item['part_id']}' not found — skipping.")
                continue
            qty = int(item.get("quantity", 1))
            wop = WorkOrderPart(
                work_order_id=wo_id,
                part_id=part.id,
                quantity_used=qty,
                unit_cost_at_time=part.unit_cost,
                created_at=now,
            )
            db.add(wop)
            part.stock_quantity = max(0, part.stock_quantity - qty)
            wo.cost += part.unit_cost * qty

    db.commit()
    logger.info(f"Created work order {wo_id} for machine {machine_id}")
    return _build_wo_response(db, wo, include_parts=True)


def update_work_order_status(
    db: Session,
    wo_id: str,
    status: str,
    actual_start_time: Optional[datetime] = None,
    actual_end_time: Optional[datetime] = None,
    downtime_minutes: Optional[int] = None,
    cost: Optional[float] = None,
    root_cause: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transition a work-order to a new status and update completion fields.

    Business rules:
    - COMPLETED → restore machine to OPERATIONAL with health_score = 98.0
    - Timestamps are validated: actual_end_time must not precede actual_start_time
      (unless it was deliberately injected as an edge case — the API validates on write)
    """
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == wo_id).first()
    if not wo:
        raise ValueError(f"Work Order '{wo_id}' not found.")

    wo.status = status
    if actual_start_time is not None:
        wo.actual_start_time = actual_start_time
    if actual_end_time is not None:
        wo.actual_end_time = actual_end_time
    if downtime_minutes is not None:
        wo.downtime_minutes = downtime_minutes
    if cost is not None:
        wo.cost = cost
    if root_cause is not None:
        wo.root_cause = root_cause

    if status == "COMPLETED":
        m = db.query(Machine).filter(Machine.id == wo.machine_id).first()
        if m:
            m.status = "OPERATIONAL"
            m.health_score = 98.0
            logger.info(f"Machine {m.id} restored to OPERATIONAL after WO {wo_id} completion")

    wo.updated_at = datetime.utcnow()
    db.commit()
    return _build_wo_response(db, wo, include_parts=True)


# ---------------------------------------------------------------------------
# Technician assignment
# ---------------------------------------------------------------------------

def assign_technician(
    db: Session,
    wo_id: str,
    technician_id: str,
    hours_spent: float = 0.0,
    role_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assign an additional technician to a work order.
    Idempotent — if the technician is already assigned, updates hours/notes only.
    """
    wo = db.query(MaintenanceWorkOrder).filter(MaintenanceWorkOrder.id == wo_id).first()
    if not wo:
        raise ValueError(f"Work Order '{wo_id}' not found.")
    tech = db.query(Technician).filter(Technician.id == technician_id).first()
    if not tech:
        raise ValueError(f"Technician '{technician_id}' not found.")

    existing = db.query(WorkOrderTechnician).filter(
        WorkOrderTechnician.work_order_id == wo_id,
        WorkOrderTechnician.technician_id == technician_id,
    ).first()

    if existing:
        existing.hours_spent = hours_spent
        if role_notes:
            existing.role_notes = role_notes
    else:
        wot = WorkOrderTechnician(
            work_order_id=wo_id,
            technician_id=technician_id,
            hours_spent=hours_spent,
            role_notes=role_notes,
            created_at=datetime.utcnow(),
        )
        db.add(wot)

    db.commit()
    logger.info(f"Technician {technician_id} assigned to WO {wo_id}")
    return _build_wo_response(db, wo, include_parts=True)

