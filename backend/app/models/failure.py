from datetime import datetime
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class FailureEvent(Base):
    __tablename__ = "failure_events"

    id = Column(String(32), primary_key=True)  # FAIL-2026-000001
    machine_id = Column(String(96), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    failure_timestamp = Column(DateTime, nullable=False, index=True)
    failure_type = Column(String(64), nullable=False, index=True)  # BEARING_WEAR, OVERHEATING, HYDRAULIC_LEAK, MOTOR_BURNOUT, SENSOR_DRIFT, MECHANICAL_JAM
    severity = Column(String(32), nullable=False, default="CRITICAL")  # CRITICAL, SEVERE, MODERATE
    pre_warning_lead_time_hours = Column(Float, nullable=False, default=0.0)
    root_cause = Column(Text, nullable=False)
    downtime_hours = Column(Float, nullable=False, default=0.0)
    work_order_id = Column(String(32), ForeignKey("maintenance_work_orders.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    machine = relationship("Machine", back_populates="failure_events")
    work_order = relationship("MaintenanceWorkOrder", back_populates="failure_events")
