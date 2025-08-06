"""
Supabase Manager for Verba RAG Application
Replaces WeaviateManager with PostgreSQL + pgvector implementation
"""

import asyncio
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import asyncpg
from supabase import create_client, Client
from pgvector.asyncpg import register_vector
from wasabi import msg

from goldenverba.components.document import Document
from goldenverba.server.helpers import LoggerManager


@dataclass
class VectorSearchResult:
    """Result from vector similarity search"""

    chunk_id: str
    document_id: str
    content: str
    document_title: str
    doc_type: str
    similarity: float
    metadata: Dict[str, Any]


class SupabaseManager:
    """
    Manages Supabase connections and operations for Verba RAG application.
    Provides vector search, document storage, and configuration management.
    """

    def __init__(self):
        self.document_table = "verba_documents"
        self.chunk_table = "verba_chunks"
        self.config_table = "verba_config"
        self.suggestion_table = "verba_suggestions"
        self.embedding_cache_table = "verba_embedding_cache"
        self.migration_log_table = "verba_migration_log"

        # Configuration UUIDs (maintain compatibility with Weaviate version)
        self.rag_config_uuid = "e0adcc12-9bad-4588-8a1e-bab0af6ed485"
        self.theme_config_uuid = "baab38a7-cb51-4108-acd8-6edeca222820"
        self.user_config_uuid = "f53f7738-08be-4d5a-b003-13eb4bf03ac7"

        # Connection objects
        self.client: Optional[Client] = None
        self.pool: Optional[asyncpg.Pool] = None
        self.embedding_table: Dict[str, str] = {}

    async def connect(self, deployment: str, url: str, key: str) -> Optional[Client]:
        """
        Connect to Supabase with both REST and direct PostgreSQL connections.

        Args:
            deployment: Deployment type (should be "Supabase")
            url: Supabase project URL
            key: Supabase service key or anon key

        Returns:
            Supabase client if successful, None otherwise
        """
        try:
            start_time = asyncio.get_event_loop().time()

            # Create Supabase REST client
            self.client = create_client(url, key)
            msg.info(f"Connecting to Supabase at {url}")

            # Extract database connection details
            # Supabase format: https://xxx.supabase.co -> postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres
            project_ref = url.replace("https://", "").replace(".supabase.co", "")
            if key and key.startswith("eyJ"):  # JWT token
                # For service role key, we need to use connection pooler
                database_url = f"postgresql://postgres.{project_ref}:{key}@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
            else:
                # For direct connection (development)
                database_url = f"postgresql://postgres:{key}@db.{project_ref}.supabase.co:5432/postgres"

            # Create PostgreSQL connection pool for vector operations
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
                server_settings={
                    "application_name": "verba_rag",
                    "jit": "off",  # Disable JIT for consistent performance
                },
            )

            # Register pgvector types
            async with self.pool.acquire() as conn:
                await register_vector(conn)

            # Verify connection and schema
            await self._verify_schema()

            end_time = asyncio.get_event_loop().time()
            msg.good("Successfully connected to Supabase")
            msg.info(f"Connection time: {end_time - start_time:.2f} seconds")

            return self.client

        except Exception as e:
            msg.fail(f"Failed to connect to Supabase: {str(e)}")
            await self.disconnect()
            raise e

    async def disconnect(self) -> bool:
        """Close Supabase connections"""
        try:
            if self.pool:
                await self.pool.close()
                self.pool = None

            self.client = None
            msg.info("Disconnected from Supabase")
            return True

        except Exception as e:
            msg.warn(f"Error during disconnect: {str(e)}")
            return False

    async def _verify_schema(self) -> bool:
        """Verify that required tables and extensions exist"""
        try:
            async with self.pool.acquire() as conn:
                # Check if required tables exist
                tables_check = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('verba_documents', 'verba_chunks', 'verba_config')
                """)

                if len(tables_check) != 3:
                    raise Exception(
                        "Required Verba tables not found. Please run migration scripts first."
                    )

                # Check pgvector extension
                vector_check = await conn.fetchval("""
                    SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')
                """)

                if not vector_check:
                    raise Exception(
                        "pgvector extension not found. Please enable it in Supabase."
                    )

                msg.good("Schema verification successful")
                return True

        except Exception as e:
            msg.fail(f"Schema verification failed: {str(e)}")
            raise e

    async def import_document(
        self, documents: List[Document], logger: LoggerManager = None
    ) -> bool:
        """
        Import documents with chunks and embeddings into Supabase.

        Args:
            documents: List of Document objects to import
            logger: Optional logger for progress updates

        Returns:
            True if successful, False otherwise
        """
        if not self.pool:
            raise Exception("Not connected to Supabase")

        if logger:
            logger.log(f"Starting import of {len(documents)} documents")

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    imported_count = 0

                    for doc in documents:
                        # Insert document
                        doc_id = await conn.fetchval(
                            """
                            INSERT INTO verba_documents (title, content, metadata, doc_name, doc_type, doc_link, chunk_count)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                            RETURNING id
                        """,
                            doc.title,
                            doc.content,
                            json.dumps(doc.metadata or {}),
                            doc.doc_name,
                            doc.doc_type,
                            doc.doc_link,
                            len(doc.chunks),
                        )

                        # Insert chunks with embeddings
                        chunk_count = 0
                        for chunk in doc.chunks:
                            if hasattr(chunk, "embedding") and chunk.embedding:
                                await conn.execute(
                                    """
                                    INSERT INTO verba_chunks (document_id, content, chunk_index, 
                                                            start_char, end_char, embedding, metadata)
                                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                                """,
                                    doc_id,
                                    chunk.content,
                                    chunk.chunk_index,
                                    getattr(chunk, "start_char", None),
                                    getattr(chunk, "end_char", None),
                                    chunk.embedding,
                                    json.dumps(chunk.metadata or {}),
                                )
                                chunk_count += 1

                        # Update actual chunk count
                        await conn.execute(
                            """
                            UPDATE verba_documents SET chunk_count = $1 WHERE id = $2
                        """,
                            chunk_count,
                            doc_id,
                        )

                        imported_count += 1

                        if logger:
                            logger.log(
                                f"Imported document: {doc.title} ({chunk_count} chunks)"
                            )

            msg.good(f"Successfully imported {imported_count} documents")
            return True

        except Exception as e:
            msg.fail(f"Document import failed: {str(e)}")
            if logger:
                logger.log(f"Import failed: {str(e)}")
            return False

    async def get_vectors(
        self,
        query_vector: List[float],
        limit: int = 10,
        doc_filter: Optional[Dict] = None,
        similarity_threshold: float = 0.0,
    ) -> List[VectorSearchResult]:
        """
        Perform vector similarity search.

        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            doc_filter: Optional document filtering criteria
            similarity_threshold: Minimum similarity score

        Returns:
            List of VectorSearchResult objects
        """
        if not self.pool:
            raise Exception("Not connected to Supabase")

        try:
            async with self.pool.acquire() as conn:
                # Build dynamic query with optional filtering
                base_query = """
                    SELECT c.id, c.document_id, c.content, c.metadata as chunk_metadata,
                           d.title, d.doc_type, d.metadata as doc_metadata,
                           1 - (c.embedding <=> $1) as similarity
                    FROM verba_chunks c
                    JOIN verba_documents d ON c.document_id = d.id
                """

                conditions = ["(1 - (c.embedding <=> $1)) >= $2"]
                params = [query_vector, similarity_threshold]
                param_count = 2

                if doc_filter:
                    if doc_filter.get("doc_type"):
                        param_count += 1
                        conditions.append(f"d.doc_type = ${param_count}")
                        params.append(doc_filter["doc_type"])

                    if doc_filter.get("doc_name"):
                        param_count += 1
                        conditions.append(f"d.doc_name = ${param_count}")
                        params.append(doc_filter["doc_name"])

                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)

                param_count += 1
                base_query += f" ORDER BY c.embedding <=> $1 LIMIT ${param_count}"
                params.append(limit)

                rows = await conn.fetch(base_query, *params)

                results = []
                for row in rows:
                    # Merge chunk and document metadata
                    combined_metadata = {
                        **(row["doc_metadata"] or {}),
                        **(row["chunk_metadata"] or {}),
                    }

                    results.append(
                        VectorSearchResult(
                            chunk_id=str(row["id"]),
                            document_id=str(row["document_id"]),
                            content=row["content"],
                            document_title=row["title"],
                            doc_type=row["doc_type"],
                            similarity=float(row["similarity"]),
                            metadata=combined_metadata,
                        )
                    )

                return results

        except Exception as e:
            msg.fail(f"Vector search failed: {str(e)}")
            return []

    async def get_embedding_cache(
        self, embedder_name: str, content: str
    ) -> Optional[List[float]]:
        """
        Retrieve cached embedding for content.

        Args:
            embedder_name: Name of the embedder
            content: Content to look up

        Returns:
            Cached embedding vector or None if not found
        """
        if not self.pool:
            return None

        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            async with self.pool.acquire() as conn:
                embedding = await conn.fetchval(
                    """
                    SELECT embedding FROM verba_embedding_cache 
                    WHERE embedder_name = $1 AND content_hash = $2
                """,
                    embedder_name,
                    content_hash,
                )

                if embedding:
                    return list(embedding)
                return None

        except Exception as e:
            msg.warn(f"Embedding cache lookup failed: {str(e)}")
            return None

    async def store_embedding_cache(
        self, embedder_name: str, content: str, embedding: List[float]
    ) -> bool:
        """
        Store embedding in cache.

        Args:
            embedder_name: Name of the embedder
            content: Original content
            embedding: Computed embedding vector

        Returns:
            True if successful, False otherwise
        """
        if not self.pool:
            return False

        try:
            content_hash = hashlib.sha256(content.encode()).hexdigest()

            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO verba_embedding_cache (embedder_name, content_hash, content, embedding)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (embedder_name, content_hash) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        created_at = NOW()
                """,
                    embedder_name,
                    content_hash,
                    content,
                    embedding,
                )

                return True

        except Exception as e:
            msg.warn(f"Embedding cache storage failed: {str(e)}")
            return False

    async def get_config(self, config_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve configuration by type.

        Args:
            config_type: Type of configuration ('rag', 'theme', 'user')

        Returns:
            Configuration data or None if not found
        """
        if not self.pool:
            return None

        try:
            async with self.pool.acquire() as conn:
                config_data = await conn.fetchval(
                    """
                    SELECT config_data FROM verba_config WHERE config_type = $1
                """,
                    config_type,
                )

                return config_data

        except Exception as e:
            msg.warn(f"Config retrieval failed: {str(e)}")
            return None

    async def set_config(self, config_type: str, config_data: Dict[str, Any]) -> bool:
        """
        Store configuration.

        Args:
            config_type: Type of configuration
            config_data: Configuration data to store

        Returns:
            True if successful, False otherwise
        """
        if not self.pool:
            return False

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO verba_config (config_type, config_data)
                    VALUES ($1, $2)
                    ON CONFLICT (config_type) DO UPDATE SET
                        config_data = EXCLUDED.config_data,
                        updated_at = NOW()
                """,
                    config_type,
                    json.dumps(config_data),
                )

                return True

        except Exception as e:
            msg.warn(f"Config storage failed: {str(e)}")
            return False

    async def delete_documents(self, document_ids: List[str]) -> bool:
        """
        Delete documents and their associated chunks.

        Args:
            document_ids: List of document IDs to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.pool or not document_ids:
            return False

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    # Delete documents (chunks will be deleted via CASCADE)
                    deleted_count = await conn.execute(
                        """
                        DELETE FROM verba_documents WHERE id = ANY($1)
                    """,
                        document_ids,
                    )

                    msg.good(f"Deleted {deleted_count} documents")
                    return True

        except Exception as e:
            msg.fail(f"Document deletion failed: {str(e)}")
            return False

    async def get_document_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive document and chunk statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.pool:
            return {}

        try:
            async with self.pool.acquire() as conn:
                stats = await conn.fetchrow("SELECT * FROM get_document_stats()")

                return {
                    "total_documents": stats["total_documents"],
                    "total_chunks": stats["total_chunks"],
                    "avg_chunks_per_document": float(
                        stats["avg_chunks_per_document"] or 0
                    ),
                    "doc_types": stats["doc_types"] or {},
                }

        except Exception as e:
            msg.warn(f"Stats retrieval failed: {str(e)}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on Supabase connection and database.

        Returns:
            Health status information
        """
        if not self.pool:
            return {"status": "disconnected", "error": "No connection pool"}

        try:
            async with self.pool.acquire() as conn:
                # Check database connectivity
                db_version = await conn.fetchval("SELECT version()")

                # Check pgvector extension
                vector_version = await conn.fetchval("""
                    SELECT default_version FROM pg_available_extensions WHERE name = 'vector'
                """)

                # Get basic stats
                stats = await self.get_document_stats()

                return {
                    "status": "healthy",
                    "database_version": db_version,
                    "pgvector_version": vector_version,
                    "pool_size": self.pool.get_size(),
                    "stats": stats,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
