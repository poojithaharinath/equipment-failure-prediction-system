from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Part(Base):
    __tablename__ = "parts"

    id = Column(String(32), primary_key=True)  # PRT-0001
    part_number = Column(String(64), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False, index=True)  # BEARING, SEAL, MOTOR, SENSOR, FILTER, VALVE
    unit_cost = Column(Float, nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0, index=True)
    minimum_reorder_level = Column(Integer, nullable=False, default=5)
    manufacturer = Column(String(128), nullable=False)
    lead_time_days = Column(Integer, nullable=False, default=7)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work_order_usages = relationship("WorkOrderPart", back_populates="part")
