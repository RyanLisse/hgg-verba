# Project Structure

## Root Directory
```
├── goldenverba/           # Main Python package (backend)
├── frontend/              # Next.js React application
├── supabase/             # Database migrations and tests
├── scripts/              # Utility scripts
├── migration/            # Data migration tools
├── img/                  # Documentation images
├── docker-compose.yml    # Docker services configuration
├── Dockerfile           # Backend container definition
├── Makefile            # Build automation
├── setup.py            # Python package configuration
└── requirements-*.txt  # Python dependencies
```

## Backend Structure (`goldenverba/`)
```
goldenverba/
├── components/           # Core RAG components
│   ├── chunking/        # Document chunking strategies
│   ├── embedding/       # Embedding model implementations
│   ├── generation/      # LLM generation components
│   ├── retriever/       # Document retrieval logic
│   ├── reader/          # Document ingestion
│   └── managers/        # Component management
├── server/              # FastAPI web server
│   ├── api.py          # Main API endpoints
│   ├── api_supabase.py # Supabase-specific endpoints
│   ├── cli.py          # Command-line interface
│   └── frontend/       # Built frontend assets
└── tests/              # Backend test suite
```

## Frontend Structure (`frontend/`)
```
frontend/
├── app/                 # Next.js app directory
│   ├── components/     # React components
│   │   ├── Chat/       # Chat interface components
│   │   ├── Document/   # Document management UI
│   │   ├── Ingestion/  # Data ingestion interface
│   │   ├── Navigation/ # Navigation components
│   │   └── Settings/   # Configuration UI
│   ├── types/          # TypeScript type definitions
│   └── utils/          # Utility functions
├── components/         # Shared UI components
│   ├── chat/          # Chat-specific components
│   └── ui/            # Base UI components (shadcn/ui)
├── lib/               # Library code
├── public/            # Static assets (3D models, shaders)
└── test/              # Frontend test setup
```

## Database Structure (`supabase/`)
```
supabase/
├── migrations/         # SQL migration files
│   ├── 001_create_verba_schema.sql
│   └── 001_initial_schema.sql
└── tests/             # Database test files
    ├── 001_schema_tests.sql
    └── 002_vector_operations_tests.sql
```

## Configuration Files
- **`.env`** - Environment variables and API keys
- **`docker-compose.yml`** - Multi-service Docker setup
- **`package.json`** - Root-level Node.js dependencies (testing)
- **`frontend/package.json`** - Frontend dependencies
- **`setup.py`** - Python package metadata and dependencies
- **`requirements-supabase.txt`** - Supabase-specific Python deps

## Key Architectural Patterns

### Component-Based Backend
- Each RAG component (chunking, embedding, generation, retrieval) is modular
- Components implement common interfaces for pluggability
- Manager classes coordinate component interactions

### Modular Frontend
- Components organized by feature area (Chat, Document, etc.)
- Shared UI components follow shadcn/ui patterns
- TypeScript for type safety across the application

### Database Abstraction
- PostgreSQL with pgvector for vector operations and data storage
- Manager classes abstract database operations
- Migration scripts for schema management

### Development Workflow
- Makefile provides consistent commands across environments
- Separate development and production configurations
- Docker Compose for local development with all services

## File Naming Conventions
- **Python**: snake_case for files and functions
- **TypeScript/React**: PascalCase for components, camelCase for utilities
- **Configuration**: kebab-case for Docker and deployment files
- **Documentation**: UPPERCASE.md for major docs, lowercase.md for guides

## Import Patterns
- Backend: Relative imports within goldenverba package
- Frontend: Absolute imports from app root (`@/components`, `@/lib`)
- Shared types and interfaces defined in dedicated modules