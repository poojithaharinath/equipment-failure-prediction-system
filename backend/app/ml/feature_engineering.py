import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.machine import Machine
from backend.app.models.sensor import Sensor
from backend.app.models.telemetry import TelemetryEvent
from backend.app.models.failure import FailureEvent
from backend.app.models.work_order import MaintenanceWorkOrder

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "avg_temperature_24h",
    "max_temperature_24h",
    "avg_vibration_24h",
    "vibration_trend",
    "pressure_fluctuation_24h",
    "current_fluctuation_24h",
    "avg_rpm_24h",
    "operating_hours",
    "missing_sensor_count",
    "previous_failure_count",
    "previous_maintenance_count",
]

class FeatureExtractor:
    """
    Extracts chronological, non-leaking feature windows for failure prediction within next 24 hours.
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_features_for_machine_at_time(
        self,
        machine: Machine,
        as_of_time: datetime,
        lookback_hours: int = 24
    ) -> Dict[str, float]:
        window_start = as_of_time - timedelta(hours=lookback_hours)
        window_start_6h = as_of_time - timedelta(hours=6)

        telemetries = self.db.query(
            TelemetryEvent.sensor_id,
            TelemetryEvent.timestamp,
            TelemetryEvent.value,
            Sensor.sensor_type
        ).join(
            Sensor, TelemetryEvent.sensor_id == Sensor.id
        ).filter(
            TelemetryEvent.machine_id == machine.id,
            TelemetryEvent.timestamp >= window_start,
            TelemetryEvent.timestamp <= as_of_time
        ).all()

        by_type: Dict[str, List[Tuple[datetime, float]]] = {}
        for s_id, ts, val, stype in telemetries:
            by_type.setdefault(stype, []).append((ts, val))

        temps = [v for ts, v in by_type.get("TEMPERATURE", [])]
        vibs = [v for ts, v in by_type.get("VIBRATION", [])]
        vibs_6h = [v for ts, v in by_type.get("VIBRATION", []) if ts >= window_start_6h]
        press = [v for ts, v in by_type.get("PRESSURE", [])]
        currs = [v for ts, v in by_type.get("CURRENT", [])]
        rpms = [v for ts, v in by_type.get("RPM", [])]

        avg_temp = float(np.mean(temps)) if temps else 65.0
        max_temp = float(np.max(temps)) if temps else 68.0
        avg_vib = float(np.mean(vibs)) if vibs else 1.8
        avg_vib_6h = float(np.mean(vibs_6h)) if vibs_6h else avg_vib

        vib_trend = float(avg_vib_6h / max(0.5, avg_vib)) if avg_vib > 0 else 1.0

        pressure_fluct = float(np.std(press)) if len(press) > 1 else 1.5
        current_fluct = float(np.std(currs)) if len(currs) > 1 else 2.0
        avg_rpm = float(np.mean(rpms)) if rpms else 1650.0

        expected_sensor_types = {"TEMPERATURE", "VIBRATION", "PRESSURE", "CURRENT", "RPM"}
        active_sensor_types = set(by_type.keys())
        missing_sensors = float(len(expected_sensor_types - active_sensor_types))

        prev_failures = self.db.query(func.count(FailureEvent.id)).filter(
            FailureEvent.machine_id == machine.id,
            FailureEvent.failure_timestamp < as_of_time
        ).scalar() or 0

        prev_work_orders = self.db.query(func.count(MaintenanceWorkOrder.id)).filter(
            MaintenanceWorkOrder.machine_id == machine.id,
            MaintenanceWorkOrder.scheduled_start_time < as_of_time
        ).scalar() or 0

        return {
            "avg_temperature_24h": round(avg_temp, 3),
            "max_temperature_24h": round(max_temp, 3),
            "avg_vibration_24h": round(avg_vib, 3),
            "vibration_trend": round(vib_trend, 3),
            "pressure_fluctuation_24h": round(pressure_fluct, 3),
            "current_fluctuation_24h": round(current_fluct, 3),
            "avg_rpm_24h": round(avg_rpm, 3),
            "operating_hours": round(float(machine.operating_hours), 1),
            "missing_sensor_count": missing_sensors,
            "previous_failure_count": float(prev_failures),
            "previous_maintenance_count": float(prev_work_orders),
        }

    def build_chronological_dataset(
        self,
        time_step_days: float = 3.0,
        prediction_horizon_hours: int = 24
    ) -> pd.DataFrame:
        """
        Ultra-fast grouped chronological dataset extraction.
        Groups telemetry by machine first, reducing filtering operations from 64,000 down to 100.
        """
        logger.info("Loading telemetry, machines, failures, and work orders into memory...")
        
        machines = {
            m.id: {"operating_hours": float(m.operating_hours), "name": m.name}
            for m in self.db.query(Machine).all()
        }

        sensors = {
            s.id: {"machine_id": s.machine_id, "sensor_type": s.sensor_type}
            for s in self.db.query(Sensor).all()
        }

        failures = [
            {"machine_id": f.machine_id, "failure_timestamp": f.failure_timestamp}
            for f in self.db.query(FailureEvent).all()
        ]
        fail_df = pd.DataFrame(failures)
        if not fail_df.empty:
            fail_df["failure_timestamp"] = pd.to_datetime(fail_df["failure_timestamp"])

        work_orders = [
            {"machine_id": wo.machine_id, "scheduled_start_time": wo.scheduled_start_time}
            for wo in self.db.query(MaintenanceWorkOrder).all()
        ]
        wo_df = pd.DataFrame(work_orders)
        if not wo_df.empty:
            wo_df["scheduled_start_time"] = pd.to_datetime(wo_df["scheduled_start_time"])

        tel_records = self.db.query(
            TelemetryEvent.sensor_id,
            TelemetryEvent.machine_id,
            TelemetryEvent.timestamp,
            TelemetryEvent.value
        ).all()
        tel_df = pd.DataFrame(tel_records, columns=["sensor_id", "machine_id", "timestamp", "value"])
        tel_df["timestamp"] = pd.to_datetime(tel_df["timestamp"])
        tel_df["sensor_type"] = tel_df["sensor_id"].map(lambda sid: sensors.get(sid, {}).get("sensor_type", "UNKNOWN"))

        logger.info(f"Loaded {len(tel_df)} telemetry points. Processing machine by machine...")

        min_ts = tel_df["timestamp"].min()
        max_ts = tel_df["timestamp"].max()

        # Regular timeline grid: 25 evenly-spaced sample points across 90 days
        base_sample_times = [
            min_ts + pd.Timedelta(days=2 + i * (86.0 / 25.0))
            for i in range(25)
        ]

        # Group telemetry by machine
        grouped_tel = dict(tuple(tel_df.groupby("machine_id")))
        records = []

        for m_id, m_meta in machines.items():
            m_tel = grouped_tel.get(m_id, pd.DataFrame())
            if m_tel.empty:
                continue

            # Failures for this specific machine
            m_fails = fail_df[fail_df["machine_id"] == m_id] if not fail_df.empty else pd.DataFrame()
            m_wos = wo_df[wo_df["machine_id"] == m_id] if not wo_df.empty else pd.DataFrame()

            # Machine-specific sample times: base times + pre-failure times for THIS machine only!
            m_sample_times = list(base_sample_times)
            if not m_fails.empty:
                for ft in m_fails["failure_timestamp"]:
                    for h_lead in [18, 12, 6, 2]:
                        pt = ft - pd.Timedelta(hours=h_lead)
                        if min_ts + pd.Timedelta(days=2) <= pt <= max_ts - pd.Timedelta(hours=prediction_horizon_hours):
                            m_sample_times.append(pt)

            m_sample_times = sorted(list(set(m_sample_times)))

            for as_of in m_sample_times:
                w_24h_start = as_of - pd.Timedelta(hours=24)
                w_6h_start = as_of - pd.Timedelta(hours=6)

                # Filter within this machine's small dataframe (~500 rows)
                m_sub = m_tel[(m_tel["timestamp"] >= w_24h_start) & (m_tel["timestamp"] <= as_of)]

                t_vals = m_sub[m_sub["sensor_type"] == "TEMPERATURE"]["value"]
                v_vals = m_sub[m_sub["sensor_type"] == "VIBRATION"]["value"]
                v_6h_vals = m_sub[(m_sub["sensor_type"] == "VIBRATION") & (m_sub["timestamp"] >= w_6h_start)]["value"]
                p_vals = m_sub[m_sub["sensor_type"] == "PRESSURE"]["value"]
                c_vals = m_sub[m_sub["sensor_type"] == "CURRENT"]["value"]
                r_vals = m_sub[m_sub["sensor_type"] == "RPM"]["value"]

                avg_temp = float(t_vals.mean()) if not t_vals.empty else 65.0
                max_temp = float(t_vals.max()) if not t_vals.empty else 68.0
                avg_vib = float(v_vals.mean()) if not v_vals.empty else 1.8
                avg_vib_6h = float(v_6h_vals.mean()) if not v_6h_vals.empty else avg_vib

                vib_trend = float(avg_vib_6h / max(0.5, avg_vib)) if avg_vib > 0 else 1.0
                p_fluct = float(p_vals.std()) if len(p_vals) > 1 else 1.5
                c_fluct = float(c_vals.std()) if len(c_vals) > 1 else 2.0
                avg_rpm = float(r_vals.mean()) if not r_vals.empty else 1650.0

                present_types = set(m_sub["sensor_type"].unique())
                missing_cnt = float(len({"TEMPERATURE", "VIBRATION", "PRESSURE", "CURRENT", "RPM"} - present_types))

                prev_fails = 0.0
                if not m_fails.empty:
                    prev_fails = float(len(m_fails[m_fails["failure_timestamp"] < as_of]))

                prev_wos = 0.0
                if not m_wos.empty:
                    prev_wos = float(len(m_wos[m_wos["scheduled_start_time"] < as_of]))

                failed_in_horizon = 0
                if not m_fails.empty:
                    upcoming = m_fails[
                        (m_fails["failure_timestamp"] > as_of) &
                        (m_fails["failure_timestamp"] <= as_of + pd.Timedelta(hours=prediction_horizon_hours))
                    ]
                    if not upcoming.empty:
                        failed_in_horizon = 1

                records.append({
                    "machine_id": m_id,
                    "as_of_time": as_of,
                    "avg_temperature_24h": round(avg_temp, 3),
                    "max_temperature_24h": round(max_temp, 3),
                    "avg_vibration_24h": round(avg_vib, 3),
                    "vibration_trend": round(vib_trend, 3),
                    "pressure_fluctuation_24h": round(p_fluct, 3),
                    "current_fluctuation_24h": round(c_fluct, 3),
                    "avg_rpm_24h": round(avg_rpm, 3),
                    "operating_hours": m_meta["operating_hours"],
                    "missing_sensor_count": missing_cnt,
                    "previous_failure_count": prev_fails,
                    "previous_maintenance_count": prev_wos,
                    "failure_in_24h": failed_in_horizon
                })

        dataset = pd.DataFrame(records)
        logger.info(f"Dataset successfully compiled: {len(dataset)} samples ({dataset['failure_in_24h'].sum()} failure positives).")
        return dataset
