"""Box Agent tool functions for document management and AI operations.

Provides tools for searching, reading, uploading, and querying documents
in Box using the box_ai_agents_toolkit and Box AI APIs.
"""

import logging
import os
from typing import Any, Optional

# IMPORTANT: Load .env BEFORE importing box_ai_agents_toolkit, because the
# toolkit reads BOX_CLIENT_ID/SECRET at module import time via its own load_dotenv().
from dotenv import load_dotenv

_agent_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_agent_dir, ".env"))
load_dotenv()  # project root fallback

from box_ai_agents_toolkit import (  # noqa: E402
    box_ai_agents_search_by_name,
    box_ai_ask_file_multi,
    box_ai_ask_file_single,
    box_ai_ask_hub,
    box_file_info,
    box_file_text_extract,
    box_file_upload,
    box_folder_create,
    box_folder_items_list,
    box_search,
    get_ccg_client,
)
from google.adk.tools.tool_context import ToolContext  # noqa: E402

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BOX_ROOT_FOLDER_ID = os.getenv("BOX_ROOT_FOLDER_ID", "0")


def _get_client():
    """Initialize and return a Box SDK Gen client using CCG authentication."""
    return get_ccg_client()


# ── Search & Read ──────────────────────────────────────────────────────


def search_files(
    query: str,
    file_extensions: Optional[str] = None,
    ancestor_folder_id: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Search for files in Box by keyword, with optional extension and folder filters.

    Args:
        query: Search keyword (e.g., 'CAPA procedure', 'incoming inspection').
        file_extensions: Comma-separated extensions to filter by (e.g., 'pdf,docx').
        ancestor_folder_id: Limit search to a specific folder and its subfolders.

    Returns:
        dict with status and list of matching files with id, name, and parent info.
    """
    try:
        logger.info("search_files: query='%s' ext=%s folder=%s", query, file_extensions, ancestor_folder_id)
        client = _get_client()

        ext_list = None
        if file_extensions:
            ext_list = [e.strip() for e in file_extensions.split(",")]

        ancestor_ids = None
        if ancestor_folder_id:
            ancestor_ids = [ancestor_folder_id]

        results = box_search(
            client, query=query,
            file_extensions=ext_list,
            ancestor_folder_ids=ancestor_ids,
        )

        files = []
        for item in results:
            files.append({
                "id": item.id,
                "name": item.name,
                "type": item.type.value if hasattr(item.type, "value") else str(item.type),
                "file_url": f"https://app.box.com/file/{item.id}",
            })

        logger.info("search_files: found %d results", len(files))
        return {"status": "success", "count": len(files), "files": files}

    except Exception as e:
        logger.error("search_files failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def get_file_content(
    file_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get the text content of a file from Box.

    Args:
        file_id: The Box file ID.

    Returns:
        dict with status and the file's text content.
    """
    try:
        logger.info("get_file_content: file_id=%s", file_id)
        client = _get_client()

        result = box_file_text_extract(client, file_id)

        logger.info("get_file_content: retrieved content for %s", file_id)
        return {
            "status": "success",
            "file_id": file_id,
            **result,
        }

    except Exception as e:
        logger.error("get_file_content failed: %s", e)
        return {"status": "error", "error_message": str(e), "file_id": file_id}


# ── CRUD Operations ────────────────────────────────────────────────────


def create_folder(
    folder_name: str,
    parent_folder_id: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Create a folder in Box.

    Args:
        folder_name: Name of the folder to create.
        parent_folder_id: ID of parent folder (defaults to root folder from env).

    Returns:
        dict with status, folder_id, folder_name, and folder_url.
    """
    try:
        logger.info("create_folder: %s", folder_name)
        client = _get_client()

        if parent_folder_id is None:
            parent_folder_id = BOX_ROOT_FOLDER_ID

        result = box_folder_create(client, name=folder_name, parent_folder_id=parent_folder_id)

        logger.info("create_folder: created %s", folder_name)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("create_folder failed: %s", e)
        return {"status": "error", "error_message": str(e), "folder_name": folder_name}


def upload_file(
    file_content: str,
    file_name: str,
    folder_id: Optional[str] = None,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Upload a file to Box.

    Args:
        file_content: The text content of the file to upload.
        file_name: Name for the uploaded file.
        folder_id: ID of the folder to upload to (defaults to root folder from env).

    Returns:
        dict with status, file_id, file_name, and file_url.
    """
    try:
        logger.info("upload_file: %s", file_name)
        client = _get_client()

        if folder_id is None:
            folder_id = BOX_ROOT_FOLDER_ID

        result = box_file_upload(
            client, content=file_content, file_name=file_name, parent_folder_id=folder_id,
        )

        logger.info("upload_file: uploaded %s", file_name)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("upload_file failed: %s", e)
        return {"status": "error", "error_message": str(e), "file_name": file_name}


def get_folder_info(
    folder_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get information about a Box folder and its contents.

    Args:
        folder_id: ID of the folder to get info for.

    Returns:
        dict with status, folder contents (files and subfolders), and total count.
    """
    try:
        logger.info("get_folder_info: %s", folder_id)
        client = _get_client()

        result = box_folder_items_list(client, folder_id)

        logger.info("get_folder_info: retrieved folder %s", folder_id)
        return {"status": "success", "folder_id": folder_id, **result}

    except Exception as e:
        logger.error("get_folder_info failed: %s", e)
        return {"status": "error", "error_message": str(e), "folder_id": folder_id}


def get_file_info(
    file_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get metadata about a Box file.

    Args:
        file_id: ID of the file to get info for.

    Returns:
        dict with status, file_id, file_name, and metadata.
    """
    try:
        logger.info("get_file_info: %s", file_id)
        client = _get_client()

        result = box_file_info(client, file_id)

        logger.info("get_file_info: retrieved file %s", file_id)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("get_file_info failed: %s", e)
        return {"status": "error", "error_message": str(e), "file_id": file_id}


# ── Box AI Operations ──────────────────────────────────────────────────


def find_ai_agent_by_name(
    agent_name: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Find a Box AI agent by name and return its ID and details.

    Args:
        agent_name: Name of the AI agent to search for.

    Returns:
        dict with status, agent_id, agent_name, and agent details if found.
    """
    try:
        logger.info("find_ai_agent_by_name: %s", agent_name)
        client = _get_client()

        result = box_ai_agents_search_by_name(client, name=agent_name)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("find_ai_agent_by_name failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def ask_ai_agent(
    item_id: str,
    item_type: str,
    agent_id: str,
    prompt: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Ask a question to a Box AI agent about a specific item.

    Args:
        item_id: ID of the item (file or hub) to ask about.
        item_type: Type of the item ('file' or 'hub').
        agent_id: ID of the AI agent to use.
        prompt: The question to ask.

    Returns:
        dict with status and the AI agent's answer.
    """
    try:
        logger.info("ask_ai_agent: agent=%s item=%s/%s", agent_id, item_type, item_id)
        client = _get_client()

        if item_type == "file":
            result = box_ai_ask_file_single(client, file_id=item_id, prompt=prompt, ai_agent_id=agent_id)
        elif item_type == "hub":
            result = box_ai_ask_hub(client, hub_id=item_id, prompt=prompt, ai_agent_id=agent_id)
        else:
            return {"status": "error", "error_message": f"Invalid item_type '{item_type}'. Must be 'file' or 'hub'."}

        return {"status": "success", **result}

    except Exception as e:
        logger.error("ask_ai_agent failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def ask_box_ai(
    file_id: str,
    question: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Ask Box AI a question about a single file (uses default Box AI, no custom agent required).

    Args:
        file_id: ID of the file to ask about.
        question: The question to ask about the file content.

    Returns:
        dict with status and the AI's answer.
    """
    try:
        logger.info("ask_box_ai: file=%s question='%s'", file_id, question[:80])
        client = _get_client()

        result = box_ai_ask_file_single(client, file_id=file_id, prompt=question)
        return {"status": "success", "file_id": file_id, **result}

    except Exception as e:
        logger.error("ask_box_ai failed: %s", e)
        return {"status": "error", "error_message": str(e), "file_id": file_id}


def ask_box_ai_multi(
    file_ids: str,
    question: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Ask Box AI a question across multiple files.

    Args:
        file_ids: Comma-separated list of Box file IDs (e.g., '123,456,789').
        question: The question to ask across all files.

    Returns:
        dict with status and the AI's synthesized answer.
    """
    try:
        ids = [fid.strip() for fid in file_ids.split(",") if fid.strip()]
        logger.info("ask_box_ai_multi: files=%s question='%s'", ids, question[:80])
        client = _get_client()

        result = box_ai_ask_file_multi(client, file_ids=ids, prompt=question)
        return {"status": "success", "file_ids": ids, **result}

    except Exception as e:
        logger.error("ask_box_ai_multi failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def ask_box_ai_hub(
    hub_id: str,
    question: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Ask Box AI a question about a Hub and its contents.

    Args:
        hub_id: ID of the Box Hub to query.
        question: The question to ask about the hub content.

    Returns:
        dict with status and the AI's answer.
    """
    try:
        logger.info("ask_box_ai_hub: hub=%s question='%s'", hub_id, question[:80])
        client = _get_client()

        result = box_ai_ask_hub(client, hub_id=hub_id, prompt=question)
        return {"status": "success", "hub_id": hub_id, **result}

    except Exception as e:
        logger.error("ask_box_ai_hub failed: %s", e)
        return {"status": "error", "error_message": str(e), "hub_id": hub_id}
