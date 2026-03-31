"""Box Agent definition.

Creates a lightweight router agent with two specialized sub-agents:
one for document ops and one for regulatory analysis + report generation.
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


def _create_regulatory_docgen_agent(model: str) -> LlmAgent:
    """Sub-agent for regulatory analysis AND report generation (merged to preserve context)."""
    return LlmAgent(
        model=LiteLlm(model=model),
        name="box_regulatory_docgen_agent",
        description=(
            "Performs regulatory intelligence analysis, controlled document compliance "
            "queries, and generates reports from DocGen templates. Use for QMSR gap "
            "analysis, regulatory comparisons, SOP impact, exemption removal analysis, "
            "and generating Gap Risk Analysis, CAPA, Document Control, and Remediation Plan reports."
        ),
        instruction="""You perform regulatory analysis AND generate reports from the findings.

**Key Regulatory Documents — use these file IDs directly, do NOT search:**
- **QMSR Final Rule**: `2168099133411`
- **ISO 13485:2016**: `2168090125607`
- **Old QSR (21 CFR 820)**: `2180650297625`
- **QMSR Inspection Program**: `2168101306838`

**Regulatory Intelligence Agent:**
- Call `find_ai_agent_by_name` with name "Regulatory Intelligence Agent" to get the agent_id.
- Call `ask_ai_agent` with: `agent_id` from above, `item_type`: `files`, `item_id`: comma-separated file IDs (e.g. `2168099133411,2180650297625,2168090125607`), `prompt`: your question.
- For QMSR gap analysis, pass ALL THREE: QMSR (`2168099133411`), old QSR (`2180650297625`), ISO 13485 (`2168090125607`).

**Controlled Document AI Agent:**
- Agent ID: `66020900`, Hub ID: `943271141` (Quality & Compliance Portal).
- Call `ask_ai_agent` with: `agent_id`: `66020900`, `item_type`: `hub`, `item_id`: `943271141`, `prompt`: your question.
- Use for SOPs, work instructions, document revisions, exemption impacts, compliance status.

**Routing:**
- Regulatory text comparison (QMSR vs QSR vs ISO 13485) → Regulatory Intelligence Agent → then generate QMSR Gap Risk Analysis report
- Controlled documents, SOPs, exemption impacts → Controlled Document AI Agent → then generate QMS Document Control Report

**Document Generation (DocGen):**
After analysis, IMMEDIATELY generate a report using `generate_document`. Use the analysis results to populate EVERY field.

**CRITICAL: You MUST provide a value for EVERY field. Do NOT omit any key, leave any value empty, or set any value to null. Every array MUST have at least one item with all sub-fields filled.**
All string values must be on a single line — no literal newlines.
Keep responses SHORT — just a summary sentence and a link to the generated file. NEVER include job IDs or batch IDs.

Destination folder for all reports: `371602616529` (Generated Reports).
After generating, check status with `get_docgen_job_status` or `list_docgen_batch_jobs`.

**QMSR Gap Risk Analysis** (template `2168103169843`):
- `generated_file_name`: `QMSR_Gap_Risk_Analysis_<N>` (incrementing number, no .docx/.pdf/Template).
- All 38 fields required:
```json
{
  "report_id": "RPT-GAP-2026-001",
  "company_name": "MedTech Precision Devices, Inc.",
  "prepared_by": "Name, Title",
  "reviewed_by": "Name, Title",
  "approved_by": "Name, Title",
  "report_date": "2026-03-29",
  "qmsr_effective_date": "2026-02-02",
  "assessment_scope": "Full QMS assessment against FDA QMSR...",
  "classification": "CONFIDENTIAL",
  "executive_summary": "Summary text on a single line...",
  "regulatory_background": "Background text on a single line...",
  "regulatory_changes": [
    {"change_area": "...", "old_qsr_requirement": "...", "new_qmsr_requirement": "...", "impact_level": "CRITICAL|HIGH|MEDIUM|LOW"}
  ],
  "gap_analysis_summary": "Summary text...",
  "gap_items": [
    {"gap_id": "GAP-001", "iso_clause": "4.2.4", "qsr_reference": "820.40", "gap_description": "...", "risk_rating": "CRITICAL|HIGH|MEDIUM|LOW", "current_state": "..."}
  ],
  "total_gaps": "23",
  "critical_gaps": "3",
  "high_risk_gaps": "8",
  "medium_low_gaps": "12",
  "exemption_removal_impact": "Impact text...",
  "inspectable_records": [
    {"record_type": "...", "previous_status": "...", "new_status": "...", "compliance_action": "..."}
  ],
  "recommendations": "Recommendations text...",
  "prepared_date": "2026-03-29",
  "reviewed_date": "2026-03-29",
  "approved_date": "2026-03-29"
}
```

