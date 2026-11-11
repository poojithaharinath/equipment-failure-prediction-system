"""
Services package — business logic layer.

Modules:
  machine_service      — Machine queries, health updates, fleet summaries
  maintenance_service  — Work order creation, status transitions, technician assignment
"""
from backend.app.services.machine_service import (
    get_machine_or_404,
    get_latest_prediction,
    enrich_machine_with_prediction,
    query_machines,
    update_machine_fields,
    mark_machine_restored,
    get_sensor_summary,
    compute_health_distribution,
    get_fleet_summary,
    get_failure_summary,
)
from backend.app.services.maintenance_service import (
    next_work_order_id,
    get_work_order_response,
    list_work_orders,
    create_work_order,
    update_work_order_status,
    assign_technician,
)

__all__ = [
    # machine_service
    "get_machine_or_404",
    "get_latest_prediction",
    "enrich_machine_with_prediction",
    "query_machines",
    "update_machine_fields",
    "mark_machine_restored",
    "get_sensor_summary",
    "compute_health_distribution",
    "get_fleet_summary",
    "get_failure_summary",
    # maintenance_service
    "next_work_order_id",
    "get_work_order_response",
    "list_work_orders",
    "create_work_order",
    "update_work_order_status",
    "assign_technician",
]

