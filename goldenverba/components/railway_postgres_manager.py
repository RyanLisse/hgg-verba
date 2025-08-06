"""Railway PostgreSQL manager for Verba - adapted from Supabase implementation."""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import numpy as np
from datetime import datetime, timedelta

import asyncpg
from pgvector.asyncpg import register_vector

from goldenverba.components.types import Document, Chunk
from goldenverba.components.managers import Manager


class RailwayPostgresManager:
    """Manages all Railway PostgreSQL operations including vector search with pgvector."""
    
    def __init__(self, database_url: str = None):
        """Initialize Railway PostgreSQL connection.
        
        Args:
            database_url: Railway PostgreSQL connection string
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        
        if not self.database_url:
            raise ValueError("Railway DATABASE_URL is required")
        
        # Async connection pool for all operations
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize async connection pool and pgvector."""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=20,
                    command_timeout=300,
                    server_settings={
                        'application_name': 'verba-rag',
                        'jit': 'off'
                    }
                )
                
                # Register pgvector type and ensure schema
                async with self.pool.acquire() as conn:
                    await register_vector(conn)
                    await self._ensure_schema(conn)
                    
                print("✅ Railway PostgreSQL initialized successfully")
                    
            except Exception as e:
                print(f"❌ Failed to initialize Railway PostgreSQL: {e}")
                raise
    
    async def _ensure_schema(self, conn):
        """Ensure all required tables and functions exist."""
        # Create extension if not exists
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        
        # Create tables (same schema as Supabase migration)
        schema_sql = """
        -- Documents table
        CREATE TABLE IF NOT EXISTS documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            path TEXT,
            content TEXT,
            metadata JSONB DEFAULT '{}',
            file_size INTEGER DEFAULT 0,
            total_chunks INTEGER DEFAULT 0,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- Document chunks with vector embeddings
        CREATE TABLE IF NOT EXISTS document_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            embedding vector(1536), -- OpenAI embedding dimension
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- Configuration storage
        CREATE TABLE IF NOT EXISTS configurations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            config_type TEXT NOT NULL,
            config_name TEXT NOT NULL,
            config_data JSONB NOT NULL,
            is_active BOOLEAN DEFAULT false,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(config_type, config_name)
        );

        -- Semantic cache
        CREATE TABLE IF NOT EXISTS semantic_cache (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            query TEXT NOT NULL,
            query_embedding vector(1536),
            response TEXT NOT NULL,
            metadata JSONB DEFAULT '{}',
            hit_count INTEGER DEFAULT 1,
            expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days'),
            last_accessed TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- Query suggestions
        CREATE TABLE IF NOT EXISTS query_suggestions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            query TEXT UNIQUE NOT NULL,
            frequency INTEGER DEFAULT 1,
            last_used TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        
        await conn.execute(schema_sql)
        
        # Create indexes for performance
        index_sql = """
        -- Vector similarity indexes (HNSW for large datasets)
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw 
        ON document_chunks USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64);

        -- B-tree indexes for exact matching
        CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
        CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
        CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_configurations_active ON configurations(config_type, is_active) WHERE is_active = true;
        
        -- GIN indexes for JSONB and text search
        CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin ON documents USING gin(metadata);
        CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata_gin ON document_chunks USING gin(metadata);
        CREATE INDEX IF NOT EXISTS idx_document_chunks_content_gin ON document_chunks USING gin(to_tsvector('english', content));
        
        -- Semantic cache indexes
        CREATE INDEX IF NOT EXISTS idx_semantic_cache_embedding_hnsw 
        ON semantic_cache USING hnsw (query_embedding vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS idx_semantic_cache_expires ON semantic_cache(expires_at);
        """
        
        await conn.execute(index_sql)
        
        # Create hybrid search function
        hybrid_search_function = """
        CREATE OR REPLACE FUNCTION hybrid_search_chunks(
            query_text TEXT,
            query_vector vector(1536),
            match_limit INT DEFAULT 10,
            alpha FLOAT DEFAULT 0.5
        )
        RETURNS TABLE (
            id UUID,
            document_id UUID,
            content TEXT,
            metadata JSONB,
            score FLOAT
        )
        LANGUAGE plpgsql
        AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                c.id,
                c.document_id,
                c.content,
                c.metadata,
                (
                    alpha * (1 - (c.embedding <=> query_vector)) +
                    (1 - alpha) * ts_rank_cd(to_tsvector('english', c.content), plainto_tsquery('english', query_text))
                ) as score
            FROM document_chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE c.embedding IS NOT NULL
                AND (
                    to_tsvector('english', c.content) @@ plainto_tsquery('english', query_text)
                    OR (1 - (c.embedding <=> query_vector)) > 0.3
                )
            ORDER BY score DESC
            LIMIT match_limit;
        END;
        $$;
        """
        
        await conn.execute(hybrid_search_function)
        
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def insert_document(self, document: Document) -> str:
        """Insert a document into the database."""
        if not self.pool:
            await self.initialize()
            
        doc_id = str(uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO documents (id, name, type, path, content, metadata, file_size, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
            doc_id,
            document.name,
            document.type.upper(),
            document.path,
            document.content[:1000000] if document.content else None,
            json.dumps(document.metadata or {}),
            len(document.content) if document.content else 0,
            "PENDING"
            )
        
        return doc_id
    
    async def insert_chunks(self, document_id: str, chunks: List[Chunk]) -> List[str]:
        """Insert document chunks with embeddings."""
        if not self.pool:
            await self.initialize()
        
        chunk_ids = []
        
        async with self.pool.acquire() as conn:
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid4())
                
                # Convert embedding to pgvector format
                embedding = None
                if hasattr(chunk, 'embedding') and chunk.embedding is not None:
                    if isinstance(chunk.embedding, list):
                        embedding = chunk.embedding
                    elif isinstance(chunk.embedding, np.ndarray):
                        embedding = chunk.embedding.tolist()

                await conn.execute("""
                    INSERT INTO document_chunks (id, document_id, chunk_index, content, metadata, embedding)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                chunk_id, 
                document_id, 
                i, 
                chunk.content, 
                json.dumps(chunk.metadata or {}), 
                embedding
                )
                
                chunk_ids.append(chunk_id)

        # Update document status and chunk count
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE documents 
                SET status = 'COMPLETED', total_chunks = $2, updated_at = NOW()
                WHERE id = $1
            """, document_id, len(chunks))
        
        return chunk_ids
    
    async def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            # Build the query with optional metadata filtering
            base_query = """
                SELECT 
                    c.id,
                    c.document_id,
                    c.content,
                    c.metadata,
                    d.name as document_name,
                    1 - (c.embedding <=> $1::vector) as similarity
                FROM document_chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE c.embedding IS NOT NULL
                    AND 1 - (c.embedding <=> $1::vector) > $2
            """
            
            params = [query_embedding, threshold]
            
            if filter_metadata:
                # Add JSONB containment check for metadata
                base_query += " AND c.metadata @> $3::jsonb"
                params.append(json.dumps(filter_metadata))
            
            base_query += f" ORDER BY c.embedding <=> $1::vector LIMIT {limit}"
            
            rows = await conn.fetch(base_query, *params)
            
            return [
                {
                    "id": row["id"],
                    "document_id": row["document_id"],
                    "document_name": row["document_name"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "similarity": float(row["similarity"])
                }
                for row in rows
            ]
    
    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        limit: int = 10,
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and text search."""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM hybrid_search_chunks($1, $2::vector, $3, $4)
            """, query_text, query_embedding, limit, alpha)
            
            # Fetch document names
            results = []
            for row in rows:
                doc = await conn.fetchrow(
                    "SELECT name FROM documents WHERE id = $1",
                    row["document_id"]
                )
                
                results.append({
                    "id": row["id"],
                    "document_id": row["document_id"],
                    "document_name": doc["name"] if doc else "Unknown",
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "score": float(row["score"])
                })
            
            return results
    
    async def get_documents(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve documents from database."""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            base_query = "SELECT * FROM documents"
            params = []
            
            if status:
                base_query += " WHERE status = $1"
                params.append(status)
            
            base_query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
            params.append(limit)
            
            if offset > 0:
                base_query += " OFFSET $" + str(len(params) + 1)
                params.append(offset)
            
            rows = await conn.fetch(base_query, *params)
            
            return [
                {
                    "id": str(row["id"]),
                    "name": row["name"],
                    "type": row["type"],
                    "path": row["path"],
                    "file_size": row["file_size"],
                    "total_chunks": row["total_chunks"],
                    "status": row["status"],
                    "created_at": row["created_at"].isoformat(),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                }
                for row in rows
            ]
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks."""
        if not self.pool:
            await self.initialize()
            
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("DELETE FROM documents WHERE id = $1", document_id)
            return True
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    async def save_configuration(
        self,
        config_type: str,
        config_name: str,
        config_data: Dict[str, Any],
        set_active: bool = False
    ) -> str:
        """Save configuration to database."""
        if not self.pool:
            await self.initialize()
            
        config_id = str(uuid4())
        
        async with self.pool.acquire() as conn:
            # Deactivate other configs of same type if setting active
            if set_active:
                await conn.execute("""
                    UPDATE configurations 
                    SET is_active = false 
                    WHERE config_type = $1
                """, config_type)
            
            await conn.execute("""
                INSERT INTO configurations (id, config_type, config_name, config_data, is_active)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (config_type, config_name)
                DO UPDATE SET 
                    config_data = EXCLUDED.config_data,
                    is_active = EXCLUDED.is_active,
                    updated_at = NOW()
            """, config_id, config_type, config_name, json.dumps(config_data), set_active)
        
        return config_id
    
    async def get_configuration(
        self,
        config_type: str,
        config_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve configuration from database."""
        if not self.pool:
            await self.initialize()
            
        async with self.pool.acquire() as conn:
            if config_name:
                row = await conn.fetchrow("""
                    SELECT config_data FROM configurations 
                    WHERE config_type = $1 AND config_name = $2
                """, config_type, config_name)
            else:
                row = await conn.fetchrow("""
                    SELECT config_data FROM configurations 
                    WHERE config_type = $1 AND is_active = true
                """, config_type)
            
            if row:
                return json.loads(row["config_data"])
        return None
    
    async def add_to_cache(
        self,
        query: str,
        query_embedding: List[float],
        response: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add entry to semantic cache."""
        if not self.pool:
            await self.initialize()
        
        cache_id = str(uuid4())
        
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO semantic_cache (id, query, query_embedding, response, metadata)
                VALUES ($1, $2, $3::vector, $4, $5)
            """, cache_id, query, query_embedding, response, json.dumps(metadata or {}))
        
        return cache_id
    
    async def search_cache(
        self,
        query_embedding: List[float],
        threshold: float = 0.95
    ) -> Optional[Dict[str, Any]]:
        """Search semantic cache for similar queries."""
        if not self.pool:
            await self.initialize()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    id,
                    query,
                    response,
                    metadata,
                    1 - (query_embedding <=> $1::vector) as similarity
                FROM semantic_cache
                WHERE query_embedding IS NOT NULL
                    AND 1 - (query_embedding <=> $1::vector) > $2
                    AND expires_at > NOW()
                ORDER BY query_embedding <=> $1::vector
                LIMIT 1
            """, query_embedding, threshold)
            
            if row:
                # Update hit count and last accessed
                await conn.execute("""
                    UPDATE semantic_cache 
                    SET hit_count = hit_count + 1, last_accessed = NOW()
                    WHERE id = $1
                """, row["id"])
                
                return {
                    "query": row["query"],
                    "response": row["response"],
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "similarity": float(row["similarity"])
                }
        
        return None