"""FastMCP Server for SAP Agent Tools.

Exposes all SAP agent tools as MCP (Model Context Protocol) tools
using the FastMCP framework for standardized AI agent integration.
"""

import logging
from typing import Any, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from .sap_tools import (
    get_controlled_documents,
    get_quality_info_records,
    get_quality_notification_detail,
    get_quality_notifications,
    search_capa_actions,
)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mcp = FastMCP("SAP Agent MCP Server")


@mcp.tool()
def mcp_get_quality_notifications(
    status: Optional[str] = None,
    notification_type: Optional[str] = None,
    material: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> dict[str, Any]:
    """Get quality notifications (CAPAs) filtered by status, type, material, or date range."""
    try:
        logger.info("MCP: get_quality_notifications")
        return get_quality_notifications(status, notification_type, material, date_from, date_to)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_get_quality_notification_detail(
    notification_number: str,
) -> dict[str, Any]:
    """Get full detail for a single quality notification including CAPA hierarchy."""
    try:
        logger.info("MCP: get_quality_notification_detail %s", notification_number)
        return get_quality_notification_detail(notification_number)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_get_quality_info_records(
    material: Optional[str] = None,
    supplier: Optional[str] = None,
    plant: Optional[str] = None,
    blocked_only: bool = False,
) -> dict[str, Any]:
    """Get quality info records for procurement quality management."""
    try:
        logger.info("MCP: get_quality_info_records")
        return get_quality_info_records(material, supplier, plant, blocked_only)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_get_controlled_documents(
    document_type: Optional[str] = None,
    iso_reference: Optional[str] = None,
    status: Optional[str] = None,
    capa_reference: Optional[str] = None,
) -> dict[str, Any]:
    """Get controlled documents filtered by type, ISO reference, status, or CAPA reference."""
    try:
        logger.info("MCP: get_controlled_documents")
        return get_controlled_documents(document_type, iso_reference, status, capa_reference)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_search_capa_actions(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
) -> dict[str, Any]:
    """Search corrective and preventive actions across all quality notifications."""
    try:
        logger.info("MCP: search_capa_actions")
        return search_capa_actions(task_type, status)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


def main():
    """Run the SAP Agent MCP server."""
    logger.info("Starting SAP Agent MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
