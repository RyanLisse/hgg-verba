-- Install pgTAP extension for testing
CREATE EXTENSION IF NOT EXISTS pgtap;

-- Start test suite
SELECT plan(30); -- Number of tests

-- Test 1: Check if required extensions are installed
SELECT has_extension('uuid-ossp', 'uuid-ossp extension should be installed');
SELECT has_extension('vector', 'pgvector extension should be installed');
SELECT has_extension('pg_trgm', 'pg_trgm extension should be installed');

-- Test 2: Check if tables exist
SELECT has_table('documents', 'documents table should exist');
SELECT has_table('document_chunks', 'document_chunks table should exist');
SELECT has_table('configurations', 'configurations table should exist');
SELECT has_table('query_suggestions', 'query_suggestions table should exist');
SELECT has_table('semantic_cache', 'semantic_cache table should exist');
SELECT has_table('conversations', 'conversations table should exist');
SELECT has_table('messages', 'messages table should exist');
SELECT has_table('embedder_configs', 'embedder_configs table should exist');

-- Test 3: Check documents table columns
SELECT has_column('documents', 'id', 'documents should have id column');
SELECT has_column('documents', 'name', 'documents should have name column');
SELECT has_column('documents', 'type', 'documents should have type column');
SELECT has_column('documents', 'status', 'documents should have status column');
SELECT col_type_is('documents', 'id', 'uuid', 'documents.id should be UUID');
SELECT col_is_pk('documents', 'id', 'documents.id should be primary key');

-- Test 4: Check document_chunks table columns
SELECT has_column('document_chunks', 'embedding', 'document_chunks should have embedding column');
SELECT col_type_is('document_chunks', 'embedding', 'vector(1536)', 'embedding should be vector(1536)');

-- Test 5: Check indexes exist
SELECT has_index('documents', 'idx_documents_name', 'documents should have name index');
SELECT has_index('document_chunks', 'idx_chunks_embedding', 'document_chunks should have embedding index');

-- Test 6: Check functions exist
SELECT has_function('search_similar_chunks', 'search_similar_chunks function should exist');
SELECT has_function('hybrid_search_chunks', 'hybrid_search_chunks function should exist');
SELECT has_function('update_updated_at_column', 'update_updated_at_column trigger function should exist');

-- Test 7: Check triggers exist
SELECT has_trigger('documents', 'update_documents_updated_at', 'documents should have updated_at trigger');
SELECT has_trigger('document_chunks', 'update_chunks_updated_at', 'document_chunks should have updated_at trigger');

-- Test 8: Check RLS is enabled
SELECT row_security_is('enabled', 'documents', 'Row Level Security should be enabled on documents');
SELECT row_security_is('enabled', 'document_chunks', 'Row Level Security should be enabled on document_chunks');

-- Test 9: Check foreign key constraints
SELECT fk_ok('document_chunks', 'document_id', 'documents', 'id', 'document_chunks.document_id should reference documents.id');
SELECT fk_ok('messages', 'conversation_id', 'conversations', 'id', 'messages.conversation_id should reference conversations.id');

-- Finish test suite
SELECT * FROM finish();

-- Rollback (tests should not persist data)
ROLLBACK;