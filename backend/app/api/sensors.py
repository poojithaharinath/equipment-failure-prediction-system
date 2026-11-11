from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.sensor import Sensor
from backend.app.models.telemetry import TelemetryEvent
from backend.app.schemas.entities import SensorResponse

router = APIRouter(prefix="/sensors", tags=["Sensors"])

@router.get("", response_model=List[SensorResponse])
def get_sensors(
    machine_id: Optional[str] = Query(None),
    sensor_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Sensor)
    if machine_id:
        query = query.filter(Sensor.machine_id == machine_id)
    if sensor_type:
        query = query.filter(Sensor.sensor_type == sensor_type)
    if status:
        query = query.filter(Sensor.status == status)

    sensors = query.all()
    res = []
    for s in sensors:
        latest = db.query(TelemetryEvent).filter(
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
            "latest_reading": latest.value if latest else None,
            "latest_reading_time": latest.timestamp if latest else None
        })
    return res

@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor(sensor_id: str, db: Session = Depends(get_db)):
    s = db.query(Sensor).filter(Sensor.id == sensor_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Sensor not found")

    latest = db.query(TelemetryEvent).filter(
        TelemetryEvent.sensor_id == s.id
    ).order_by(TelemetryEvent.timestamp.desc()).first()

    return {
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
        "latest_reading_time": latest.timestamp if latest else None
    }
