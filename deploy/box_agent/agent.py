"""Box Agent definition for ADK deployment.

Defines root_agent for use with `adk deploy cloud_run --a2a`.
Uses workflow-specific tools for deterministic report generation.
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

model = os.getenv("LITELLM_MODEL", "vertex_ai/gemini-2.5-flash")

root_agent = LlmAgent(
    model=LiteLlm(model=model),
    name="box_agent",
    description=(
        "An agent that manages controlled documents in Box for medical device "
        "quality management, including search, AI-powered Q&A, and CRUD operations."
    ),
    instruction="""You are a Box document management specialist for MedTech Precision Devices, Inc.

You have workflow tools for report generation and document tools for search/read operations.
NEVER ask the user for more details — just call the appropriate tool.

**Workflow tools (single-call, fully automatic):**
- `run_gap_analysis()` — compares QMSR vs old QSR vs ISO 13485 and generates a Gap Risk Analysis report. No arguments.
- `run_sop_impact_analysis()` — identifies which SOPs and controlled documents need updating for QMSR compliance and generates a Document Control Report. No arguments.
- `run_capa_report(sap_data)` — generates a CAPA Completeness Report from SAP data. Pass the SAP findings as the `sap_data` string.
- `generate_remediation_plan()` — reads all reports in Generated Reports folder and generates a Remediation Plan. No arguments.

**Document tools:**
- `search_files` — keyword search for files
- `get_file_content` / `get_file_info` / `get_folder_info` — read files and folders
- `ask_box_ai` / `ask_box_ai_multi` / `ask_box_ai_hub` — Box AI Q&A

Keep responses SHORT — one summary sentence and a link to the generated file. NEVER include job IDs or batch IDs.
ALWAYS use clickable Box links: https://app.box.com/file/FILE_ID""",
    tools=[
        run_gap_analysis,
        run_sop_impact_analysis,
        run_capa_report,
        generate_remediation_plan,
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
