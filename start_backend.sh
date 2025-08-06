#!/bin/bash

# Kill any existing process on port 8000
echo "Cleaning up port 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Give it a moment to release the port
sleep 1

cd "$(dirname "$0")" || exit
source .venv/bin/activate
verba start --port 8000 --host localhost