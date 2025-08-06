-- Verba PostgreSQL Schema Migration from Weaviate
-- Phase 1: Core Tables and Vector Support

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgtap";

-- Documents table (replaces VERBA_DOCUMENTS collection)
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

-- Chunks table with vector embeddings
CREATE TABLE verba_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES verba_documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    embedding vector(1536), -- OpenAI ada-002 dimensions, can be adjusted
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Configuration table (replaces VERBA_CONFIG collection)
CREATE TABLE verba_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_type TEXT NOT NULL, -- 'rag', 'theme', 'user'
    config_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(config_type)
);

-- Suggestions table (replaces VERBA_SUGGESTION collection)
CREATE TABLE verba_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT NOT NULL,
    response TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Embeddings cache tables (dynamic creation per embedder)
CREATE TABLE verba_embedding_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedder_name TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(embedder_name, content_hash)
);

-- Vector indexes for performance
-- HNSW index for similarity search (can be created immediately)
CREATE INDEX verba_chunks_embedding_hnsw_idx 
ON verba_chunks USING hnsw (embedding vector_cosine_ops);

-- Additional indexes for metadata queries
CREATE INDEX verba_chunks_document_id_idx ON verba_chunks(document_id);
CREATE INDEX verba_chunks_metadata_gin_idx ON verba_chunks USING gin(metadata);
CREATE INDEX verba_documents_doc_type_idx ON verba_documents(doc_type);
CREATE INDEX verba_documents_metadata_gin_idx ON verba_documents USING gin(metadata);
CREATE INDEX verba_config_type_idx ON verba_config(config_type);
CREATE INDEX verba_embedding_cache_embedder_hash_idx ON verba_embedding_cache(embedder_name, content_hash);

-- Performance optimization: partial indexes for common queries
CREATE INDEX verba_chunks_recent_idx ON verba_chunks(created_at DESC) 
WHERE created_at > NOW() - INTERVAL '30 days';

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_verba_documents_updated_at 
    BEFORE UPDATE ON verba_documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verba_config_updated_at 
    BEFORE UPDATE ON verba_config 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) setup for multi-tenancy if needed
-- ALTER TABLE verba_documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE verba_chunks ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE verba_config ENABLE ROW LEVEL SECURITY;

-- Helper functions for vector operations
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding vector(1536),
    similarity_threshold float DEFAULT 0.7,
    max_results int DEFAULT 10,
    doc_type_filter text DEFAULT NULL
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    document_title TEXT,
    doc_type TEXT,
    similarity float
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id as chunk_id,
        c.document_id,
        c.content,
        d.title as document_title,
        d.doc_type,
        1 - (c.embedding <=> query_embedding) as similarity
    FROM verba_chunks c
    JOIN verba_documents d ON c.document_id = d.id
    WHERE 
        (doc_type_filter IS NULL OR d.doc_type = doc_type_filter)
        AND (1 - (c.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents bigint,
    total_chunks bigint,
    avg_chunks_per_document numeric,
    doc_types jsonb
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(DISTINCT d.id) as total_documents,
        COUNT(c.id) as total_chunks,
        ROUND(COUNT(c.id)::numeric / NULLIF(COUNT(DISTINCT d.id), 0), 2) as avg_chunks_per_document,
        jsonb_object_agg(d.doc_type, type_count.cnt) as doc_types
    FROM verba_documents d
    LEFT JOIN verba_chunks c ON d.id = c.document_id
    LEFT JOIN (
        SELECT doc_type, COUNT(*) as cnt
        FROM verba_documents
        GROUP BY doc_type
    ) type_count ON d.doc_type = type_count.doc_type;
END;
$$ LANGUAGE plpgsql;

-- Migration tracking table
CREATE TABLE verba_migration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    migration_name TEXT NOT NULL,
    status TEXT NOT NULL, -- 'started', 'completed', 'failed', 'rolled_back'
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Insert initial configuration markers
INSERT INTO verba_config (config_type, config_data) VALUES
('migration', '{"version": "1.0.0", "source": "weaviate", "target": "supabase", "started_at": "' || NOW() || '"}'),
('schema', '{"version": "001", "tables": ["verba_documents", "verba_chunks", "verba_config", "verba_suggestions", "verba_embedding_cache"]}');

-- Comments for documentation
COMMENT ON TABLE verba_documents IS 'Main documents table, replaces Weaviate VERBA_DOCUMENTS collection';
COMMENT ON TABLE verba_chunks IS 'Document chunks with vector embeddings for similarity search';
COMMENT ON TABLE verba_config IS 'Application configuration, replaces Weaviate VERBA_CONFIG collection';
COMMENT ON TABLE verba_suggestions IS 'Query suggestions and responses, replaces Weaviate VERBA_SUGGESTION collection';
COMMENT ON TABLE verba_embedding_cache IS 'Cache for computed embeddings to avoid recomputation';
COMMENT ON FUNCTION search_similar_chunks IS 'Optimized vector similarity search with filtering';
COMMENT ON FUNCTION get_document_stats IS 'Get comprehensive statistics about documents and chunks';