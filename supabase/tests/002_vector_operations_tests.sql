-- Verba Vector Operations Tests with pgTAP
-- Tests for vector similarity search and embedding operations

BEGIN;
SELECT plan(15);

-- Setup test data
INSERT INTO verba_documents (id, title, content, doc_type) VALUES
('11111111-1111-1111-1111-111111111111', 'Test Document 1', 'This is test content about artificial intelligence', 'markdown'),
('22222222-2222-2222-2222-222222222222', 'Test Document 2', 'This is content about machine learning algorithms', 'html'),
('33333333-3333-3333-3333-333333333333', 'Test Document 3', 'This document discusses natural language processing', 'text');

-- Insert test chunks with mock embeddings (simplified 3-dimensional for testing)
INSERT INTO verba_chunks (document_id, content, chunk_index, embedding) VALUES
('11111111-1111-1111-1111-111111111111', 'Artificial intelligence is transforming technology', 0, '[0.1,0.2,0.3]'::vector),
('11111111-1111-1111-1111-111111111111', 'Machine learning models require training data', 1, '[0.4,0.5,0.6]'::vector),
('22222222-2222-2222-2222-222222222222', 'Deep learning uses neural networks', 0, '[0.7,0.8,0.9]'::vector),
('22222222-2222-2222-2222-222222222222', 'Algorithms process information efficiently', 1, '[0.2,0.4,0.6]'::vector),
('33333333-3333-3333-3333-333333333333', 'Natural language processing analyzes text', 0, '[0.3,0.6,0.9]'::vector);

-- Test 1: Vector similarity search returns results
PREPARE vector_similarity_search AS 
    SELECT COUNT(*) FROM verba_chunks 
    WHERE embedding <=> '[0.1,0.2,0.3]'::vector < 1.0;

SELECT results_eq(
    'vector_similarity_search',
    'VALUES(5::bigint)',
    'Vector similarity search returns all test chunks'
);

-- Test 2: Vector distance calculation works
SELECT ok(
    (SELECT embedding <=> '[0.1,0.2,0.3]'::vector FROM verba_chunks LIMIT 1) >= 0,
    'Vector distance calculation returns non-negative values'
);

-- Test 3: HNSW index improves query performance
EXPLAIN (FORMAT JSON, ANALYZE false, BUFFERS false) 
SELECT * FROM verba_chunks ORDER BY embedding <=> '[0.1,0.2,0.3]'::vector LIMIT 5;

SELECT has_index('verba_chunks', 'verba_chunks_embedding_hnsw_idx', 'HNSW index exists for vector operations');

-- Test 4: Search similar chunks function works
SELECT results_eq(
    'SELECT COUNT(*) FROM search_similar_chunks(''[0.1,0.2,0.3]''::vector, 0.0, 10)',
    'VALUES(5::bigint)',
    'search_similar_chunks function returns expected results'
);

-- Test 5: Search with document type filtering
SELECT results_eq(
    'SELECT COUNT(*) FROM search_similar_chunks(''[0.1,0.2,0.3]''::vector, 0.0, 10, ''markdown'')',
    'VALUES(2::bigint)',
    'search_similar_chunks filters by document type correctly'
);

-- Test 6: Similarity threshold filtering works
SELECT results_eq(
    'SELECT COUNT(*) FROM search_similar_chunks(''[0.1,0.2,0.3]''::vector, 0.9, 10)',
    'VALUES(1::bigint)',
    'search_similar_chunks respects similarity threshold'
);

-- Test 7: Vector embedding insertion and retrieval
INSERT INTO verba_chunks (document_id, content, chunk_index, embedding) 
VALUES ('11111111-1111-1111-1111-111111111111', 'Test embedding insertion', 2, '[0.15,0.25,0.35]'::vector);

SELECT ok(
    (SELECT COUNT(*) FROM verba_chunks WHERE document_id = '11111111-1111-1111-1111-111111111111') = 3,
    'Vector embedding insertion successful'
);

-- Test 8: Embedding cache functionality
INSERT INTO verba_embedding_cache (embedder_name, content_hash, content, embedding) VALUES
('test_embedder', 'hash123', 'test content', '[0.1,0.1,0.1]'::vector),
('test_embedder', 'hash456', 'another content', '[0.2,0.2,0.2]'::vector);

SELECT results_eq(
    'SELECT COUNT(*) FROM verba_embedding_cache WHERE embedder_name = ''test_embedder''',
    'VALUES(2::bigint)',
    'Embedding cache stores multiple entries per embedder'
);

-- Test 9: Embedding cache unique constraint
SELECT throws_ok(
    'INSERT INTO verba_embedding_cache (embedder_name, content_hash, content, embedding) VALUES (''test_embedder'', ''hash123'', ''duplicate'', ''[0.3,0.3,0.3]''::vector)',
    '23505', -- unique violation error code
    NULL,
    'Embedding cache prevents duplicate hash entries'
);

-- Test 10: Document statistics function
SELECT results_eq(
    'SELECT total_documents FROM get_document_stats()',
    'VALUES(3::bigint)',
    'get_document_stats returns correct document count'
);

SELECT results_eq(
    'SELECT total_chunks FROM get_document_stats()',
    'VALUES(6::bigint)',  -- 5 original + 1 added in test
    'get_document_stats returns correct chunk count'
);

-- Test 11: Vector operations with metadata filtering
UPDATE verba_chunks SET metadata = '{"category": "ai", "priority": "high"}' 
WHERE content LIKE '%artificial intelligence%';

SELECT results_eq(
    'SELECT COUNT(*) FROM verba_chunks WHERE metadata->>''category'' = ''ai''',
    'VALUES(1::bigint)',
    'Metadata filtering works with JSONB queries'
);

-- Test 12: Cosine similarity vs other distance metrics
SELECT ok(
    (SELECT embedding <=> '[0.1,0.2,0.3]'::vector FROM verba_chunks LIMIT 1) != 
    (SELECT embedding <#> '[0.1,0.2,0.3]'::vector FROM verba_chunks LIMIT 1),
    'Cosine distance differs from inner product distance'
);

-- Test 13: Vector dimension consistency
SELECT ok(
    vector_dims((SELECT embedding FROM verba_chunks LIMIT 1)) = 3,
    'Vector dimensions are consistent (test uses 3D vectors)'
);

-- Test 14: Performance optimization - partial index usage
SELECT has_index('verba_chunks', 'verba_chunks_recent_idx', 'Recent chunks index exists for performance');

SELECT * FROM finish();
ROLLBACK;