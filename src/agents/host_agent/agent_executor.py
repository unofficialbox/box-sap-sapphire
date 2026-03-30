"""QMS Orchestrator executor for A2A request handling.

Executor pattern for the QMS orchestrator agent that delegates
to sub-agents via the ADK Runner.
"""

import asyncio

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content

from .qms_orchestrator import create_root_agent

KEEPALIVE_INTERVAL = 15  # seconds between heartbeat status updates


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
        query = context.get_user_input()
        task = context.current_task

        if not task:
            if not context.message:
                return
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(event_queue, task.id, task.context_id)
        session_id = task.context_id

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

        content = Content(role="user", parts=[{"text": query}])

        await updater.start_work()

        # Background keepalive: sends periodic status updates so the SSE
        # stream doesn't go silent during long tool executions.
        keepalive_active = True

        async def keepalive():
            while keepalive_active:
                await asyncio.sleep(KEEPALIVE_INTERVAL)
                if keepalive_active:
                    await updater.update_status(
                        TaskState.working,
                        message=new_agent_text_message("Processing..."),
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
                        and event.content.parts[0].text
                    ):
                        await updater.add_artifact(
                            [Part(root=TextPart(text=event.content.parts[0].text))],
                            name="response",
                        )
                        await updater.complete()
                elif event.content and event.content.parts:
                    has_function_call = False
                    has_text = False
                    for part in event.content.parts:
                        if hasattr(part, "function_call") and part.function_call:
                            has_function_call = True
                            fc = part.function_call
                            # Provide descriptive progress messages
                            tool_descriptions = {
                                "query_sap": "Querying SAP Quality Management system",
                                "query_box": "Querying Box document management system",
                            }
                            desc = tool_descriptions.get(fc.name, f"Calling {fc.name}")
                            # Include query snippet if available
                            query_arg = (fc.args or {}).get("query", "")
                            if query_arg:
                                snippet = query_arg[:120]
                                desc = f"{desc}: {snippet}{'...' if len(query_arg) > 120 else ''}"
                            await updater.update_status(
                                TaskState.working,
                                message=new_agent_text_message(desc),
                            )
                        elif hasattr(part, "text") and part.text:
                            has_text = True
                    # Stream intermediate text (LLM thinking/reasoning) as progress
                    if has_text and not has_function_call:
                        text_parts = [
                            p.text for p in event.content.parts
                            if hasattr(p, "text") and p.text
                        ]
                        if text_parts:
                            await updater.update_status(
                                TaskState.working,
                                message=new_agent_text_message(
                                    " ".join(text_parts)
                                ),
                            )
        except Exception as e:
            await updater.failed(
                message=new_agent_text_message(f"Task failed with error: {e}")
            )
        finally:
            keepalive_active = False
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        raise ServerError(error=UnsupportedOperationError())
