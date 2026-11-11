"""
machine_service.py
Service layer for Machine business logic.

Abstracts repeated DB query patterns from the API layer so routers stay thin
and identical sub-queries are not duplicated across endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from backend.app.models.machine import Machine
from backend.app.models.production_line import ProductionLine
from backend.app.models.sensor import Sensor
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.audit import FailurePredictionLog, MachineHealthAuditTrail
from backend.app.models.failure import FailureEvent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def get_machine_or_404(db: Session, machine_id: str) -> Machine:
    """Return Machine by ID or raise ValueError if not found."""
    m = db.query(Machine).filter(Machine.id == machine_id).first()
    if not m:
        raise ValueError(f"Machine '{machine_id}' not found.")
    return m


def get_latest_prediction(db: Session, machine_id: str) -> Optional[FailurePredictionLog]:
    """Return the most recent FailurePredictionLog for a machine, or None."""
    return (
        db.query(FailurePredictionLog)
        .filter(FailurePredictionLog.machine_id == machine_id)
        .order_by(FailurePredictionLog.prediction_timestamp.desc())
        .first()
    )


def enrich_machine_with_prediction(
    db: Session,
    machine: Machine,
    default_probability_pct: float = 12.5,
) -> Dict[str, Any]:
    """
    Return a dictionary of machine fields enriched with the latest prediction.
    Used by both GET /machines and GET /machines/{id}.

    List responses keep the historical 12.5% placeholder when no prediction
    exists. Detail responses pass 10.0 so the existing API contract is unchanged.
    """
    latest_pred = get_latest_prediction(db, machine.id)
    return {
        "id": machine.id,
        "line_id": machine.line_id,
        "name": machine.name,
        "machine_type": machine.machine_type,
        "model_number": machine.model_number,
        "serial_number": machine.serial_number,
        "installation_date": machine.installation_date,
        "criticality": machine.criticality,
        "health_score": machine.health_score,
        "status": machine.status,
        "operating_hours": machine.operating_hours,
        "created_at": machine.created_at,
        "updated_at": machine.updated_at,
        "sensor_count": db.query(func.count(Sensor.id))
            .filter(Sensor.machine_id == machine.id).scalar() or 0,
        "failure_probability_pct": (
            round(latest_pred.failure_probability * 100, 2)
            if latest_pred
            else default_probability_pct
        ),
        "risk_category": (
            latest_pred.risk_category if latest_pred else "Low Risk"
        ),
    }


def query_machines(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    line_id: Optional[str] = None,
    plant_id: Optional[str] = None,
    status: Optional[str] = None,
    criticality: Optional[str] = None,
    risk_category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Paginated, filterable machine query.
    Returns a dict compatible with PaginatedResponse[MachineResponse].
    """
    q = db.query(Machine)

    if plant_id:
        q = q.join(ProductionLine, Machine.line_id == ProductionLine.id).filter(
            ProductionLine.plant_id == plant_id
        )
    if line_id:
        q = q.filter(Machine.line_id == line_id)
    if status:
        q = q.filter(Machine.status == status)
    if criticality:
        q = q.filter(Machine.criticality == criticality)
    if search:
        s = f"%{search}%"
        q = q.filter(
            or_(
                Machine.name.ilike(s),
                Machine.serial_number.ilike(s),
                Machine.model_number.ilike(s),
            )
        )

    total = q.count()
    machines = q.order_by(Machine.id).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for m in machines:
        enriched = enrich_machine_with_prediction(db, m)
        if risk_category and enriched["risk_category"] != risk_category:
            continue
        items.append(enriched)

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

def update_machine_fields(
    db: Session,
    machine: Machine,
    name: Optional[str] = None,
    criticality: Optional[str] = None,
    health_score: Optional[float] = None,
    status: Optional[str] = None,
    operating_hours: Optional[float] = None,
    trigger_event: str = "MANUAL_OPERATOR_UPDATE",
) -> Machine:
    """
    Apply permitted field updates to a Machine and record an audit trail entry
    when status or health_score change.  Commits the session.
    """
    prev_status = machine.status
    prev_health = machine.health_score

    if name is not None:
        machine.name = name
    if criticality is not None:
        machine.criticality = criticality
    if health_score is not None:
        machine.health_score = health_score
    if status is not None:
        machine.status = status
    if operating_hours is not None:
        machine.operating_hours = operating_hours

    # Audit trail only on meaningful state change
    if status is not None or health_score is not None:
        audit = MachineHealthAuditTrail(
            machine_id=machine.id,
            previous_status=prev_status,
            new_status=machine.status,
            previous_health_score=prev_health,
            new_health_score=machine.health_score,
            trigger_event=trigger_event,
        )
        db.add(audit)

    db.commit()
    db.refresh(machine)
    return machine


