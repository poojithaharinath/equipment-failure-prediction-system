import os
import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal, init_db
from backend.app.models.plant import Plant
from backend.app.models.production_line import ProductionLine
from backend.app.models.machine import Machine
from backend.app.models.sensor import Sensor
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.shift import OperatingShift
from backend.app.models.technician import Technician
from backend.app.models.part import Part
from backend.app.models.work_order import MaintenanceWorkOrder, WorkOrderPart, WorkOrderTechnician
from backend.app.models.failure import FailureEvent
from backend.app.models.audit import MachineHealthAuditTrail
from backend.app.validation.validator import DataValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataGenerator")

class SyntheticDataGenerator:
    """
    Industrial Synthetic Data Generator for Predictive Maintenance.
    Generates 3 plants, 12 production lines, 100 machines, 500 sensors,
    90 days of telemetry, 100-200 machine failures, work orders, parts,
    and 5 realistic edge cases. Fixed seed: 20261022.
    """

    def __init__(self, seed: int = 20261022, mode: str = "starter", db: Session = None):
        self.seed = seed
        self.mode = mode.lower()
        self.db = db
        self.random = random.Random(seed)
        np.random.seed(seed)

        # 90-day timeline ending at reference date
        self.end_time = datetime(2026, 11, 10, 23, 59, 59)
        self.start_time = self.end_time - timedelta(days=90)

        # Containers
        self.plants: List[Plant] = []
        self.lines: List[ProductionLine] = []
        self.machines: List[Machine] = []
        self.sensors: List[Sensor] = []
        self.technicians: List[Technician] = []
        self.parts: List[Part] = []
        self.shifts: List[OperatingShift] = []
        self.failures: List[FailureEvent] = []
        self.work_orders: List[MaintenanceWorkOrder] = []
        self.wo_parts: List[WorkOrderPart] = []
        self.wo_techs: List[WorkOrderTechnician] = []
        self.telemetry_events: List[TelemetryEvent] = []
        self.ground_truth_records: List[Dict[str, Any]] = []

    def set_seed(self):
        self.random.seed(self.seed)
        np.random.seed(self.seed)

    def generate_plants(self):
        logger.info("Generating 3 Plants...")
        plant_defs = [
            ("PLT-001", "Detroit Advanced Manufacturing Hub", "DAM-01", "Detroit, MI, USA", 45.0, datetime(2021, 3, 15).date()),
            ("PLT-002", "Stuttgart Precision Engineering Plant", "SPE-02", "Stuttgart, Germany", 60.0, datetime(2019, 8, 20).date()),
            ("PLT-003", "Yokohama Smart Robotics Facility", "YSR-03", "Yokohama, Japan", 55.0, datetime(2020, 11, 10).date())
        ]
        for pid, name, code, loc, cap, c_date in plant_defs:
            plant = Plant(
                id=pid,
                name=name,
                code=code,
                location=loc,
                capacity_mw=cap,
                commissioning_date=c_date,
                status="ACTIVE",
                created_at=self.start_time,
                updated_at=self.end_time
            )
            self.plants.append(plant)

    def generate_production_lines(self):
        logger.info("Generating 12 Production Lines (4 per plant)...")
        line_types = ["MACHINING", "ASSEMBLY", "HYDRAULIC_PRESSING", "PACKAGING"]
        for plant in self.plants:
            for l_idx in range(1, 5):
                line_id = f"LINE-{plant.id}-{l_idx:03d}"
                l_type = line_types[(l_idx - 1) % len(line_types)]
                line = ProductionLine(
                    id=line_id,
                    plant_id=plant.id,
                    name=f"{plant.name.split()[0]} Line {l_idx} - {l_type.title()}",
                    line_number=l_idx,
                    line_type=l_type,
                    target_units_per_hour=self.random.choice([80, 100, 120, 150]),
                    status="OPERATIONAL",
                    created_at=self.start_time,
                    updated_at=self.end_time
                )
                self.lines.append(line)

    def generate_machines(self):
        logger.info("Generating 100 Machines across 12 lines...")
        # 12 lines distribution: 8 lines with 8 machines, 4 lines with 9 machines = 64 + 36 = 100
        machine_counts = [8, 8, 8, 9, 8, 8, 8, 9, 8, 8, 9, 9]
        m_types = ["CNC_MILLING", "HYDRAULIC_PRESS", "ROBOTIC_ARM", "COMPRESSOR", "CONVEYOR", "TURBINE"]
        criticalities = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

        m_counter = 1
        for line, count in zip(self.lines, machine_counts):
            for m_num in range(1, count + 1):
                machine_id = f"MCH-{line.id}-{m_num:03d}"
                m_type = m_types[(m_counter - 1) % len(m_types)]
                crit = self.random.choice(criticalities)
                # Initial baseline health score (most healthy, a few degraded)
                initial_health = round(self.random.uniform(85.0, 99.5), 1)

                machine = Machine(
                    id=machine_id,
                    line_id=line.id,
                    name=f"{m_type.replace('_', ' ').title()} #{m_counter:03d}",
                    machine_type=m_type,
                    model_number=f"MDL-{m_type[:3]}-{self.random.randint(100, 999)}",
                    serial_number=f"SN-{self.random.randint(10000000, 99999999)}",
                    installation_date=(self.start_time - timedelta(days=self.random.randint(300, 1500))).date(),
                    criticality=crit,
                    health_score=initial_health,
                    status="OPERATIONAL",
                    operating_hours=round(self.random.uniform(2500.0, 18000.0), 1),
                    created_at=self.start_time,
                    updated_at=self.end_time
                )
                self.machines.append(machine)
                m_counter += 1

    def generate_sensors(self):
        logger.info("Generating 500 Sensors (5 per machine)...")
        sensor_configs = [
            ("TEMP-01", "Bearing Temperature Sensor", "TEMPERATURE", "Celsius", 1.0, 20.0, 95.0),
            ("VIB-01", "Triaxial Vibration Sensor", "VIBRATION", "mm/s", 1.0, 0.0, 6.0),
            ("PRESS-01", "Hydraulic / Inlet Pressure Sensor", "PRESSURE", "Bar", 1.0, 8.0, 40.0),
            ("CURR-01", "Motor Current Transducer", "CURRENT", "Amperes", 1.0, 10.0, 50.0),
            ("RPM-01", "Rotational Speed Tachometer", "RPM", "RPM", 1.0, 1000.0, 2200.0),
        ]
        for m in self.machines:
            for s_suffix, s_name, s_type, s_unit, freq, min_th, max_th in sensor_configs:
                s_id = f"SNS-{m.id}-{s_suffix}"
                sensor = Sensor(
                    id=s_id,
                    machine_id=m.id,
                    name=f"{m.name} {s_name}",
                    sensor_type=s_type,
                    unit=s_unit,
                    sampling_frequency_hz=freq,
                    min_threshold=min_th,
                    max_threshold=max_th,
                    status="ACTIVE",
                    last_calibrated_at=self.start_time + timedelta(days=self.random.randint(10, 60)),
                    created_at=self.start_time,
                    updated_at=self.end_time
                )
                self.sensors.append(sensor)

    def generate_technicians(self):
        logger.info("Generating Technicians...")
        names = [
            ("Marcus", "Vance", "MECHANICAL", "EXPERT"),
            ("Elena", "Rostova", "ELECTRICAL", "SENIOR"),
            ("Kenji", "Sato", "AUTOMATION", "EXPERT"),
            ("Sarah", "Jenkins", "HYDRAULIC", "SENIOR"),
            ("David", "Kim", "SENSOR_CALIBRATION", "SENIOR"),
            ("Liam", "O'Connor", "MECHANICAL", "JUNIOR"),
            ("Aisha", "Patel", "ELECTRICAL", "EXPERT"),
            ("Mateo", "Hernandez", "HYDRAULIC", "SENIOR"),
            ("Sophie", "Dubois", "AUTOMATION", "SENIOR"),
            ("Lucas", "Weber", "MECHANICAL", "SENIOR"),
            ("Yuki", "Tanaka", "SENSOR_CALIBRATION", "JUNIOR"),
            ("Chloe", "Martin", "ELECTRICAL", "JUNIOR"),
            ("Alexander", "Novak", "HYDRAULIC", "EXPERT"),
            ("Priya", "Sharma", "AUTOMATION", "EXPERT"),
            ("Carlos", "Gomez", "MECHANICAL", "SENIOR")
        ]
        for idx, (fn, ln, spec, skill) in enumerate(names, 1):
            t_id = f"TECH-{idx:03d}"
            tech = Technician(
                id=t_id,
                first_name=fn,
                last_name=ln,
                employee_code=f"EMP-2026-{idx:04d}",
                email=f"{fn.lower()}.{ln.lower()}@industrial-pm.com",
                phone=f"+1-555-{self.random.randint(100, 999)}-{self.random.randint(1000, 9999)}",
                specialization=spec,
                skill_level=skill,
                status="AVAILABLE",
                created_at=self.start_time
            )
            self.technicians.append(tech)

    def generate_parts(self):
        logger.info("Generating Spare Parts...")
        part_data = [
            ("SKF-6205-2RSH", "Deep Groove Ball Bearing 25x52x15mm", "BEARING", 45.0, 40, 10, "SKF Industrial", 5),
            ("NSK-7208-BEP", "Angular Contact Bearing 40x80x18mm", "BEARING", 120.0, 25, 8, "NSK Bearing", 7),
            ("TIM-32210", "Tapered Roller Bearing 50x90x24mm", "BEARING", 85.0, 30, 8, "Timken", 6),
            ("FKM-TC-45-65", "Viton Double Lip Shaft Oil Seal 45x65x8", "SEAL", 18.5, 60, 15, "Parker Hannifin", 3),
            ("NBR-OR-250", "Nitrile O-Ring High Pressure Pack", "SEAL", 12.0, 100, 20, "Freudenberg", 2),
            ("HYD-VALV-P40", "Hydraulic Directional Control Valve 40L/min", "VALVE", 240.0, 15, 5, "Bosch Rexroth", 14),
            ("PNEU-REG-FR", "Pneumatic Filter Regulator Lubricator Unit", "FILTER", 95.0, 20, 6, "SMC Pneumatics", 7),
            ("HYD-FLTR-10M", "High Pressure Hydraulic Return Filter 10 Micron", "FILTER", 65.0, 35, 10, "Eaton Vickers", 5),
            ("MOT-3PH-7KW", "3-Phase Induction Motor 7.5kW 4-Pole", "MOTOR", 850.0, 8, 2, "Siemens", 21),
            ("MOT-SRV-2KW", "AC Brushless Servo Motor 2.0kW with Brake", "MOTOR", 1450.0, 5, 2, "Yaskawa Electric", 30),
            ("DRV-VFD-11K", "Variable Frequency Drive Inverter 11kW", "MOTOR", 980.0, 6, 2, "ABB Robotics", 15),
            ("SNS-PT100-RTD", "PT100 RTD Industrial Temperature Probe", "SENSOR", 75.0, 50, 12, "Endress+Hauser", 4),
            ("SNS-ACC-100MV", "Piezoelectric Accelerometer 100 mV/g", "SENSOR", 310.0, 25, 8, "PCB Piezotronics", 10),
            ("SNS-PRS-40BAR", "Piezoresistive Pressure Transmitter 0-40 Bar", "SENSOR", 180.0, 20, 6, "WIKA Instrument", 7),
            ("SNS-CUR-100A", "Hall Effect Current Sensor 0-100A Split Core", "SENSOR", 110.0, 30, 8, "LEM Electronics", 5),
            ("SNS-OPT-TACH", "Optical Laser Tachometer Sensor 10-10000 RPM", "SENSOR", 145.0, 20, 5, "Keyence", 8),
            ("BLT-TIM-H200", "High-Torque Timing Belt H-Pitch 200 teeth", "BEARING", 35.0, 50, 12, "Gates Corporation", 4),
            ("CPL-FLX-D50", "Flexible Jaw Coupling 50mm Shaft Bore", "BEARING", 55.0, 30, 8, "Lovejoy", 5),
            ("LUB-SYN-ISO68", "Synthetic Industrial Gear Oil ISO VG 68 20L", "FILTER", 160.0, 25, 8, "Mobil Industrial", 3),
            ("LUB-GRE-HD2", "High-Temp Lithium Complex Grease 400g Cartridge", "FILTER", 14.0, 80, 20, "Castrol Heavy Duty", 2),
        ]
        for idx, (p_num, name, cat, cost, stock, min_reorder, mfr, lead) in enumerate(part_data, 1):
            p_id = f"PRT-{idx:04d}"
            part = Part(
                id=p_id,
                part_number=p_num,
                name=name,
                category=cat,
                unit_cost=cost,
                stock_quantity=stock,
                minimum_reorder_level=min_reorder,
                manufacturer=mfr,
                lead_time_days=lead,
                created_at=self.start_time,
                updated_at=self.end_time
            )
            self.parts.append(part)

    def generate_shifts(self):
        logger.info("Generating Operating Shifts across 90 days...")
        shift_templates = [
            ("Morning Shift", "SHF-MORN", 6, 14),
            ("Afternoon Shift", "SHF-AFTN", 14, 22),
            ("Night Shift", "SHF-NGHT", 22, 6),
        ]
        supervisors = ["John Davis", "Maria Santos", "Hiroshi Takahashi", "Hans Mueller"]

        # Sample shifts across plants
        cur_day = self.start_time.date()
        end_day = self.end_time.date()
        shift_id_counter = 1

        while cur_day <= end_day:
            for plant in self.plants:
                for s_name, s_code, s_start_h, s_end_h in shift_templates:
                    st = datetime.combine(cur_day, datetime.min.time()) + timedelta(hours=s_start_h)
                    if s_end_h < s_start_h:
                        et = datetime.combine(cur_day + timedelta(days=1), datetime.min.time()) + timedelta(hours=s_end_h)
                    else:
                        et = datetime.combine(cur_day, datetime.min.time()) + timedelta(hours=s_end_h)

                    shift = OperatingShift(
                        id=f"SHF-{plant.id}-{cur_day.strftime('%Y%m%d')}-{s_code[-4:]}",
                        plant_id=plant.id,
                        shift_name=s_name,
                        shift_code=s_code,
                        start_time=st,
                        end_time=et,
                        shift_supervisor=self.random.choice(supervisors),
                        operating_mode="FULL_CAPACITY",
                        created_at=st
                    )
                    self.shifts.append(shift)
                    shift_id_counter += 1
            cur_day += timedelta(days=7) # Sample weekly shifts to keep volume clean

    def generate_failures_and_work_orders(self):
        logger.info("Generating 120-150 Machine Failures and Maintenance Work Orders...")
        failure_types = [
            ("BEARING_WEAR", "Severe bearing race spalling, elevated high-frequency vibration and metal friction.", 36.0),
            ("OVERHEATING", "Thermal breakdown caused by cooling circulation loss and excessive coil current.", 24.0),
            ("HYDRAULIC_LEAK", "Seal rupture causing system pressure loss and irregular actuation speed.", 18.0),
            ("MOTOR_BURNOUT", "Phase insulation failure resulting from voltage spikes and harmonic load.", 12.0),
            ("SENSOR_DRIFT", "Calibration degradation causing erroneous feedback loop and motor stall.", 48.0),
            ("MECHANICAL_JAM", "Spindle or guide rail obstruction causing sudden rotor lockup.", 0.0) # Sudden failure!
        ]

        # Target between 120 and 150 failure events across the 90-day period
        num_failures = self.random.randint(120, 145)
        # Select machines that fail (some machines fail multiple times, e.g. 70-80 unique machines)
        failing_machines = self.random.choices(self.machines, k=num_failures)

        wo_counter = 1
        fail_counter = 1

        for idx, machine in enumerate(failing_machines):
            f_type, root_cause, nominal_lead_hours = self.random.choice(failure_types)
            # Pick a failure timestamp between start_time + 5 days and end_time - 1 day
            fail_day_offset = self.random.uniform(5.0, 88.0)
            fail_timestamp = self.start_time + timedelta(days=fail_day_offset)

            # Edge Case 3 injection: mechanical jam or sudden snap with zero pre-warning lead time
            if f_type == "MECHANICAL_JAM" or idx == 12:
                lead_time_hours = 0.0
            else:
                lead_time_hours = round(max(2.0, nominal_lead_hours + self.random.uniform(-6.0, 6.0)), 1)

            downtime_hours = round(self.random.uniform(2.5, 14.0), 1)
            severity = "CRITICAL" if downtime_hours > 8.0 or lead_time_hours == 0.0 else "SEVERE" if downtime_hours > 4.0 else "MODERATE"

            # Create corresponding maintenance work order
            wo_id = f"WO-2026-{wo_counter:06d}"
            wo_start = fail_timestamp + timedelta(minutes=self.random.randint(15, 45))
            wo_end = wo_start + timedelta(hours=downtime_hours)

            # Edge Case 4 injection: Inverted maintenance timestamps for 2 work orders
            if idx == 7: # Injection
                wo_end = wo_start - timedelta(hours=2.5) # actual_end_time earlier than start!

            tech = self.random.choice(self.technicians)
            wo = MaintenanceWorkOrder(
                id=wo_id,
                machine_id=machine.id,
                priority="CRITICAL" if severity == "CRITICAL" else "HIGH",
                work_order_type="EMERGENCY" if lead_time_hours == 0.0 else "CORRECTIVE",
                status="COMPLETED",
                description=f"Repair and restore {machine.name} following {f_type.replace('_', ' ').lower()}.",
                root_cause=root_cause,
                scheduled_start_time=wo_start,
                actual_start_time=wo_start,
                actual_end_time=wo_end,
                lead_technician_id=tech.id,
                downtime_minutes=int(downtime_hours * 60),
                cost=round(self.random.uniform(350.0, 2400.0), 2),
                created_at=wo_start,
                updated_at=wo_end
            )
            self.work_orders.append(wo)

            # Parts used in work order
            part_sample = self.random.sample(self.parts, k=self.random.randint(1, 3))
            for p in part_sample:
                qty = self.random.randint(1, 2)
                wop = WorkOrderPart(
                    work_order_id=wo.id,
                    part_id=p.id,
                    quantity_used=qty,
                    unit_cost_at_time=p.unit_cost,
                    created_at=wo_start
                )
                self.wo_parts.append(wop)

            # Technician assignment
            wot = WorkOrderTechnician(
                work_order_id=wo.id,
                technician_id=tech.id,
                hours_spent=downtime_hours,
                role_notes=f"Primary repair technician for {f_type}.",
                created_at=wo_start
            )
            self.wo_techs.append(wot)

            # Failure event record
            f_id = f"FAIL-2026-{fail_counter:06d}"
            failure = FailureEvent(
                id=f_id,
                machine_id=machine.id,
                failure_timestamp=fail_timestamp,
                failure_type=f_type,
                severity=severity,
                pre_warning_lead_time_hours=lead_time_hours,
                root_cause=root_cause,
                downtime_hours=downtime_hours,
                work_order_id=wo.id,
                created_at=fail_timestamp
            )
            self.failures.append(failure)

            # Ground truth entry
            self.ground_truth_records.append({
                "failure_id": f_id,
                "machine_id": machine.id,
                "failure_timestamp": fail_timestamp.isoformat(),
                "failure_type": f_type,
                "severity": severity,
                "lead_time_hours": lead_time_hours,
                "downtime_hours": downtime_hours,
                "work_order_id": wo_id,
                "is_zero_warning_anomaly": (lead_time_hours == 0.0)
            })

            # Update machine health score and status if failure was recent (last 7 days)
            days_ago = (self.end_time - fail_timestamp).total_seconds() / 86400.0
            if days_ago <= 1.0:
                machine.status = "FAILED"
                machine.health_score = round(self.random.uniform(15.0, 35.0), 1)
            elif days_ago <= 4.0:
                machine.status = "DEGRADED"
                machine.health_score = round(self.random.uniform(45.0, 68.0), 1)

            wo_counter += 1
            fail_counter += 1

    def generate_telemetry(self):
        logger.info(f"Generating Telemetry in {self.mode.upper()} mode...")
        # Map failures by machine
        failures_by_machine: Dict[str, List[FailureEvent]] = {}
        for f in self.failures:
            failures_by_machine.setdefault(f.machine_id, []).append(f)

        # Baseline sensors map
        sensors_by_machine: Dict[str, Dict[str, Sensor]] = {}
        for s in self.sensors:
            sensors_by_machine.setdefault(s.machine_id, {})[s.sensor_type] = s

        # In starter mode: generate observations across the 90 days
        # E.g., for each machine, 80-120 time points distributed across normal periods and pre-failure windows
        # Giving ~40,000 to 50,000 high-fidelity telemetry events across 500 sensors!
        if self.mode == "full":
            time_steps = 2500  # generates ~1.25M events
        else:
            time_steps = 90    # ~1 time point per day + pre-failure dense sampling (~45,000 events)

        # Base nominal values & standard deviations
        nominal_configs = {
            "TEMPERATURE": (65.0, 3.5, "Celsius"),
            "VIBRATION": (1.8, 0.4, "mm/s"),
            "PRESSURE": (22.0, 2.0, "Bar"),
            "CURRENT": (25.0, 2.5, "Amperes"),
            "RPM": (1650.0, 45.0, "RPM"),
        }

        telemetry_counter = 1
        edge_case_injected = False

        for m_idx, machine in enumerate(self.machines):
            m_sensors = sensors_by_machine.get(machine.id, {})
            m_failures = sorted(failures_by_machine.get(machine.id, []), key=lambda x: x.failure_timestamp)

            # Generate regular timeline timestamps
            timestamps = [
                self.start_time + timedelta(hours=h * (90 * 24 / time_steps))
                for h in range(time_steps)
            ]

            # Add dense pre-failure timestamps (24h before each failure)
            for f in m_failures:
                if f.pre_warning_lead_time_hours > 0:
                    for h_pre in [24, 18, 12, 6, 4, 2, 1]:
                        ts = f.failure_timestamp - timedelta(hours=h_pre)
                        if self.start_time <= ts <= self.end_time:
                            timestamps.append(ts)

            timestamps = sorted(list(set(timestamps)))

            for ts_idx, ts in enumerate(timestamps):
                # Determine machine operating condition at this timestamp:
                # Is machine within a pre-failure window?
                imminent_failure = None
                hours_to_failure = 9999.0
                for f in m_failures:
                    if f.failure_timestamp > ts:
                        diff_h = (f.failure_timestamp - ts).total_seconds() / 3600.0
                        if diff_h <= max(24.0, f.pre_warning_lead_time_hours):
                            imminent_failure = f
                            hours_to_failure = diff_h
                            break

                for s_type, sensor in m_sensors.items():
                    base_mean, base_std, unit = nominal_configs[s_type]
                    val = float(np.random.normal(base_mean, base_std))
                    is_anomaly = False
                    anomaly_score = 0.0

                    if imminent_failure:
                        # Gradual ramp-up towards failure
                        severity_factor = max(0.0, 1.0 - (hours_to_failure / 24.0)) # 0.0 -> 1.0
                        if imminent_failure.failure_type == "BEARING_WEAR":
                            if s_type == "VIBRATION":
                                val += severity_factor * 5.5 # Vibration ramps up past threshold
                                is_anomaly = (val > sensor.max_threshold)
                                anomaly_score = min(1.0, severity_factor * 0.95)
                            elif s_type == "TEMPERATURE":
                                val += severity_factor * 18.0
                        elif imminent_failure.failure_type == "OVERHEATING":
                            if s_type == "TEMPERATURE":
                                val += severity_factor * 28.0 # Temp exceeds 90-95°C
                                is_anomaly = (val > sensor.max_threshold)
                                anomaly_score = min(1.0, severity_factor * 0.98)
                            elif s_type == "CURRENT":
                                val += severity_factor * 16.0
                        elif imminent_failure.failure_type == "HYDRAULIC_LEAK":
                            if s_type == "PRESSURE":
                                val -= severity_factor * 15.0 # Pressure drops drastically
                                is_anomaly = (val < sensor.min_threshold)
                                anomaly_score = min(1.0, severity_factor * 0.90)
                        elif imminent_failure.failure_type == "MOTOR_BURNOUT":
                            if s_type == "CURRENT":
                                val += severity_factor * 26.0
                                is_anomaly = (val > sensor.max_threshold)
                                anomaly_score = min(1.0, severity_factor * 0.99)
                        elif imminent_failure.failure_type == "MECHANICAL_JAM":
                            if hours_to_failure <= 1.0:
                                if s_type == "RPM":
                                    val = 0.0
                                elif s_type == "CURRENT":
                                    val += 35.0
                                is_anomaly = True
                                anomaly_score = 1.0

                    # -------------------------------------------------------------
                    # EDGE CASE INJECTIONS (The 5 Required Negative Scenarios)
                    # -------------------------------------------------------------
                    target_sensor_id = sensor.id

                    # Edge Case 1: Unknown sensor ID telemetry event
                    if m_idx == 3 and s_type == "TEMPERATURE" and ts_idx == 10:
                        target_sensor_id = "SNS-UNKNOWN-999-TEMP-01" # UNKNOWN SENSOR!
                        is_anomaly = True
                        anomaly_score = 1.0

                    # Edge Case 2: Impossible sensor readings & invalid units
                    if m_idx == 5 and s_type == "TEMPERATURE" and ts_idx == 15:
                        val = 999.0 # Impossible temperature
                        is_anomaly = True
                        anomaly_score = 1.0
                    elif m_idx == 6 and s_type == "VIBRATION" and ts_idx == 20:
                        val = -22.5 # Negative vibration amplitude is physically impossible
                        is_anomaly = True
                        anomaly_score = 1.0
                    elif m_idx == 7 and s_type == "CURRENT" and ts_idx == 25:
                        unit = "Fahrenheit" # Invalid unit for electrical current!

                    # Edge Case 5: Missing sensor readings incorrectly represented as exact 0.000
                    if m_idx == 9 and s_type == "RPM" and ts_idx == 30:
                        val = 0.0 # Dropped telemetry represented as 0.000
                        is_anomaly = True

                    val = round(float(val), 2)
                    tel_id = f"TEL-{target_sensor_id}-{ts.strftime('%Y%m%d%H%M%S')}"

                    tel_event = TelemetryEvent(
                        id=tel_id,
                        sensor_id=target_sensor_id,
                        machine_id=machine.id,
                        timestamp=ts,
                        value=val,
                        raw_value=val,
                        unit=unit,
                        is_anomaly=is_anomaly,
                        anomaly_score=round(anomaly_score, 4),
                        created_at=ts
                    )
                    self.telemetry_events.append(tel_event)
                    telemetry_counter += 1

    def save_ground_truth(self):
        logger.info("Saving ground truth dataset to data/ground_truth/ground_truth.csv...")
        os.makedirs("data/ground_truth", exist_ok=True)
        gt_df = pd.DataFrame(self.ground_truth_records)
        gt_path = os.path.abspath("data/ground_truth/ground_truth.csv")
        gt_df.to_csv(gt_path, index=False)
        logger.info(f"Ground truth saved: {len(gt_df)} failure ground truth records at {gt_path}")

    def populate_database(self, batch_size: int = 2000):
        if not self.db:
            logger.warning("No database session provided. Skipping database commit.")
            return

        logger.info("Populating database with generated synthetic records...")
        # 1. Plants
        self.db.bulk_save_objects(self.plants)
        self.db.commit()

        # 2. Lines
        self.db.bulk_save_objects(self.lines)
        self.db.commit()

        # 3. Machines
        self.db.bulk_save_objects(self.machines)
        self.db.commit()

        # 4. Sensors
        self.db.bulk_save_objects(self.sensors)
        self.db.commit()

        # 5. Technicians & Parts
        self.db.bulk_save_objects(self.technicians)
        self.db.bulk_save_objects(self.parts)
        self.db.commit()

        # 6. Shifts
        self.db.bulk_save_objects(self.shifts)
        self.db.commit()

        # 7. Maintenance Work Orders & Failures
        self.db.bulk_save_objects(self.work_orders)
        self.db.commit()

        self.db.bulk_save_objects(self.failures)
        self.db.bulk_save_objects(self.wo_parts)
        self.db.bulk_save_objects(self.wo_techs)
        self.db.commit()

        # 8. Telemetry Events (in batches)
        logger.info(f"Saving {len(self.telemetry_events)} telemetry events in batches of {batch_size}...")
        for i in range(0, len(self.telemetry_events), batch_size):
            chunk = self.telemetry_events[i:i + batch_size]
            self.db.bulk_save_objects(chunk)
            self.db.commit()

        logger.info("All synthetic records persisted successfully.")

    def clean_existing_data(self):
        if not self.db:
            return
        logger.info("Cleaning existing database records prior to generation...")
        for tbl in [
            "data_validation_exceptions", "failure_prediction_logs", "machine_health_audit_trail",
            "work_order_technicians", "work_order_parts", "failure_events",
            "maintenance_work_orders", "operating_shifts", "telemetry_events",
            "sensors", "machines", "production_lines", "plants", "parts", "technicians"
        ]:
            try:
                self.db.execute(text(f"DELETE FROM {tbl}"))
            except Exception as e:
                logger.warning(f"Could not clear table {tbl}: {e}")
        self.db.commit()

    def run(self):
        self.clean_existing_data()
        self.set_seed()
        self.generate_plants()
        self.generate_production_lines()
        self.generate_machines()
        self.generate_sensors()
        self.generate_technicians()
        self.generate_parts()
        self.generate_shifts()
        self.generate_failures_and_work_orders()
        self.generate_telemetry()
        self.save_ground_truth()

        if self.db:
            self.populate_database()
            # Run validator to capture validation exceptions & edge cases
            validator = DataValidator(self.db)
            report = validator.run_all_validations()
            os.makedirs("data/reports", exist_ok=True)
            report_path = os.path.abspath("data/reports/validation_report.json")
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
            logger.info(f"Validation report saved: {report_path}")

        return {
            "plants": len(self.plants),
            "production_lines": len(self.lines),
            "machines": len(self.machines),
            "sensors": len(self.sensors),
            "technicians": len(self.technicians),
            "parts": len(self.parts),
            "shifts": len(self.shifts),
            "work_orders": len(self.work_orders),
            "failures": len(self.failures),
            "telemetry_events": len(self.telemetry_events),
        }

if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    try:
        gen = SyntheticDataGenerator(seed=20261022, mode="starter", db=db)
        summary = gen.run()
        print("Data Generation Complete:")
        print(json.dumps(summary, indent=2))
    finally:
        db.close()
