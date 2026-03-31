"""Box Agent definition.

Creates a lightweight router agent with two specialized sub-agents:
one for document ops and one for workflow-specific report generation.
"""

import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .box_tools import (
    ask_box_ai,
    ask_box_ai_hub,
    ask_box_ai_multi,
    create_folder,
    generate_remediation_plan,
    get_file_content,
    get_file_info,
    get_folder_info,
    run_capa_report,
    run_gap_analysis,
    run_sop_impact_analysis,
    search_files,
    upload_file,
)


def _create_document_agent(model: str) -> LlmAgent:
    """Sub-agent for searching, reading, and managing files/folders in Box."""
    return LlmAgent(
        model=LiteLlm(model=model),
        name="box_document_agent",
        description=(
            "Searches, retrieves, and manages documents and folders in Box, "
            "including Box AI Q&A on single files, multiple files, and Hubs."
        ),
        instruction="""You are a Box document specialist for MedTech Precision Devices, Inc.

- Box stores all QMS controlled documents: SOPs, work instructions, quality manuals, validation protocols, medical device files, and reports.
- Document naming: SOP-XXX-NNN, WI-XXX-NNN, MDF-XXXXX, VP-XXX, RPT-XXX.
- Use `search_files` with keyword search first. Use 'pdf' as file extension for controlled documents.
- For Box AI: `ask_box_ai` (single file), `ask_box_ai_multi` (multiple files), `ask_box_ai_hub` (hub-level).
- ALWAYS use clickable Box links: https://app.box.com/file/FILE_ID or https://app.box.com/folder/FOLDER_ID.
- Keep responses SHORT — one summary sentence and a table if needed.""",
        tools=[
            search_files,
            get_file_content,
            get_file_info,
            get_folder_info,
            create_folder,
            upload_file,
            ask_box_ai,
            ask_box_ai_multi,
            ask_box_ai_hub,
        ],
    )


def _create_workflow_agent(model: str) -> LlmAgent:
    """Sub-agent with single-call workflow tools for report generation."""
    return LlmAgent(
        model=LiteLlm(model=model),
        name="box_workflow_agent",
        description=(
            "Runs complete analysis-to-report workflows with a single tool call. "
            "Use for: QMSR gap analysis, SOP/exemption impact analysis, "
            "CAPA completeness reports, and remediation plans."
        ),
        instruction="""You have four workflow tools. Each one handles an entire analysis-to-report pipeline automatically. Just call the right tool — no other steps needed.

- `run_gap_analysis()` — compares QMSR vs old QSR vs ISO 13485 and generates a Gap Risk Analysis report. No arguments.
- `run_sop_impact_analysis()` — analyzes §820.180(c) exemption removal impact on SOPs and generates a Document Control Report. No arguments.
- `run_capa_report(sap_data)` — generates a CAPA Completeness Report from SAP data. Pass the SAP findings as the `sap_data` string.
- `generate_remediation_plan()` — reads all reports in Generated Reports folder and generates a Remediation Plan. No arguments.

NEVER ask the user for details. Just call the tool and return the result.
Keep responses SHORT — one summary sentence and the report link. NEVER include job IDs or batch IDs.""",
        tools=[
            run_gap_analysis,
            run_sop_impact_analysis,
            run_capa_report,
            generate_remediation_plan,
        ],
    )


def create_box_agent() -> LlmAgent:
    """Constructs the ADK agent for Box document management operations."""
    model = os.getenv("LITELLM_MODEL", "vertex_ai/gemini-3-flash-preview")
    return LlmAgent(
        model=LiteLlm(model=model),
        name="box_agent",
        description=(
            "An agent that manages controlled documents in Box for medical device "
            "quality management, including search, AI-powered Q&A, and CRUD operations."
        ),
        instruction="""You route requests to specialized sub-agents. Do NOT answer directly — always delegate. NEVER ask the user for more details.

- **box_document_agent** — file search, read, folder ops, Box AI Q&A
- **box_workflow_agent** — gap analysis, SOP impact analysis, CAPA reports, remediation plans (single-call automated workflows)

Keep responses SHORT. Use clickable Box links. NEVER include job IDs or batch IDs.""",
        tools=[],
        sub_agents=[
            _create_document_agent(model),
            _create_workflow_agent(model),
        ],
    )
