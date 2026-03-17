"""QMS Orchestrator tool wrappers for calling remote A2A agents.

These tools allow the orchestrator LLM to call sub-agents as function calls,
enabling multi-step workflows where both agents are called sequentially.
"""

import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

SAP_AGENT_URL = os.environ.get("SAP_AGENT_URL", "http://localhost:8001")
BOX_AGENT_URL = os.environ.get("BOX_AGENT_URL", "http://localhost:8002")

_counter = 0


def _next_id() -> str:
    global _counter
    _counter += 1
    return f"host-call-{_counter}"


async def _call_agent(url: str, query: str) -> str:
    """Send an A2A message/send request and return the agent's text response."""
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
    async with httpx.AsyncClient(timeout=120.0) as client:
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
        result = await _call_agent(SAP_AGENT_URL, query)
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
        result = await _call_agent(BOX_AGENT_URL, query)
        return {"status": "success", "response": result}
    except Exception as e:
        logger.error("query_box failed: %s", e)
        return {"status": "error", "error_message": str(e)}
