-- ============================================================================
-- AI-Based Predictive Maintenance System - Database Schema (PostgreSQL DDL)
-- Version: 1.0.0
-- Created for: Equipment Failure Prediction System
--
-- REFERENCE ONLY. Runtime schema is applied by Alembic
-- (database/migrations/versions/001_initial_schema.py), which uses FLOAT and
-- naive TIMESTAMP types matching the SQLAlchemy models. This file may use
-- NUMERIC / TIMESTAMPTZ for readable PostgreSQL documentation.
-- telemetry_events.sensor_id has no FK (UNKNOWN_SENSOR edge case).
-- ============================================================================

-- Drop existing tables if re-initializing (in reverse dependency order)
DROP TABLE IF EXISTS failure_prediction_logs CASCADE;
DROP TABLE IF EXISTS machine_health_audit_trail CASCADE;
DROP TABLE IF EXISTS data_validation_exceptions CASCADE;
DROP TABLE IF EXISTS work_order_technicians CASCADE;
DROP TABLE IF EXISTS work_order_parts CASCADE;
DROP TABLE IF EXISTS failure_events CASCADE;
DROP TABLE IF EXISTS maintenance_work_orders CASCADE;
DROP TABLE IF EXISTS operating_shifts CASCADE;
DROP TABLE IF EXISTS telemetry_events CASCADE;
DROP TABLE IF EXISTS sensors CASCADE;
DROP TABLE IF EXISTS machines CASCADE;
DROP TABLE IF EXISTS production_lines CASCADE;
DROP TABLE IF EXISTS plants CASCADE;
DROP TABLE IF EXISTS parts CASCADE;
DROP TABLE IF EXISTS technicians CASCADE;

