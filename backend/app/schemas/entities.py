from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# ----------------- Plants -----------------
class PlantBase(BaseModel):
    name: str
    code: str
    location: str
    capacity_mw: float
    commissioning_date: date
    status: str = "ACTIVE"

class PlantCreate(PlantBase):
    id: str

class PlantResponse(PlantBase):
    id: str
    created_at: datetime
    updated_at: datetime
    line_count: Optional[int] = 0
    machine_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ----------------- Production Lines -----------------
class ProductionLineBase(BaseModel):
    plant_id: str
    name: str
    line_number: int
    line_type: str
    target_units_per_hour: int
    status: str = "OPERATIONAL"

class ProductionLineCreate(ProductionLineBase):
    id: str

class ProductionLineResponse(ProductionLineBase):
    id: str
    created_at: datetime
    updated_at: datetime
    machine_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ----------------- Machines -----------------
class MachineBase(BaseModel):
    line_id: str
    name: str
    machine_type: str
    model_number: str
    serial_number: str
    installation_date: date
    criticality: str = "MEDIUM"
    health_score: float = 100.0
    status: str = "OPERATIONAL"
    operating_hours: float = 0.0

class MachineCreate(MachineBase):
    id: str

class MachineUpdate(BaseModel):
    name: Optional[str] = None
    criticality: Optional[str] = None
    health_score: Optional[float] = None
    status: Optional[str] = None
    operating_hours: Optional[float] = None

class MachineResponse(MachineBase):
    id: str
    created_at: datetime
    updated_at: datetime
    sensor_count: Optional[int] = 0
    failure_probability_pct: Optional[float] = None
    risk_category: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- Sensors -----------------
class SensorBase(BaseModel):
    machine_id: str
    name: str
    sensor_type: str
    unit: str
    sampling_frequency_hz: float = 1.0
    min_threshold: float
    max_threshold: float
    status: str = "ACTIVE"

class SensorResponse(SensorBase):
    id: str
    last_calibrated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    latest_reading: Optional[float] = None
    latest_reading_time: Optional[datetime] = None

    class Config:
        from_attributes = True

# ----------------- Telemetry -----------------
class TelemetryEventCreate(BaseModel):
    sensor_id: str
    machine_id: str
    timestamp: Optional[datetime] = None
    value: float
    raw_value: Optional[float] = None
    unit: str

class TelemetryEventResponse(BaseModel):
    id: str
    sensor_id: str
    machine_id: str
    timestamp: datetime
    value: float
    raw_value: float
    unit: str
    is_anomaly: bool
    anomaly_score: float
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Technicians -----------------
class TechnicianBase(BaseModel):
    first_name: str
    last_name: str
    employee_code: str
    email: str
    phone: str
    specialization: str
    skill_level: str = "SENIOR"
    status: str = "AVAILABLE"

class TechnicianResponse(TechnicianBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Parts -----------------
class PartBase(BaseModel):
    part_number: str
    name: str
    category: str
    unit_cost: float
    stock_quantity: int
    minimum_reorder_level: int = 5
    manufacturer: str
    lead_time_days: int = 7

class PartResponse(PartBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ----------------- Work Orders -----------------
class WorkOrderPartUsage(BaseModel):
    part_id: str
    quantity: int = 1

class WorkOrderCreate(BaseModel):
    machine_id: str
    priority: str = "MEDIUM" # CRITICAL, HIGH, MEDIUM, LOW
    work_order_type: str = "PREVENTIVE" # PREVENTIVE, CORRECTIVE, EMERGENCY, INSPECTION
    description: str
    root_cause: Optional[str] = None
    scheduled_start_time: datetime
    lead_technician_id: Optional[str] = None
    parts_to_use: Optional[List[WorkOrderPartUsage]] = None

class WorkOrderStatusUpdate(BaseModel):
    status: str # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    downtime_minutes: Optional[int] = None
    cost: Optional[float] = None
    root_cause: Optional[str] = None

class WorkOrderResponse(BaseModel):
    id: str
    machine_id: str
    machine_name: Optional[str] = None
    priority: str
    work_order_type: str
    status: str
    description: str
    root_cause: Optional[str] = None
    scheduled_start_time: datetime
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    lead_technician_id: Optional[str] = None
    lead_technician_name: Optional[str] = None
    downtime_minutes: int
    cost: float
    created_at: datetime
    updated_at: datetime
    parts_used: Optional[List[Dict[str, Any]]] = None

    class Config:
        from_attributes = True

# ----------------- Failures -----------------
class FailureEventResponse(BaseModel):
    id: str
    machine_id: str
    machine_name: Optional[str] = None
    failure_timestamp: datetime
    failure_type: str
    severity: str
    pre_warning_lead_time_hours: float
    root_cause: str
    downtime_hours: float
    work_order_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ----------------- Predictions -----------------
class MachinePredictionResponse(BaseModel):
    machine_id: str
    machine_name: str
    machine_type: str
    line_id: str
    prediction_timestamp: datetime
    target_horizon_hours: int = 24
    failure_probability_pct: float
    risk_category: str # Low Risk, Medium Risk, High Risk
    health_score: float
    status: str
    features: Dict[str, float]
    contributing_factors: List[Dict[str, Any]]
    recommendation: str

# ----------------- Validation & Exceptions -----------------
class ValidationExceptionResponse(BaseModel):
    issue_id: str
    issue_type: str
    related_entity_id: str
    description: str
    timestamp: datetime
    severity: str
    resolution_status: str
    details_json: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ExceptionResolutionUpdate(BaseModel):
    resolution_status: str # RESOLVED, UNDER_REVIEW, DISMISSED
    resolution_notes: Optional[str] = None
