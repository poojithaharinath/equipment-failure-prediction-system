from datetime import datetime
from sqlalchemy import Column, String, Float, Date, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class Plant(Base):
    __tablename__ = "plants"

    id = Column(String(32), primary_key=True)  # PLT-001
    name = Column(String(128), nullable=False)
    code = Column(String(32), nullable=False, unique=True)
    location = Column(String(255), nullable=False)
    capacity_mw = Column(Float, nullable=False, default=0.0)
    commissioning_date = Column(Date, nullable=False)
    status = Column(String(32), nullable=False, default="ACTIVE")  # ACTIVE, INACTIVE, MAINTENANCE
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    production_lines = relationship("ProductionLine", back_populates="plant", cascade="all, delete-orphan")
    shifts = relationship("OperatingShift", back_populates="plant", cascade="all, delete-orphan")
