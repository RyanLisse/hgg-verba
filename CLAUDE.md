# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Verba is an open-source Retrieval-Augmented Generation (RAG) application that provides a user-friendly interface for querying and interacting with documents using AI. It consists of a Python FastAPI backend and a Next.js React frontend, using PostgreSQL with pgvector as the vector database.

## Key Architecture

### Backend Architecture
- **FastAPI server** with async support in `goldenverba/server/api.py`
- **Component-based plugin system** with base interfaces in `goldenverba/components/interfaces.py`
- **Manager pattern** for handling different component types (readers, chunkers, embedders, retrievers, generators)
- **PostgreSQL with pgvector** for vector storage and configuration persistence
- **WebSocket support** for real-time updates during document processing

### Frontend Architecture
- **Next.js 14** with TypeScript in `frontend/`
- **Feature-based component organization** (Chat, Document, Ingestion, Navigation, Settings)
- **Three.js integration** for 3D vector visualization
- **Real-time updates** via WebSocket connections

## Common Development Commands

### Backend Development

**With uv (Recommended):**
```bash
# Install dependencies and sync
uv sync --group dev

# Install with specific extras
uv sync --group huggingface  # For local embeddings
uv sync --group google       # For Google Vertex AI

# Start the server
uv run verba start --port 8000 --host localhost

# Reset configuration
uv run verba reset --deployment Local

# Run tests
uv run pytest
uv run pytest --cov=goldenverba  # With coverage

# Run a specific test
uv run pytest goldenverba/tests/test_verba_manager.py::TestVerbaManager::test_initialization

# Code quality with Astral tools
uv run ruff check goldenverba     # Lint code
uv run ruff format goldenverba    # Format code (replaces black)
uv run ty check goldenverba       # Type checking (preview)
```

**With pip (Alternative):**
```bash
# Install the package in development mode
pip install -e ".[dev]"

# Install with specific extras
pip install -e ".[huggingface]"  # For local embeddings
pip install -e ".[google]"        # For Google Vertex AI

# Start the server
verba start --port 8000 --host localhost

# Run tests and linting
pytest --cov=goldenverba
ruff check goldenverba
ruff format goldenverba
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps  # Use this flag if you encounter peer dependency issues

# Development server
npm run dev  # Runs on localhost:3000

# Build and copy to FastAPI static folder
npm run build  # Builds and copies to ../goldenverba/server/frontend/out/

# Run tests
npm run test              # Vitest tests
npm run test:ui           # Vitest with UI
npm run test:coverage     # Tests with coverage
bun test --preload ./test/setup.ts  # Alternative Jest-based tests

# Linting and formatting
npm run lint              # Biome check with auto-fix
npm run lint:check        # Biome check only
npm run format            # Biome format with auto-fix
npm run format:check      # Biome format check only
```

### Makefile Commands
The project includes a comprehensive Makefile for streamlined development:

```bash
# Setup and installation
make setup              # Complete project setup (backend + frontend)
make setup-backend      # Setup Python virtual environment and install backend dependencies
make setup-frontend     # Install frontend dependencies

# Development
make dev                # Run both backend and frontend in development mode
make backend            # Run backend server only
make frontend           # Run frontend development server only
make build              # Build frontend for production

# Testing
make test               # Run all tests (backend + frontend)
make test-backend       # Run backend tests with coverage
make test-frontend      # Run frontend tests with Vitest
make test-ui            # Run frontend tests with Vitest UI

# Code quality
make lint               # Run linters (backend + frontend)
make format             # Format code (backend + frontend)
make typecheck          # Run type checking with ty
make check              # Run all checks (lint + format + tests + typecheck)
make check-backend      # Run comprehensive backend checks with Astral tools

# Utilities
make clean              # Clean build artifacts and logs
make reset              # Reset project (clean + remove dependencies)
make kill-ports         # Kill processes on default ports (8000, 3000)
```

