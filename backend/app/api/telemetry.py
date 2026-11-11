from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.core.database import get_db
from backend.app.models.sensor import Sensor
from backend.app.models.machine import Machine
from backend.app.models.telemetry import TelemetryEvent
from backend.app.schemas.entities import TelemetryEventCreate, TelemetryEventResponse
from backend.app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

@router.get("", response_model=PaginatedResponse[TelemetryEventResponse])
def get_telemetry_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    machine_id: Optional[str] = Query(None),
    sensor_id: Optional[str] = Query(None),
    is_anomaly: Optional[bool] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(TelemetryEvent)
    if machine_id:
        query = query.filter(TelemetryEvent.machine_id == machine_id)
    if sensor_id:
        query = query.filter(TelemetryEvent.sensor_id == sensor_id)
    if is_anomaly is not None:
        query = query.filter(TelemetryEvent.is_anomaly == is_anomaly)
    if start_time:
        query = query.filter(TelemetryEvent.timestamp >= start_time)
    if end_time:
        query = query.filter(TelemetryEvent.timestamp <= end_time)

    total = query.count()
    events = query.order_by(TelemetryEvent.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "items": events,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }

@router.get("/machine/{machine_id}/chart-data")
def get_machine_chart_data(
    machine_id: str,
    limit: int = Query(60, ge=10, le=200),
    db: Session = Depends(get_db)
):
    """
    Returns time-aligned multi-sensor series for dashboard visualization:
    Temperature, Vibration, Pressure, Current, RPM.
    """
    sensors = db.query(Sensor).filter(Sensor.machine_id == machine_id).all()
    if not sensors:
        raise HTTPException(status_code=404, detail=f"No sensors found for machine {machine_id}")

    sensor_map = {s.id: (s.sensor_type, s.unit, s.min_threshold, s.max_threshold) for s in sensors}

    # Query latest events for this machine
    events = db.query(
        TelemetryEvent.timestamp,
        TelemetryEvent.sensor_id,
        TelemetryEvent.value,
        TelemetryEvent.is_anomaly
    ).filter(
        TelemetryEvent.machine_id == machine_id
    ).order_by(TelemetryEvent.timestamp.desc()).limit(limit * 5).all()

    # Pivot by timestamp
    grouped: Dict[str, Dict[str, Any]] = {}
    for ts, s_id, val, is_anom in sorted(events, key=lambda x: x[0]):
        iso = ts.isoformat()
        if iso not in grouped:
            grouped[iso] = {
                "timestamp": iso,
                "formatted_time": ts.strftime("%m/%d %H:%M"),
                "is_anomaly": False
            }
        stype, unit, min_th, max_th = sensor_map.get(s_id, ("UNKNOWN", "", 0, 0))
        grouped[iso][stype.lower()] = val
        if is_anom:
            grouped[iso]["is_anomaly"] = True

    thresholds = {
        s.sensor_type.lower(): {
            "min": s.min_threshold,
            "max": s.max_threshold,
            "unit": s.unit
        }
        for s in sensors
    }

    return {
        "machine_id": machine_id,
        "points": list(grouped.values()),
        "thresholds": thresholds
    }

@router.get("/machine/{machine_id}/latest")
def get_machine_latest_telemetry(machine_id: str, db: Session = Depends(get_db)):
    sensors = db.query(Sensor).filter(Sensor.machine_id == machine_id).all()
    res = {}
    for s in sensors:
        latest = db.query(TelemetryEvent).filter(
            TelemetryEvent.sensor_id == s.id
        ).order_by(TelemetryEvent.timestamp.desc()).first()

        res[s.sensor_type.lower()] = {
            "sensor_id": s.id,
            "name": s.name,
            "value": latest.value if latest else None,
            "unit": s.unit,
            "min_threshold": s.min_threshold,
            "max_threshold": s.max_threshold,
            "is_anomaly": latest.is_anomaly if latest else False,
            "timestamp": latest.timestamp.isoformat() if latest else None
        }
    return res

@router.post("", response_model=TelemetryEventResponse)
def create_telemetry_event(payload: TelemetryEventCreate, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.id == payload.sensor_id).first()
    ts = payload.timestamp or datetime.utcnow()

    is_anomaly = False
    anomaly_score = 0.0

    if sensor:
        if payload.value > sensor.max_threshold or payload.value < sensor.min_threshold:
            is_anomaly = True
            delta = abs(payload.value - (sensor.max_threshold if payload.value > sensor.max_threshold else sensor.min_threshold))
            anomaly_score = min(1.0, round(delta / max(1.0, sensor.max_threshold), 4))
    else:
        # Unknown sensor!
        is_anomaly = True
        anomaly_score = 1.0

    tel_id = f"TEL-{payload.sensor_id}-{ts.strftime('%Y%m%d%H%M%S%f')[:17]}"
    tel = TelemetryEvent(
        id=tel_id,
        sensor_id=payload.sensor_id,
        machine_id=payload.machine_id,
        timestamp=ts,
        value=payload.value,
        raw_value=payload.raw_value if payload.raw_value is not None else payload.value,
        unit=payload.unit,
        is_anomaly=is_anomaly,
        anomaly_score=anomaly_score,
        created_at=datetime.utcnow()
    )
    db.add(tel)
    db.commit()
    db.refresh(tel)
    return tel
