import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import asyncpg
from wasabi import msg

from goldenverba.components.document import Document, Chunk
from goldenverba.server.types import ChunkScore


class PostgreSQLManager:
    """PostgreSQL Manager for Verba with pgvector extension for vector similarity search."""
    
    def __init__(self):
        self.config_collection_name = "verba_config"
        self.document_collection_name = "verba_documents"
        self.chunk_collection_name = "verba_chunks"
        self.suggestion_collection_name = "verba_suggestions"
        self.pool: Optional[asyncpg.Pool] = None
        
    async def connect(self, deployment: str = None, url: str = None, key: str = None) -> asyncpg.Pool:
        """Connect to Railway PostgreSQL database with connection pooling."""
        try:
            # Use Railway PostgreSQL environment variables or provided credentials
            database_url = url or os.getenv("RAILWAY_POSTGRES_URL") or os.getenv("DATABASE_URL")
            
            if not database_url:
                # Build URL from individual components if not provided as full URL
                host = os.getenv("RAILWAY_POSTGRES_HOST", "localhost")
                port = os.getenv("RAILWAY_POSTGRES_PORT", "5432")
                database = os.getenv("RAILWAY_POSTGRES_DATABASE", "railway")
                user = os.getenv("RAILWAY_POSTGRES_USER", "postgres")
                password = key or os.getenv("RAILWAY_POSTGRES_PASSWORD")
                
                if not password:
                    raise ValueError("PostgreSQL password required. Set RAILWAY_POSTGRES_PASSWORD or provide key parameter.")
                
                database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
            
            # Initialize database schema
            await self._init_schema()
            
            msg.good(f"Connected to Railway PostgreSQL database")
            return self.pool
            
        except Exception as e:
            msg.fail(f"Failed to connect to PostgreSQL: {str(e)}")
            raise e
    
    async def disconnect(self, pool: asyncpg.Pool = None):
        """Close the connection pool."""
        try:
            if pool and not pool._closed:
                await pool.close()
            elif self.pool and not self.pool._closed:
                await self.pool.close()
            msg.info("Disconnected from PostgreSQL")
            return True
        except Exception as e:
            msg.warn(f"Error disconnecting from PostgreSQL: {str(e)}")
            return False
    
    async def _init_schema(self):
        """Initialize database schema with pgvector extension and required tables."""
        async with self.pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create config table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.config_collection_name} (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    config JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create documents table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.document_collection_name} (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title TEXT NOT NULL,
                    content TEXT,
                    extension TEXT,
                    file_size BIGINT,
                    source TEXT,
                    labels TEXT[],
                    meta JSONB,
                    metadata JSONB,
                    embedder TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create chunks table with vector column
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.chunk_collection_name} (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_uuid UUID REFERENCES {self.document_collection_name}(uuid) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    content_without_overlap TEXT,
                    chunk_id INTEGER,
                    chunk_index INTEGER,
                    vector vector(1536),  -- Default OpenAI embedding dimension
                    embedder TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create suggestions table
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.suggestion_collection_name} (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    query TEXT NOT NULL,
                    count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
            """)
            
            # Create indexes for performance
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_chunks_vector ON {self.chunk_collection_name} USING ivfflat (vector vector_cosine_ops);")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_chunks_document_uuid ON {self.chunk_collection_name}(document_uuid);")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_chunks_embedder ON {self.chunk_collection_name}(embedder);")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_documents_title ON {self.document_collection_name}(title);")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_documents_embedder ON {self.document_collection_name}(embedder);")
            await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_suggestions_query ON {self.suggestion_collection_name}(query);")
    
    async def verify_collection(self, pool: asyncpg.Pool, collection_name: str) -> bool:
        """Verify that a table exists."""
        async with pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = $1
                );
            """, collection_name)
            return result
    
    # Configuration methods
    async def set_config(self, pool: asyncpg.Pool, config_uuid: str, config: dict):
        """Set configuration in the database."""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self.config_collection_name} (uuid, config, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (uuid) 
                DO UPDATE SET config = $2, updated_at = NOW();
            """, uuid.UUID(config_uuid), json.dumps(config))
    
    async def get_config(self, pool: asyncpg.Pool, config_uuid: str) -> Optional[dict]:
        """Get configuration from the database."""
        async with pool.acquire() as conn:
            result = await conn.fetchval(f"""
                SELECT config FROM {self.config_collection_name} WHERE uuid = $1;
            """, uuid.UUID(config_uuid))
            return json.loads(result) if result else None
    
    async def reset_config(self, pool: asyncpg.Pool, config_uuid: str):
        """Delete configuration from the database."""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM {self.config_collection_name} WHERE uuid = $1;
            """, uuid.UUID(config_uuid))
    
    # Document methods
    async def import_document(self, pool: asyncpg.Pool, document: Document, embedder: str):
        """Import a document and its chunks into PostgreSQL."""
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Insert document
                doc_uuid = await conn.fetchval(f"""
                    INSERT INTO {self.document_collection_name} 
                    (uuid, title, content, extension, file_size, source, labels, meta, metadata, embedder)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    RETURNING uuid;
                """, 
                uuid.uuid4(),
                document.title,
                document.text,
                getattr(document, 'extension', None),
                getattr(document, 'file_size', 0),
                getattr(document, 'source', ''),
                getattr(document, 'labels', []),
                json.dumps(getattr(document, 'meta', {})),
                json.dumps(getattr(document, 'metadata', {})),
                embedder
                )
                
                # Insert chunks
                for chunk in document.chunks:
                    await conn.execute(f"""
                        INSERT INTO {self.chunk_collection_name}
                        (document_uuid, content, content_without_overlap, chunk_id, chunk_index, vector, embedder)
                        VALUES ($1, $2, $3, $4, $5, $6, $7);
                    """,
                    doc_uuid,
                    chunk.text,
                    getattr(chunk, 'content_without_overlap', chunk.text),
                    chunk.chunk_id,
                    getattr(chunk, 'chunk_index', 0),
                    chunk.vector if hasattr(chunk, 'vector') and chunk.vector else None,
                    embedder
                    )
                
                return doc_uuid
    
    async def get_document(self, pool: asyncpg.Pool, doc_uuid: str, properties: List[str] = None) -> Optional[dict]:
        """Get a document by UUID."""
        async with pool.acquire() as conn:
            if properties:
                props = ', '.join(properties)
            else:
                props = '*'
                
            result = await conn.fetchrow(f"""
                SELECT {props} FROM {self.document_collection_name} WHERE uuid = $1;
            """, uuid.UUID(doc_uuid))
            
            return dict(result) if result else None
    
    async def exist_document_name(self, pool: asyncpg.Pool, title: str) -> Optional[str]:
        """Check if a document with the given title exists."""
        async with pool.acquire() as conn:
            result = await conn.fetchval(f"""
                SELECT uuid FROM {self.document_collection_name} WHERE title = $1;
            """, title)
            return str(result) if result else None
    
    async def delete_document(self, pool: asyncpg.Pool, doc_uuid: str):
        """Delete a document and its chunks."""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM {self.document_collection_name} WHERE uuid = $1;
            """, uuid.UUID(doc_uuid))
    
    async def get_documents(self, pool: asyncpg.Pool, query: str = "", page_size: int = 10, 
                          page: int = 0, labels: List[str] = None, properties: List[str] = None) -> Tuple[List[dict], int]:
        """Get documents with pagination and search."""
        async with pool.acquire() as conn:
            if properties:
                props = ', '.join(properties)
            else:
                props = '*'
            
            offset = page * page_size
            where_clause = "WHERE TRUE"
            params = []
            
            if query:
                where_clause += " AND title ILIKE $" + str(len(params) + 1)
                params.append(f"%{query}%")
            
            if labels:
                where_clause += " AND labels && $" + str(len(params) + 1)
                params.append(labels)
            
            # Get documents
            documents = await conn.fetch(f"""
                SELECT {props} FROM {self.document_collection_name} 
                {where_clause}
                ORDER BY created_at DESC
                LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2) + ";
            """, *params, page_size, offset)
            
            # Get total count
            total_count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {self.document_collection_name} {where_clause};
            """, *params)
            
            return [dict(doc) for doc in documents], total_count
    
    # Chunk methods
    async def get_chunk(self, pool: asyncpg.Pool, chunk_uuid: str, embedder: str) -> Optional[dict]:
        """Get a chunk by UUID."""
        async with pool.acquire() as conn:
            result = await conn.fetchrow(f"""
                SELECT * FROM {self.chunk_collection_name} 
                WHERE uuid = $1 AND embedder = $2;
            """, uuid.UUID(chunk_uuid), embedder)
            
            return dict(result) if result else None
    
    async def get_chunks(self, pool: asyncpg.Pool, doc_uuid: str, page: int = 0, page_size: int = 10) -> List[dict]:
        """Get chunks for a document with pagination."""
        async with pool.acquire() as conn:
            offset = page * page_size
            chunks = await conn.fetch(f"""
                SELECT * FROM {self.chunk_collection_name} 
                WHERE document_uuid = $1
                ORDER BY chunk_id
                LIMIT $2 OFFSET $3;
            """, uuid.UUID(doc_uuid), page_size, offset)
            
            return [dict(chunk) for chunk in chunks]
    
    async def get_chunk_by_ids(self, pool: asyncpg.Pool, embedder: str, doc_uuid: str, ids: List[int]) -> List[dict]:
        """Get chunks by chunk IDs."""
        async with pool.acquire() as conn:
            chunks = await conn.fetch(f"""
                SELECT * FROM {self.chunk_collection_name} 
                WHERE document_uuid = $1 AND embedder = $2 AND chunk_id = ANY($3)
                ORDER BY chunk_id;
            """, uuid.UUID(doc_uuid), embedder, ids)
            
            return [{'properties': dict(chunk)} for chunk in chunks]
    
    async def get_chunk_count(self, pool: asyncpg.Pool, embedder: str, doc_uuid: str) -> int:
        """Get total chunk count for a document."""
        async with pool.acquire() as conn:
            count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {self.chunk_collection_name} 
                WHERE document_uuid = $1 AND embedder = $2;
            """, uuid.UUID(doc_uuid), embedder)
            
            return count
    
    # Vector search methods
    async def similarity_search(self, pool: asyncpg.Pool, vector: List[float], embedder: str, 
                              limit: int = 10, labels: List[str] = None, document_uuids: List[str] = None) -> List[ChunkScore]:
        """Perform vector similarity search."""
        async with pool.acquire() as conn:
            where_clause = "WHERE c.embedder = $2"
            params = [vector, embedder]
            
            if labels:
                where_clause += " AND d.labels && $" + str(len(params) + 1)
                params.append(labels)
            
            if document_uuids:
                uuid_list = [uuid.UUID(doc_uuid) for doc_uuid in document_uuids]
                where_clause += " AND c.document_uuid = ANY($" + str(len(params) + 1) + ")"
                params.append(uuid_list)
            
            results = await conn.fetch(f"""
                SELECT c.uuid, c.content, c.chunk_id, d.uuid as doc_uuid, d.title,
                       (c.vector <=> $1::vector) as distance
                FROM {self.chunk_collection_name} c
                JOIN {self.document_collection_name} d ON c.document_uuid = d.uuid
                {where_clause}
                ORDER BY distance ASC
                LIMIT $" + str(len(params) + 1) + ";
            """, *params, limit)
            
            chunk_scores = []
            for row in results:
                chunk_scores.append(ChunkScore(
                    uuid=str(row['uuid']),
                    score=1.0 - row['distance'],  # Convert distance to similarity score
                    chunk_id=row['chunk_id'],
                    doc_uuid=str(row['doc_uuid']),
                    doc_name=row['title'],
                    embedder=embedder
                ))
            
            return chunk_scores
    
    # Suggestion methods
    async def add_suggestion(self, pool: asyncpg.Pool, query: str):
        """Add or increment a suggestion."""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                INSERT INTO {self.suggestion_collection_name} (query, count, updated_at)
                VALUES ($1, 1, NOW())
                ON CONFLICT (query) 
                DO UPDATE SET count = {self.suggestion_collection_name}.count + 1, updated_at = NOW();
            """, query)
    
    async def retrieve_suggestions(self, pool: asyncpg.Pool, query: str, limit: int = 5) -> List[str]:
        """Get suggestions based on query prefix."""
        async with pool.acquire() as conn:
            results = await conn.fetch(f"""
                SELECT query FROM {self.suggestion_collection_name}
                WHERE query ILIKE $1
                ORDER BY count DESC, updated_at DESC
                LIMIT $2;
            """, f"{query}%", limit)
            
            return [row['query'] for row in results]
    
    async def retrieve_all_suggestions(self, pool: asyncpg.Pool, page: int = 0, page_size: int = 10) -> Tuple[List[dict], int]:
        """Get all suggestions with pagination."""
        async with pool.acquire() as conn:
            offset = page * page_size
            
            suggestions = await conn.fetch(f"""
                SELECT uuid, query, count, created_at, updated_at FROM {self.suggestion_collection_name}
                ORDER BY count DESC, updated_at DESC
                LIMIT $1 OFFSET $2;
            """, page_size, offset)
            
            total_count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {self.suggestion_collection_name};
            """)
            
            return [dict(sugg) for sugg in suggestions], total_count
    
    async def delete_suggestions(self, pool: asyncpg.Pool, suggestion_uuid: str):
        """Delete a suggestion."""
        async with pool.acquire() as conn:
            await conn.execute(f"""
                DELETE FROM {self.suggestion_collection_name} WHERE uuid = $1;
            """, uuid.UUID(suggestion_uuid))
    
    # Utility methods
    async def get_labels(self, pool: asyncpg.Pool) -> List[str]:
        """Get all unique labels."""
        async with pool.acquire() as conn:
            results = await conn.fetch(f"""
                SELECT DISTINCT unnest(labels) as label FROM {self.document_collection_name}
                WHERE labels IS NOT NULL AND array_length(labels, 1) > 0;
            """)
            
            return [row['label'] for row in results if row['label']]
    
    async def get_datacount(self, pool: asyncpg.Pool, embedder: str, document_uuids: List[str] = None) -> int:
        """Get count of chunks for an embedder."""
        async with pool.acquire() as conn:
            where_clause = "WHERE embedder = $1"
            params = [embedder]
            
            if document_uuids:
                uuid_list = [uuid.UUID(doc_uuid) for doc_uuid in document_uuids]
                where_clause += " AND document_uuid = ANY($2)"
                params.append(uuid_list)
            
            count = await conn.fetchval(f"""
                SELECT COUNT(*) FROM {self.chunk_collection_name} {where_clause};
            """, *params)
            
            return count
    
    async def get_metadata(self, pool: asyncpg.Pool) -> Tuple[dict, dict]:
        """Get metadata about the database."""
        async with pool.acquire() as conn:
            # Database information
            db_info = await conn.fetchrow("""
                SELECT version() as version, current_database() as database;
            """)
            
            # Table counts
            doc_count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.document_collection_name};")
            chunk_count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.chunk_collection_name};")
            config_count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.config_collection_name};")
            suggestion_count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.suggestion_collection_name};")
            
            node_payload = {
                "version": db_info['version'],
                "database": db_info['database'],
                "status": "healthy"
            }
            
            collection_payload = {
                "documents": doc_count,
                "chunks": chunk_count,
                "configs": config_count,
                "suggestions": suggestion_count
            }
            
            return node_payload, collection_payload
    
    # Admin methods
    async def delete_all(self, pool: asyncpg.Pool):
        """Delete all data from all tables."""
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.chunk_collection_name};")
            await conn.execute(f"DELETE FROM {self.document_collection_name};")
            await conn.execute(f"DELETE FROM {self.config_collection_name};")
            await conn.execute(f"DELETE FROM {self.suggestion_collection_name};")
    
    async def delete_all_documents(self, pool: asyncpg.Pool):
        """Delete all documents and chunks."""
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.document_collection_name};")
    
    async def delete_all_configs(self, pool: asyncpg.Pool):
        """Delete all configurations."""
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.config_collection_name};")
    
    async def delete_all_suggestions(self, pool: asyncpg.Pool):
        """Delete all suggestions."""
        async with pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {self.suggestion_collection_name};")
    
    # Vector operations placeholder methods (to maintain compatibility)
    async def get_vectors(self, pool: asyncpg.Pool, doc_uuid: str, show_all: bool = False) -> List[dict]:
        """Get vectors for a document (placeholder for compatibility)."""
        # This would need to be implemented based on specific requirements
        return []