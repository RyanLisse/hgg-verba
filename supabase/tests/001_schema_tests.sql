-- Verba Schema Tests with pgTAP
-- Tests for PostgreSQL schema migration from Weaviate

BEGIN;
SELECT plan(35);

-- Test extensions are enabled
SELECT has_extension('uuid-ossp', 'uuid-ossp extension is enabled');
SELECT has_extension('vector', 'pgvector extension is enabled');
SELECT has_extension('pgtap', 'pgTAP extension is enabled');

-- Test core tables exist
SELECT has_table('verba_documents', 'Documents table exists');
SELECT has_table('verba_chunks', 'Chunks table exists');
SELECT has_table('verba_config', 'Config table exists');
SELECT has_table('verba_suggestions', 'Suggestions table exists');
SELECT has_table('verba_embedding_cache', 'Embedding cache table exists');
SELECT has_table('verba_migration_log', 'Migration log table exists');

-- Test verba_documents table structure
SELECT has_column('verba_documents', 'id', 'Documents table has id column');
SELECT col_type_is('verba_documents', 'id', 'uuid', 'Documents id is UUID type');
SELECT col_is_pk('verba_documents', 'id', 'Documents id is primary key');
SELECT has_column('verba_documents', 'title', 'Documents table has title column');
SELECT col_not_null('verba_documents', 'title', 'Documents title is not null');
SELECT has_column('verba_documents', 'metadata', 'Documents table has metadata column');
SELECT col_type_is('verba_documents', 'metadata', 'jsonb', 'Documents metadata is JSONB type');

-- Test verba_chunks table structure  
SELECT has_column('verba_chunks', 'embedding', 'Chunks table has embedding column');
SELECT col_type_is('verba_chunks', 'embedding', 'vector', 'Chunks embedding is vector type');
SELECT has_column('verba_chunks', 'document_id', 'Chunks table has document_id column');
SELECT col_type_is('verba_chunks', 'document_id', 'uuid', 'Chunks document_id is UUID type');

-- Test foreign key relationships
SELECT has_fk('verba_chunks', 'Chunks table has foreign key');
SELECT fk_ok('verba_chunks', 'document_id', 'verba_documents', 'id', 'FK constraint from chunks to documents is correct');

-- Test indexes exist
SELECT has_index('verba_chunks', 'verba_chunks_embedding_hnsw_idx', 'HNSW vector index exists');
SELECT has_index('verba_chunks', 'verba_chunks_document_id_idx', 'Document ID index exists');
SELECT has_index('verba_chunks', 'verba_chunks_metadata_gin_idx', 'Chunks metadata GIN index exists');
SELECT has_index('verba_documents', 'verba_documents_doc_type_idx', 'Document type index exists');  
SELECT has_index('verba_documents', 'verba_documents_metadata_gin_idx', 'Documents metadata GIN index exists');
SELECT has_index('verba_config', 'verba_config_type_idx', 'Config type index exists');

-- Test unique constraints
SELECT has_unique('verba_config', 'config_type', 'Config type has unique constraint');
SELECT has_unique('verba_embedding_cache', ARRAY['embedder_name', 'content_hash'], 'Embedding cache has unique constraint');

-- Test functions exist
SELECT has_function('search_similar_chunks', 'search_similar_chunks function exists');
SELECT has_function('get_document_stats', 'get_document_stats function exists');
SELECT has_function('update_updated_at_column', 'update_updated_at_column trigger function exists');

-- Test triggers exist
SELECT has_trigger('verba_documents', 'update_verba_documents_updated_at', 'Documents table has update trigger');
SELECT has_trigger('verba_config', 'update_verba_config_updated_at', 'Config table has update trigger');

-- Test initial data exists
SELECT results_eq(
    'SELECT COUNT(*) FROM verba_config WHERE config_type = ''migration''',
    'VALUES(1::bigint)',
    'Migration config record exists'
);

SELECT results_eq(
    'SELECT COUNT(*) FROM verba_config WHERE config_type = ''schema''',
    'VALUES(1::bigint)', 
    'Schema config record exists'
);

SELECT * FROM finish();
ROLLBACK;