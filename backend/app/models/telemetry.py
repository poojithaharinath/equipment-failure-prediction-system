from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class TelemetryEvent(Base):
    __tablename__ = "telemetry_events"

    id = Column(String(160), primary_key=True)  # TEL-SENSOR-ID-TIMESTAMP
    # Soft reference (no FK): allows intentional UNKNOWN_SENSOR telemetry for data-quality edge cases.
    sensor_id = Column(String(128), nullable=False, index=True)
    machine_id = Column(String(96), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    raw_value = Column(Float, nullable=False)
    unit = Column(String(32), nullable=False)
    is_anomaly = Column(Boolean, nullable=False, default=False, index=True)
    anomaly_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_telemetry_sensor_timestamp", "sensor_id", "timestamp"),
        Index("idx_telemetry_machine_timestamp", "machine_id", "timestamp"),
    )

    # Relationships
    sensor = relationship(
        "Sensor",
        primaryjoin="TelemetryEvent.sensor_id==Sensor.id",
        foreign_keys=[sensor_id],
        viewonly=True,
    )
    machine = relationship("Machine", back_populates="telemetry_events")
