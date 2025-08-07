#!/usr/bin/env bash

# SETUP.sh - Idempotent setup script for Verba project
# This script can be run multiple times safely
#
# Supports multiple environments:
# - Standard Linux/macOS/Windows development
# - Docker containers
# - codex-universal environment (https://github.com/openai/codex-universal)
#
# For codex-universal environments, the script will:
# - Detect and use pyenv for Python version management
# - Use nvm for Node.js version management
# - Prefer uv for package management (pre-installed in codex-universal)
# - Respect CODEX_ENV_* environment variables

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

# Detect OS and environment
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
    
    # Check if running in codex-universal environment
    if [[ -n "$CODEX_ENV_PYTHON_VERSION" ]] || [[ -f "/.dockerenv" && -f "/usr/local/bin/setup_universal.sh" ]]; then
        print_info "Detected codex-universal environment"
        CODEX_ENV=true
    else
        CODEX_ENV=false
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."
    
    # In codex-universal, check for pyenv and use it if available
    if [[ "$CODEX_ENV" == true ]] && command_exists pyenv; then
        print_info "Using pyenv in codex-universal environment"
        # Set the Python version if specified
        if [[ -n "$CODEX_ENV_PYTHON_VERSION" ]]; then
            print_info "Setting Python version to $CODEX_ENV_PYTHON_VERSION"
            pyenv global "$CODEX_ENV_PYTHON_VERSION" || true
        fi
        PYTHON_CMD="python"
    elif command_exists python3; then
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
    
    # In codex-universal, check for nvm and use it if available
    if [[ "$CODEX_ENV" == true ]] && [[ -s "$HOME/.nvm/nvm.sh" ]]; then
        print_info "Loading nvm in codex-universal environment"
        source "$HOME/.nvm/nvm.sh"
        # Set the Node version if specified
        if [[ -n "$CODEX_ENV_NODE_VERSION" ]]; then
            print_info "Using Node.js version $CODEX_ENV_NODE_VERSION"
            nvm use "$CODEX_ENV_NODE_VERSION" || true
        fi
    fi
    
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
    
    # Check if venv module is available
    if ! $PYTHON_CMD -c "import venv" 2>/dev/null; then
        print_error "Python venv module is not available"
        print_info "Try installing python3-venv package:"
        if [[ "$OS" == "linux" ]]; then
            # In Docker/codex-universal, we might not have sudo
            if [[ -f "/.dockerenv" ]] || [[ "$CODEX_ENV" == true ]]; then
                print_info "  apt-get update && apt-get install -y python3-venv"
            else
                print_info "  sudo apt-get install python3-venv  # For Ubuntu/Debian"
                print_info "  sudo yum install python3-venv      # For RHEL/CentOS"
            fi
        elif [[ "$OS" == "macos" ]]; then
            print_info "  brew install python@3"
        fi
        exit 1
    fi
    
    if [[ ! -d ".venv" ]]; then
        # Prefer uv for virtual environment creation
        if command_exists uv; then
            print_info "Creating virtual environment with uv (preferred)..."
            if ! uv venv .venv --python "$PYTHON_CMD"; then
                print_error "Failed to create virtual environment with uv"
                exit 1
            fi
        else
            print_info "uv not found, creating virtual environment with $PYTHON_CMD..."
            if ! $PYTHON_CMD -m venv .venv; then
                print_error "Failed to create virtual environment"
                exit 1
            fi
        fi
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
        
        # Check for OS mismatch in pyvenv.cfg
        if [[ -f ".venv/pyvenv.cfg" ]]; then
            VENV_HOME=$(grep "^home = " .venv/pyvenv.cfg | cut -d' ' -f3-)
            OS_MISMATCH=false
            
            # Check for cross-platform issues
            if [[ "$OS" == "linux" ]] && [[ "$VENV_HOME" == *"macos"* || "$VENV_HOME" == "/Users/"* || "$VENV_HOME" == *"Darwin"* ]]; then
                OS_MISMATCH=true
                print_warning "Virtual environment was created on macOS but you're on Linux"
            elif [[ "$OS" == "macos" ]] && [[ "$VENV_HOME" == "/home/"* || "$VENV_HOME" == "/usr/bin/python"* ]]; then
                OS_MISMATCH=true
                print_warning "Virtual environment was created on Linux but you're on macOS"
            elif [[ "$OS" == "windows" ]] && [[ "$VENV_HOME" != *"Scripts"* && "$VENV_HOME" != *"Windows"* ]]; then
                OS_MISMATCH=true
                print_warning "Virtual environment was created on Unix but you're on Windows"
            fi
            
            if [[ "$OS_MISMATCH" == true ]]; then
                print_info "Recreating virtual environment for current OS..."
                rm -rf .venv
                
                # Try using uv if available, otherwise use standard venv
                if command_exists uv; then
                    print_info "Using uv to create virtual environment..."
                    if ! uv venv .venv --python "$PYTHON_CMD"; then
                        print_error "Failed to recreate virtual environment with uv"
                        exit 1
                    fi
                else
                    if ! $PYTHON_CMD -m venv .venv; then
                        print_error "Failed to recreate virtual environment"
                        exit 1
                    fi
                fi
                print_success "Virtual environment recreated for $OS"
            fi
        fi
        
        # Check if it's valid
        if [[ "$OS" == "windows" ]]; then
            VENV_PYTHON=".venv/Scripts/python"
        else
            VENV_PYTHON=".venv/bin/python"
        fi
        
        # Check for broken symlinks or missing files
        VENV_CORRUPTED=false
        if [[ -L "$VENV_PYTHON" ]]; then
            # It's a symlink, check if it's broken
            if [[ ! -e "$VENV_PYTHON" ]]; then
                print_warning "Virtual environment has broken symlinks"
                VENV_CORRUPTED=true
            fi
        elif [[ ! -f "$VENV_PYTHON" ]]; then
            print_warning "Virtual environment Python executable not found"
            VENV_CORRUPTED=true
        fi
        
        if [[ "$VENV_CORRUPTED" == true ]]; then
            print_info "Recreating virtual environment due to corruption..."
            rm -rf .venv
            
            # Try using uv if available, otherwise use standard venv
            if command_exists uv; then
                print_info "Using uv to create virtual environment..."
                if ! uv venv .venv --python "$PYTHON_CMD"; then
                    print_error "Failed to recreate virtual environment with uv"
                    exit 1
                fi
            else
                if ! $PYTHON_CMD -m venv .venv; then
                    print_error "Failed to recreate virtual environment"
                    exit 1
                fi
            fi
            print_success "Virtual environment recreated"
        fi
    fi
    
    # Verify activation script exists
    if [[ "$OS" == "windows" ]]; then
        ACTIVATE_SCRIPT=".venv/Scripts/activate"
    else
        ACTIVATE_SCRIPT=".venv/bin/activate"
    fi
    
    if [[ -f "$ACTIVATE_SCRIPT" ]]; then
        print_info "Virtual environment activation script: source $ACTIVATE_SCRIPT"
    else
        print_error "Could not find activation script at $ACTIVATE_SCRIPT"
        print_info "Virtual environment structure:"
        ls -la .venv/
        exit 1
    fi
}