def mark_machine_restored(db: Session, machine_id: str) -> Machine:
    """
    Mark a machine OPERATIONAL with a refreshed health score of 98.
    Called after a maintenance work order is COMPLETED.
    """
    m = get_machine_or_404(db, machine_id)
    return update_machine_fields(
        db, m,
        status="OPERATIONAL",
        health_score=98.0,
        trigger_event="WORK_ORDER_COMPLETED",
    )


# ---------------------------------------------------------------------------
# Sensor / Telemetry helpers
# ---------------------------------------------------------------------------

def get_sensor_summary(db: Session, machine_id: str) -> List[Dict[str, Any]]:
    """
    Return all sensors for a machine with their most recent reading attached.
    """
    sensors = db.query(Sensor).filter(Sensor.machine_id == machine_id).all()
    result = []
    for s in sensors:
        latest = (
            db.query(TelemetryEvent)
            .filter(TelemetryEvent.sensor_id == s.id)
            .order_by(TelemetryEvent.timestamp.desc())
            .first()
        )
        result.append(
            {
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
                "latest_reading": latest.value if latest else None,
                "latest_reading_time": latest.timestamp if latest else None,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Health statistics helper (used by dashboard)
# ---------------------------------------------------------------------------

def compute_health_distribution(machines: List[Machine]) -> Dict[str, int]:
    """Bucket 100 machines into 5 health-score ranges."""
    buckets = {"0-20%": 0, "21-40%": 0, "41-60%": 0, "61-80%": 0, "81-100%": 0}
    for m in machines:
        s = m.health_score
        if s <= 20:
            buckets["0-20%"] += 1
        elif s <= 40:
            buckets["21-40%"] += 1
        elif s <= 60:
            buckets["41-60%"] += 1
        elif s <= 80:
            buckets["61-80%"] += 1
        else:
            buckets["81-100%"] += 1
    return buckets


def get_fleet_summary(db: Session) -> Dict[str, Any]:
    """
    Single-query fleet overview used by the dashboard and health reports.
    Returns counts, average health, and machine-level risk tallies.
    """
    machines = db.query(Machine).all()
    total = len(machines)
    failed = sum(1 for m in machines if m.status == "FAILED")
    healthy = sum(1 for m in machines if m.health_score >= 80.0 and m.status != "FAILED")
    avg_health = round(
        float(db.query(func.avg(Machine.health_score)).scalar() or 85.0), 1
    )
    health_dist = compute_health_distribution(machines)

    high_risk, med_risk, low_risk = 0, 0, 0
    for m in machines:
        pred = get_latest_prediction(db, m.id)
        risk = (
            pred.risk_category
            if pred
            else ("High Risk" if m.health_score < 40 else "Medium Risk" if m.health_score < 75 else "Low Risk")
        )
        if risk == "High Risk":
            high_risk += 1
        elif risk == "Medium Risk":
            med_risk += 1
        else:
            low_risk += 1

    return {
        "total_machines": total,
        "failed_machines": failed,
        "healthy_machines": healthy,
        "average_health_score": avg_health,
        "high_risk_count": high_risk,
        "medium_risk_count": med_risk,
        "low_risk_count": low_risk,
        "health_distribution": [{"range": k, "count": v} for k, v in health_dist.items()],
    }


# ---------------------------------------------------------------------------
# Failure history helpers
# ---------------------------------------------------------------------------

def get_failure_summary(db: Session) -> Dict[str, Any]:
    """
    Aggregate failure statistics with the same shape as GET /failure-events/summary.
    Uses SQL aggregates so the router does not repeat the grouping queries.
    """
    total = db.query(func.count(FailureEvent.id)).scalar() or 0
    total_downtime = db.query(func.sum(FailureEvent.downtime_hours)).scalar() or 0.0
    avg_downtime = db.query(func.avg(FailureEvent.downtime_hours)).scalar() or 0.0
    avg_lead = db.query(func.avg(FailureEvent.pre_warning_lead_time_hours)).scalar() or 0.0

    by_type = dict(
        db.query(FailureEvent.failure_type, func.count(FailureEvent.id))
        .group_by(FailureEvent.failure_type)
        .all()
    )
    by_severity = dict(
        db.query(FailureEvent.severity, func.count(FailureEvent.id))
        .group_by(FailureEvent.severity)
        .all()
    )

    return {
        "total_failures": total,
        "total_downtime_hours": round(float(total_downtime), 1),
        "average_downtime_hours": round(float(avg_downtime), 1),
        "average_lead_time_hours": round(float(avg_lead), 1),
        "failures_by_type": by_type,
        "failures_by_severity": by_severity,
    }