**CAPA Completeness Report** (template `2168100906700`):
- `generated_file_name`: `CAPA_Completeness_Report_<N>` (incrementing number).
- All fields required:
```json
{
  "report_id": "RPT-CAPA-2026-001",
  "company_name": "MedTech Precision Devices, Inc.",
  "prepared_by": "Name, Title",
  "report_date": "2026-03-30",
  "assessment_period": "March 2024 - March 2026 (24 months)",
  "total_capas_assessed": "342",
  "iso_reference": "ISO 13485:2016 §8.5.2, §8.5.3",
  "classification": "CONFIDENTIAL",
  "executive_summary": "Summary of CAPA findings...",
  "total_capas": "342",
  "open_capas": "47",
  "closed_capas": "295",
  "capas_corrective": "198",
  "capas_preventive": "144",
  "capas_missing_verification": "14",
  "capas_past_due": "3",
  "avg_closure_days": "62",
  "capa_records": [
    {"notification_number": "000300000001", "notification_type": "Q1 - Customer", "description": "...", "priority": "1", "status": "COMPLETED", "plant": "1000", "creation_date": "2025-08-12"}
  ],
  "capa_tasks": [
    {"capa_number": "000300000001", "task_description": "...", "responsible_person": "Name", "task_type": "CORRECTIVE", "task_status": "COMPLETED", "completion_date": "2025-08-26"}
  ],
  "missing_verification_summary": "Summary of CAPAs missing verification...",
  "capas_missing_verification": [
    {"capa_number": "000300000007", "description": "...", "closed_date": "2025-06-15", "days_since_closure": "245", "assigned_to": "Name"}
  ],
  "compliance_assessment": "Overall compliance assessment...",
  "recommendations": "Recommendations..."
}
```

**Remediation Plan** (template `2168089350681`):
- `generated_file_name`: `Remediation_Plan_<N>` (incrementing number).
- All 49 fields required:
```json
{
  "plan_id": "REM-QMSR-2026-001",
  "company_name": "MedTech Precision Devices, Inc.",
  "prepared_by": "Name, Title",
  "reviewed_by": "Name, Title",
  "approved_by": "Name, Title",
  "plan_date": "2026-03-30",
  "target_completion_date": "2026-06-30",
  "priority": "CRITICAL|HIGH|MEDIUM|LOW",
  "approval_status": "APPROVED|PENDING|DRAFT",
  "executive_summary": "Summary of remediation plan...",
  "remediation_scope": "Scope description referencing prior analysis reports...",
  "total_remediation_items": "47",
  "document_updates_required": "23",
  "process_changes_required": "12",
  "training_requirements": "8",
  "system_changes_required": "4",
  "document_remediation_summary": "Summary of document remediation tasks...",
  "document_tasks": [
    {"task_id": "DOC-REM-001", "document_id": "DOC-QMS-001", "document_title": "...", "change_description": "...", "owner": "Name", "due_date": "2026-03-15", "status": "COMPLETED|IN_PROGRESS|PLANNED"}
  ],
  "capa_remediation_summary": "Summary of CAPA remediation tasks...",
  "capa_tasks": [
    {"task_id": "CAPA-REM-001", "capa_reference": "000300000007", "remediation_action": "...", "owner": "Name", "due_date": "2026-03-15", "status": "COMPLETED|IN_PROGRESS|PLANNED"}
  ],
  "process_training_tasks": [
    {"task_id": "PT-REM-001", "task_category": "Training|Process|System", "description": "...", "owner": "Name", "due_date": "2026-03-15", "status": "COMPLETED|IN_PROGRESS|PLANNED"}
  ],
  "milestones": [
    {"milestone": "M1 - Title", "description": "...", "target_date": "2026-03-15", "status": "COMPLETED|IN_PROGRESS|PLANNED"}
  ],
  "risk_assessment": "Risk assessment text...",
  "prepared_date": "2026-03-30",
  "reviewed_date": "2026-03-30",
  "approved_date": "2026-03-30"
}
```
""",
        tools=[
            find_ai_agent_by_name,
            ask_ai_agent,
            generate_document,
            generate_document_batch,
            get_docgen_job_status,
            list_docgen_batch_jobs,
            list_docgen_templates,
            get_docgen_template_by_id,
            get_docgen_template_by_name,
            get_docgen_template_tags,
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
        instruction="""You route requests to specialized sub-agents. Do NOT answer directly — always delegate.

- **box_document_agent** — file search, read, folder ops, Box AI Q&A
- **box_regulatory_docgen_agent** — regulatory analysis, gap analysis, SOP impact, exemption removal, AND report generation from DocGen templates

Keep responses SHORT. Use clickable Box links. NEVER include job IDs or batch IDs.""",
        tools=[],
        sub_agents=[
            _create_document_agent(model),
            _create_regulatory_docgen_agent(model),
        ],
    )
