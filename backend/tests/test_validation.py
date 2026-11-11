import pytest
from backend.app.core.database import SessionLocal
from backend.app.models.validation import DataValidationException
from backend.app.validation.validator import DataValidator

def test_five_negative_scenarios_captured():
    """Verify that all five required edge cases exist in data_validation_exceptions."""
    db = SessionLocal()
    try:
        validator = DataValidator(db)
        report = validator.run_all_validations()

        # Check breakdown
        breakdown = report["breakdown_by_category"]
        assert breakdown["unknown_sensors"] >= 1, "Edge Case 1 (Unknown Sensor) must be detected"
        assert breakdown["out_of_range_or_unit_mismatch"] >= 1, "Edge Case 2 (Out of Range / Invalid Unit) must be detected"
        assert breakdown["failure_without_lead_warning"] >= 1, "Edge Case 3 (Failure Without Warning) must be detected"
        assert breakdown["invalid_maintenance_timestamps"] >= 1, "Edge Case 4 (Inverted Maintenance Times) must be detected"
        assert breakdown["zero_instead_of_missing"] >= 1, "Edge Case 5 (Missing Represented as Zero) must be detected"

        # Check database records
        types = {
            r[0] for r in db.query(DataValidationException.issue_type).distinct().all()
        }
        assert "UNKNOWN_SENSOR" in types
        assert "OUT_OF_RANGE_READING" in types or "INVALID_UNIT" in types
        assert "FAILURE_WITHOUT_WARNING" in types
        assert "INVALID_MAINTENANCE_TIME" in types
        assert "ZERO_INSTEAD_OF_MISSING" in types
    finally:
        db.close()

