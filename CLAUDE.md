# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Multi-agent A2A system for SAP Sapphire conference demo. Showcases SAP S/4HANA Quality Management integration with Box for medical device QMS compliance, focused on controlled documents and CAPA records triggered by the FDA QMSR / ISO 13485:2016 regulatory change.

## Architecture

```
QMS Orchestrator :8000 (qms_orchestrator)
├── query_sap ──→ SAP Agent :8001 (sap_agent) → BigQuery (sap_qm dataset)
└── query_box ──→ Box Agent :8002 (box_agent) → Box API (CCG Auth)
```

- **A2A Protocol** (JSON-RPC 2.0) for inter-agent communication
- **Google ADK** (Agent Development Kit) with Gemini 2.5 Flash via LiteLLM
- **FastMCP** wrappers on each agent's tools for MCP protocol support

**Orchestrator→sub-agent communication**: The QMS Orchestrator does NOT use ADK sub-agents. Instead, `qms_orchestrator_tools.py` makes synchronous HTTP POST calls (via httpx) to the sub-agents' A2A endpoints. Each sub-agent runs its own independent ADK Runner.

## Key Commands

```bash
# Setup
uv sync                                 # Install dependencies
cp .env.sample .env                     # Configure host env
cp src/agents/sap_agent/.env.sample src/agents/sap_agent/.env
cp src/agents/box_agent/.env.sample src/agents/box_agent/.env
gcloud auth application-default login   # Authenticate for BigQuery
python scripts/load_bigquery.py         # Load JSONL data into BigQuery (one-time)

# Run agents (each in separate terminal)
uvicorn src.agents.sap_agent.__main__:a2a_app --host 0.0.0.0 --port 8001 --reload
uvicorn src.agents.box_agent.__main__:a2a_app --host 0.0.0.0 --port 8002 --reload
uvicorn main:app --reload               # Host agent on port 8000

# Verify agent cards
curl http://localhost:8000/.well-known/agent.json
curl http://localhost:8001/.well-known/agent.json
curl http://localhost:8002/.well-known/agent.json

# Generate sample PDFs
python scripts/generate_pdfs.py
```

## Project Structure

```
main.py / qms_orchestrator.py / qms_orchestrator_tools.py / agent_executor.py  — QMS Orchestrator (port 8000)
src/common/converters.py                     — Shared A2A ↔ GenAI part converters
src/agents/sap_agent/                        — SAP QM agent (port 8001)
    bigquery_client.py                       — BigQuery query engine (singleton)
    sap_tools.py                             — 5 tool functions
    sap_agent.py / sap_executor.py           — ADK agent + A2A executor
src/agents/box_agent/                        — Box document agent (port 8002)
    box_tools.py                             — 11 tool functions (CRUD + AI)
    box_agent.py / box_executor.py           — ADK agent + A2A executor
scripts/load_bigquery.py                     — JSONL → BigQuery data loader
scripts/generate_pdfs.py                     — Controlled document PDF generator
data/*.jsonl                                 — Synthetic test data
data/documents/*.pdf                         — Generated document PDFs
deploy/                                      — Cloud Run deployment (Dockerfiles, flattened agents)
```

## Agent File Convention

Each agent follows this pattern:
- `*_agent.py` — LlmAgent definition with tools and instruction prompt
- `*_executor.py` — AgentExecutor (A2A request → ADK Runner → response)
- `*_tools.py` — Pure tool functions returning `{"status": "success"|"error", ...}` dicts
- `*_mcp.py` — FastMCP server wrapping tool functions
- `__main__.py` — Uvicorn entry point with AgentCard, Runner, A2A app
- `.env.sample` — Environment variables template

## Environment Variables

QMS Orchestrator (`.env`): `GOOGLE_GENAI_USE_VERTEXAI`, `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`, `LITELLM_MODEL`, `AGENT_URL`

SAP agent adds: `BIGQUERY_DATASET`, `APP_URL`

Box agent adds: `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET`, `BOX_SUBJECT_TYPE`, `BOX_SUBJECT_ID`, `BOX_ROOT_FOLDER_ID`, `APP_URL`

## BigQuery Schema

Dataset `sap_qm` with three tables (all STRING columns, nested arrays as JSON strings):
- **quality_notifications**: 10 records — CAPAs with `_Item`, `_Task`, `_Activity` JSON fields
- **quality_info_records**: 30 records — procurement quality data with `to_QltyFirstArticleInsp` JSON field
- **controlled_documents**: 20 records — QMS document metadata (flat, no nested fields)

## Data Conventions

- Material prefixes: `FG-` (finished), `RM-` (raw), `HALB-` (semi-finished), `HAWA-` (trading)
- Plants: `1000`, `1100`, `2000`; Suppliers: 10-digit zero-padded
- Notification types: `Q1` (customer), `Q2` (vendor), `Q3` (internal)
- Task types: `CORRECTIVE`, `PREVENTIVE`; Status: `COMPLETED`, `IN_PROCESS`
- Doc types: `QM`, `SOP`, `WI`, `MDF`, `VP`, `RPT`
- Personnel: JSMITH, AKUMAR, RJONES, SLEE, DKIM, MWEBER, TCHEN, LPARK, VPQUALITY

## SAP API References

- **Quality Info Record**: `API_QUALITYINFORECORD_SRV` (OData v2)
- **Quality Notification (CAPA)**: `CE_QUALITYNOTIFICATION_0001` (OData v4)

## Demo Scenario

FDA QMSR (effective Feb 2, 2026) amends 21 CFR 820 to incorporate ISO 13485:2016. Key change: §820.180(c) exemption removed — management review, audit, and supplier audit records now inspectable by FDA. Data shows bulk document revisions in Jan 2026, CAPA-driven procedure updates, gap assessment report, and full traceability from CAPA → document changes → ISO clause references.

# currentDate
Today's date is 2026-03-12.
