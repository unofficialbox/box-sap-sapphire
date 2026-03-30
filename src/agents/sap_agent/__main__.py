"""SAP Agent A2A application entry point.

Runs on port 8001 by default. Start with:
    uvicorn src.agents.sap_agent.__main__:a2a_app --host 0.0.0.0 --port 8001 --reload
"""

import logging
import os

import click
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from .sap_agent import create_sap_agent
from .sap_executor import SapExecutor

# Load .env from the agent's own directory first, then project root
_agent_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_agent_dir, ".env"))
load_dotenv()  # project root .env as fallback

logging.basicConfig()

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8001


def create_app():
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") != "TRUE" and not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set and "
            "GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
        )

    skill = AgentSkill(
        id="sap_quality_management",
        name="SAP Quality Management",
        description=(
            "Queries SAP Quality Management data: quality notifications (CAPAs), "
            "quality info records, and controlled documents for medical device QMS"
        ),
        tags=["sap", "quality", "capa", "notification", "iso13485", "qmsr", "fda"],
        examples=[
            "Show me all open CAPAs related to the QMSR transition",
            "Get details for quality notification 000300000005 including corrective actions",
            "Which supplier quality notifications were created in January 2026?",
            "Find controlled document metadata referencing ISO 13485 clause 8.5.2",
            "What preventive actions are still in process for the §820.180(c) remediation?",
        ],
    )

    app_url = os.environ.get("APP_URL", f"http://localhost:{DEFAULT_PORT}")

    agent_card = AgentCard(
        name="SAP Quality Agent",
        description=(
            "Queries SAP Quality Management data including quality notifications "
            "(CAPAs), quality info records, and controlled documents"
        ),
        url=app_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    adk_agent = create_sap_agent()
    runner = Runner(
        app_name=agent_card.name,
        agent=adk_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = SapExecutor(runner, agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    return A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )


# Create app instance at module level for uvicorn
a2a_app = create_app().build()


def main(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    uvicorn.run(a2a_app, host=host, port=port)


@click.command()
@click.option("--host", "host", default=DEFAULT_HOST)
@click.option("--port", "port", default=DEFAULT_PORT)
def cli(host: str, port: int):
    main(host, port)


if __name__ == "__main__":
    main()
