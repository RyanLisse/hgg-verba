# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Verba is an open-source Retrieval-Augmented Generation (RAG) application that provides a user-friendly interface for querying and interacting with documents using AI. It consists of a Python FastAPI backend and a Next.js React frontend, using Weaviate as the vector database.

## Key Architecture

### Backend Architecture
- **FastAPI server** with async support in `goldenverba/server/api.py`
- **Component-based plugin system** with base interfaces in `goldenverba/components/interfaces.py`
- **Manager pattern** for handling different component types (readers, chunkers, embedders, retrievers, generators)
- **Weaviate integration** for vector storage and configuration persistence
- **WebSocket support** for real-time updates during document processing

### Frontend Architecture
- **Next.js 14** with TypeScript in `frontend/`
- **Feature-based component organization** (Chat, Document, Ingestion, Navigation, Settings)
- **Three.js integration** for 3D vector visualization
- **Real-time updates** via WebSocket connections

## Common Development Commands

### Backend Development
```bash
# Install the package in development mode
pip install -e .

# Install with specific extras
pip install -e ".[huggingface]"  # For local embeddings
pip install -e ".[google]"        # For Google Vertex AI
pip install -e ".[dev]"           # For development tools

# Start the server
verba start --port 8000 --host localhost

# Reset configuration
verba reset --deployment Local

# Run tests
pytest
pytest --cov=goldenverba  # With coverage

# Run a specific test
pytest goldenverba/tests/test_verba_manager.py::TestVerbaManager::test_initialization
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
bun test --preload ./test/setup.ts

# Linting
npm run lint
```

### Docker Development
```bash
# Build and run with Docker Compose
docker compose --env-file .env up -d --build

# Services will be available at:
# - Verba: localhost:8000
# - Weaviate: localhost:8080
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
Configuration is stored in Weaviate and can be accessed via:
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
- Mock Weaviate client for isolated testing
- Use `pytest-asyncio` for async test functions

### Frontend Tests
- Component tests using React Testing Library
- Tests located in `__tests__` folders next to components
- Mock API responses for isolated testing

## Important Patterns

### Document Processing Pipeline
1. **Reader** loads raw content
2. **Chunker** splits into manageable pieces
3. **Embedder** creates vector representations
4. **Weaviate** stores chunks with metadata
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
- `WEAVIATE_URL_VERBA` - Weaviate instance URL
- `WEAVIATE_API_KEY_VERBA` - Weaviate API key
- `OPENAI_API_KEY` - For OpenAI models (now using Responses API)
- `ANTHROPIC_API_KEY` - For Anthropic Claude 4 models
- `COHERE_API_KEY` - For Cohere models
- `GOOGLE_API_KEY` - For Google Gemini models (new genai client)
- `UNSTRUCTURED_API_KEY` - For UnstructuredIO reader
- `FIRECRAWL_API_KEY` - For Firecrawl reader

Note: `GOOGLE_APPLICATION_CREDENTIALS` is no longer needed for Gemini models.