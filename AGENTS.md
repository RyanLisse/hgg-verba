# AGENTS.md

## Project Overview
Verba is an open-source RAG (Retrieval-Augmented Generation) application with a Python FastAPI backend and Next.js React frontend.
It uses Weaviate as the vector database and supports multiple LLM providers through a plugin-based architecture.

## Architecture
- **Backend**: FastAPI server (`goldenverba/server/api.py`) with async support and WebSocket for real-time updates
- **Frontend**: Next.js 14 with TypeScript (`frontend/`), Three.js for visualizations
- **Components**: Plugin system for readers, chunkers, embedders, retrievers, and generators
- **Storage**: Weaviate for vectors and configuration persistence

## Essential Commands
```bash
# Backend
pip install -e .                    # Install in development mode
verba start --port 8000            # Start server
verba reset --deployment Local     # Reset configuration

# Frontend (from frontend/)
npm install --legacy-peer-deps     # Install dependencies
npm run dev                        # Development server (localhost:3000)
npm run build                      # Build and copy to backend

# Testing
pytest                             # Backend tests
bun test --preload ./test/setup.ts # Frontend tests
```

## Key Patterns
- All I/O operations must be async (use `aiohttp`, `aiofiles`)
- Send WebSocket updates during long operations
- Components auto-discovered by naming pattern in subfolders
- Configuration stored in Weaviate, accessed via `config_manager`
- Error handling: wrap exceptions in specific error types (e.g., `UploadError`)

## Important Notes
- Environment variables: `WEAVIATE_URL_VERBA`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.
- Document pipeline: Reader → Chunker → Embedder → Weaviate → Retriever → Generator
- Frontend-backend: REST API for CRUD, WebSocket for real-time updates
- See `CLAUDE.md` for detailed instructions and patterns
