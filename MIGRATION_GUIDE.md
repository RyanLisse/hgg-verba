# Verba Migration Guide: Weaviate to Supabase

This guide documents the migration from Weaviate to Supabase with pgvector, and the UI upgrade to Tailwind v4 with shadcn components.

## Overview

### Key Changes
1. **Database**: Migrated from Weaviate to Supabase with pgvector for vector operations
2. **Testing**: Added pgtap for PostgreSQL testing
3. **Frontend UI**: Upgraded to Tailwind CSS v4 with shadcn components
4. **Chat Interface**: New AI chatbot component inspired by kibo-ui design

## Backend Migration

### 1. Database Setup

#### Create a Supabase Project
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Create a new project
3. Enable the pgvector extension in your database

#### Run Database Migrations
```bash
# Apply the initial schema
psql -h your-database-host -U postgres -d postgres -f supabase/migrations/001_initial_schema.sql
```

### 2. Environment Configuration

Update your `.env` file with Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_DB_HOST=aws-0-us-west-1.pooler.supabase.com
SUPABASE_DB_PASSWORD=your_database_password
SUPABASE_DB_NAME=postgres
SUPABASE_DB_PORT=5432

# Frontend Configuration
NEXT_PUBLIC_SUPABASE_URL=https://your-project-ref.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Install Dependencies

```bash
# Backend dependencies
pip install supabase asyncpg pgvector

# Frontend dependencies
cd frontend
npm install --legacy-peer-deps
```

### 4. Database Schema

The new schema includes:
- **documents**: Main document storage with metadata
- **document_chunks**: Vectorized chunks with pgvector support
- **configurations**: Application configurations
- **conversations**: Chat conversation history
- **messages**: Individual chat messages
- **semantic_cache**: Query result caching
- **query_suggestions**: Autocomplete suggestions

### 5. Vector Operations

The migration includes optimized vector functions:
- `search_similar_chunks()`: Pure vector similarity search
- `hybrid_search_chunks()`: Combined vector and text search

## Frontend Migration

### 1. Tailwind v4 Setup

The project now uses Tailwind CSS v4 with:
- CSS variables for theming
- Dark mode support
- shadcn UI components
- Responsive design utilities

### 2. shadcn Components

New UI components added:
- Button
- Avatar
- ScrollArea
- And more shadcn components

### 3. AI Chatbot Component

New chat interface at `frontend/components/chat/AIChatbot.tsx`:
- Modern chat UI inspired by kibo-ui
- Real-time streaming responses
- File attachment support
- Markdown rendering with syntax highlighting
- Message history with copy/regenerate functions

## Testing with pgtap

### Run Database Tests

```bash
# Install pgtap extension in your database
CREATE EXTENSION IF NOT EXISTS pgtap;

# Run schema tests
psql -h your-database-host -U postgres -d postgres -f supabase/tests/001_test_schema.sql

# Run vector operation tests
psql -h your-database-host -U postgres -d postgres -f supabase/tests/002_test_vector_operations.sql
```

## API Changes

### Old Weaviate API
```python
from goldenverba.components.managers import WeaviateManager
manager = WeaviateManager()
```

### New Supabase API
```python
from goldenverba.components.supabase_manager import SupabaseManager
manager = SupabaseManager()
await manager.initialize()
```

## Key Differences

### 1. Connection Management
- **Weaviate**: Multiple deployment types (Local, Docker, Cloud)
- **Supabase**: Single connection with async pool for vector operations

### 2. Vector Storage
- **Weaviate**: Automatic vectorization with modules
- **Supabase**: Manual embedding storage with pgvector

### 3. Search Operations
- **Weaviate**: GraphQL-based queries
- **Supabase**: SQL functions with vector operators

### 4. Configuration
- **Weaviate**: Stored as objects in collections
- **Supabase**: Stored in relational tables with JSONB

## Migration Checklist

- [ ] Create Supabase project
- [ ] Enable pgvector extension
- [ ] Run database migrations
- [ ] Update environment variables
- [ ] Install new dependencies
- [ ] Update backend code to use SupabaseManager
- [ ] Update frontend to use Supabase client
- [ ] Test vector operations
- [ ] Run pgtap tests
- [ ] Deploy application

## Rollback Plan

If you need to rollback to Weaviate:
1. Keep your original `.env` file with Weaviate configuration
2. Revert the code changes using git
3. Reinstall weaviate-client dependency
4. Restart the application

## Support

For issues or questions about the migration:
1. Check the Supabase documentation: https://supabase.com/docs
2. Review pgvector documentation: https://github.com/pgvector/pgvector
3. Check shadcn documentation: https://ui.shadcn.com