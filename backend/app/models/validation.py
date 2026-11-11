from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Index
from backend.app.core.database import Base

class DataValidationException(Base):
    __tablename__ = "data_validation_exceptions"

    issue_id = Column(String(64), primary_key=True)  # VAL-20261022-0001
    issue_type = Column(String(64), nullable=False, index=True)
    # Types: UNKNOWN_SENSOR, OUT_OF_RANGE_READING, FAILURE_WITHOUT_WARNING, INVALID_MAINTENANCE_TIME, ZERO_INSTEAD_OF_MISSING, DUPLICATE_RECORD, FK_VIOLATION
    related_entity_id = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    severity = Column(String(32), nullable=False, default="HIGH", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    resolution_status = Column(String(32), nullable=False, default="UNRESOLVED", index=True)  # UNRESOLVED, UNDER_REVIEW, RESOLVED, DISMISSED
    details_json = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
