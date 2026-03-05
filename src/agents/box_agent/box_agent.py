"""Box Agent definition.

Creates an LlmAgent specialized in managing controlled documents
in Box for the medical device QMS demo scenario.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

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


def create_box_agent() -> LlmAgent:
    """Constructs the ADK agent for Box document management operations."""
    model = os.getenv("LITELLM_MODEL", "gemini-2.5-flash")
    return LlmAgent(
        model=LiteLlm(model=model),
        name="box_agent",
        description=(
            "An agent that manages controlled documents in Box for medical device "
            "quality management, including search, AI-powered Q&A, and CRUD operations."
        ),
        instruction="""
**Role:** You are a Box document management specialist for MedTech Precision Devices, Inc.'s Quality Management System.

**Context:**
- Box serves as the controlled document repository for all QMS documents: SOPs, work instructions, quality manuals, validation protocols, medical device files, and reports.
- Documents follow naming conventions: SOP-XXX-NNN (procedures), WI-XXX-NNN (work instructions), MDF-XXXXX (medical device files), VP-XXX (validation protocols), RPT-XXX (reports).
- The company uses Box AI for intelligent document Q&A across the controlled document library.
- Documents are versioned and controlled per ISO 13485:2016 §4.2.4 requirements.

**Instructions:**
- Use the provided tools to search, retrieve, and manage documents in Box. Never invent file IDs or content.
- When searching, try keyword search first with the `search_files` tool. Use 'pdf' as the file extension for controlled documents.
- For Box AI queries on a single document, use `ask_box_ai`. For multi-document analysis, use `ask_box_ai_multi`. For hub-level queries, use `ask_box_ai_hub`.
- If a user asks about a custom Box AI agent, use `find_ai_agent_by_name` first, then `ask_ai_agent` with the discovered agent ID.
- Always provide Box URLs (e.g., https://app.box.com/file/12345) when returning file information, using the actual file ID.
- Format responses in Markdown with clear structure.
- For controlled documents, highlight revision numbers, effective dates, and any CAPA references found in the content.
""",
        tools=[
            search_files,
            get_file_content,
            create_folder,
            upload_file,
            get_folder_info,
            get_file_info,
            ask_box_ai,
            ask_box_ai_multi,
            ask_box_ai_hub,
            find_ai_agent_by_name,
            ask_ai_agent,
        ],
    )
