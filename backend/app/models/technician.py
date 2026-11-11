from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Technician(Base):
    __tablename__ = "technicians"

    id = Column(String(32), primary_key=True)  # TECH-001
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    employee_code = Column(String(32), nullable=False, unique=True)
    email = Column(String(128), nullable=False, unique=True)
    phone = Column(String(32), nullable=False)
    specialization = Column(String(64), nullable=False, index=True)  # MECHANICAL, ELECTRICAL, HYDRAULIC, SENSOR_CALIBRATION, AUTOMATION
    skill_level = Column(String(32), nullable=False, default="SENIOR")  # EXPERT, SENIOR, JUNIOR
    status = Column(String(32), nullable=False, default="AVAILABLE", index=True)  # AVAILABLE, ASSIGNED, ON_LEAVE
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    led_work_orders = relationship("MaintenanceWorkOrder", back_populates="lead_technician")
    work_order_assignments = relationship("WorkOrderTechnician", back_populates="technician")
