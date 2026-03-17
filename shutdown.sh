#!/usr/bin/env bash

SAP_PORT=8001
BOX_PORT=8002
ORCHESTRATOR_PORT=8000

echo "Stopping agents on ports $SAP_PORT, $BOX_PORT, $ORCHESTRATOR_PORT..."
pids=$(lsof -ti:$SAP_PORT,$BOX_PORT,$ORCHESTRATOR_PORT 2>/dev/null)

if [ -z "$pids" ]; then
  echo "No agents running."
  exit 0
fi

kill $pids 2>/dev/null
sleep 1

# Force-kill any stragglers
remaining=$(lsof -ti:$SAP_PORT,$BOX_PORT,$ORCHESTRATOR_PORT 2>/dev/null)
if [ -n "$remaining" ]; then
  kill -9 $remaining 2>/dev/null
fi

echo "All agents stopped."
