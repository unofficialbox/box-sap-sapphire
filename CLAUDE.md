# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Multi-agent A2A system for SAP Sapphire conference demo. Showcases SAP S/4HANA Quality Management integration with Box for medical device QMS compliance, focused on controlled documents and CAPA records triggered by the FDA QMSR / ISO 13485:2016 regulatory change.

## Architecture

```
Host Agent :8000 (routing_agent)
├── SAP Agent :8001 (sap_agent) → BigTable Emulator :8086
└── Box Agent :8002 (box_agent) → Box API (CCG Auth)
```

- **A2A Protocol** (JSON-RPC 2.0) for inter-agent communication
- **Google ADK** (Agent Development Kit) with Gemini 2.5 Flash via LiteLLM
- **FastMCP** wrappers on each agent's tools for MCP protocol support

## Key Commands

```bash
# Setup
docker compose up -d                    # Start BigTable emulator
uv sync                                 # Install dependencies
python scripts/load_bigtable.py         # Load JSONL data into BigTable

# Run agents (each in separate terminal)
uvicorn src.agents.sap_agent.__main__:a2a_app --host 0.0.0.0 --port 8001 --reload
uvicorn src.agents.box_agent.__main__:a2a_app --host 0.0.0.0 --port 8002 --reload
uvicorn main:app --reload               # Host agent on port 8000

# Verify agent cards
curl http://localhost:8000/.well-known/agent-card.json
curl http://localhost:8001/.well-known/agent-card.json
curl http://localhost:8002/.well-known/agent-card.json

# Generate sample PDFs
python scripts/generate_pdfs.py
```

## Project Structure

```
main.py / host_agent.py / agent_executor.py  — Host routing agent (port 8000)
src/common/converters.py                     — Shared A2A ↔ GenAI part converters
src/agents/sap_agent/                        — SAP QM agent (port 8001)
    bigtable_client.py                       — BigTable query engine
    sap_tools.py                             — 5 tool functions
    sap_agent.py / sap_executor.py           — ADK agent + A2A executor
src/agents/box_agent/                        — Box document agent (port 8002)
    box_tools.py                             — 11 tool functions (CRUD + AI)
    box_agent.py / box_executor.py           — ADK agent + A2A executor
scripts/load_bigtable.py                     — JSONL → BigTable data loader
scripts/generate_pdfs.py                     — Controlled document PDF generator
data/*.jsonl                                 — Synthetic test data
data/documents/*.pdf                         — Generated document PDFs
```

## Agent File Convention

Each agent follows this pattern (from reference project box-adk-a2a-agents):
- `*_agent.py` — LlmAgent definition with tools and instruction prompt
- `*_executor.py` — AgentExecutor (A2A request → ADK Runner → response)
- `*_tools.py` — Pure tool functions returning `{"status": "success"|"error", ...}` dicts
- `*_mcp.py` — FastMCP server wrapping tool functions
- `__main__.py` — Uvicorn entry point with AgentCard, Runner, A2A app
- `.env.sample` — Environment variables template

## Data Files

- `data/quality_notifications.jsonl` — 10 notifications with full CAPA hierarchy (_Item → _Cause, _Defect; _Task; _Activity)
- `data/quality_info_records.jsonl` — 30 QualityInProcurement records
- `data/controlled_documents.jsonl` — 20 controlled document records with CAPA cross-references

## BigTable Schema

Row key design for prefix-scan queries:
- **quality_notifications**: `{Type}#{Status}#{Number}` + secondary `MAT#{Material}#`, `SUP#{Supplier}#`
- **quality_info_records**: `{Plant}#{Material}#{IntID}` + secondary `SUP#{Supplier}#`
- **controlled_documents**: `{DocType}#{Status}#{DocID}` + secondary `CAPA#{Ref}#`, `ISO#{Clause}#`

Single column family `data`. Nested arrays stored as JSON-serialized values.

## SAP API References

- **Quality Info Record**: `API_QUALITYINFORECORD_SRV` (OData v2)
- **Quality Notification (CAPA)**: `CE_QUALITYNOTIFICATION_0001` (OData v4)

## Data Conventions

- Material prefixes: `FG-` (finished), `RM-` (raw), `HALB-` (semi-finished), `HAWA-` (trading)
- Plants: `1000`, `1100`, `2000`; Suppliers: 10-digit zero-padded
- Notification types: `Q1` (customer), `Q2` (vendor), `Q3` (internal)
- Task types: `CORRECTIVE`, `PREVENTIVE`; Status: `COMPLETED`, `IN_PROCESS`
- Doc types: `QM`, `SOP`, `WI`, `MDF`, `VP`, `RPT`
- Personnel: JSMITH, AKUMAR, RJONES, SLEE, DKIM, MWEBER, TCHEN, LPARK, VPQUALITY

## Demo Scenario

FDA QMSR (effective Feb 2, 2026) amends 21 CFR 820 to incorporate ISO 13485:2016. Key change: §820.180(c) exemption removed — management review, audit, and supplier audit records now inspectable by FDA. Data shows bulk document revisions in Jan 2026, CAPA-driven procedure updates, gap assessment report, and full traceability from CAPA → document changes → ISO clause references.
