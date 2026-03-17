"""Box Agent definition for ADK deployment.

Defines root_agent for use with `adk deploy cloud_run --a2a`.
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
    generate_document,
    generate_document_batch,
    get_docgen_job_status,
    get_docgen_template_by_id,
    get_docgen_template_by_name,
    get_docgen_template_tags,
    get_file_content,
    get_file_info,
    get_folder_info,
    list_docgen_batch_jobs,
    list_docgen_templates,
    search_files,
    upload_file,
)

model = os.getenv("LITELLM_MODEL", "anthropic/claude-opus-4-6")

root_agent = LlmAgent(
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

**Document Generation (DocGen):**
- Box DocGen generates documents from .docx templates by merging data into tagged placeholders.
- Available templates include: QMSR Gap Risk Analysis, QMS Document Control Report, CAPA Completeness Report, and Remediation Plan.
- To generate a document: (1) find the template with `list_docgen_templates` or `get_docgen_template_by_name`, (2) discover required fields with `get_docgen_template_tags`, (3) generate the document with `generate_document` providing template_id, destination_folder_id, and user_input as a JSON string of field values.
- For batch generation of multiple documents from the same template, use `generate_document_batch`.
- After generating, check status with `get_docgen_job_status` or `list_docgen_batch_jobs` using the returned batch_id.
- Default output format is PDF; DOCX is also supported via the output_type parameter.
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
        list_docgen_templates,
        get_docgen_template_by_id,
        get_docgen_template_by_name,
        get_docgen_template_tags,
        generate_document,
        generate_document_batch,
        get_docgen_job_status,
        list_docgen_batch_jobs,
    ],
)
