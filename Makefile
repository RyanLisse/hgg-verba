# Makefile for Verba Project

# Variables
PYTHON := python3
PIP := pip
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
	@echo "  make check          - Run all checks (lint + tests)"
	@echo ""
	@echo "$(GREEN)Docker Commands:$(NC)"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start services with Docker Compose"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make docker-logs    - View Docker logs"
	@echo ""
	@echo "$(GREEN)Utility Commands:$(NC)"
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
	@if [ ! -d "$(VENV)" ]; then \
		$(PYTHON) -m venv $(VENV); \
		echo "$(GREEN)✓ Virtual environment created$(NC)"; \
	fi
	@. $(VENV)/bin/activate && pip install --upgrade pip
	@. $(VENV)/bin/activate && pip install -e ".[dev]"
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
	@. $(VENV)/bin/activate && verba start

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
	@. $(VENV)/bin/activate && pytest --cov=goldenverba

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
	@. $(VENV)/bin/activate && ruff check goldenverba

# Frontend linting
.PHONY: lint-frontend
lint-frontend:
	@echo "$(BLUE)Linting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run lint:check

# Format all code
.PHONY: format
format: format-backend format-frontend
	@echo "$(GREEN)✓ Formatting completed$(NC)"

# Backend formatting
.PHONY: format-backend
format-backend:
	@echo "$(BLUE)Formatting backend...$(NC)"
	@. $(VENV)/bin/activate && black goldenverba

# Frontend formatting
.PHONY: format-frontend
format-frontend:
	@echo "$(BLUE)Formatting frontend...$(NC)"
	@cd $(FRONTEND_DIR) && $(NPM) run format

# Run all checks
.PHONY: check
check: lint test
	@echo "$(GREEN)✓ All checks passed$(NC)"

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
	@. $(VENV)/bin/activate && pip install black ruff pytest pytest-cov
	@echo "$(GREEN)✓ Development tools installed$(NC)"