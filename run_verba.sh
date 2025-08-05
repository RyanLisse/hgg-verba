#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Verba Application...${NC}"

# Kill any existing processes
echo -e "${BLUE}Cleaning up existing processes...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Start backend
echo -e "${GREEN}Starting Backend Server on http://localhost:8000${NC}"
cd "$(dirname "$0")"
source .venv/bin/activate
verba start --port 8000 --host localhost &
BACKEND_PID=$!

# Wait for backend to start
echo -e "${BLUE}Waiting for backend to start...${NC}"
sleep 25

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null; then
    echo -e "${GREEN}✓ Backend is running!${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    exit 1
fi

# Start frontend
echo -e "${GREEN}Starting Frontend Server on http://localhost:3000${NC}"
cd frontend || exit
bun dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo -e "${BLUE}Waiting for frontend to start...${NC}"
sleep 5

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Verba is running!${NC}"
echo -e "${GREEN}================================${NC}"
echo -e "Backend: ${BLUE}http://localhost:8000${NC}"
echo -e "Frontend: ${BLUE}http://localhost:3000${NC}"
echo -e ""
echo -e "Press ${RED}Ctrl+C${NC} to stop both servers"
echo -e "${GREEN}================================${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping Verba...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}Verba stopped.${NC}"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT

# Keep script running
wait