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
    box_docgen_create_batch,
    box_docgen_create_single_file_from_user_input,
    box_docgen_get_job_by_id,
    box_docgen_list_jobs_by_batch,
    box_docgen_template_get_by_id,
    box_docgen_template_get_by_name,
    box_docgen_template_list,
    box_docgen_template_list_tags,
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


def _box_file_url(file_id: str) -> str:
    """Return the Box web app URL for a file."""
    return f"https://app.box.com/file/{file_id}"


def _box_folder_url(folder_id: str) -> str:
    """Return the Box web app URL for a folder."""
    return f"https://app.box.com/folder/{folder_id}"


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
            "file_url": _box_file_url(file_id),
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

        folder_id = result.get("id", "")
        logger.info("create_folder: created %s", folder_name)
        return {"status": "success", "folder_url": _box_folder_url(folder_id), **result}

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

        file_id = result.get("id", "")
        logger.info("upload_file: uploaded %s", file_name)
        return {"status": "success", "file_url": _box_file_url(file_id), **result}

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
        return {"status": "success", "file_url": _box_file_url(file_id), **result}

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
    """Ask a question to a Box AI agent about a specific item or multiple items.

    Args:
        item_id: ID of the item (file or hub) to ask about. For multi-file queries,
            provide comma-separated file IDs (e.g., '123,456,789').
        item_type: Type of the item ('file', 'files', or 'hub').
            Use 'files' for multi-file queries with a custom agent.
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
        elif item_type == "files":
            file_ids = [fid.strip() for fid in item_id.split(",") if fid.strip()]
            result = box_ai_ask_file_multi(client, file_ids=file_ids, prompt=prompt, ai_agent_id=agent_id)
        elif item_type == "hub":
            result = box_ai_ask_hub(client, hub_id=item_id, prompt=prompt, ai_agent_id=agent_id)
        else:
            return {"status": "error", "error_message": f"Invalid item_type '{item_type}'. Must be 'file', 'files', or 'hub'."}

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


# ── Box DocGen Operations ─────────────────────────────────────────────


def list_docgen_templates(
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """List all available Box DocGen templates.

    Returns:
        dict with status and list of DocGen templates with id, name, and details.
    """
    try:
        logger.info("list_docgen_templates")
        client = _get_client()

        results = box_docgen_template_list(client)

        logger.info("list_docgen_templates: found %d templates", len(results))
        return {"status": "success", "count": len(results), "templates": results}

    except Exception as e:
        logger.error("list_docgen_templates failed: %s", e)
        return {"status": "error", "error_message": str(e)}


def get_docgen_template_by_id(
    template_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get details of a specific Box DocGen template by its ID.

    Args:
        template_id: The Box file ID of the DocGen template.

    Returns:
        dict with status and template metadata.
    """
    try:
        logger.info("get_docgen_template_by_id: %s", template_id)
        client = _get_client()

        result = box_docgen_template_get_by_id(client, template_id)

        logger.info("get_docgen_template_by_id: retrieved %s", template_id)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("get_docgen_template_by_id failed: %s", e)
        return {"status": "error", "error_message": str(e), "template_id": template_id}


