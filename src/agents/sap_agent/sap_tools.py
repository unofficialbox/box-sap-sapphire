"""SAP Agent tool functions for quality management queries.

Each tool queries BigTable (emulating SAP S/4HANA QM data) and returns
structured results following the A2A agent tool convention.
"""

import logging
from typing import Any, Optional

from google.adk.tools.tool_context import ToolContext

from .bigtable_client import BigTableClient

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_client() -> BigTableClient:
    return BigTableClient.get_instance()


def get_quality_notifications(
    status: Optional[str] = None,
    notification_type: Optional[str] = None,
    material: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get quality notifications (CAPAs) filtered by status, type, material, or date range.

    Args:
        status: Filter by notification status - COMPLETED or IN_PROCESS.
        notification_type: Filter by type - Q1 (customer complaint), Q2 (vendor complaint), Q3 (internal issue).
        material: Filter by material number (e.g., FG-00012345, RM-00034782).
        date_from: Filter notifications created on or after this date (YYYY-MM-DD).
        date_to: Filter notifications created on or before this date (YYYY-MM-DD).

    Returns:
        dict with status, count, and list of notification summaries (without nested CAPA details).
    """
    try:
        logger.info("get_quality_notifications: status=%s type=%s material=%s", status, notification_type, material)
        client = _get_client()
        results = client.get_quality_notifications(
            status=status,
            notification_type=notification_type,
            material=material,
        )

        # Date filtering
        if date_from:
            results = [r for r in results if r.get("CreationDate", "") >= date_from]
        if date_to:
            results = [r for r in results if r.get("CreationDate", "") <= date_to]

        # Return summaries (strip nested data)
        summaries = []
        for r in results:
            summaries.append({
                "QualityNotification": r.get("QualityNotification"),
                "NotificationType": r.get("NotificationType"),
                "NotificationText": r.get("NotificationText"),
                "NotificationPriority": r.get("NotificationPriority"),
                "NotificationStatus": r.get("NotificationStatus"),
                "Material": r.get("Material"),
                "Plant": r.get("Plant"),
                "CreationDate": r.get("CreationDate"),
                "Supplier": r.get("Supplier"),
                "Customer": r.get("Customer"),
            })

        logger.info("get_quality_notifications: found %d results", len(summaries))
        return {"status": "success", "count": len(summaries), "notifications": summaries}

    except Exception as e:
        logger.error("get_quality_notifications failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def get_quality_notification_detail(
    notification_number: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get full detail for a single quality notification including items, defects, causes, tasks (CAPAs), and activities.

    Args:
        notification_number: The 12-digit notification number (e.g., 000300000001).

    Returns:
        dict with status and the complete notification record including nested _Item, _Task, _Activity arrays.
    """
    try:
        logger.info("get_quality_notification_detail: %s", notification_number)
        client = _get_client()
        result = client.get_quality_notification_detail(notification_number)

        if result is None:
            return {"status": "not_found", "error_message": f"Notification {notification_number} not found"}

        logger.info("get_quality_notification_detail: found notification %s", notification_number)
        return {"status": "success", "notification": result}

    except Exception as e:
        logger.error("get_quality_notification_detail failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def get_quality_info_records(
    material: Optional[str] = None,
    supplier: Optional[str] = None,
    plant: Optional[str] = None,
    blocked_only: bool = False,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get quality info records for procurement quality management.

    Args:
        material: Filter by material number (e.g., FG-00012345, RM-00034782).
        supplier: Filter by supplier number (10-digit, e.g., 0000100234).
        plant: Filter by plant code (e.g., 1000, 1100, 2000).
        blocked_only: If true, only return records with procurement block (ProcurementBlock=99).

    Returns:
        dict with status, count, and list of quality info records.
    """
    try:
        logger.info("get_quality_info_records: material=%s supplier=%s plant=%s blocked=%s",
                     material, supplier, plant, blocked_only)
        client = _get_client()
        results = client.get_quality_info_records(
            material=material,
            supplier=supplier,
            plant=plant,
            blocked_only=blocked_only,
        )

        logger.info("get_quality_info_records: found %d results", len(results))
        return {"status": "success", "count": len(results), "records": results}

    except Exception as e:
        logger.error("get_quality_info_records failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def get_controlled_documents(
    document_type: Optional[str] = None,
    iso_reference: Optional[str] = None,
    status: Optional[str] = None,
    capa_reference: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get controlled documents filtered by type, ISO reference, status, or CAPA reference.

    Args:
        document_type: Filter by type - QM (quality manual), SOP, WI (work instruction), MDF (medical device file), VP (validation protocol), RPT (report).
        iso_reference: Filter by ISO 13485:2016 clause (e.g., 4.2.4, 8.5.2, 8.5.3).
        status: Filter by status - EFFECTIVE or IN_REVIEW.
        capa_reference: Filter by related CAPA notification number (e.g., 000300000005).

    Returns:
        dict with status, count, and list of controlled document records.
    """
    try:
        logger.info("get_controlled_documents: type=%s iso=%s status=%s capa=%s",
                     document_type, iso_reference, status, capa_reference)
        client = _get_client()
        results = client.get_controlled_documents(
            doc_type=document_type,
            iso_reference=iso_reference,
            status=status,
            capa_reference=capa_reference,
        )

        logger.info("get_controlled_documents: found %d results", len(results))
        return {"status": "success", "count": len(results), "documents": results}

    except Exception as e:
        logger.error("get_controlled_documents failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def search_capa_actions(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Search corrective and preventive actions across all quality notifications.

    Args:
        task_type: Filter by action type - CORRECTIVE or PREVENTIVE.
        status: Filter by task status - COMPLETED or IN_PROCESS.

    Returns:
        dict with status, count, and flat list of CAPA actions with parent notification context.
    """
    try:
        logger.info("search_capa_actions: task_type=%s status=%s", task_type, status)
        client = _get_client()
        results = client.search_capa_actions(
            task_type=task_type,
            status=status,
        )

        logger.info("search_capa_actions: found %d actions", len(results))
        return {"status": "success", "count": len(results), "actions": results}

    except Exception as e:
        logger.error("search_capa_actions failed: %s", e)
        return {"status": "error", "error_message": str(e)}