# Install backend dependencies
install_backend() {
    print_info "Installing backend dependencies..."
    
    # Determine Python executable path
    if [[ "$OS" == "windows" ]]; then
        VENV_PYTHON=".venv/Scripts/python"
        PIP_CMD=".venv/Scripts/pip"
    else
        VENV_PYTHON=".venv/bin/python"
        PIP_CMD=".venv/bin/pip"
    fi
    
    # Check if uv is available and prefer it for package management
    if command_exists uv; then
        print_info "Using uv for package installation (preferred)..."
        print_info "Installing Verba package in development mode..."
        uv sync --group dev
    else
        print_warning "uv not found, falling back to pip..."

        # Check if virtual environment Python exists
        VENV_CORRUPTED=false
        if [[ -L "$VENV_PYTHON" ]]; then
            # It's a symlink, check if it's broken
            if [[ ! -e "$VENV_PYTHON" ]]; then
                print_error "Virtual environment has broken symlinks at $VENV_PYTHON"
                VENV_CORRUPTED=true
            fi
        elif [[ ! -f "$VENV_PYTHON" ]]; then
            print_error "Virtual environment Python not found at $VENV_PYTHON"
            VENV_CORRUPTED=true
        fi

        if [[ "$VENV_CORRUPTED" == true ]]; then
            print_info "Attempting to recreate virtual environment..."
            rm -rf .venv
            $PYTHON_CMD -m venv .venv

            # Check again
            STILL_CORRUPTED=false
            if [[ -L "$VENV_PYTHON" ]]; then
                if [[ ! -e "$VENV_PYTHON" ]]; then
                    STILL_CORRUPTED=true
                fi
            elif [[ ! -f "$VENV_PYTHON" ]]; then
                STILL_CORRUPTED=true
            fi

            if [[ "$STILL_CORRUPTED" == true ]]; then
                print_error "Failed to create virtual environment"
                exit 1
            fi
        fi

        # Ensure pip is up to date in the virtual environment
        print_info "Upgrading pip..."
        $VENV_PYTHON -m pip install --upgrade pip

        # Check if pip command exists
        if [[ ! -f "$PIP_CMD" ]] && [[ ! -L "$PIP_CMD" ]]; then
            print_error "pip not found at $PIP_CMD"
            print_info "Installing pip in virtual environment..."
            $VENV_PYTHON -m ensurepip --upgrade
        fi

        # Install package in development mode with dev extras
        print_info "Installing Verba package in development mode..."
        if [[ -f "$PIP_CMD" ]] || [[ -L "$PIP_CMD" ]]; then
            $PIP_CMD install -e ".[dev]"
        else
            $VENV_PYTHON -m pip install -e ".[dev]"
        fi
    fi
    
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
# PostgreSQL Configuration
# DATABASE_URL=postgresql://user:password@localhost:5432/verba

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
    if command_exists uv; then
        echo "  1. With uv (recommended):"
        echo "     uv run verba start"
        echo "  2. Or install globally and run:"
        echo "     uvx goldenverba start"
        echo "  3. Or activate the virtual environment:"
        if [[ "$OS" == "windows" ]]; then
            echo "     .venv\\Scripts\\activate"
        else
            echo "     source .venv/bin/activate"
        fi
        echo "     verba start"
    else
        echo "  1. Activate the virtual environment:"
        if [[ "$OS" == "windows" ]]; then
            echo "     .venv\\Scripts\\activate"
        else
            echo "     source .venv/bin/activate"
        fi
        echo "  2. Start Verba:"
        echo "     verba start"
    fi
    echo "  3. Update .env file with your API keys"
    echo "  4. For local development with PostgreSQL:"
    echo "     Set DATABASE_URL in .env or use Railway PostgreSQL"
    echo "  5. For development with modern tooling:"
    echo "     uv run ruff format goldenverba  # Format code"
    echo "     uv run ruff check goldenverba   # Lint code"
    echo "     uv run ty check goldenverba     # Type check (preview)"
    echo
}

# Run main function
main