# Technology Stack

## Backend
- **Language**: Python 3.10+ (FastAPI framework)
- **Package Manager**: uv (recommended) or pip
- **Code Quality**: ruff (linter/formatter), ty (type checker)
- **Key Dependencies**:
  - `fastapi` - Web framework
  - `uvicorn` - ASGI server
  - `supabase` - Database client for PostgreSQL
  - `asyncpg` - Async PostgreSQL driver
  - `pgvector` - Vector similarity search
  - `instructor` - Structured LLM outputs
  - `langchain-*` - RAG pipeline components
  - `spacy` - NLP processing
  - `tiktoken` - Token counting
  - `sentence-transformers` - Local embeddings

## Frontend
- **Framework**: Next.js 14+ with React 18+
- **Language**: TypeScript
- **Package Manager**: npm (with `--legacy-peer-deps` flag)
- **Styling**: Tailwind CSS v4 (beta), Radix UI components
- **Key Dependencies**:
  - `@react-three/fiber` & `@react-three/drei` - 3D visualization
  - `framer-motion` - Animations
  - `@supabase/supabase-js` - Database client
  - `lucide-react` - Icons
  - `react-markdown` - Markdown rendering

## Database Options
- **Primary**: Supabase (PostgreSQL with pgvector extension)
- **Alternative**: Weaviate (vector database)
- **Local Development**: Docker Compose with Weaviate

## Development Tools
- **Backend**: ruff (linting/formatting), ty (type checking), pytest (testing)
- **Frontend**: Biome (linting/formatting), Vitest (testing)
- **Package Management**: uv (recommended), pip (fallback)
- **Build System**: Make (see Makefile for commands)

## Common Commands

### Setup
```bash
# Complete setup (backend + frontend)
make setup

# Backend only (uses uv)
make setup-backend

# Frontend only  
make setup-frontend
```

### Development
```bash
# Run both backend and frontend
make dev

# Backend only (port 8000)
uv run verba start  # Recommended
# or
verba start         # If using pip
# or
make backend

# Frontend only (port 3000)
cd frontend && npm run dev
# or
make frontend
```

### Docker Deployment
```bash
# Quick local start with Weaviate
./start-local.sh

# Manual Docker Compose
docker compose up -d
```

### Testing
```bash
# All tests
make test

# Backend tests with coverage
make test-backend

# Frontend tests
make test-frontend
```

### Code Quality
```bash
# Lint and format all code
make lint
make format

# Type checking
make typecheck

# Check everything (lint + format + typecheck + tests)
make check

# Backend-specific with Astral tools
uv run ruff format goldenverba  # Format code
uv run ruff check goldenverba   # Lint code
uv run ty check goldenverba     # Type check (preview)
```

## Environment Configuration
- Use `.env` file for API keys and configuration
- Copy from `.env.example` or `.env.local` template
- Required for LLM providers (OpenAI, Anthropic, etc.)
- Weaviate URL defaults to `http://localhost:8080` for local development

## Package Installation Notes
- **Recommended**: Use `uv sync --group dev` for backend development
- **Alternative**: Use `pip install -e ".[dev]"` for development mode
- **Quick install**: Use `uvx goldenverba start` for direct usage
- Frontend requires `npm install --legacy-peer-deps` due to peer dependency conflicts
- Optional dependency groups: `[huggingface]`, `[google]`, `[all]` for additional model support