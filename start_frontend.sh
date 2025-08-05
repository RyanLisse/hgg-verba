#!/bin/bash

# Kill any existing process on port 3000
echo "Cleaning up port 3000..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Give it a moment to release the port
sleep 1

cd "$(dirname "$0")/frontend" || exit
bun dev