-- ----------------------------------------------------------------------------
-- 1. Plants
-- ----------------------------------------------------------------------------
CREATE TABLE plants (
    id VARCHAR(32) PRIMARY KEY, -- ID convention: PLT-001
    name VARCHAR(128) NOT NULL,
    code VARCHAR(32) NOT NULL UNIQUE,
    location VARCHAR(255) NOT NULL,
    capacity_mw NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    commissioning_date DATE NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, MAINTENANCE
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_plants_status ON plants(status);

-- ----------------------------------------------------------------------------
-- 2. Production Lines
-- ----------------------------------------------------------------------------
CREATE TABLE production_lines (
    id VARCHAR(64) PRIMARY KEY, -- ID convention: LINE-PLT-001-001
    plant_id VARCHAR(32) NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    line_number INTEGER NOT NULL,
    line_type VARCHAR(64) NOT NULL, -- MACHINING, ASSEMBLY, PACKAGING, HYDRAULIC_PRESSING
    target_units_per_hour INTEGER NOT NULL DEFAULT 100,
    status VARCHAR(32) NOT NULL DEFAULT 'OPERATIONAL', -- OPERATIONAL, DEGRADED, STOPPED
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_plant_line_number UNIQUE (plant_id, line_number)
);

CREATE INDEX idx_production_lines_plant_id ON production_lines(plant_id);
CREATE INDEX idx_production_lines_status ON production_lines(status);

-- ----------------------------------------------------------------------------
-- 3. Machines
-- ----------------------------------------------------------------------------
CREATE TABLE machines (
    id VARCHAR(96) PRIMARY KEY, -- ID convention: MCH-LINE-PLT-001-001-001
    line_id VARCHAR(64) NOT NULL REFERENCES production_lines(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    machine_type VARCHAR(64) NOT NULL, -- CNC_MILLING, HYDRAULIC_PRESS, ROBOTIC_ARM, COMPRESSOR, CONVEYOR, TURBINE
    model_number VARCHAR(64) NOT NULL,
    serial_number VARCHAR(64) NOT NULL UNIQUE,
    installation_date DATE NOT NULL,
    criticality VARCHAR(32) NOT NULL DEFAULT 'MEDIUM', -- CRITICAL, HIGH, MEDIUM, LOW
    health_score NUMERIC(5, 2) NOT NULL DEFAULT 100.00, -- 0.00 to 100.00
    status VARCHAR(32) NOT NULL DEFAULT 'OPERATIONAL', -- OPERATIONAL, DEGRADED, MAINTENANCE, FAILED, OFFLINE
    operating_hours NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_machines_line_id ON machines(line_id);
CREATE INDEX idx_machines_status ON machines(status);
CREATE INDEX idx_machines_criticality ON machines(criticality);
CREATE INDEX idx_machines_health_score ON machines(health_score);

-- ----------------------------------------------------------------------------
-- 4. Sensors
-- ----------------------------------------------------------------------------
CREATE TABLE sensors (
    id VARCHAR(128) PRIMARY KEY, -- ID convention: SNS-MACHINE-ID-TEMP-01
    machine_id VARCHAR(96) NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    name VARCHAR(128) NOT NULL,
    sensor_type VARCHAR(32) NOT NULL, -- TEMPERATURE, VIBRATION, PRESSURE, CURRENT, RPM
    unit VARCHAR(32) NOT NULL, -- Celsius, mm/s, Bar, Amperes, RPM
    sampling_frequency_hz NUMERIC(6, 2) NOT NULL DEFAULT 1.00,
    min_threshold NUMERIC(10, 2) NOT NULL,
    max_threshold NUMERIC(10, 2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, FAULTY, CALIBRATING, OFFLINE
    last_calibrated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sensors_machine_id ON sensors(machine_id);
CREATE INDEX idx_sensors_type ON sensors(sensor_type);
CREATE INDEX idx_sensors_status ON sensors(status);

-- ----------------------------------------------------------------------------
-- 5. Telemetry Events (Time-series machine data)
-- ----------------------------------------------------------------------------
CREATE TABLE telemetry_events (
    id VARCHAR(160) PRIMARY KEY, -- ID convention: TEL-SENSOR-ID-TIMESTAMP
    -- sensor_id is a soft reference (no FK) so UNKNOWN_SENSOR edge-case rows can persist under PostgreSQL.
    sensor_id VARCHAR(128) NOT NULL,
    machine_id VARCHAR(96) NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    raw_value NUMERIC(12, 4) NOT NULL,
    unit VARCHAR(32) NOT NULL,
    is_anomaly BOOLEAN NOT NULL DEFAULT FALSE,
    anomaly_score NUMERIC(6, 4) NOT NULL DEFAULT 0.0000,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_telemetry_sensor_timestamp ON telemetry_events(sensor_id, timestamp DESC);
CREATE INDEX idx_telemetry_machine_timestamp ON telemetry_events(machine_id, timestamp DESC);
CREATE INDEX idx_telemetry_is_anomaly ON telemetry_events(is_anomaly);
CREATE INDEX idx_telemetry_timestamp ON telemetry_events(timestamp DESC);

-- ----------------------------------------------------------------------------
-- 6. Operating Shifts
-- ----------------------------------------------------------------------------
CREATE TABLE operating_shifts (
    id VARCHAR(64) PRIMARY KEY, -- ID convention: SHF-PLT-001-20261022-1
    plant_id VARCHAR(32) NOT NULL REFERENCES plants(id) ON DELETE CASCADE,
    shift_name VARCHAR(64) NOT NULL, -- Morning, Afternoon, Night
    shift_code VARCHAR(32) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    shift_supervisor VARCHAR(128) NOT NULL,
    operating_mode VARCHAR(32) NOT NULL DEFAULT 'FULL_CAPACITY', -- FULL_CAPACITY, REDUCED, IDLE, MAINTENANCE
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shifts_plant_id ON operating_shifts(plant_id);
CREATE INDEX idx_shifts_start_time ON operating_shifts(start_time);

-- ----------------------------------------------------------------------------
-- 7. Technicians
-- ----------------------------------------------------------------------------
CREATE TABLE technicians (
    id VARCHAR(32) PRIMARY KEY, -- ID convention: TECH-001
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    employee_code VARCHAR(32) NOT NULL UNIQUE,
    email VARCHAR(128) NOT NULL UNIQUE,
    phone VARCHAR(32) NOT NULL,
    specialization VARCHAR(64) NOT NULL, -- MECHANICAL, ELECTRICAL, HYDRAULIC, SENSOR_CALIBRATION, AUTOMATION
    skill_level VARCHAR(32) NOT NULL DEFAULT 'SENIOR', -- EXPERT, SENIOR, JUNIOR
    status VARCHAR(32) NOT NULL DEFAULT 'AVAILABLE', -- AVAILABLE, ASSIGNED, ON_LEAVE
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_technicians_status ON technicians(status);
CREATE INDEX idx_technicians_specialization ON technicians(specialization);

-- ----------------------------------------------------------------------------
-- 8. Parts (Inventory)
-- ----------------------------------------------------------------------------
CREATE TABLE parts (
    id VARCHAR(32) PRIMARY KEY, -- ID convention: PRT-0001
    part_number VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL, -- BEARING, SEAL, MOTOR, SENSOR, FILTER, VALVE
    unit_cost NUMERIC(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    minimum_reorder_level INTEGER NOT NULL DEFAULT 5,
    manufacturer VARCHAR(128) NOT NULL,
    lead_time_days INTEGER NOT NULL DEFAULT 7,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parts_category ON parts(category);
CREATE INDEX idx_parts_stock ON parts(stock_quantity);

-- ----------------------------------------------------------------------------
-- 9. Maintenance Work Orders
-- ----------------------------------------------------------------------------
CREATE TABLE maintenance_work_orders (
    id VARCHAR(32) PRIMARY KEY, -- ID convention: WO-2026-000001
    machine_id VARCHAR(96) NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    priority VARCHAR(32) NOT NULL DEFAULT 'MEDIUM', -- CRITICAL, HIGH, MEDIUM, LOW
    work_order_type VARCHAR(32) NOT NULL, -- PREVENTIVE, CORRECTIVE, EMERGENCY, INSPECTION
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    description TEXT NOT NULL,
    root_cause TEXT,
    scheduled_start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_start_time TIMESTAMP WITH TIME ZONE,
    actual_end_time TIMESTAMP WITH TIME ZONE,
    lead_technician_id VARCHAR(32) REFERENCES technicians(id) ON DELETE SET NULL,
    downtime_minutes INTEGER NOT NULL DEFAULT 0,
    cost NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_work_orders_machine_id ON maintenance_work_orders(machine_id);
CREATE INDEX idx_work_orders_status ON maintenance_work_orders(status);
CREATE INDEX idx_work_orders_priority ON maintenance_work_orders(priority);
CREATE INDEX idx_work_orders_lead_tech ON maintenance_work_orders(lead_technician_id);

-- ----------------------------------------------------------------------------
-- 10. Failure Events
-- ----------------------------------------------------------------------------
CREATE TABLE failure_events (
    id VARCHAR(32) PRIMARY KEY, -- ID convention: FAIL-2026-000001
    machine_id VARCHAR(96) NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    failure_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    failure_type VARCHAR(64) NOT NULL, -- BEARING_WEAR, OVERHEATING, HYDRAULIC_LEAK, MOTOR_BURNOUT, SENSOR_DRIFT, MECHANICAL_JAM
    severity VARCHAR(32) NOT NULL DEFAULT 'CRITICAL', -- CRITICAL, SEVERE, MODERATE
    pre_warning_lead_time_hours NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    root_cause TEXT NOT NULL,
    downtime_hours NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    work_order_id VARCHAR(32) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_failure_events_machine_id ON failure_events(machine_id);
CREATE INDEX idx_failure_events_timestamp ON failure_events(failure_timestamp DESC);
CREATE INDEX idx_failure_events_type ON failure_events(failure_type);

-- ----------------------------------------------------------------------------
-- 11. Work Order Parts Bridge
-- ----------------------------------------------------------------------------
CREATE TABLE work_order_parts (
    id SERIAL PRIMARY KEY,
    work_order_id VARCHAR(32) NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
    part_id VARCHAR(32) NOT NULL REFERENCES parts(id) ON DELETE CASCADE,
    quantity_used INTEGER NOT NULL DEFAULT 1,
    unit_cost_at_time NUMERIC(10, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wo_part UNIQUE (work_order_id, part_id)
);

CREATE INDEX idx_wo_parts_wo ON work_order_parts(work_order_id);
CREATE INDEX idx_wo_parts_part ON work_order_parts(part_id);

-- ----------------------------------------------------------------------------
-- 12. Work Order Technicians Bridge
-- ----------------------------------------------------------------------------
CREATE TABLE work_order_technicians (
    id SERIAL PRIMARY KEY,
    work_order_id VARCHAR(32) NOT NULL REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
    technician_id VARCHAR(32) NOT NULL REFERENCES technicians(id) ON DELETE CASCADE,
    hours_spent NUMERIC(6, 2) NOT NULL DEFAULT 0.00,
    role_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_wo_tech UNIQUE (work_order_id, technician_id)
);

CREATE INDEX idx_wo_techs_wo ON work_order_technicians(work_order_id);
CREATE INDEX idx_wo_techs_tech ON work_order_technicians(technician_id);

-- ----------------------------------------------------------------------------
-- 13. Data Validation Exceptions (Audit of Edge Cases & Data Quality)
-- ----------------------------------------------------------------------------
CREATE TABLE data_validation_exceptions (
    issue_id VARCHAR(64) PRIMARY KEY, -- ID convention: VAL-20261022-0001
    issue_type VARCHAR(64) NOT NULL, -- UNKNOWN_SENSOR, OUT_OF_RANGE_READING, FAILURE_WITHOUT_WARNING, INVALID_MAINTENANCE_TIME, ZERO_INSTEAD_OF_MISSING, DUPLICATE_RECORD, FK_VIOLATION
    related_entity_id VARCHAR(128) NOT NULL,
    description TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    severity VARCHAR(32) NOT NULL DEFAULT 'HIGH', -- CRITICAL, HIGH, MEDIUM, LOW
    resolution_status VARCHAR(32) NOT NULL DEFAULT 'UNRESOLVED', -- UNRESOLVED, UNDER_REVIEW, RESOLVED, DISMISSED
    details_json TEXT, -- Additional diagnostic payload
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_validation_exceptions_type ON data_validation_exceptions(issue_type);
CREATE INDEX idx_validation_exceptions_status ON data_validation_exceptions(resolution_status);
CREATE INDEX idx_validation_exceptions_severity ON data_validation_exceptions(severity);

-- ----------------------------------------------------------------------------
-- 14. Machine Health Audit Trail (Historical Status & Health Changes)
-- ----------------------------------------------------------------------------
CREATE TABLE machine_health_audit_trail (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(96) NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    previous_status VARCHAR(32) NOT NULL,
    new_status VARCHAR(32) NOT NULL,
    previous_health_score NUMERIC(5, 2) NOT NULL,
    new_health_score NUMERIC(5, 2) NOT NULL,
    failure_probability NUMERIC(5, 2),
    risk_category VARCHAR(32), -- LOW, MEDIUM, HIGH
    trigger_event VARCHAR(128) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_machine_timestamp ON machine_health_audit_trail(machine_id, timestamp DESC);

-- ----------------------------------------------------------------------------
-- 15. Failure Prediction Logs (Audit trail of ML predictions)
-- ----------------------------------------------------------------------------
CREATE TABLE failure_prediction_logs (
    id SERIAL PRIMARY KEY,
    machine_id VARCHAR(96) NOT NULL REFERENCES machines(id) ON DELETE CASCADE,
    prediction_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    target_horizon_hours INTEGER NOT NULL DEFAULT 24,
    failure_probability NUMERIC(5, 4) NOT NULL, -- 0.0000 to 1.0000
    risk_category VARCHAR(32) NOT NULL, -- Low Risk, Medium Risk, High Risk
    contributing_factors TEXT, -- JSON payload of key sensor anomalies & weights
    recommendations TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pred_machine_timestamp ON failure_prediction_logs(machine_id, prediction_timestamp DESC);
CREATE INDEX idx_pred_risk ON failure_prediction_logs(risk_category);
