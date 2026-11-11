"""Initial schema with 10 main entities and audit/bridge tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-11-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Plants
    op.create_table(
        'plants',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('capacity_mw', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('commissioning_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('idx_plants_status', 'plants', ['status'])

    # 2. Production Lines
    op.create_table(
        'production_lines',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('plant_id', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('line_number', sa.Integer(), nullable=False),
        sa.Column('line_type', sa.String(length=64), nullable=False),
        sa.Column('target_units_per_hour', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPERATIONAL'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('plant_id', 'line_number', name='uq_plant_line_number')
    )
    op.create_index('idx_production_lines_plant_id', 'production_lines', ['plant_id'])
    op.create_index('idx_production_lines_status', 'production_lines', ['status'])

    # 3. Machines
    op.create_table(
        'machines',
        sa.Column('id', sa.String(length=96), nullable=False),
        sa.Column('line_id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('machine_type', sa.String(length=64), nullable=False),
        sa.Column('model_number', sa.String(length=64), nullable=False),
        sa.Column('serial_number', sa.String(length=64), nullable=False),
        sa.Column('installation_date', sa.Date(), nullable=False),
        sa.Column('criticality', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('health_score', sa.Float(), nullable=False, server_default='100.0'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='OPERATIONAL'),
        sa.Column('operating_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['line_id'], ['production_lines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number')
    )
    op.create_index('idx_machines_line_id', 'machines', ['line_id'])
    op.create_index('idx_machines_status', 'machines', ['status'])
    op.create_index('idx_machines_criticality', 'machines', ['criticality'])
    op.create_index('idx_machines_health_score', 'machines', ['health_score'])

    # 4. Sensors
    op.create_table(
        'sensors',
        sa.Column('id', sa.String(length=128), nullable=False),
        sa.Column('machine_id', sa.String(length=96), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('sensor_type', sa.String(length=32), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False),
        sa.Column('sampling_frequency_hz', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('min_threshold', sa.Float(), nullable=False),
        sa.Column('max_threshold', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('last_calibrated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_sensors_machine_id', 'sensors', ['machine_id'])
    op.create_index('idx_sensors_type', 'sensors', ['sensor_type'])
    op.create_index('idx_sensors_status', 'sensors', ['status'])

    # 5. Telemetry Events
    op.create_table(
        'telemetry_events',
        sa.Column('id', sa.String(length=160), nullable=False),
        sa.Column('sensor_id', sa.String(length=128), nullable=False),
        sa.Column('machine_id', sa.String(length=96), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('raw_value', sa.Float(), nullable=False),
        sa.Column('unit', sa.String(length=32), nullable=False),
        sa.Column('is_anomaly', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('anomaly_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sensor_id'], ['sensors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_telemetry_sensor_timestamp', 'telemetry_events', ['sensor_id', 'timestamp'])
    op.create_index('idx_telemetry_machine_timestamp', 'telemetry_events', ['machine_id', 'timestamp'])
    op.create_index('idx_telemetry_is_anomaly', 'telemetry_events', ['is_anomaly'])
    op.create_index('idx_telemetry_timestamp', 'telemetry_events', ['timestamp'])

    # 6. Operating Shifts
    op.create_table(
        'operating_shifts',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('plant_id', sa.String(length=32), nullable=False),
        sa.Column('shift_name', sa.String(length=64), nullable=False),
        sa.Column('shift_code', sa.String(length=32), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('shift_supervisor', sa.String(length=128), nullable=False),
        sa.Column('operating_mode', sa.String(length=32), nullable=False, server_default='FULL_CAPACITY'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['plant_id'], ['plants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_shifts_plant_id', 'operating_shifts', ['plant_id'])
    op.create_index('idx_shifts_start_time', 'operating_shifts', ['start_time'])

    # 7. Technicians
    op.create_table(
        'technicians',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('first_name', sa.String(length=64), nullable=False),
        sa.Column('last_name', sa.String(length=64), nullable=False),
        sa.Column('employee_code', sa.String(length=32), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('specialization', sa.String(length=64), nullable=False),
        sa.Column('skill_level', sa.String(length=32), nullable=False, server_default='SENIOR'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='AVAILABLE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('employee_code')
    )
    op.create_index('idx_technicians_status', 'technicians', ['status'])
    op.create_index('idx_technicians_specialization', 'technicians', ['specialization'])

    # 8. Parts
    op.create_table(
        'parts',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('part_number', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('unit_cost', sa.Float(), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('minimum_reorder_level', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('manufacturer', sa.String(length=128), nullable=False),
        sa.Column('lead_time_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('part_number')
    )
    op.create_index('idx_parts_category', 'parts', ['category'])
    op.create_index('idx_parts_stock', 'parts', ['stock_quantity'])

    # 9. Maintenance Work Orders
    op.create_table(
        'maintenance_work_orders',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('machine_id', sa.String(length=96), nullable=False),
        sa.Column('priority', sa.String(length=32), nullable=False, server_default='MEDIUM'),
        sa.Column('work_order_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('scheduled_start_time', sa.DateTime(), nullable=False),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('lead_technician_id', sa.String(length=32), nullable=True),
        sa.Column('downtime_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('cost', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lead_technician_id'], ['technicians.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_work_orders_machine_id', 'maintenance_work_orders', ['machine_id'])
    op.create_index('idx_work_orders_status', 'maintenance_work_orders', ['status'])
    op.create_index('idx_work_orders_priority', 'maintenance_work_orders', ['priority'])
    op.create_index('idx_work_orders_lead_tech', 'maintenance_work_orders', ['lead_technician_id'])

    # 10. Failure Events
    op.create_table(
        'failure_events',
        sa.Column('id', sa.String(length=32), nullable=False),
        sa.Column('machine_id', sa.String(length=96), nullable=False),
        sa.Column('failure_timestamp', sa.DateTime(), nullable=False),
        sa.Column('failure_type', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='CRITICAL'),
        sa.Column('pre_warning_lead_time_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('root_cause', sa.Text(), nullable=False),
        sa.Column('downtime_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('work_order_id', sa.String(length=32), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_failure_events_machine_id', 'failure_events', ['machine_id'])
    op.create_index('idx_failure_events_timestamp', 'failure_events', ['failure_timestamp'])
    op.create_index('idx_failure_events_type', 'failure_events', ['failure_type'])

    # 11. Work Order Parts Bridge
    op.create_table(
        'work_order_parts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('work_order_id', sa.String(length=32), nullable=False),
        sa.Column('part_id', sa.String(length=32), nullable=False),
        sa.Column('quantity_used', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit_cost_at_time', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['part_id'], ['parts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_order_id', 'part_id', name='uq_wo_part')
    )

    # 12. Work Order Technicians Bridge
    op.create_table(
        'work_order_technicians',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('work_order_id', sa.String(length=32), nullable=False),
        sa.Column('technician_id', sa.String(length=32), nullable=False),
        sa.Column('hours_spent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('role_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['technician_id'], ['technicians.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['work_order_id'], ['maintenance_work_orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('work_order_id', 'technician_id', name='uq_wo_tech')
    )

    # 13. Data Validation Exceptions
    op.create_table(
        'data_validation_exceptions',
        sa.Column('issue_id', sa.String(length=64), nullable=False),
        sa.Column('issue_type', sa.String(length=64), nullable=False),
        sa.Column('related_entity_id', sa.String(length=128), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False, server_default='HIGH'),
        sa.Column('resolution_status', sa.String(length=32), nullable=False, server_default='UNRESOLVED'),
        sa.Column('details_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('issue_id')
    )
    op.create_index('idx_validation_exceptions_type', 'data_validation_exceptions', ['issue_type'])
    op.create_index('idx_validation_exceptions_status', 'data_validation_exceptions', ['resolution_status'])
    op.create_index('idx_validation_exceptions_severity', 'data_validation_exceptions', ['severity'])

    # 14. Machine Health Audit Trail
    op.create_table(
        'machine_health_audit_trail',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('machine_id', sa.String(length=96), nullable=False),
        sa.Column('previous_status', sa.String(length=32), nullable=False),
        sa.Column('new_status', sa.String(length=32), nullable=False),
        sa.Column('previous_health_score', sa.Float(), nullable=False),
        sa.Column('new_health_score', sa.Float(), nullable=False),
        sa.Column('failure_probability', sa.Float(), nullable=True),
        sa.Column('risk_category', sa.String(length=32), nullable=True),
        sa.Column('trigger_event', sa.String(length=128), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_audit_machine_timestamp', 'machine_health_audit_trail', ['machine_id', 'timestamp'])

    # 15. Failure Prediction Logs
    op.create_table(
        'failure_prediction_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('machine_id', sa.String(length=96), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(), nullable=False),
        sa.Column('target_horizon_hours', sa.Integer(), nullable=False, server_default='24'),
        sa.Column('failure_probability', sa.Float(), nullable=False),
        sa.Column('risk_category', sa.String(length=32), nullable=False),
        sa.Column('contributing_factors', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['machine_id'], ['machines.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_pred_machine_timestamp', 'failure_prediction_logs', ['machine_id', 'prediction_timestamp'])
    op.create_index('idx_pred_risk', 'failure_prediction_logs', ['risk_category'])

def downgrade() -> None:
    op.drop_table('failure_prediction_logs')
    op.drop_table('machine_health_audit_trail')
    op.drop_table('data_validation_exceptions')
    op.drop_table('work_order_technicians')
    op.drop_table('work_order_parts')
    op.drop_table('failure_events')
    op.drop_table('maintenance_work_orders')
    op.drop_table('operating_shifts')
    op.drop_table('telemetry_events')
    op.drop_table('sensors')
    op.drop_table('machines')
    op.drop_table('production_lines')
    op.drop_table('plants')
    op.drop_table('parts')
    op.drop_table('technicians')
