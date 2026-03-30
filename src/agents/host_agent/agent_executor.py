"""QMS Orchestrator executor for A2A request handling.

Executor pattern for the QMS orchestrator agent that delegates
to sub-agents via the ADK Runner. Sub-agent progress updates are
forwarded to the user in real time via a shared asyncio.Queue.
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
from .qms_orchestrator_tools import progress_queue

KEEPALIVE_INTERVAL = 30  # seconds between heartbeat status updates


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

        # Drain any stale messages from previous runs
        while not progress_queue.empty():
            try:
                progress_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        # Background task: drain progress_queue and forward sub-agent
        # status updates to the user via TaskUpdater.
        progress_active = True

        async def drain_progress():
            while progress_active:
                try:
                    msg = await asyncio.wait_for(
                        progress_queue.get(), timeout=1.0
                    )
                    await updater.update_status(
                        TaskState.working,
                        message=new_agent_text_message(msg),
                    )
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    continue

        progress_task = asyncio.create_task(drain_progress())

        # Background keepalive for truly silent periods
        keepalive_active = True

        async def keepalive():
            while keepalive_active:
                await asyncio.sleep(KEEPALIVE_INTERVAL)
                if keepalive_active:
                    await updater.update_status(
                        TaskState.working,
                        message=new_agent_text_message("Still processing..."),
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
                    for part in event.content.parts:
                        # Forward function call info as progress
                        if hasattr(part, "function_call") and part.function_call:
                            fc = part.function_call
                            tool_labels = {
                                "query_sap": "Routing to SAP Quality Management agent",
                                "query_box": "Routing to Box document management agent",
                            }
                            desc = tool_labels.get(fc.name, f"Calling {fc.name}")
                            query_arg = (fc.args or {}).get("query", "")
                            if query_arg:
                                snippet = query_arg[:150]
                                desc = f"{desc}: {snippet}{'...' if len(query_arg) > 150 else ''}"
                            await updater.update_status(
                                TaskState.working,
                                message=new_agent_text_message(desc),
                            )
                        # Forward intermediate LLM text as progress
                        elif hasattr(part, "text") and part.text:
                            await updater.update_status(
                                TaskState.working,
                                message=new_agent_text_message(part.text),
                            )
        except Exception as e:
            await updater.failed(
                message=new_agent_text_message(f"Task failed with error: {e}")
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
