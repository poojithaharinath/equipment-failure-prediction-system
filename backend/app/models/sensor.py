from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String(128), primary_key=True)  # SNS-MACHINE-ID-TEMP-01
    machine_id = Column(String(96), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    sensor_type = Column(String(32), nullable=False, index=True)  # TEMPERATURE, VIBRATION, PRESSURE, CURRENT, RPM
    unit = Column(String(32), nullable=False)  # Celsius, mm/s, Bar, Amperes, RPM
    sampling_frequency_hz = Column(Float, nullable=False, default=1.0)
    min_threshold = Column(Float, nullable=False)
    max_threshold = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE", index=True)  # ACTIVE, FAULTY, CALIBRATING, OFFLINE
    last_calibrated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    machine = relationship("Machine", back_populates="sensors")
    telemetry_events = relationship(
        "TelemetryEvent",
        primaryjoin="Sensor.id==TelemetryEvent.sensor_id",
        foreign_keys="TelemetryEvent.sensor_id",
        viewonly=True,
    )
