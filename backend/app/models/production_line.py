from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(String(64), primary_key=True)  # LINE-PLT-001-001
    plant_id = Column(String(32), ForeignKey("plants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    line_number = Column(Integer, nullable=False)
    line_type = Column(String(64), nullable=False)  # MACHINING, ASSEMBLY, PACKAGING, HYDRAULIC_PRESSING
    target_units_per_hour = Column(Integer, nullable=False, default=100)
    status = Column(String(32), nullable=False, default="OPERATIONAL", index=True)  # OPERATIONAL, DEGRADED, STOPPED
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("plant_id", "line_number", name="uq_plant_line_number"),
    )

    # Relationships
    plant = relationship("Plant", back_populates="production_lines")
    machines = relationship("Machine", back_populates="production_line", cascade="all, delete-orphan")
