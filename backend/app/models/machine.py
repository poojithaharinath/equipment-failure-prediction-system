from datetime import datetime
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Machine(Base):
    __tablename__ = "machines"

    id = Column(String(96), primary_key=True)  # MCH-LINE-PLT-001-001-001
    line_id = Column(String(64), ForeignKey("production_lines.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    machine_type = Column(String(64), nullable=False)  # CNC_MILLING, HYDRAULIC_PRESS, ROBOTIC_ARM, COMPRESSOR, CONVEYOR, TURBINE
    model_number = Column(String(64), nullable=False)
    serial_number = Column(String(64), nullable=False, unique=True)
    installation_date = Column(Date, nullable=False)
    criticality = Column(String(32), nullable=False, default="MEDIUM", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    health_score = Column(Float, nullable=False, default=100.0, index=True)  # 0.0 to 100.0
    status = Column(String(32), nullable=False, default="OPERATIONAL", index=True)  # OPERATIONAL, DEGRADED, MAINTENANCE, FAILED, OFFLINE
    operating_hours = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    production_line = relationship("ProductionLine", back_populates="machines")
    sensors = relationship("Sensor", back_populates="machine", cascade="all, delete-orphan")
    work_orders = relationship("MaintenanceWorkOrder", back_populates="machine", cascade="all, delete-orphan")
    failure_events = relationship("FailureEvent", back_populates="machine", cascade="all, delete-orphan")
    telemetry_events = relationship("TelemetryEvent", back_populates="machine", cascade="all, delete-orphan")
    health_audits = relationship("MachineHealthAuditTrail", back_populates="machine", cascade="all, delete-orphan")
    prediction_logs = relationship("FailurePredictionLog", back_populates="machine", cascade="all, delete-orphan")
