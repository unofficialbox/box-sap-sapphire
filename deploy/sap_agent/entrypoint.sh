#!/bin/bash
set -e

echo "Starting BigTable emulator..."
gcloud beta emulators bigtable start --host-port=localhost:8086 &
EMULATOR_PID=$!

# Wait for emulator to be ready
echo "Waiting for BigTable emulator to start..."
for i in $(seq 1 30); do
    if nc -z localhost 8086 2>/dev/null; then
        echo "BigTable emulator is ready."
        break
    fi
    if [ $i -eq 30 ]; then
        echo "WARNING: Emulator may not be ready yet, proceeding anyway..."
    fi
    sleep 1
done

# Load data into emulator
echo "Loading data into BigTable emulator..."
export BIGTABLE_EMULATOR_HOST=localhost:8086
python load_bigtable.py

# Start the ADK A2A server
echo "Starting ADK A2A server on port ${PORT:-8080}..."
exec adk api_server --a2a --port "${PORT:-8080}" --host 0.0.0.0 /home/myuser/agents
