#!/usr/bin/env bash
set -e

# Ports for each agent
SAP_PORT=8001
BOX_PORT=8002
ORCHESTRATOR_PORT=8000

# Kill any existing processes on these ports
echo "Stopping any existing agents..."
lsof -ti:$SAP_PORT,$BOX_PORT,$ORCHESTRATOR_PORT 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

# Start SAP Agent
echo "Starting SAP Agent on port $SAP_PORT..."
uv run uvicorn src.agents.sap_agent.__main__:a2a_app \
  --host 0.0.0.0 --port $SAP_PORT --reload &

# Start Box Agent
echo "Starting Box Agent on port $BOX_PORT..."
uv run uvicorn src.agents.box_agent.__main__:a2a_app \
  --host 0.0.0.0 --port $BOX_PORT --reload &

# Start QMS Orchestrator
echo "Starting QMS Orchestrator on port $ORCHESTRATOR_PORT..."
uv run uvicorn main:app \
  --reload --port $ORCHESTRATOR_PORT &

# Wait for agents to be ready
echo ""
echo "Waiting for agents to start..."
for port in $SAP_PORT $BOX_PORT $ORCHESTRATOR_PORT; do
  for i in {1..20}; do
    if curl -s -o /dev/null http://localhost:$port/.well-known/agent.json 2>/dev/null; then
      echo "  Port $port ready"
      break
    fi
    sleep 0.5
  done
done

echo ""
echo "All agents running:"
echo "  SAP Agent:         http://localhost:$SAP_PORT"
echo "  Box Agent:         http://localhost:$BOX_PORT"
echo "  QMS Orchestrator:  http://localhost:$ORCHESTRATOR_PORT"
echo ""
echo "Press Ctrl+C to stop all agents."

# Wait for background processes; forward Ctrl+C to all
trap 'echo "Shutting down..."; kill 0; wait' INT TERM
wait
