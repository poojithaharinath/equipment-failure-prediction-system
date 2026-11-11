from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class OperatingShift(Base):
    __tablename__ = "operating_shifts"

    id = Column(String(64), primary_key=True)  # SHF-PLT-001-20261022-1
    plant_id = Column(String(32), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False, index=True)
    shift_name = Column(String(64), nullable=False)  # Morning, Afternoon, Night
    shift_code = Column(String(32), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    shift_supervisor = Column(String(128), nullable=False)
    operating_mode = Column(String(32), nullable=False, default="FULL_CAPACITY")  # FULL_CAPACITY, REDUCED, IDLE, MAINTENANCE
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    plant = relationship("Plant", back_populates="shifts")
