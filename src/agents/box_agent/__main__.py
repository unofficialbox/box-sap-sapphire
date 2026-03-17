"""Box Agent A2A application entry point.

Runs on port 8002 by default. Start with:
    uvicorn src.agents.box_agent.__main__:a2a_app --host 0.0.0.0 --port 8002 --reload
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

from .box_agent import create_box_agent
from .box_executor import BoxExecutor

# Load .env from the agent's own directory first, then project root
_agent_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_agent_dir, ".env"))
load_dotenv()  # project root .env as fallback

logging.basicConfig()

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8002


def create_app():
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") != "TRUE" and not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set and "
            "GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
        )

    skill = AgentSkill(
        id="box_document_management",
        name="Box Document Management",
        description=(
            "Manages controlled QMS documents in Box: search, read content, "
            "AI-powered Q&A, upload files, organize folders, and generate "
            "documents from DocGen templates"
        ),
        tags=["box", "documents", "files", "folders", "ai", "qms", "controlled", "docgen", "templates"],
        examples=[
            "Search for CAPA procedure documents",
            "What does the incoming inspection SOP say about trace metals?",
            "Upload a document to the QMS folder",
            "Ask Box AI about the quality manual",
            "List available DocGen templates",
            "Generate a QMSR Gap Risk Analysis report from the template",
        ],
    )

    app_url = os.environ.get("APP_URL", f"http://localhost:{DEFAULT_PORT}")

    agent_card = AgentCard(
        name="Box Agent",
        description=(
            "Manages controlled documents in Box for medical device quality "
            "management, including search, AI-powered Q&A, CRUD operations, "
            "and document generation from DocGen templates"
        ),
        url=app_url,
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    adk_agent = create_box_agent()
    runner = Runner(
        app_name=agent_card.name,
        agent=adk_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService(),
    )
    agent_executor = BoxExecutor(runner, agent_card)

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
