"""Host Agent definition.

Creates the root routing agent that delegates requests to
SAP and Box sub-agents via tool-based A2A calls.
"""

import os

from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from host_tools import query_box, query_sap


def create_root_agent() -> LlmAgent:
    """Constructs the host routing agent with SAP and Box tools."""
    model = os.getenv("LITELLM_MODEL", "gemini-2.5-flash")
    return LlmAgent(
        model=LiteLlm(model=model),
        name="routing_agent",
        description="Orchestrates quality management workflows across SAP and Box systems",
        instruction="""You are a quality management orchestration agent for MedTech Precision Devices, Inc.

You have two tools:
- **query_sap**: Queries SAP Quality Management data (CAPAs, quality notifications, quality info records, controlled document metadata, CAPA actions).
- **query_box**: Manages documents in Box (search files, read content, Box AI Q&A, upload, create folders).

RULES:
1. ALWAYS use your tools. Never answer from your own knowledge.
2. When a request needs data from BOTH SAP and Box, call BOTH tools — one after the other.
3. Combine the results from all tool calls into a single comprehensive Markdown response.

Routing guide:
- SAP data (CAPAs, notifications, quality records, document metadata) → query_sap
- Box files (search, read, AI Q&A, upload) → query_box
- Both systems → call query_sap first, then call query_box

Context: The FDA QMSR (effective Feb 2, 2026) incorporates ISO 13485:2016 into 21 CFR Part 820. The company uses SAP QM for CAPA tracking and Box for controlled document storage.""",
        tools=[query_sap, query_box],
        sub_agents=[],
    )


def create_agent_card(agent, agent_url: str) -> AgentCard:
    """Create the A2A agent card for the host agent."""
    return AgentCard(
        name=agent.name,
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
                    "Show me all open CAPAs",
                    "What documents were updated for CAPA 000300000005?",
                    "What does our incoming inspection SOP say about trace metals?",
                    "Show me supplier quality issues for RM-00078234",
                    "What preventive actions are still in process?",
                ],
            )
        ],
    )
