#!/bin/bash
set -e

echo "Starting ADK A2A server on port ${PORT:-8080}..."
exec adk api_server --a2a --port "${PORT:-8080}" --host 0.0.0.0 /home/myuser/agents
