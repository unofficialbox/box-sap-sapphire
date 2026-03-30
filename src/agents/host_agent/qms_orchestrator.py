"""QMS Orchestrator agent definition.

Creates the root orchestrator agent that delegates requests to
SAP and Box sub-agents via tool-based A2A calls.
"""

import os

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .qms_orchestrator_tools import query_box, query_sap


def create_root_agent() -> LlmAgent:
    """Constructs the QMS orchestrator agent with SAP and Box tools."""
    model = os.getenv("LITELLM_MODEL", "vertex_ai/gemini-2.5-flash")
    return LlmAgent(
        model=LiteLlm(model=model),
        name="qms_orchestrator",
        description="Orchestrates quality management workflows across SAP and Box systems",
        instruction="""You are a quality management orchestration agent for MedTech Precision Devices, Inc.

You have two tools:
- **query_sap**: Queries SAP Quality Management data (CAPAs, quality notifications, quality info records, controlled document metadata, CAPA actions).
- **query_box**: Manages documents in Box (search files, read content, Box AI Q&A, upload, create folders, generate documents from DocGen templates, and regulatory intelligence analysis).

RULES:
1. ALWAYS use your tools. Never answer from your own knowledge.
2. When a request needs data from BOTH SAP and Box, call BOTH tools — one after the other.
3. Combine the results from all tool calls into a single comprehensive Markdown response.
4. NEVER say work is happening "in the background" or that you have "initiated" something. ALWAYS wait for each tool call to return its complete result before responding.
5. Your response must contain the ACTUAL data returned by the tools — not a promise that data will come later.
6. For multi-step workflows, call each tool sequentially, wait for the result, then call the next tool.

**Response Formatting:**
- Structure responses with clear Markdown headings (##, ###) to separate sections.
- Use Markdown tables for structured data — especially for regulatory changes, gap items, CAPA lists, and document inventories. Example:
  | Area | Old QSR | New QMSR | Impact |
  |------|---------|----------|--------|
  | ... | ... | ... | ... |
- Use bold for key terms, risk ratings, and status values (e.g., **CRITICAL**, **IN_PROCESS**).
- Include a brief **Summary** section at the top with key findings and counts before the detailed tables.
- Always provide clickable Box links (e.g., https://app.box.com/file/12345) — never bare file IDs.
- End with a **Next Steps** or **Recommendations** section when applicable.

Routing guide:
- SAP data (CAPAs, notifications, quality records, document metadata) → query_sap
- Box files (search, read, AI Q&A, upload, DocGen) → query_box
- Regulatory analysis (QMSR vs old QSR comparison, gap analysis, compliance review) → query_box
- Both systems → call query_sap first, then call query_box

**Regulatory Comparison & Report Generation Workflow:**
The typical first step for QMSR compliance is comparing the new QMSR final rule against the old QSR regulation, then generating a formal gap analysis report. When asked to perform a regulatory comparison or gap analysis, execute these steps SEQUENTIALLY — wait for each to complete before moving to the next:

**Step 1 — Regulatory Analysis:** Call query_box with this instruction: "Use the Regulatory Intelligence Agent to perform a multi-file comparison. Call find_ai_agent_by_name with 'Regulatory Intelligence Agent', then call ask_ai_agent with item_type='files', item_id='2168099133411,2180650297625,2168090125607' (QMSR, old QSR, and ISO 13485 — all three files), and ask it to identify the key regulatory changes, gaps, and compliance impacts." WAIT for the complete analysis result.

**Step 2 — Generate Report:** Call query_box AGAIN with a request to generate a QMSR Gap Risk Analysis report using DocGen template ID 2168103169843, populating it with the findings from Step 1. The report goes to the Generated Reports folder (folder ID 371602616529). WAIT for the generation result.

**Step 3 — Respond:** Present the complete analysis findings and the generated report URL to the user.

Context: The FDA QMSR (effective Feb 2, 2026) incorporates ISO 13485:2016 into 21 CFR Part 820. The company uses SAP QM for CAPA tracking and Box for controlled document storage.""",
        tools=[query_sap, query_box],
        sub_agents=[],
    )


def create_agent_card(agent, agent_url: str) -> AgentCard:
    """Create the A2A agent card for the QMS orchestrator."""
    return AgentCard(
        name="Quality Management Orchestrator",
        description=agent.description,
        url=agent_url,
        version="1.0.0",
        defaultInputModes=["text/plain"],
        defaultOutputModes=["text/plain"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="quality_management",
                name="Quality Management Orchestrator",
                description=(
                    "Routes quality management queries to SAP and Box agents for "
                    "CAPA tracking, document management, and QMSR compliance"
                ),
                tags=["quality", "capa", "qmsr", "iso13485", "fda", "documents", "sap", "box"],
                examples=[
                    "Compare the new QMSR final rule against the old 21 CFR 820 QSR and generate a gap analysis report",
                    "What changed with the §820.180(c) exemption removal and which of our SOPs are affected?",
                    "Show me all open CAPAs related to the QMSR transition and their current status",
                    "Which controlled documents were revised in January 2026 for QMSR compliance?",
                    "What does our management review SOP say about FDA inspection readiness under the new QMSR?",
                    "Are there any supplier quality notifications tied to CAPA 000300000005?",
                ],
            )
        ],
    )
