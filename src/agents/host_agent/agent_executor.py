"""QMS Orchestrator executor for A2A request handling.

Executor pattern for the QMS orchestrator agent that delegates
to sub-agents via the ADK Runner. Sub-agent progress updates are
forwarded to the user in real time via a shared asyncio.Queue.
"""

import asyncio
import logging
import random

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from src.common.converters import convert_genai_part_to_a2a

from .qms_orchestrator import create_root_agent
from .qms_orchestrator_tools import progress_queue

logger = logging.getLogger(__name__)

KEEPALIVE_INTERVAL = 10  # seconds between spinner status updates

SPINNER_VERBS = [
    "Alphabetizing", "Archiving", "Boxing", "Browsing",
    "Cataloging", "Collating", "Color-coding", "Curating",
    "Decluttering", "Digging", "Dusting off", "Excavating",
    "Filing", "Flipping through", "Fossicking", "Fumbling",
    "Gathering", "Leafing", "Nesting", "Nudging",
    "Origami-ing", "Packing", "Papershuffling", "Perusing",
    "Pigeon-holing", "Pruning", "Riffling", "Rifling",
    "Rummaging", "Rustling", "Scouring", "Scrapbooking",
    "Shelving", "Sifting", "Skimming", "Sorting",
    "Stacking", "Stamping", "Stapling", "Tabbing",
    "Thumbing", "Tidying", "Tracing", "Transcribing",
    "Trawling", "Tucking", "Unboxing", "Uncovering",
    "Unearthing", "Unfolding", "Unfurling", "Unpacking",
    "Unraveling", "Unscrolling", "Unwrapping", "Wrangling",
]



class QmsOrchestratorExecutor(AgentExecutor):
    """Executor for the QMS orchestrator agent."""

    def __init__(self):
        self._agent = create_root_agent()
        self._runner = Runner(
            app_name=self._agent.name,
            agent=self._agent,
            session_service=InMemorySessionService(),
            artifact_service=InMemoryArtifactService(),
            memory_service=InMemoryMemoryService(),
        )
        self._user_id = "remote_agent"

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        # Extract user query from the incoming message
        query = context.get_user_input()
        if not query:
            return

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)

        if not context.current_task:
            await updater.update_status(TaskState.submitted)
        await updater.update_status(TaskState.working)

        session_id = context.context_id

        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        content = types.UserContent(parts=[types.Part(text=query)])

        # Drain any stale messages from previous runs
        while not progress_queue.empty():
            try:
                progress_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Background task: drain progress_queue and forward sub-agent
        # status updates to the user via TaskUpdater.
        progress_active = True

        # Phrases that are too generic to show the user
        _skip_phrases = {"processing query", "processing request"}

        async def drain_progress():
            while progress_active:
                try:
                    msg = await asyncio.wait_for(
                        progress_queue.get(), timeout=1.0
                    )
                    # Skip noisy/generic progress messages
                    if any(p in msg.lower() for p in _skip_phrases):
                        continue
                    await updater.update_status(
                        TaskState.working,
                        message=updater.new_agent_message(
                            [Part(root=TextPart(text=msg))],
                        ),
                    )
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    continue

        progress_task = asyncio.create_task(drain_progress())

        # Background spinner for silent periods
        keepalive_active = True

        async def keepalive():
            used_verbs = []
            while keepalive_active:
                await asyncio.sleep(KEEPALIVE_INTERVAL)
                if keepalive_active:
                    if not used_verbs:
                        used_verbs = random.sample(SPINNER_VERBS, len(SPINNER_VERBS))
                    verb = used_verbs.pop()
                    await updater.update_status(
                        TaskState.working,
                        message=updater.new_agent_message(
                            [Part(root=TextPart(text=f"{verb}..."))],
                        ),
                    )

        keepalive_task = asyncio.create_task(keepalive())

        try:
            async for event in self._runner.run_async(
                user_id=self._user_id,
                session_id=session.id,
                new_message=content,
            ):
                if event.is_final_response():
                    if (
                        event.content
                        and event.content.parts
                    ):
                        parts = [
                            convert_genai_part_to_a2a(part)
                            for part in event.content.parts
                            if (part.text or part.file_data or part.inline_data)
                        ]
                        if parts:
                            await updater.add_artifact(parts)
                            await updater.update_status(TaskState.completed, final=True)
                elif event.content and event.content.parts:
                    for part in event.content.parts:
                        # Forward function call routing as a single progress message
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            tool_labels = {
                                "query_sap": "Querying SAP Quality Management...",
                                "query_box": "Querying Box documents...",
                            }
                            desc = tool_labels.get(fc.name)
                            if desc:
                                await updater.update_status(
                                    TaskState.working,
                                    message=updater.new_agent_message(
                                        [Part(root=TextPart(text=desc))],
                                    ),
                                )
        except Exception as e:
            logger.error("Host executor failed: %s", e, exc_info=True)
            await updater.update_status(
                TaskState.failed,
                message=updater.new_agent_message(
                    [Part(root=TextPart(text=f"Task failed with error: {e}"))],
                ),
                final=True,
            )
        finally:
            progress_active = False
            keepalive_active = False
            progress_task.cancel()
            keepalive_task.cancel()
            for t in (progress_task, keepalive_task):
                try:
                    await t
                except asyncio.CancelledError:
                    pass

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise ServerError(error=UnsupportedOperationError())
