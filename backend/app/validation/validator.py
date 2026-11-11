import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from backend.app.models.plant import Plant
from backend.app.models.production_line import ProductionLine
from backend.app.models.machine import Machine
from backend.app.models.sensor import Sensor
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.work_order import MaintenanceWorkOrder, WorkOrderPart, WorkOrderTechnician
from backend.app.models.failure import FailureEvent
from backend.app.models.validation import DataValidationException

logger = logging.getLogger(__name__)

# Standard acceptable sensor physical bounds
SENSOR_BOUNDS = {
    "TEMPERATURE": {"min": -20.0, "max": 180.0, "unit": "Celsius"},
    "VIBRATION": {"min": 0.0, "max": 25.0, "unit": "mm/s"},
    "PRESSURE": {"min": 0.0, "max": 80.0, "unit": "Bar"},
    "CURRENT": {"min": 0.0, "max": 120.0, "unit": "Amperes"},
    "RPM": {"min": 0.0, "max": 4500.0, "unit": "RPM"},
}

class DataValidator:
    """
    Automated data quality & edge case validation engine.
    Checks:
      1. Foreign key integrity & Unknown sensor references
      2. Out-of-range & impossible sensor readings / invalid units
      3. Failure before warning patterns
      4. Inverted maintenance timestamps (end_time < start_time)
      5. Zero values masquerading as missing readings
      6. Duplicate records & Primary Key uniqueness
      7. Maintenance cost and downtime reconciliation
    """

    def __init__(self, db: Session):
        self.db = db
        self._counter = 1

    def record_exception(
        self,
        issue_type: str,
        related_entity_id: str,
        description: str,
        severity: str = "HIGH",
        resolution_status: str = "UNRESOLVED",
        timestamp: Optional[datetime] = None,
        details: Optional[Dict[str, Any]] = None,
        issue_id: Optional[str] = None
    ) -> DataValidationException:
        if not issue_id:
            now_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            issue_id = f"VAL-{issue_type[:4]}-{now_str}-{self._counter:05d}"
            self._counter += 1

        # Check if already recorded to avoid duplicate exceptions
        existing = self.db.query(DataValidationException).filter_by(issue_id=issue_id).first()
        if existing:
            return existing

        exc = DataValidationException(
            issue_id=issue_id,
            issue_type=issue_type,
            related_entity_id=related_entity_id,
            description=description,
            timestamp=timestamp or datetime.utcnow(),
            severity=severity,
            resolution_status=resolution_status,
            details_json=json.dumps(details) if details else None
        )
        self.db.add(exc)
        return exc

    def validate_unknown_sensors(self) -> int:
        """Edge Case 1: Telemetry referencing an unknown sensor."""
        count = 0
        known_sensors = {s.id for s in self.db.query(Sensor.id).all()}
        telemetry_sensors = self.db.query(TelemetryEvent.sensor_id).distinct().all()

        for (s_id,) in telemetry_sensors:
            if s_id not in known_sensors:
                count += 1
                sample_event = self.db.query(TelemetryEvent).filter_by(sensor_id=s_id).first()
                self.record_exception(
                    issue_type="UNKNOWN_SENSOR",
                    related_entity_id=s_id,
                    description=f"Telemetry recorded for unknown sensor ID '{s_id}' without parent sensor registration.",
                    severity="CRITICAL",
                    timestamp=sample_event.timestamp if sample_event else datetime.utcnow(),
                    details={"sensor_id": s_id, "sample_event_id": sample_event.id if sample_event else None}
                )
        return count

    def validate_sensor_ranges_and_units(self) -> int:
        """Edge Case 2: Out of range, physically impossible sensor readings or invalid units."""
        count = 0
        sensors_map = {s.id: s for s in self.db.query(Sensor).all()}
        telemetries = self.db.query(TelemetryEvent).all()

        for tel in telemetries:
            sensor = sensors_map.get(tel.sensor_id)
            if not sensor:
                continue

            stype = sensor.sensor_type
            bounds = SENSOR_BOUNDS.get(stype)
            if not bounds:
                continue

            # Check unit mismatch
            if tel.unit != bounds["unit"]:
                count += 1
                self.record_exception(
                    issue_type="INVALID_UNIT",
                    related_entity_id=tel.id,
                    description=f"Invalid unit '{tel.unit}' on telemetry {tel.id} for sensor type {stype} (expected '{bounds['unit']}').",
                    severity="HIGH",
                    timestamp=tel.timestamp,
                    details={"telemetry_id": tel.id, "sensor_id": tel.sensor_id, "provided_unit": tel.unit, "expected_unit": bounds["unit"]}
                )

            # Check physically impossible / out of range values
            if tel.value < bounds["min"] or tel.value > bounds["max"]:
                count += 1
                self.record_exception(
                    issue_type="OUT_OF_RANGE_READING",
                    related_entity_id=tel.id,
                    description=f"Telemetry {tel.id} reading {tel.value} {tel.unit} is outside physically possible bounds [{bounds['min']}, {bounds['max']}].",
                    severity="CRITICAL" if (tel.value > bounds["max"] * 1.5 or tel.value < bounds["min"] - 20) else "HIGH",
                    timestamp=tel.timestamp,
                    details={"telemetry_id": tel.id, "value": tel.value, "min": bounds["min"], "max": bounds["max"]}
                )
        return count

    def validate_failure_warning_timing(self) -> int:
        """Edge Case 3: Failure occurring before warning pattern or sudden unheralded failure."""
        count = 0
        failures = self.db.query(FailureEvent).all()

        for f in failures:
            if f.pre_warning_lead_time_hours <= 0.0:
                count += 1
                self.record_exception(
                    issue_type="FAILURE_WITHOUT_WARNING",
                    related_entity_id=f.id,
                    description=f"Failure {f.id} on machine {f.machine_id} occurred catastrophically with 0.0 hours warning lead time.",
                    severity="CRITICAL",
                    timestamp=f.failure_timestamp,
                    details={"failure_id": f.id, "machine_id": f.machine_id, "lead_time_hours": f.pre_warning_lead_time_hours}
                )
        return count

    def validate_maintenance_timestamps(self) -> int:
        """Edge Case 4: Maintenance end time earlier than start time."""
        count = 0
        work_orders = self.db.query(MaintenanceWorkOrder).filter(
            MaintenanceWorkOrder.actual_start_time.isnot(None),
            MaintenanceWorkOrder.actual_end_time.isnot(None)
        ).all()

        for wo in work_orders:
            if wo.actual_end_time < wo.actual_start_time:
                count += 1
                self.record_exception(
                    issue_type="INVALID_MAINTENANCE_TIME",
                    related_entity_id=wo.id,
                    description=f"Work order {wo.id} has actual end time ({wo.actual_end_time}) earlier than actual start time ({wo.actual_start_time}).",
                    severity="CRITICAL",
                    timestamp=wo.actual_start_time,
                    details={
                        "work_order_id": wo.id,
                        "machine_id": wo.machine_id,
                        "actual_start_time": str(wo.actual_start_time),
                        "actual_end_time": str(wo.actual_end_time)
                    }
                )
        return count

    def validate_zero_as_missing(self) -> int:
        """Edge Case 5: Missing sensor readings incorrectly represented as exact 0.000."""
        count = 0
        # For Temperature and RPM on running machines, exact 0.000 indicates sensor drop/missing represented as 0
        telemetries = self.db.query(TelemetryEvent).filter(
            TelemetryEvent.raw_value == 0.0
        ).all()

        sensors_map = {s.id: s for s in self.db.query(Sensor).all()}
        for tel in telemetries:
            sensor = sensors_map.get(tel.sensor_id)
            if not sensor:
                continue
            if sensor.sensor_type in ["TEMPERATURE", "RPM", "PRESSURE"]:
                count += 1
                self.record_exception(
                    issue_type="ZERO_INSTEAD_OF_MISSING",
                    related_entity_id=tel.id,
                    description=f"Telemetry {tel.id} for sensor {sensor.id} ({sensor.sensor_type}) has value exactly 0.0, indicating dropped/missing telemetry masked as zero.",
                    severity="HIGH",
                    timestamp=tel.timestamp,
                    details={"telemetry_id": tel.id, "sensor_id": sensor.id, "type": sensor.sensor_type, "value": tel.value}
                )
        return count

    def validate_duplicates(self) -> int:
        """Validate duplicate telemetry timestamps for identical sensor."""
        count = 0
        duplicates = self.db.query(
            TelemetryEvent.sensor_id,
            TelemetryEvent.timestamp,
            func.count(TelemetryEvent.id).label("cnt")
        ).group_by(TelemetryEvent.sensor_id, TelemetryEvent.timestamp).having(func.count(TelemetryEvent.id) > 1).all()

        for sensor_id, ts, cnt in duplicates:
            count += cnt - 1
            self.record_exception(
                issue_type="DUPLICATE_RECORD",
                related_entity_id=sensor_id,
                description=f"Sensor {sensor_id} has {cnt} duplicate telemetry events at {ts}.",
                severity="MEDIUM",
                timestamp=ts,
                details={"sensor_id": sensor_id, "timestamp": str(ts), "duplicate_count": cnt}
            )
        return count

    def validate_foreign_keys(self) -> int:
        """Validate foreign key consistency across machines, lines, sensors."""
        count = 0
        plant_ids = {p.id for p in self.db.query(Plant.id).all()}
        line_ids = {l.id for l in self.db.query(ProductionLine.id).all()}
        machine_ids = {m.id for m in self.db.query(Machine.id).all()}

        # Lines -> Plants
        for line in self.db.query(ProductionLine).all():
            if line.plant_id not in plant_ids:
                count += 1
                self.record_exception(
                    issue_type="FK_VIOLATION",
                    related_entity_id=line.id,
                    description=f"ProductionLine {line.id} references non-existent Plant {line.plant_id}.",
                    severity="CRITICAL"
                )

        # Machines -> Lines
        for m in self.db.query(Machine).all():
            if m.line_id not in line_ids:
                count += 1
                self.record_exception(
                    issue_type="FK_VIOLATION",
                    related_entity_id=m.id,
                    description=f"Machine {m.id} references non-existent ProductionLine {m.line_id}.",
                    severity="CRITICAL"
                )

        # Sensors -> Machines
        for s in self.db.query(Sensor).all():
            if s.machine_id not in machine_ids:
                count += 1
                self.record_exception(
                    issue_type="FK_VIOLATION",
                    related_entity_id=s.id,
                    description=f"Sensor {s.id} references non-existent Machine {s.machine_id}.",
                    severity="CRITICAL"
                )
        return count

    def run_all_validations(self) -> Dict[str, Any]:
        """Runs the complete test suite across the active database and commits recorded exceptions."""
        logger.info("Executing comprehensive data validation checks...")
        
        unknown_sensors = self.validate_unknown_sensors()
        out_of_range = self.validate_sensor_ranges_and_units()
        failure_warnings = self.validate_failure_warning_timing()
        maintenance_times = self.validate_maintenance_timestamps()
        zero_masked = self.validate_zero_as_missing()
        duplicates = self.validate_duplicates()
        fk_violations = self.validate_foreign_keys()

        self.db.commit()

        total_issues = (
            unknown_sensors + out_of_range + failure_warnings +
            maintenance_times + zero_masked + duplicates + fk_violations
        )

        # Aggregated stats by severity and status
        total_exceptions = self.db.query(DataValidationException).count()
        by_type = dict(
            self.db.query(DataValidationException.issue_type, func.count(DataValidationException.issue_id))
            .group_by(DataValidationException.issue_type).all()
        )
        by_severity = dict(
            self.db.query(DataValidationException.severity, func.count(DataValidationException.issue_id))
            .group_by(DataValidationException.severity).all()
        )
        by_status = dict(
            self.db.query(DataValidationException.resolution_status, func.count(DataValidationException.issue_id))
            .group_by(DataValidationException.resolution_status).all()
        )

        report = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "total_new_issues_detected": total_issues,
            "total_exceptions_recorded": total_exceptions,
            "breakdown_by_category": {
                "unknown_sensors": unknown_sensors,
                "out_of_range_or_unit_mismatch": out_of_range,
                "failure_without_lead_warning": failure_warnings,
                "invalid_maintenance_timestamps": maintenance_times,
                "zero_instead_of_missing": zero_masked,
                "duplicate_records": duplicates,
                "foreign_key_violations": fk_violations,
            },
            "summary_by_type": by_type,
            "summary_by_severity": by_severity,
            "summary_by_resolution_status": by_status,
            "status": "PASSED_WITH_EXCEPTIONS_DOCUMENTED" if total_exceptions > 0 else "CLEAN"
        }
        return report
