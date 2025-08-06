# Verba Supabase Migration Guide

## Overview

This guide provides complete instructions for migrating Verba from Weaviate to Supabase with pgvector. The migration maintains full RAG functionality while leveraging PostgreSQL's mature ecosystem and Supabase's developer-friendly platform.

## 🎯 Migration Benefits

- **Unified Database**: Combine relational and vector data in PostgreSQL
- **Better Performance**: pgvector with HNSW indexing offers excellent performance
- **Cost Efficiency**: Eliminate separate vector database costs
- **SQL Compatibility**: Use familiar SQL queries alongside vector operations
- **Scalability**: PostgreSQL's proven scalability for production workloads
- **Developer Experience**: Rich tooling, backup/restore, monitoring

## 📋 Prerequisites

### Environment Requirements

1. **Supabase Project**: Create a new project at [supabase.com](https://supabase.com)
2. **Python Environment**: Python 3.9+ with virtual environment
3. **Node.js Environment**: Node.js 18+ for frontend development
4. **Database Access**: Supabase service role key for full database access

### Dependencies

Install Supabase-specific dependencies:

```bash
pip install -r requirements-supabase.txt
```

Key packages:

- `supabase>=2.8.0` - Supabase Python client
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `pgvector>=0.2.4` - pgvector Python bindings

## 🚀 Quick Start Migration

### Step 1: Database Setup

1. **Create Supabase Project**

   ```bash
   # Visit https://supabase.com/dashboard
   # Create new project and note the URL and service role key
   ```

2. **Enable Extensions**
   Navigate to Database → Extensions in Supabase dashboard:
   - Enable `vector` (pgvector)
   - Enable `pgtap` (for testing)

3. **Run Schema Migration**

   ```bash
   cd migration-workspace
   psql "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres" \
     -f supabase/migrations/001_create_verba_schema.sql
   ```

### Step 2: Configure Environment

```bash
# Set environment variables
export SUPABASE_URL="https://[PROJECT].supabase.co"
export SUPABASE_SERVICE_KEY="[SERVICE_ROLE_KEY]"

# For migration from Weaviate
export WEAVIATE_URL_VERBA="https://your-weaviate-instance.com"
export WEAVIATE_API_KEY_VERBA="your-weaviate-key"
```

### Step 3: Run Migration

```bash
# Dry run first (analyze only)
python migration/migrate_weaviate_to_supabase.py \
  --weaviate-url $WEAVIATE_URL_VERBA \
  --weaviate-key $WEAVIATE_API_KEY_VERBA \
  --supabase-url $SUPABASE_URL \
  --supabase-key $SUPABASE_SERVICE_KEY \
  --dry-run

# Run actual migration
python migration/migrate_weaviate_to_supabase.py \
  --weaviate-url $WEAVIATE_URL_VERBA \
  --weaviate-key $WEAVIATE_API_KEY_VERBA \
  --supabase-url $SUPABASE_URL \
  --supabase-key $SUPABASE_SERVICE_KEY \
  --batch-size 50
```

### Step 4: Update Application

```python
# Update your Verba initialization
from goldenverba.verba_manager_supabase import VerbaManagerSupabase

# Initialize with Supabase
manager = VerbaManagerSupabase(use_supabase=True)

# Connect using Supabase credentials
credentials = Credentials(
    deployment="Supabase",
    url=os.getenv("SUPABASE_URL"),
    key=os.getenv("SUPABASE_SERVICE_KEY")
)

client = await manager.connect(credentials)
```

## 🗄️ Database Schema

### Core Tables

#### Documents Table

```sql
CREATE TABLE verba_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    doc_name TEXT,
    doc_type TEXT,
    doc_link TEXT,
    chunk_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Chunks Table with Vector Embeddings

```sql
CREATE TABLE verba_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES verba_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    embedding vector(1536), -- Configurable dimensions
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### High-Performance Indexes

```sql
-- HNSW index for vector similarity search
CREATE INDEX verba_chunks_embedding_hnsw_idx 
ON verba_chunks USING hnsw (embedding vector_cosine_ops);

-- Metadata indexes for filtering
CREATE INDEX verba_chunks_metadata_gin_idx ON verba_chunks USING gin(metadata);
CREATE INDEX verba_documents_doc_type_idx ON verba_documents(doc_type);
```

## 🔧 API Changes

### Vector Search

**Before (Weaviate):**

```python
# Weaviate client search
results = await client.collections.get("Documents").query.near_vector(
    near_vector=query_vector,
    limit=10
).objects
```

**After (Supabase):**

```python
# Supabase vector search
results = await supabase_manager.get_vectors(
    query_vector=query_vector,
    limit=10,
    similarity_threshold=0.7
)
```

### Document Import

**Before (Weaviate):**

```python
await weaviate_manager.import_document(client, documents, logger)
```

**After (Supabase):**

```python
await supabase_manager.import_document(documents, logger)
```

### Configuration Management

**Before (Weaviate):**

```python
config = await weaviate_manager.get_config_by_type(client, "rag")
await weaviate_manager.set_config_by_type(client, "rag", config_data)
```

**After (Supabase):**

```python
config = await supabase_manager.get_config("rag")
await supabase_manager.set_config("rag", config_data)
```

## 🧪 Testing

### Schema Tests

```bash
# Run pgTAP schema tests
psql "postgresql://..." -f supabase/tests/001_schema_tests.sql
psql "postgresql://..." -f supabase/tests/002_vector_operations_tests.sql
```

### Integration Tests

```python
# Python integration tests
import pytest
from goldenverba.components.supabase_manager import SupabaseManager

@pytest.mark.asyncio
async def test_vector_search():
    manager = SupabaseManager()
    await manager.connect("Supabase", SUPABASE_URL, SUPABASE_KEY)
    
    results = await manager.get_vectors([0.1] * 1536, limit=5)
    assert len(results) <= 5
    
    await manager.disconnect()
```

### Performance Benchmarks

```python
# Vector search performance test
async def benchmark_search_performance():
    import time
    import numpy as np
    
    manager = SupabaseManager()
    await manager.connect("Supabase", url, key)
    
    # Generate random query vectors
    queries = [np.random.rand(1536).tolist() for _ in range(100)]
    
    start_time = time.time()
    tasks = [manager.get_vectors(q, limit=10) for q in queries]
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    qps = len(queries) / (end_time - start_time)
    print(f"Queries per second: {qps:.2f}")
```

## 📊 Performance Optimizations

### Vector Index Tuning

```sql
-- Optimize HNSW parameters for your data size
CREATE INDEX verba_chunks_embedding_hnsw_idx 
ON verba_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- For large datasets (>1M vectors), consider:
-- m = 16-32, ef_construction = 64-128
```

### Connection Pool Configuration

```python
# Optimize connection pool for production
self.pool = await asyncpg.create_pool(
    database_url,
    min_size=5,      # Minimum connections
    max_size=20,     # Maximum connections
    max_queries=50000,  # Queries per connection
    max_inactive_connection_lifetime=300,  # 5 minutes
    command_timeout=60,
    server_settings={
        'application_name': 'verba_rag',
        'jit': 'off'  # Disable JIT for consistent performance
    }
)
```

### Query Optimization

```sql
-- Use prepared statements for better performance
PREPARE vector_search AS 
SELECT c.id, c.content, d.title, 1 - (c.embedding <=> $1) as similarity
FROM verba_chunks c
JOIN verba_documents d ON c.document_id = d.id
WHERE d.doc_type = $2
ORDER BY c.embedding <=> $1
LIMIT $3;
```

## 🔍 Monitoring & Observability

### Health Checks

```python
# Comprehensive health check
health_status = await supabase_manager.health_check()
print(f"Status: {health_status['status']}")
print(f"Database version: {health_status['database_version']}")
print(f"pgvector version: {health_status['pgvector_version']}")
```

### Statistics Monitoring

```python
# Get comprehensive statistics
stats = await supabase_manager.get_document_stats()
print(f"Total documents: {stats['total_documents']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Average chunks per document: {stats['avg_chunks_per_document']}")
```

### Query Performance Monitoring

```sql
-- Enable query statistics
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Monitor slow vector queries
SELECT query, calls, total_exec_time, mean_exec_time 
FROM pg_stat_statements 
WHERE query LIKE '%embedding%' 
ORDER BY total_exec_time DESC 
LIMIT 10;
```

## 🚧 Rollback Plan

### Emergency Rollback to Weaviate

```python
# Switch back to Weaviate if needed
manager = VerbaManagerSupabase(use_supabase=False)

# Original Weaviate credentials
weaviate_credentials = Credentials(
    deployment="Weaviate",
    url=os.getenv("WEAVIATE_URL_VERBA"),
    key=os.getenv("WEAVIATE_API_KEY_VERBA")
)

client = await manager.connect(weaviate_credentials)
```

### Data Export from Supabase

```bash
# Export data for backup
pg_dump "postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres" \
  --table=verba_documents \
  --table=verba_chunks \
  --table=verba_config \
  --data-only > verba_backup.sql
```

## 🎛️ Configuration Management

### Environment Variables

```bash
# Production environment
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key

# Development environment
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_KEY=your-local-service-key

# Optional: Enable connection pooling
SUPABASE_POOL_SIZE=10
SUPABASE_MAX_CONNECTIONS=20
```

### Feature Flags

```python
# Feature flag for gradual rollout
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"

manager = VerbaManagerSupabase(use_supabase=USE_SUPABASE)
```

## 📝 Migration Checklist

### Pre-Migration

- [ ] Supabase project created and configured
- [ ] pgvector and pgTAP extensions enabled  
- [ ] Schema migration scripts executed
- [ ] Environment variables configured
- [ ] Dependencies installed

### Migration Execution

- [ ] Dry run completed successfully
- [ ] Data migration executed
- [ ] Vector search functionality verified
- [ ] Configuration data migrated
- [ ] Performance tests passed

### Post-Migration

- [ ] Application updated to use Supabase
- [ ] Integration tests passing
- [ ] Performance monitoring configured
- [ ] Backup procedures established
- [ ] Documentation updated

### Verification

- [ ] Document import/export working
- [ ] Vector similarity search accurate
- [ ] RAG pipeline functional
- [ ] User interface responsive
- [ ] API endpoints operational

## 🆘 Troubleshooting

### Common Issues

**Connection Errors:**

```bash
# Check connection string format
postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres

# Verify service role key has sufficient permissions
```

**Vector Search Issues:**

```sql
-- Check if pgvector extension is enabled
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Verify index is being used
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM verba_chunks 
ORDER BY embedding <=> '[0.1,0.2,0.3]'::vector LIMIT 10;
```

**Performance Issues:**

```sql
-- Check index statistics
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE indexname LIKE '%embedding%';

-- Monitor connection pool
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE application_name = 'verba_rag';
```

### Support Resources

- **Supabase Documentation**: [supabase.com/docs](https://supabase.com/docs)
- **pgvector Documentation**: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector)  
- **PostgreSQL Performance**: [postgresql.org/docs/current/performance-tips.html](https://postgresql.org/docs/current/performance-tips.html)

## 🎉 Success Metrics

After successful migration, you should achieve:

- **Query Performance**: >500 queries per second for vector similarity search
- **Accuracy**: >95% similarity with Weaviate results  
- **Availability**: <5 seconds downtime during migration
- **Cost Reduction**: Significant savings from unified database
- **Developer Experience**: Improved debugging and monitoring capabilities

---

**Migration completed successfully! 🚀**

Your Verba RAG application now runs on Supabase with full PostgreSQL and pgvector capabilities.
