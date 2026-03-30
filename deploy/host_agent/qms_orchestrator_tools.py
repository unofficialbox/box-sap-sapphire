"""QMS Orchestrator tool wrappers for calling remote A2A agents.

These tools allow the orchestrator LLM to call sub-agents as function calls,
enabling multi-step workflows where both agents are called sequentially.

Sub-agent calls use A2A `message/stream` (SSE) so that intermediate status
updates from the sub-agents are forwarded to the user in real time via a
shared asyncio.Queue consumed by the host executor.
"""

import asyncio
import json
import logging
import os

import httpx
from httpx_sse import aconnect_sse

logger = logging.getLogger(__name__)

SAP_AGENT_URL = os.environ.get("SAP_AGENT_URL", "http://localhost:8001")
BOX_AGENT_URL = os.environ.get("BOX_AGENT_URL", "http://localhost:8002")

_counter = 0

# Shared queue: tools push progress strings, host executor drains and
# forwards them to the user via TaskUpdater.
progress_queue: asyncio.Queue[str] = asyncio.Queue()


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"host-call-{_counter}"


async def _call_agent(url: str, query: str, agent_label: str = "Agent") -> str:
    """Send an A2A message/stream request, forward progress, return final text."""
    payload = {
        "jsonrpc": "2.0",
        "method": "message/stream",
        "id": _next_id(),
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
                "messageId": _next_id(),
            }
        },
    }

    final_text = ""

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            async with aconnect_sse(
                client, "POST", url, json=payload,
            ) as event_source:
                async for sse_event in event_source.aiter_sse():
                    if not sse_event.data:
                        continue
                    try:
                        data = json.loads(sse_event.data)
                    except json.JSONDecodeError:
                        continue

                    result = data.get("result")
                    if not result:
                        continue

                    # --- TaskStatusUpdateEvent ---
                    status = result.get("status") or {}
                    state = status.get("state", "")
                    message = status.get("message")

                    if state == "working" and message:
                        parts = message.get("parts", [])
                        for part in parts:
                            text = part.get("text", "")
                            if text:
                                await progress_queue.put(
                                    f"[{agent_label}] {text}"
                                )

                    # --- TaskArtifactUpdateEvent ---
                    artifact = result.get("artifact")
                    if artifact:
                        for part in artifact.get("parts", []):
                            if part.get("kind") == "text" and part.get("text"):
                                final_text = part["text"]

                    # --- Completed status with no artifact (inline) ---
                    if state == "completed":
                        # Some agents embed artifacts at top level
                        artifacts = result.get("artifacts", [])
                        for art in artifacts:
                            for part in art.get("parts", []):
                                if part.get("kind") == "text" and part.get("text"):
                                    final_text = part["text"]

    except httpx.ReadError:
        logger.debug("SSE stream closed by %s", agent_label)
    except Exception as e:
        logger.error("_call_agent SSE failed for %s: %s", agent_label, e)
        # Fallback: try non-streaming message/send
        return await _call_agent_fallback(url, query)

    if final_text:
        return final_text

    # Fallback if streaming didn't yield a final artifact
    return await _call_agent_fallback(url, query)


async def _call_agent_fallback(url: str, query: str) -> str:
    """Non-streaming fallback using message/send."""
    payload = {
        "jsonrpc": "2.0",
        "method": "message/send",
        "id": _next_id(),
        "params": {
            "message": {
                "role": "user",
                "parts": [{"kind": "text", "text": query}],
                "messageId": _next_id(),
            }
        },
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(url, json=payload)
    data = resp.json()
    try:
        return data["result"]["artifacts"][0]["parts"][0]["text"]
    except (KeyError, IndexError):
        return json.dumps(data.get("result", data.get("error", data)), indent=2)


async def query_sap(query: str) -> dict:
    """Query the SAP Quality Management agent for CAPA, quality notification,
    quality info record, or controlled document data.

    Args:
        query: Natural language question about SAP quality data
            (e.g., "Get details of CAPA 000300000005",
             "Show all IN_PROCESS notifications",
             "Find documents related to CAPA 000300000001").

    Returns:
        dict with the SAP agent's response text.
    """
    try:
        logger.info("query_sap: %s", query[:100])
        await progress_queue.put("[SAP Agent] Processing query...")
        result = await _call_agent(SAP_AGENT_URL, query, agent_label="SAP Agent")
        return {"status": "success", "response": result}
    except Exception as e:
        logger.error("query_sap failed: %s", e)
        return {"status": "error", "error_message": str(e)}


async def query_box(query: str) -> dict:
    """Query the Box document management agent to search files, read content,
    or ask Box AI questions about documents.

    Args:
        query: Natural language question about Box documents
            (e.g., "Search for incoming inspection documents",
             "What does the quality manual say about management review?",
             "Get folder info for folder ID 335620450992").

    Returns:
        dict with the Box agent's response text.
    """
    try:
        logger.info("query_box: %s", query[:100])
        await progress_queue.put("[Box Agent] Processing query...")
        result = await _call_agent(BOX_AGENT_URL, query, agent_label="Box Agent")
        return {"status": "success", "response": result}
    except Exception as e:
        logger.error("query_box failed: %s", e)
        return {"status": "error", "error_message": str(e)}
