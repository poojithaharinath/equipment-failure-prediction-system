from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MachineHealthAuditTrail(Base):
    __tablename__ = "machine_health_audit_trail"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String(96), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(32), nullable=False)
    new_status = Column(String(32), nullable=False)
    previous_health_score = Column(Float, nullable=False)
    new_health_score = Column(Float, nullable=False)
    failure_probability = Column(Float, nullable=True)
    risk_category = Column(String(32), nullable=True)  # LOW, MEDIUM, HIGH
    trigger_event = Column(String(128), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    machine = relationship("Machine", back_populates="health_audits")

class FailurePredictionLog(Base):
    __tablename__ = "failure_prediction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String(96), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    target_horizon_hours = Column(Integer, nullable=False, default=24)
    failure_probability = Column(Float, nullable=False)  # 0.0000 to 1.0000
    risk_category = Column(String(32), nullable=False, index=True)  # Low Risk, Medium Risk, High Risk
    contributing_factors = Column(Text, nullable=True)  # JSON formatted key sensor contributions
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    machine = relationship("Machine", back_populates="prediction_logs")
