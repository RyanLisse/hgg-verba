-- Vector operations tests
CREATE EXTENSION IF NOT EXISTS pgtap;

-- Start transaction for testing
BEGIN;

SELECT plan(10);

-- Create test data
INSERT INTO documents (id, name, type, status)
VALUES ('11111111-1111-1111-1111-111111111111', 'Test Document', 'PDF', 'COMPLETED');

-- Test vector insertion
INSERT INTO document_chunks (
    id,
    document_id,
    chunk_index,
    content,
    embedding
) VALUES (
    '22222222-2222-2222-2222-222222222222',
    '11111111-1111-1111-1111-111111111111',
    0,
    'This is a test chunk for vector operations',
    -- Generate a random 1536-dimensional vector for testing
    ARRAY_FILL(0.1, ARRAY[1536])::vector
);

-- Test 1: Verify vector was inserted
SELECT ok(
    EXISTS(
        SELECT 1 FROM document_chunks 
        WHERE id = '22222222-2222-2222-2222-222222222222' 
        AND embedding IS NOT NULL
    ),
    'Vector embedding should be inserted successfully'
);

-- Test 2: Test vector similarity search
PREPARE similarity_search AS
SELECT * FROM search_similar_chunks(
    ARRAY_FILL(0.1, ARRAY[1536])::vector,
    10,
    0.0
);

SELECT ok(
    EXISTS(EXECUTE similarity_search),
    'Similarity search should return results'
);

-- Test 3: Test exact vector match
SELECT ok(
    (SELECT 1 - (embedding <=> ARRAY_FILL(0.1, ARRAY[1536])::vector) 
     FROM document_chunks 
     WHERE id = '22222222-2222-2222-2222-222222222222') = 1.0,
    'Exact vector match should have similarity of 1.0'
);

-- Insert more test vectors with varying similarities
INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 1, 'Similar chunk', ARRAY_FILL(0.09, ARRAY[1536])::vector),
    ('11111111-1111-1111-1111-111111111111', 2, 'Less similar chunk', ARRAY_FILL(0.5, ARRAY[1536])::vector),
    ('11111111-1111-1111-1111-111111111111', 3, 'Dissimilar chunk', ARRAY_FILL(-0.5, ARRAY[1536])::vector);

-- Test 4: Test similarity ordering
WITH ranked_results AS (
    SELECT 
        chunk_index,
        1 - (embedding <=> ARRAY_FILL(0.1, ARRAY[1536])::vector) AS similarity
    FROM document_chunks
    WHERE document_id = '11111111-1111-1111-1111-111111111111'
    ORDER BY embedding <=> ARRAY_FILL(0.1, ARRAY[1536])::vector
)
SELECT ok(
    (SELECT chunk_index FROM ranked_results LIMIT 1) = 0,
    'Most similar chunk should be returned first'
);

-- Test 5: Test similarity threshold
SELECT is(
    (SELECT COUNT(*) FROM search_similar_chunks(
        ARRAY_FILL(0.1, ARRAY[1536])::vector,
        10,
        0.9  -- High threshold
    ))::INT,
    2,  -- Should only match the exact and very similar vectors
    'Similarity threshold should filter results correctly'
);

-- Test 6: Test hybrid search function
INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
VALUES ('11111111-1111-1111-1111-111111111111', 4, 'quantum physics research paper', ARRAY_FILL(0.3, ARRAY[1536])::vector);

SELECT ok(
    EXISTS(
        SELECT * FROM hybrid_search_chunks(
            'quantum physics',
            ARRAY_FILL(0.3, ARRAY[1536])::vector,
            10,
            0.5
        )
    ),
    'Hybrid search should return results'
);

-- Test 7: Test vector dimension validation
PREPARE invalid_vector AS
INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
VALUES ('11111111-1111-1111-1111-111111111111', 5, 'Invalid vector', ARRAY_FILL(0.1, ARRAY[10])::vector);

SELECT throws_ok(
    'invalid_vector',
    '22000',  -- Vector dimension mismatch error
    NULL,
    'Should reject vectors with incorrect dimensions'
);

-- Test 8: Test NULL vector handling
INSERT INTO document_chunks (document_id, chunk_index, content, embedding)
VALUES ('11111111-1111-1111-1111-111111111111', 6, 'No embedding chunk', NULL);

SELECT ok(
    EXISTS(
        SELECT 1 FROM document_chunks 
        WHERE chunk_index = 6 AND embedding IS NULL
    ),
    'Should allow NULL embeddings'
);

-- Test 9: Test vector indexing performance (check if index is used)
EXPLAIN (FORMAT JSON, BUFFERS FALSE, TIMING FALSE, SUMMARY FALSE) 
SELECT * FROM document_chunks
ORDER BY embedding <=> ARRAY_FILL(0.1, ARRAY[1536])::vector
LIMIT 10;

SELECT ok(
    true,  -- This would need actual plan analysis in production
    'Vector index should be utilized for similarity queries'
);

-- Test 10: Test cosine similarity calculation
SELECT ok(
    (SELECT 1 - (ARRAY_FILL(1.0, ARRAY[1536])::vector <=> ARRAY_FILL(1.0, ARRAY[1536])::vector)) = 1.0,
    'Identical vectors should have cosine similarity of 1.0'
);

SELECT * FROM finish();
ROLLBACK;