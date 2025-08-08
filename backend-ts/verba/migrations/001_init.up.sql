-- Enable extensions (best-effort)
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Config table
CREATE TABLE IF NOT EXISTS verba_config (
  uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  config_type TEXT NOT NULL,
  config JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Documents
CREATE TABLE IF NOT EXISTS verba_documents (
  uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title TEXT NOT NULL,
  content TEXT,
  extension TEXT,
  file_size BIGINT,
  source TEXT,
  labels TEXT[] DEFAULT '{}',
  meta JSONB DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  embedder TEXT DEFAULT 'default',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Chunks with optional vector
CREATE TABLE IF NOT EXISTS verba_chunks (
  uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_uuid UUID NOT NULL REFERENCES verba_documents(uuid) ON DELETE CASCADE,
  content TEXT NOT NULL,
  content_without_overlap TEXT,
  chunk_id INTEGER NOT NULL,
  chunk_index INTEGER DEFAULT 0,
  vector vector(1536),
  embedder TEXT DEFAULT 'default',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(document_uuid, chunk_id)
);

-- Suggestions
CREATE TABLE IF NOT EXISTS verba_suggestions (
  uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  query TEXT NOT NULL UNIQUE,
  count INTEGER DEFAULT 1,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_chunks_vector_hnsw ON verba_chunks USING hnsw (vector vector_cosine_ops) WITH (m=16, ef_construction=64);
CREATE INDEX IF NOT EXISTS idx_chunks_document_uuid ON verba_chunks(document_uuid);
CREATE INDEX IF NOT EXISTS idx_documents_title ON verba_documents(title);
CREATE INDEX IF NOT EXISTS idx_documents_labels ON verba_documents USING gin(labels);
CREATE INDEX IF NOT EXISTS idx_suggestions_query ON verba_suggestions(query);