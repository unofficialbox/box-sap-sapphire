"""QMS Orchestrator A2A application entry point.

Runs on port 8000 by default. Start with:
    uvicorn src.agents.host_agent.__main__:app --host 0.0.0.0 --port 8000 --reload
"""

import os

from a2a.server.apps.jsonrpc.starlette_app import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv

from .agent_executor import QmsOrchestratorExecutor
from .qms_orchestrator import create_agent_card, create_root_agent

load_dotenv()

AGENT_URL = os.environ.get("AGENT_URL", "http://127.0.0.1:8000")

orchestrator = create_root_agent()
agent_card = create_agent_card(orchestrator, AGENT_URL)

request_handler = DefaultRequestHandler(
    agent_executor=QmsOrchestratorExecutor(),
    task_store=InMemoryTaskStore(),
)

app = A2AStarletteApplication(
    agent_card=agent_card,
    http_handler=request_handler,
).build()