def get_docgen_template_by_name(
    template_name: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Get details of a specific Box DocGen template by its name.

    Args:
        template_name: The name of the DocGen template to find.

    Returns:
        dict with status and template metadata.
    """
    try:
        logger.info("get_docgen_template_by_name: %s", template_name)
        client = _get_client()

        result = box_docgen_template_get_by_name(client, template_name)

        logger.info("get_docgen_template_by_name: found '%s'", template_name)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("get_docgen_template_by_name failed: %s", e)
        return {"status": "error", "error_message": str(e), "template_name": template_name}


def get_docgen_template_tags(
    template_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """List all tags (merge fields/placeholders) for a Box DocGen template.

    Use this to discover what data fields a template expects before generating a document.

    Args:
        template_id: The Box file ID of the DocGen template.

    Returns:
        dict with status and list of template tags (field names and types).
    """
    try:
        logger.info("get_docgen_template_tags: %s", template_id)
        client = _get_client()

        results = box_docgen_template_list_tags(client, template_id)

        logger.info("get_docgen_template_tags: found %d tags for %s", len(results), template_id)
        return {"status": "success", "template_id": template_id, "count": len(results), "tags": results}

    except Exception as e:
        logger.error("get_docgen_template_tags failed: %s", e)
        return {"status": "error", "error_message": str(e), "template_id": template_id}


GENERATED_REPORTS_FOLDER_ID = os.getenv("BOX_GENERATED_REPORTS_FOLDER_ID", "371602616529")

_DOCGEN_POLL_INTERVAL = 3   # seconds between status checks
_DOCGEN_MAX_WAIT = 120      # max seconds to wait for completion


def _parse_user_input_json(user_input):
    """Parse a JSON string from LLM output, handling common issues."""
    import json as _json

    if not isinstance(user_input, str):
        return user_input

    import re
    sanitized = re.sub(
        r'(?<=": ")((?:[^"\\]|\\.)*)(?=")',
        lambda m: m.group(0).replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t"),
        user_input,
    )
    try:
        return _json.loads(sanitized)
    except _json.JSONDecodeError:
        cleaned = user_input.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        return _json.loads(cleaned)


def _extract_batch_id(result: dict) -> str | None:
    """Extract batch ID from the toolkit's create response."""
    msg = result.get("message", "")
    if "id " in msg:
        return msg.split("id ")[-1].strip()
    return None


def _poll_batch_completion(client, batch_id: str) -> list[dict]:
    """Poll a DocGen batch until all jobs complete or timeout."""
    import time

    terminal_states = {"completed", "failed", "completed_with_error"}
    elapsed = 0

    while elapsed < _DOCGEN_MAX_WAIT:
        time.sleep(_DOCGEN_POLL_INTERVAL)
        elapsed += _DOCGEN_POLL_INTERVAL

        jobs = box_docgen_list_jobs_by_batch(client, batch_id)
        if not jobs or "error" in jobs[0]:
            logger.warning("_poll_batch_completion: error polling batch %s", batch_id)
            continue

        all_done = all(j.get("status") in terminal_states for j in jobs)
        if all_done:
            logger.info("_poll_batch_completion: batch %s finished in %ds", batch_id, elapsed)
            for job in jobs:
                _enrich_docgen_job(job)
            return jobs

        logger.debug("_poll_batch_completion: batch %s still processing (%ds)", batch_id, elapsed)

    logger.warning("_poll_batch_completion: batch %s timed out after %ds", batch_id, _DOCGEN_MAX_WAIT)
    jobs = box_docgen_list_jobs_by_batch(client, batch_id)
    for job in jobs:
        _enrich_docgen_job(job)
    return jobs


def generate_document(
    template_id: str,
    user_input: dict[str, Any],
    destination_folder_id: Optional[str] = None,
    generated_file_name: Optional[str] = None,
    output_type: str = "pdf",
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Generate a document from a Box DocGen template and wait for completion.

    Merges the provided data into a DocGen template, polls until the job
    finishes, and returns the output file URL directly.

    Args:
        template_id: The Box file ID of the DocGen template.
        user_input: Dictionary of key-value pairs to merge into the template fields.
            Must contain ALL template tag keys with populated values.
        destination_folder_id: The Box folder ID where the generated document will be saved.
            Defaults to the Generated Reports folder (371602616529).
        generated_file_name: Optional name for the output file (without extension).
        output_type: Output format — 'pdf' or 'docx' (defaults to 'pdf').

    Returns:
        dict with status, output file URL, and job details.
    """
    try:
        if not destination_folder_id:
            destination_folder_id = GENERATED_REPORTS_FOLDER_ID

        logger.info(
            "generate_document: template=%s folder=%s output=%s",
            template_id, destination_folder_id, output_type,
        )

        # Accept both dict and JSON string
        if isinstance(user_input, str):
            input_data = _parse_user_input_json(user_input)
        else:
            input_data = user_input

        # Log for debugging
        ui_type = type(user_input).__name__
        ui_preview = str(user_input)[:500] if user_input else "<EMPTY>"
        logger.info("generate_document: user_input type=%s preview=%s", ui_type, ui_preview)

        if not input_data or (isinstance(input_data, dict) and len(input_data) == 0):
            return {"status": "error", "error_message": "user_input is empty — no data to populate the template"}

        logger.info(
            "generate_document: parsed %d top-level keys: %s",
            len(input_data) if isinstance(input_data, dict) else 0,
            list(input_data.keys()) if isinstance(input_data, dict) else "not a dict",
        )

        result = box_docgen_create_single_file_from_user_input(
            client,
            docgen_template_id=template_id,
            destination_folder_id=destination_folder_id,
            user_input=input_data,
            generated_file_name=generated_file_name,
            output_type=output_type,
        )

        if "error" in result:
            return {"status": "error", "error_message": result["error"]}

        batch_id = _extract_batch_id(result)
        if not batch_id:
            return {"status": "error", "error_message": "Could not extract batch ID from response"}

        logger.info("generate_document: polling batch %s for completion", batch_id)
        jobs = _poll_batch_completion(client, batch_id)

        # Extract the output file info from the first (only) job
        job = jobs[0] if jobs else {}
        output_url = job.get("output_file_url")

        return {
            "status": "success",
            "output_file_url": output_url,
            "destination_folder_url": _box_folder_url(destination_folder_id),
            "job_status": job.get("status", "unknown"),
        }

    except Exception as e:
        logger.error("generate_document failed: %s", e)
        return {"status": "error", "error_message": str(e), "template_id": template_id}


def generate_document_batch(
    template_id: str,
    document_generation_data: str,
    destination_folder_id: Optional[str] = None,
    output_type: str = "pdf",
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Generate multiple documents from a Box DocGen template and wait for completion.

    Each entry in document_generation_data produces a separate output document.
    Polls until all jobs finish and returns output file URLs.

    Args:
        template_id: The Box file ID of the DocGen template.
        document_generation_data: JSON string — an array of objects, each with
            'generated_file_name' (str) and 'user_input' (dict of template field values).
        destination_folder_id: The Box folder ID where generated documents will be saved.
            Defaults to the Generated Reports folder (371602616529).
        output_type: Output format — 'pdf' or 'docx' (defaults to 'pdf').

    Returns:
        dict with status and list of output file URLs.
    """
    import json as _json

    try:
        if not destination_folder_id:
            destination_folder_id = GENERATED_REPORTS_FOLDER_ID

        logger.info(
            "generate_document_batch: template=%s folder=%s output=%s",
            template_id, destination_folder_id, output_type,
        )
        client = _get_client()

        if isinstance(document_generation_data, str):
            try:
                gen_data = _json.loads(document_generation_data)
            except _json.JSONDecodeError:
                cleaned = document_generation_data.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                gen_data = _json.loads(cleaned)
        else:
            gen_data = document_generation_data

        result = box_docgen_create_batch(
            client,
            docgen_template_id=template_id,
            destination_folder_id=destination_folder_id,
            document_generation_data=gen_data,
            output_type=output_type,
        )

        if "error" in result:
            return {"status": "error", "error_message": result["error"]}

        batch_id = _extract_batch_id(result)
        if not batch_id:
            return {"status": "error", "error_message": "Could not extract batch ID from response"}

        logger.info("generate_document_batch: polling batch %s for completion", batch_id)
        jobs = _poll_batch_completion(client, batch_id)

        output_files = [
            {"file_url": j.get("output_file_url"), "status": j.get("status", "unknown")}
            for j in jobs
        ]

        return {
            "status": "success",
            "count": len(output_files),
            "output_files": output_files,
            "destination_folder_url": _box_folder_url(destination_folder_id),
        }

    except Exception as e:
        logger.error("generate_document_batch failed: %s", e)
        return {"status": "error", "error_message": str(e), "template_id": template_id}


_METADATA_APPLIED: set[str] = set()


def _apply_regulatory_metadata(client, file_id: str) -> None:
    """Apply the regulatoryIntelligence metadata template to a generated file."""
    if file_id in _METADATA_APPLIED:
        return
    try:
        from box_sdk_gen.managers.file_metadata import CreateFileMetadataByIdScope

        client.file_metadata.create_file_metadata_by_id(
            file_id=file_id,
            scope=CreateFileMetadataByIdScope.ENTERPRISE,
            template_key="regulatoryIntelligence",
            request_body={"processingStatus": "Processing"},
        )
        _METADATA_APPLIED.add(file_id)
        logger.info("Applied regulatoryIntelligence metadata to file %s", file_id)
    except Exception as e:
        logger.warning("Failed to apply metadata to file %s: %s", file_id, e)


def _enrich_docgen_job(job: dict) -> None:
    """Add output_file_url to a DocGen job dict if output_file is present."""
    output_file = job.get("output_file")
    if isinstance(output_file, dict) and output_file.get("id"):
        file_id = output_file["id"]
        job["output_file_url"] = _box_file_url(file_id)
        _apply_regulatory_metadata(_get_client(), file_id)


def get_docgen_job_status(
    job_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """Check the status of a Box DocGen job.

    Args:
        job_id: The ID of the DocGen job to check.

    Returns:
        dict with status and job details including processing state and output file info.
    """
    try:
        logger.info("get_docgen_job_status: %s", job_id)
        client = _get_client()

        result = box_docgen_get_job_by_id(client, job_id)
        _enrich_docgen_job(result)

        logger.info("get_docgen_job_status: retrieved job %s", job_id)
        return {"status": "success", **result}

    except Exception as e:
        logger.error("get_docgen_job_status failed: %s", e)
        return {"status": "error", "error_message": str(e), "job_id": job_id}


def list_docgen_batch_jobs(
    batch_id: str,
    tool_context: Optional[ToolContext] = None,
) -> dict[str, Any]:
    """List all jobs in a Box DocGen batch to check their status and output files.

    Args:
        batch_id: The ID of the DocGen batch.

    Returns:
        dict with status and list of jobs in the batch.
    """
    try:
        logger.info("list_docgen_batch_jobs: %s", batch_id)
        client = _get_client()

        results = box_docgen_list_jobs_by_batch(client, batch_id)
        for job in results:
            _enrich_docgen_job(job)

        logger.info("list_docgen_batch_jobs: found %d jobs in batch %s", len(results), batch_id)
        return {"status": "success", "batch_id": batch_id, "count": len(results), "jobs": results}

    except Exception as e:
        logger.error("list_docgen_batch_jobs failed: %s", e)
        return {"status": "error", "error_message": str(e), "batch_id": batch_id}
