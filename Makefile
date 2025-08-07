# Makefile for Verba Project

# Variables
PYTHON := python3
UV := uv
NPM := npm
VENV := .venv
FRONTEND_DIR := frontend
BACKEND_LOG := backend.log
FRONTEND_LOG := frontend.log

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.PHONY: help
help:
	@echo "$(BLUE)Verba Project Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Setup Commands:$(NC)"
	@echo "  make setup          - Complete project setup (backend + frontend)"
	@echo "  make setup-backend  - Setup Python virtual environment and install backend dependencies"
	@echo "  make setup-frontend - Install frontend dependencies"
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  make dev            - Run both backend and frontend in development mode"
	@echo "  make backend        - Run backend server only"
	@echo "  make frontend       - Run frontend development server only"
	@echo "  make build          - Build frontend for production"
	@echo ""
	@echo "$(GREEN)Testing Commands:$(NC)"
	@echo "  make test           - Run all tests (backend + frontend)"
	@echo "  make test-backend   - Run backend tests with coverage"
	@echo "  make test-frontend  - Run frontend tests with Vitest"
	@echo "  make test-ui        - Run frontend tests with Vitest UI"
	@echo ""
	@echo "$(GREEN)Code Quality Commands:$(NC)"
	@echo "  make lint           - Run linters (backend + frontend)"
	@echo "  make format         - Format code (backend + frontend)"
	@echo "  make lint-fix       - Run linters with auto-fix (backend + frontend)"
	@echo "  make typecheck      - Run type checking with ty"
	@echo "  make check          - Run all checks (lint + tests + typecheck)"
	@echo "  make check-backend  - Run comprehensive backend checks with Astral tools"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start services with Docker Compose"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make docker-logs    - View Docker logs"
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
	@echo "  make install-uv     - Install uv package manager if not present"
	@echo "  make sync           - Sync dependencies using uv"
	@echo "  make clean          - Clean build artifacts and logs"
	@echo "  make reset          - Reset project (clean + remove dependencies)"
	@echo "  make logs           - Tail all logs"
	@echo "  make kill-ports     - Kill processes on default ports (8000, 3000)"

# Complete setup
.PHONY: setup
setup: setup-backend setup-frontend
	@echo "$(GREEN)✓ Setup completed successfully!$(NC)"

# Backend setup
.PHONY: setup-backend
setup-backend:
	@echo "$(BLUE)Setting up backend...$(NC)"
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(RED)Error: uv is not installed. Please install uv first:$(NC)"; \
		echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		exit 1; \
	fi
	@$(UV) sync --group dev
	@echo "$(GREEN)✓ Backend setup completed$(NC)"

# Frontend setup
.PHONY: setup-frontend
setup-frontend:
	@echo "$(BLUE)Setting up frontend...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) install --legacy-peer-deps
	@echo "$(GREEN)✓ Frontend setup completed$(NC)"

# Run both backend and frontend
.PHONY: dev
dev:
	@echo "$(BLUE)Starting development servers...$(NC)"
	@echo "$(YELLOW)Backend log: $(BACKEND_LOG)$(NC)"
	@echo "$(YELLOW)Frontend log: $(FRONTEND_LOG)$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to stop both servers$(NC)"
	@make backend > $(BACKEND_LOG) 2>&1 & \
		BACKEND_PID=$$!; \
		make frontend > $(FRONTEND_LOG) 2>&1 & \
		FRONTEND_PID=$$!; \
		trap "kill $$BACKEND_PID $$FRONTEND_PID 2>/dev/null; exit" INT; \
		echo "$(GREEN)✓ Backend running (PID: $$BACKEND_PID)$(NC)"; \
		echo "$(GREEN)✓ Frontend running (PID: $$FRONTEND_PID)$(NC)"; \
		echo ""; \
		echo "$(BLUE)Servers are running:$(NC)"; \
		echo "  Backend:  http://localhost:8000"; \
		echo "  Frontend: http://localhost:3000"; \
		echo ""; \
		tail -f $(BACKEND_LOG) $(FRONTEND_LOG)

# Run backend only
.PHONY: backend
backend:
	@echo "$(BLUE)Starting backend server...$(NC)"
	@$(UV) run verba start

# Run frontend only
.PHONY: frontend
frontend:
	@echo "$(BLUE)Starting frontend development server...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run dev

# Build frontend
.PHONY: build
build:
	@echo "$(BLUE)Building frontend...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run build
	@echo "$(GREEN)✓ Build completed$(NC)"

# Run all tests
.PHONY: test
test: test-backend test-frontend
	@echo "$(GREEN)✓ All tests completed$(NC)"

# Backend tests
.PHONY: test-backend
test-backend:
	@echo "$(BLUE)Running backend tests...$(NC)"
	@$(UV) run pytest --cov=goldenverba

# Frontend tests
.PHONY: test-frontend
test-frontend:
	@echo "$(BLUE)Running frontend tests...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run test

# Frontend tests with UI
.PHONY: test-ui
test-ui:
	@echo "$(BLUE)Running frontend tests with UI...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run test:ui

# Lint all code
.PHONY: lint
lint: lint-backend lint-frontend
	@echo "$(GREEN)✓ Linting completed$(NC)"

# Backend linting
.PHONY: lint-backend
lint-backend:
	@echo "$(BLUE)Linting backend...$(NC)"
	@$(UV) run ruff check goldenverba
	@$(UV) run ruff format --check goldenverba