### Docker Development
```bash
# Build and run with Docker Compose
docker compose --env-file .env up -d --build

# Services will be available at:
# - Verba: localhost:8000
# - PostgreSQL: Managed by Railway or local instance

# Docker commands via Makefile
make docker-build       # Build Docker images
make docker-up          # Start services with Docker Compose
make docker-down        # Stop Docker services
make docker-logs        # View Docker logs
```

## Component Extension Pattern

When creating new components, follow the established pattern:

1. **Create a new component** inheriting from the appropriate base interface:
   - `VerbaComponent` for all components
   - `Reader`, `Chunker`, `Embedding`, `Retriever`, or `Generator` for specific types

2. **Register the component** in the appropriate manager:
   - Components are auto-discovered if they follow the naming pattern
   - Place in the correct subfolder (e.g., `goldenverba/components/chunking/`)

3. **Implement required methods**:
   - `__init__()` with proper configuration
   - Async methods for processing (e.g., `aload()`, `achunk()`, `aembed()`)
   - `get_config()` for frontend configuration

## Key Implementation Details

### Async Operations
All I/O operations should be async. Use `aiohttp` for HTTP requests and `aiofiles` for file operations:

```python
async def aload(self, config: dict) -> List[Document]:
    # Use aiohttp for web requests
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
```

### WebSocket Updates
Send progress updates during long operations:

```python
await self.manager.verb_manager.send_update(
    "client",
    {
        "type": "status",
        "message": "Processing document...",
        "data": {"document": doc_name}
    }
)
```

### Configuration Storage
Configuration is stored in PostgreSQL and can be accessed via:
```python
config = await manager.config_manager.get_config()
```

### Error Handling Pattern
Use the consistent error handling pattern:
```python
try:
    # Operation
    result = await some_async_operation()
except Exception as e:
    raise UploadError(f"Failed to process: {str(e)}")
```

## Testing Approach

### Backend Tests
- Unit tests for individual components in `goldenverba/tests/`
- Mock PostgreSQL client for isolated testing
- Use `pytest-asyncio` for async test functions
- Run with `pytest --cov=goldenverba` for coverage reports

### Frontend Tests
- **Vitest**: Primary testing framework with React Testing Library
- **Jest**: Alternative testing framework (via Bun)
- Tests located in `__tests__` folders next to components
- Mock API responses for isolated testing
- Test configuration in `vitest.config.ts` with happy-dom environment
- Coverage reports available with `npm run test:coverage`

## Important Patterns

### Document Processing Pipeline
1. **Reader** loads raw content
2. **Chunker** splits into manageable pieces
3. **Embedder** creates vector representations
4. **PostgreSQL** stores chunks with metadata and vector embeddings
5. **Retriever** finds relevant chunks
6. **Generator** creates responses using LLM

### Frontend-Backend Communication
- REST API for CRUD operations
- WebSocket for real-time updates
- Configuration changes trigger full page reload
- Status messages displayed via StatusMessenger component

### Multi-Modal Support
The architecture is designed to support multi-modal data (images, videos) in future releases. Keep this in mind when extending components.

## Environment Variables

Key environment variables to set:
- `DATABASE_URL` - PostgreSQL connection URL
- `POSTGRES_HOST` - PostgreSQL host
- `POSTGRES_PASSWORD` - PostgreSQL password
- `OPENAI_API_KEY` - For OpenAI models (now using Responses API)
- `ANTHROPIC_API_KEY` - For Anthropic Claude 4 models
- `COHERE_API_KEY` - For Cohere models
- `GOOGLE_API_KEY` - For Google Gemini models (new genai client)
- `UNSTRUCTURED_API_KEY` - For UnstructuredIO reader
- `FIRECRAWL_API_KEY` - For Firecrawl reader

Note: `GOOGLE_APPLICATION_CREDENTIALS` is no longer needed for Gemini models.
