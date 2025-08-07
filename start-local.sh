#!/bin/bash

# Verba Local Deployment Startup Script
# This script sets up and starts Verba with local Weaviate Docker deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${2}${1}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is available
port_available() {
    ! lsof -Pi :"$1" -sTCP:LISTEN -t >/dev/null 2>&1
}

# Header
print_color "=====================================" "$BLUE"
print_color "   Verba Local Deployment Startup    " "$BLUE"
print_color "   (PostgreSQL + uv optimized)       " "$BLUE"
print_color "=====================================" "$BLUE"
echo

# Check prerequisites
print_color "Checking prerequisites..." "$YELLOW"

# Check Docker
if ! command_exists docker; then
    print_color "Error: Docker is not installed" "$RED"
    print_color "Please install Docker from https://docs.docker.com/get-docker/" "$YELLOW"
    exit 1
fi

# Check Docker Compose
if ! command_exists docker || ! docker compose version >/dev/null 2>&1; then
    print_color "Error: Docker Compose is not installed" "$RED"
    print_color "Please install Docker Compose" "$YELLOW"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_color "Error: Docker is not running" "$RED"
    print_color "Please start Docker Desktop or Docker daemon" "$YELLOW"
    exit 1
fi

print_color "✓ Docker and Docker Compose are installed and running" "$GREEN"

# Check ports (only need 8000 for Verba now)
print_color "\nChecking port availability..." "$YELLOW"

PORTS_OK=true
for port in 8000; do
    if port_available $port; then
        print_color "✓ Port $port is available" "$GREEN"
    else
        print_color "✗ Port $port is already in use" "$RED"
        PORTS_OK=false
    fi
done

if [ "$PORTS_OK" = false ]; then
    print_color "\nPort 8000 is in use. Please free it or modify the configuration" "$YELLOW"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for .env file
print_color "\nChecking environment configuration..." "$YELLOW"

if [ ! -f .env ]; then
    if [ -f .env.local ]; then
        print_color "Creating .env from .env.local template..." "$YELLOW"
        cp .env.local .env
        print_color "✓ Created .env file" "$GREEN"
    elif [ -f .env.example ]; then
        print_color "Creating .env from .env.example template..." "$YELLOW"
        cp .env.example .env
        # Update for local deployment with PostgreSQL
        print_color "✓ Created .env file configured for PostgreSQL deployment" "$GREEN"
    else
        print_color "Warning: No .env file found" "$YELLOW"
        print_color "Creating minimal .env for PostgreSQL deployment..." "$YELLOW"
        cat > .env << EOF
# Verba Local Deployment Configuration - PostgreSQL
# Configure your PostgreSQL connection details here
# DATABASE_URL=postgresql://user:password@localhost:5432/verba

# Add your API keys here
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=
COHERE_API_KEY=
EOF
        print_color "✓ Created minimal .env file" "$GREEN"
    fi
fi

# Check for API keys
print_color "\nChecking API keys..." "$YELLOW"
source .env

API_KEYS_SET=false
if [ -n "$OPENAI_API_KEY" ]; then
    print_color "✓ OpenAI API key is set" "$GREEN"
    API_KEYS_SET=true
fi
if [ -n "$ANTHROPIC_API_KEY" ]; then
    print_color "✓ Anthropic API key is set" "$GREEN"
    API_KEYS_SET=true
fi
if [ -n "$GOOGLE_API_KEY" ]; then
    print_color "✓ Google API key is set" "$GREEN"
    API_KEYS_SET=true
fi
if [ -n "$COHERE_API_KEY" ]; then
    print_color "✓ Cohere API key is set" "$GREEN"
    API_KEYS_SET=true
fi

if [ "$API_KEYS_SET" = false ]; then
    print_color "\nWarning: No API keys are set in .env" "$YELLOW"
    print_color "You'll need to add API keys to use embedding and generation features" "$YELLOW"
    print_color "Edit .env and add your API keys" "$YELLOW"
    echo
fi

# Start or restart services
print_color "\nStarting services..." "$YELLOW"

# Check if services are already running
if docker compose ps | grep -q "verba.*running"; then
    print_color "Services are already running. Restarting..." "$YELLOW"
    docker compose down
    sleep 2
fi

# Start services
print_color "Starting Verba with PostgreSQL backend..." "$YELLOW"
docker compose up -d

# Wait for services to be ready
print_color "\nWaiting for Verba to start..." "$YELLOW"

# Wait for Verba
VERBA_READY=false
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        VERBA_READY=true
        break
    fi
    echo -n "."
    sleep 2
done
echo

if [ "$VERBA_READY" = true ]; then
    print_color "✓ Verba is ready" "$GREEN"
else
    print_color "✗ Verba failed to start" "$RED"
    print_color "Check logs with: docker compose logs verba" "$YELLOW"
    print_color "Make sure your DATABASE_URL is configured correctly" "$YELLOW"
    exit 1
fi

# Success message
print_color "\n=====================================" "$GREEN"
print_color "   Local Deployment Started Successfully! " "$GREEN"
print_color "=====================================" "$GREEN"
echo
print_color "Access points:" "$BLUE"
print_color "  • Verba UI:      http://localhost:8000" "$GREEN"
print_color "  • Health check:  http://localhost:8000/health" "$GREEN"
echo
print_color "Database:" "$BLUE"
print_color "  • Using PostgreSQL with pgvector" "$GREEN"
print_color "  • Configure DATABASE_URL in .env" "$YELLOW"
echo
print_color "Useful commands:" "$BLUE"
print_color "  • View logs:      docker compose logs -f" "$YELLOW"
print_color "  • Stop services:  docker compose down" "$YELLOW"
print_color "  • View status:    docker compose ps" "$YELLOW"
print_color "  • Development:    uv run verba start" "$YELLOW"
print_color "  • Direct install: uvx goldenverba start" "$YELLOW"
echo

# Open browser if available
if command_exists open; then
    # macOS
    print_color "Opening Verba in your browser..." "$YELLOW"
    open http://localhost:8000
elif command_exists xdg-open; then
    # Linux
    print_color "Opening Verba in your browser..." "$YELLOW"
    xdg-open http://localhost:8000
elif command_exists start; then
    # Windows
    print_color "Opening Verba in your browser..." "$YELLOW"
    start http://localhost:8000
else
    print_color "Please open http://localhost:8000 in your browser" "$YELLOW"
fi

# Option to tail logs
echo
read -p "Would you like to view the logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker compose logs -f
fi