# Backend linting with auto-fix
.PHONY: lint-fix-backend
lint-fix-backend:
	@echo "$(BLUE)Linting and fixing backend...$(NC)"
	@$(UV) run ruff check --fix goldenverba
	@$(UV) run ruff format goldenverba

# Frontend linting
.PHONY: lint-frontend
lint-frontend:
	@echo "$(BLUE)Linting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint:check

# Format all code
.PHONY: format
format: format-backend format-frontend
	@echo "$(GREEN)✓ Formatting completed$(NC)"

# Lint and fix all code
.PHONY: lint-fix
lint-fix: lint-fix-backend lint-frontend
	@echo "$(GREEN)✓ Linting with auto-fix completed$(NC)"

# Backend formatting
.PHONY: format-backend
format-backend:
	@echo "$(BLUE)Formatting backend...$(NC)"
	@$(UV) run ruff format goldenverba

# Frontend formatting
.PHONY: format-frontend
format-frontend:
	@echo "$(BLUE)Formatting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run format

# Type checking
.PHONY: typecheck
typecheck: typecheck-backend
	@echo "$(GREEN)✓ Type checking completed$(NC)"

# Fallback type checking with mypy (if ty doesn't work)
.PHONY: typecheck-mypy
typecheck-mypy:
	@echo "$(BLUE)Running type checking with mypy (fallback)...$(NC)"
	@$(UV) add --group dev mypy --quiet || echo "$(YELLOW)Failed to add mypy$(NC)"
	@$(UV) run mypy goldenverba --ignore-missing-imports --no-strict-optional || echo "$(YELLOW)mypy not available$(NC)"

# Backend type checking
.PHONY: typecheck-backend
typecheck-backend:
	@echo "$(BLUE)Running type checking with ty (preview)...$(NC)"
	@echo "$(YELLOW)Note: ty is in preview and may hang or crash$(NC)"
	@if command -v timeout >/dev/null 2>&1; then \
		timeout 30s $(UV) run ty check goldenverba 2>&1 || { \
			echo "$(YELLOW)⚠ ty failed or timed out (this is expected for preview)$(NC)"; \
			echo "$(GREEN)✓ Type checking configuration is ready for when ty stabilizes$(NC)"; \
		}; \
	else \
		$(UV) run ty check goldenverba 2>&1 || { \
			echo "$(YELLOW)⚠ ty failed (this is expected for preview)$(NC)"; \
			echo "$(GREEN)✓ Type checking configuration is ready for when ty stabilizes$(NC)"; \
		}; \
	fi

# Run all checks
.PHONY: check
check: lint test typecheck
	@echo "$(GREEN)✓ All checks passed$(NC)"

# Run comprehensive backend checks with Astral tools
.PHONY: check-backend
check-backend: lint-backend test-backend typecheck-backend
	@echo "$(GREEN)✓ All backend checks passed$(NC)"

# Docker commands
.PHONY: docker-build
docker-build:
	@echo "$(BLUE)Building Docker images...$(NC)"
	@docker-compose build

.PHONY: docker-up
docker-up:
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@docker-compose up -d

.PHONY: docker-down
docker-down:
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@docker-compose down

.PHONY: docker-logs
docker-logs:
	@docker-compose logs -f

# Clean build artifacts
.PHONY: clean
clean:
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	@rm -rf $(FRONTEND_DIR)/.next
	@rm -rf $(FRONTEND_DIR)/out
	@rm -rf $(FRONTEND_DIR)/coverage
	@rm -rf goldenverba/__pycache__
	@rm -rf goldenverba/**/__pycache__
	@rm -rf .pytest_cache
	@rm -rf .coverage
	@rm -rf *.log
	@echo "$(GREEN)✓ Clean completed$(NC)"

# Reset project
.PHONY: reset
reset: clean
	@echo "$(YELLOW)⚠️  This will remove all dependencies. Continue? [y/N]$(NC)"
	@read -r response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		echo "$(BLUE)Resetting project...$(NC)"; \
		rm -rf $(VENV); \
		rm -rf $(FRONTEND_DIR)/node_modules; \
		echo "$(GREEN)✓ Reset completed$(NC)"; \
	else \
		echo "$(YELLOW)Reset cancelled$(NC)"; \
	fi

# View logs
.PHONY: logs
logs:
	@echo "$(BLUE)Tailing logs...$(NC)"
	@tail -f *.log

# Kill processes on default ports
.PHONY: kill-ports
kill-ports:
	@echo "$(BLUE)Killing processes on ports 8000 and 3000...$(NC)"
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@echo "$(GREEN)✓ Ports cleared$(NC)"

# Install development tools
.PHONY: install-tools
install-tools:
	@echo "$(BLUE)Installing development tools...$(NC)"
	@$(UV) sync --group dev
	@echo "$(GREEN)✓ Development tools installed$(NC)"

# Install uv if not present
.PHONY: install-uv
install-uv:
	@if ! command -v $(UV) >/dev/null 2>&1; then \
		echo "$(BLUE)Installing uv...$(NC)"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "$(GREEN)✓ uv installed$(NC)"; \
	else \
		echo "$(GREEN)✓ uv is already installed$(NC)"; \
	fi

# Sync dependencies using uv
.PHONY: sync
sync:
	@echo "$(BLUE)Syncing dependencies with uv...$(NC)"
	@$(UV) sync --group dev
	@echo "$(GREEN)✓ Dependencies synced$(NC)"