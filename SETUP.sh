#!/usr/bin/env bash

# SETUP.sh - Idempotent setup script for Verba project
# This script can be run multiple times safely

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    print_info "Detected OS: $OS"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.10 or higher."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info[0])')
    PYTHON_MINOR=$($PYTHON_CMD -c 'import sys; print(sys.version_info[1])')
    
    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 10 ]]; then
        print_error "Python 3.10 or higher is required. Found: Python $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION is installed"
}

# Check Node.js version
check_nodejs() {
    print_info "Checking Node.js installation..."
    
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18 or higher."
        exit 1
    fi
    
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    
    if [[ $NODE_VERSION -lt 18 ]]; then
        print_error "Node.js 18 or higher is required. Found: Node.js $(node -v)"
        exit 1
    fi
    
    print_success "Node.js $(node -v) is installed"
}

# Check npm
check_npm() {
    print_info "Checking npm installation..."
    
    if ! command_exists npm; then
        print_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    print_success "npm $(npm -v) is installed"
}

# Create and activate virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [[ ! -d ".venv" ]]; then
        print_info "Creating virtual environment..."
        $PYTHON_CMD -m venv .venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    if [[ "$OS" == "windows" ]]; then
        ACTIVATE_SCRIPT=".venv/Scripts/activate"
    else
        ACTIVATE_SCRIPT=".venv/bin/activate"
    fi
    
    if [[ -f "$ACTIVATE_SCRIPT" ]]; then
        print_info "Virtual environment activation script: source $ACTIVATE_SCRIPT"
    else
        print_error "Could not find activation script at $ACTIVATE_SCRIPT"
        exit 1
    fi
}

# Install backend dependencies
install_backend() {
    print_info "Installing backend dependencies..."
    
    # Ensure pip is up to date in the virtual environment
    if [[ "$OS" == "windows" ]]; then
        .venv/Scripts/python -m pip install --upgrade pip
        PIP_CMD=".venv/Scripts/pip"
    else
        .venv/bin/python -m pip install --upgrade pip
        PIP_CMD=".venv/bin/pip"
    fi
    
    # Install package in development mode with dev extras
    print_info "Installing Verba package in development mode..."
    $PIP_CMD install -e ".[dev]"
    
    print_success "Backend dependencies installed"
}

# Install frontend dependencies
install_frontend() {
    print_info "Installing frontend dependencies..."
    
    # Change to frontend directory
    if [[ ! -d "frontend" ]]; then
        print_error "Frontend directory not found"
        exit 1
    fi
    
    cd frontend
    
    # Install dependencies with legacy peer deps flag
    print_info "Running npm install with legacy peer deps..."
    npm install --legacy-peer-deps
    
    cd ..
    
    print_success "Frontend dependencies installed"
}

# Setup environment file
setup_env() {
    print_info "Setting up environment file..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            print_info "Copying .env.example to .env..."
            cp .env.example .env
            print_success "Environment file created"
            print_warning "Please update .env with your API keys and configuration"
        else
            print_warning "No .env.example file found. Creating basic .env file..."
            cat > .env << EOF
# Weaviate Configuration
WEAVIATE_URL_VERBA=http://localhost:8080
WEAVIATE_API_KEY_VERBA=

# API Keys (add your keys here)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
COHERE_API_KEY=
GOOGLE_API_KEY=
UNSTRUCTURED_API_KEY=
FIRECRAWL_API_KEY=
EOF
            print_success "Basic .env file created"
            print_warning "Please update .env with your API keys"
        fi
    else
        print_info "Environment file already exists"
    fi
}

# Main setup function
main() {
    echo "=================================="
    echo "Verba Project Setup Script"
    echo "=================================="
    echo
    
    # Check if we're in the right directory
    if [[ ! -f "setup.py" ]] || [[ ! -d "goldenverba" ]]; then
        print_error "This script must be run from the Verba project root directory"
        exit 1
    fi
    
    # Detect OS
    detect_os
    
    # Check requirements
    check_python
    check_nodejs
    check_npm
    
    # Setup components
    setup_venv
    install_backend
    install_frontend
    setup_env
    
    echo
    echo "=================================="
    print_success "Setup completed successfully!"
    echo "=================================="
    echo
    print_info "Next steps:"
    echo "  1. Activate the virtual environment:"
    if [[ "$OS" == "windows" ]]; then
        echo "     .venv\\Scripts\\activate"
    else
        echo "     source .venv/bin/activate"
    fi
    echo "  2. Update .env file with your API keys"
    echo "  3. Start Weaviate (if using locally):"
    echo "     docker compose up -d weaviate"
    echo "  4. Start Verba:"
    echo "     verba start"
    echo
}

# Run main function
main