# Box + SAP Sapphire Demo

Multi-agent A2A system for the SAP Sapphire conference demo. Showcases SAP S/4HANA Quality Management integration with Box for medical device QMS compliance, focused on controlled documents and CAPA records triggered by the FDA QMSR / ISO 13485:2016 regulatory change.

## Architecture

```
Client (A2A Inspector / curl)
    ↓ A2A (JSON-RPC 2.0)
QMS Orchestrator :8000  (qms_orchestrator - Gemini 2.5 Flash)
    ├── query_sap ──→ SAP Agent :8001  (sap_agent)
    │                     └── BigTable Emulator :8086
    │                           ├── quality_notifications (10 records)
    │                           ├── quality_info_records (30 records)
    │                           └── controlled_documents (20 records)
    └── query_box ──→ Box Agent :8002  (box_agent)
                          └── Box API (CCG Auth)
                                ├── Search / CRUD files & folders
                                └── Box AI (single, multi-file, hub Q&A)
```

- **A2A Protocol** (JSON-RPC 2.0) for inter-agent communication
- **Google ADK** (Agent Development Kit) with Gemini 2.5 Flash via LiteLLM
- **FastMCP** wrappers on each agent's tools for MCP protocol support

## Setup

```bash
# Install dependencies
uv sync

# Start BigTable emulator
gcloud beta emulators bigtable start --host-port=localhost:8086

# Load synthetic data into BigTable
python scripts/load_bigtable.py

# Copy and configure environment variables
cp .env.sample .env
cp src/agents/sap_agent/.env.sample src/agents/sap_agent/.env
cp src/agents/box_agent/.env.sample src/agents/box_agent/.env
```

## Running

Start each agent in a separate terminal:

```bash
# SAP Agent (port 8001)
BIGTABLE_EMULATOR_HOST=localhost:8086 uvicorn src.agents.sap_agent.__main__:a2a_app --host 0.0.0.0 --port 8001 --reload

# Box Agent (port 8002)
uvicorn src.agents.box_agent.__main__:a2a_app --host 0.0.0.0 --port 8002 --reload

# QMS Orchestrator (port 8000)
uvicorn main:app --reload
```

Verify agent cards:

```bash
curl http://localhost:8000/.well-known/agent.json
curl http://localhost:8001/.well-known/agent.json
curl http://localhost:8002/.well-known/agent.json
```

## Testing with A2A Inspector

The [A2A Inspector](https://github.com/google-a2a/a2a-inspector) is a web-based debugging tool for the A2A protocol. It lets you connect to any A2A agent, inspect its agent card, send messages via an interactive chat UI, and view the raw JSON-RPC traffic in a console panel. All responses are validated against the A2A spec in real time.

**Option 1: Hosted version (no install)**

Go to [a2ainspect.com](https://a2ainspect.com/), enter `http://localhost:8000` as the agent URL, and start chatting.

**Option 2: Run locally**

```bash
git clone https://github.com/google-a2a/a2a-inspector.git
cd a2a-inspector
uv sync

# Terminal 1 — frontend
cd frontend && npm install && npm run dev

# Terminal 2 — backend
uv run a2a-inspector
```

Then open `http://127.0.0.1:5001` in your browser, enter `http://localhost:8000` as the agent URL, and click **Connect**. You can also connect directly to the sub-agents at `:8001` (SAP) or `:8002` (Box).

**Option 3: curl**

```bash
curl -s -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Show me all open CAPAs"}],
        "messageId": "msg-1"
      }
    }
  }'
```

## Example Prompts

```
Show me all open CAPAs
What documents were updated for CAPA 000300000005?
What does our incoming inspection SOP say about trace metals?
Show me supplier quality issues for RM-00078234
What preventive actions are still in process?
```

Multi-agent workflows (hits both SAP and Box):

```
Get the details of CAPA 000300000005 from SAP, then search Box for incoming inspection documents.
Find all in-process preventive actions from SAP, then search Box for supplier quality documents.
```

## Demo Scenario

The FDA QMSR became effective February 2, 2026, amending 21 CFR 820 to incorporate ISO 13485:2016. Key change: §820.180(c) exemption removed — management review, audit, and supplier audit records are now inspectable by FDA. The synthetic data shows bulk document revisions in January 2026, CAPA-driven procedure updates, a gap assessment report, and full traceability from CAPA → document changes → ISO clause references.

## Project Structure

```
main.py / qms_orchestrator.py / qms_orchestrator_tools.py / agent_executor.py  — QMS Orchestrator (port 8000)
src/common/converters.py                                      — Shared A2A ↔ GenAI converters
src/agents/sap_agent/                                         — SAP QM agent (BigTable queries)
src/agents/box_agent/                                         — Box document agent (Box SDK + AI)
scripts/load_bigtable.py                                      — JSONL → BigTable data loader
scripts/generate_pdfs.py                                      — Controlled document PDF generator
data/*.jsonl                                                  — Synthetic test data
data/documents/*.pdf                                          — Generated document PDFs
```
