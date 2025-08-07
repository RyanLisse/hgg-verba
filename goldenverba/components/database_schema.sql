-- Verba PostgreSQL Schema with pgvector extension
-- This schema works with any PostgreSQL instance with pgvector extension

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Documents table
CREATE TABLE IF NOT EXISTS verba_documents (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    extension TEXT,
    file_size INTEGER DEFAULT 0,
    source TEXT DEFAULT '',
    labels TEXT[] DEFAULT '{}',
    meta JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    embedder TEXT NOT NULL DEFAULT 'default',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS verba_chunks (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_uuid UUID NOT NULL REFERENCES verba_documents(uuid) ON DELETE CASCADE,
    chunk_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536), -- Adjust dimension based on your embedding model
    embedder TEXT NOT NULL DEFAULT 'default',
    meta JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(document_uuid, chunk_id, embedder)
);

-- Configuration table
CREATE TABLE IF NOT EXISTS verba_config (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query suggestions table
CREATE TABLE IF NOT EXISTS verba_suggestions (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query TEXT UNIQUE NOT NULL,
    count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_title ON verba_documents USING GIN (to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_documents_content ON verba_documents USING GIN (to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_documents_embedder ON verba_documents(embedder);
CREATE INDEX IF NOT EXISTS idx_documents_labels ON verba_documents USING GIN (labels);
CREATE INDEX IF NOT EXISTS idx_documents_created_at ON verba_documents(created_at);

CREATE INDEX IF NOT EXISTS idx_chunks_document_uuid ON verba_chunks(document_uuid);
CREATE INDEX IF NOT EXISTS idx_chunks_embedder ON verba_chunks(embedder);
CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON verba_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_chunks_content ON verba_chunks USING GIN (to_tsvector('english', content));

CREATE INDEX IF NOT EXISTS idx_config_type ON verba_config USING GIN ((config->>'config_type') gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_config_active ON verba_config USING btree (((config->>'is_active')::boolean));

CREATE INDEX IF NOT EXISTS idx_suggestions_query ON verba_suggestions(query);
CREATE INDEX IF NOT EXISTS idx_suggestions_count ON verba_suggestions(count DESC);

-- Functions for vector search
CREATE OR REPLACE FUNCTION search_similar_chunks(
    query_embedding VECTOR(1536),
    embedder_name TEXT DEFAULT 'default',
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    document_filter UUID[] DEFAULT NULL
)
RETURNS TABLE (
    chunk_uuid UUID,
    document_uuid UUID,
    chunk_id INTEGER,
    content TEXT,
    similarity FLOAT,
    document_title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.uuid,
        c.document_uuid,
        c.chunk_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        d.title
    FROM verba_chunks c
    JOIN verba_documents d ON c.document_uuid = d.uuid
    WHERE 
        c.embedder = embedder_name
        AND (document_filter IS NULL OR c.document_uuid = ANY(document_filter))
        AND (1 - (c.embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function for hybrid search (vector + text)
CREATE OR REPLACE FUNCTION hybrid_search_chunks(
    query_text TEXT,
    query_embedding VECTOR(1536),
    embedder_name TEXT DEFAULT 'default',
    similarity_threshold FLOAT DEFAULT 0.7,
    max_results INTEGER DEFAULT 10,
    document_filter UUID[] DEFAULT NULL,
    vector_weight FLOAT DEFAULT 0.7,
    text_weight FLOAT DEFAULT 0.3
)
RETURNS TABLE (
    chunk_uuid UUID,
    document_uuid UUID,
    chunk_id INTEGER,
    content TEXT,
    combined_score FLOAT,
    vector_similarity FLOAT,
    text_rank FLOAT,
    document_title TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.uuid,
        c.document_uuid,
        c.chunk_id,
        c.content,
        (vector_weight * (1 - (c.embedding <=> query_embedding))) + 
        (text_weight * ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text))) AS combined_score,
        1 - (c.embedding <=> query_embedding) AS vector_similarity,
        ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', query_text)) AS text_rank,
        d.title
    FROM verba_chunks c
    JOIN verba_documents d ON c.document_uuid = d.uuid
    WHERE 
        c.embedder = embedder_name
        AND (document_filter IS NULL OR c.document_uuid = ANY(document_filter))
        AND (
            (1 - (c.embedding <=> query_embedding)) >= similarity_threshold
            OR to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text)
        )
    ORDER BY combined_score DESC
    LIMIT max_results;
END;
$$ LANGUAGE plpgsql;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_document_stats()
RETURNS TABLE (
    total_documents BIGINT,
    total_chunks BIGINT,
    avg_chunks_per_document NUMERIC,
    total_size_bytes BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT,
        (SELECT COUNT(*) FROM verba_chunks)::BIGINT,
        CASE 
            WHEN COUNT(*) > 0 THEN (SELECT COUNT(*) FROM verba_chunks)::NUMERIC / COUNT(*)::NUMERIC
            ELSE 0::NUMERIC
        END,
        COALESCE(SUM(file_size), 0)::BIGINT
    FROM verba_documents;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
DROP TRIGGER IF EXISTS update_verba_documents_updated_at ON verba_documents;
CREATE TRIGGER update_verba_documents_updated_at
    BEFORE UPDATE ON verba_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_verba_config_updated_at ON verba_config;
CREATE TRIGGER update_verba_config_updated_at
    BEFORE UPDATE ON verba_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_verba_suggestions_updated_at ON verba_suggestions;
CREATE TRIGGER update_verba_suggestions_updated_at
    BEFORE UPDATE ON verba_suggestions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE verba_documents IS 'Main documents table for Verba RAG application';
COMMENT ON TABLE verba_chunks IS 'Document chunks with vector embeddings for similarity search';
COMMENT ON TABLE verba_config IS 'Application configuration storage';
COMMENT ON TABLE verba_suggestions IS 'Query suggestions and autocomplete data';
COMMENT ON FUNCTION search_similar_chunks IS 'Optimized vector similarity search with filtering';
COMMENT ON FUNCTION hybrid_search_chunks IS 'Combined vector and text search for better results';
COMMENT ON FUNCTION get_document_stats IS 'Get comprehensive statistics about documents and chunks';
