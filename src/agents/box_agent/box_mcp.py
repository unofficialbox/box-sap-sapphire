"""FastMCP Server for Box Agent Tools.

Exposes all Box agent tools as MCP (Model Context Protocol) tools
using the FastMCP framework for standardized AI agent integration.
"""

import logging
from typing import Any, Optional

from dotenv import load_dotenv
from fastmcp import FastMCP

from .box_tools import (
    ask_ai_agent,
    ask_box_ai,
    ask_box_ai_hub,
    ask_box_ai_multi,
    create_folder,
    find_ai_agent_by_name,
    get_file_content,
    get_file_info,
    get_folder_info,
    search_files,
    upload_file,
)

load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

mcp = FastMCP("Box Agent MCP Server")


@mcp.tool()
def mcp_search_files(
    query: str,
    file_extensions: Optional[str] = None,
    ancestor_folder_id: Optional[str] = None,
) -> dict[str, Any]:
    """Search for files in Box by keyword."""
    try:
        logger.info("MCP: search_files query='%s'", query)
        return search_files(query, file_extensions, ancestor_folder_id)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_get_file_content(file_id: str) -> dict[str, Any]:
    """Get the text content of a Box file."""
    try:
        logger.info("MCP: get_file_content %s", file_id)
        return get_file_content(file_id)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_create_folder(
    folder_name: str,
    parent_folder_id: Optional[str] = None,
) -> dict[str, Any]:
    """Create a folder in Box."""
    try:
        logger.info("MCP: create_folder '%s'", folder_name)
        return create_folder(folder_name, parent_folder_id)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_upload_file(
    file_content: str,
    file_name: str,
    folder_id: Optional[str] = None,
) -> dict[str, Any]:
    """Upload a file to Box."""
    try:
        logger.info("MCP: upload_file '%s'", file_name)
        return upload_file(file_content, file_name, folder_id)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_get_folder_info(folder_id: str) -> dict[str, Any]:
    """Get information about a Box folder and its contents."""
    try:
        logger.info("MCP: get_folder_info %s", folder_id)
        return get_folder_info(folder_id)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_get_file_info(file_id: str) -> dict[str, Any]:
    """Get metadata about a Box file."""
    try:
        logger.info("MCP: get_file_info %s", file_id)
        return get_file_info(file_id)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_ask_box_ai(file_id: str, question: str) -> dict[str, Any]:
    """Ask Box AI a question about a single file."""
    try:
        logger.info("MCP: ask_box_ai file=%s", file_id)
        return ask_box_ai(file_id, question)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_ask_box_ai_multi(file_ids: str, question: str) -> dict[str, Any]:
    """Ask Box AI a question across multiple files (comma-separated IDs)."""
    try:
        logger.info("MCP: ask_box_ai_multi files=%s", file_ids)
        return ask_box_ai_multi(file_ids, question)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_ask_box_ai_hub(hub_id: str, question: str) -> dict[str, Any]:
    """Ask Box AI a question about a Hub."""
    try:
        logger.info("MCP: ask_box_ai_hub hub=%s", hub_id)
        return ask_box_ai_hub(hub_id, question)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_find_ai_agent_by_name(agent_name: str) -> dict[str, Any]:
    """Find a Box AI agent by name."""
    try:
        logger.info("MCP: find_ai_agent_by_name '%s'", agent_name)
        return find_ai_agent_by_name(agent_name)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


@mcp.tool()
def mcp_ask_ai_agent(
    item_id: str,
    item_type: str,
    agent_id: str,
    prompt: str,
) -> dict[str, Any]:
    """Ask a question to a Box AI agent about a specific item."""
    try:
        logger.info("MCP: ask_ai_agent agent=%s item=%s/%s", agent_id, item_type, item_id)
        return ask_ai_agent(item_id, item_type, agent_id, prompt)
    except Exception as e:
        return {"status": "error", "error_type": "MCPException", "error_message": str(e)}


def main():
    """Run the Box Agent MCP server."""
    logger.info("Starting Box Agent MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
