from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class MaintenanceWorkOrder(Base):
    __tablename__ = "maintenance_work_orders"

    id = Column(String(32), primary_key=True)  # WO-2026-000001
    machine_id = Column(String(96), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(String(32), nullable=False, default="MEDIUM", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    work_order_type = Column(String(32), nullable=False)  # PREVENTIVE, CORRECTIVE, EMERGENCY, INSPECTION
    status = Column(String(32), nullable=False, default="PENDING", index=True)  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    description = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    scheduled_start_time = Column(DateTime, nullable=False)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    lead_technician_id = Column(String(32), ForeignKey("technicians.id", ondelete="SET NULL"), nullable=True, index=True)
    downtime_minutes = Column(Integer, nullable=False, default=0)
    cost = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    machine = relationship("Machine", back_populates="work_orders")
    lead_technician = relationship("Technician", back_populates="led_work_orders")
    parts_used = relationship("WorkOrderPart", back_populates="work_order", cascade="all, delete-orphan")
    assigned_technicians = relationship("WorkOrderTechnician", back_populates="work_order", cascade="all, delete-orphan")
    failure_events = relationship("FailureEvent", back_populates="work_order")

class WorkOrderPart(Base):
    __tablename__ = "work_order_parts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(String(32), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    part_id = Column(String(32), ForeignKey("parts.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity_used = Column(Integer, nullable=False, default=1)
    unit_cost_at_time = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("work_order_id", "part_id", name="uq_wo_part"),
    )

    work_order = relationship("MaintenanceWorkOrder", back_populates="parts_used")
    part = relationship("Part", back_populates="work_order_usages")

class WorkOrderTechnician(Base):
    __tablename__ = "work_order_technicians"

    id = Column(Integer, primary_key=True, autoincrement=True)
    work_order_id = Column(String(32), ForeignKey("maintenance_work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    technician_id = Column(String(32), ForeignKey("technicians.id", ondelete="CASCADE"), nullable=False, index=True)
    hours_spent = Column(Float, nullable=False, default=0.0)
    role_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("work_order_id", "technician_id", name="uq_wo_tech"),
    )

    work_order = relationship("MaintenanceWorkOrder", back_populates="assigned_technicians")
    technician = relationship("Technician", back_populates="work_order_assignments")
