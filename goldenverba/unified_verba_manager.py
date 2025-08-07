"""
Unified Verba Manager with Pure PostgreSQL Support
Consolidated manager that handles all RAG operations with PostgreSQL + pgvector
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import asyncpg
from dotenv import load_dotenv
from wasabi import msg
from pgvector.asyncpg import register_vector

from goldenverba.components.document import Document
from goldenverba.components.managers import (
    ChunkerManager,
    EmbeddingManager,
    GeneratorManager,
    ReaderManager,
    RetrieverManager,
)
from goldenverba.server.helpers import LoggerManager
from goldenverba.server.types import (
    ChunkScore,
    Credentials,
    FileConfig,
    FileStatus,
)

load_dotenv()


class VerbaManager:
    """
    Unified Verba Manager with pure PostgreSQL backend.
    Handles all RAG operations using PostgreSQL with pgvector extension.
    """

    def __init__(self) -> None:
        """Initialize VerbaManager with PostgreSQL support."""
        self.reader_manager = ReaderManager()
        self.chunker_manager = ChunkerManager()
        self.embedder_manager = EmbeddingManager()
        self.retriever_manager = RetrieverManager()
        self.generator_manager = GeneratorManager()

        # PostgreSQL connection pool
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url: Optional[str] = None

        # Configuration UUIDs (maintain compatibility)
        self.rag_config_uuid = "e0adcc12-9bad-4588-8a1e-bab0af6ed485"
        self.theme_config_uuid = "baab38a7-cb51-4108-acd8-6edeca222820"
        self.user_config_uuid = "f53f7738-08be-4d5a-b003-13eb4bf03ac7"

        self.environment_variables = {}
        self.installed_libraries = {}

        self.verify_installed_libraries()
        self.verify_variables()

    def verify_installed_libraries(self) -> None:
        """Verify that required libraries are installed"""
        # Core libraries
        try:
            import fastapi
            self.installed_libraries["fastapi"] = True
        except ImportError:
            self.installed_libraries["fastapi"] = False

        try:
            import uvicorn
            self.installed_libraries["uvicorn"] = True
        except ImportError:
            self.installed_libraries["uvicorn"] = False

        # PostgreSQL libraries
        try:
            import asyncpg
            import pgvector
            self.installed_libraries["asyncpg"] = True
            self.installed_libraries["pgvector"] = True
        except ImportError as e:
            msg.warn(f"PostgreSQL dependencies not installed: {e}")
            self.installed_libraries["asyncpg"] = False
            self.installed_libraries["pgvector"] = False

    def verify_variables(self) -> None:
        """Verify that required environment variables are set"""
        # PostgreSQL environment variables
        self.environment_variables["DATABASE_URL"] = bool(os.getenv("DATABASE_URL"))
        self.environment_variables["POSTGRES_HOST"] = bool(os.getenv("POSTGRES_HOST"))
        self.environment_variables["POSTGRES_PASSWORD"] = bool(os.getenv("POSTGRES_PASSWORD"))

    async def connect(self, credentials: Credentials) -> Optional[asyncpg.Pool]:
        """
        Connect to PostgreSQL database.

        Args:
            credentials: Connection credentials

        Returns:
            Connection pool or None if failed
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Determine database URL
            if credentials.url and credentials.url.strip():
                self.database_url = credentials.url
            else:
                self.database_url = (
                    os.getenv("DATABASE_URL") or 
                    os.getenv("RAILWAY_POSTGRES_URL") or
                    self._build_database_url()
                )

            if not self.database_url:
                raise Exception("No database URL provided")

            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=20,
                command_timeout=300,
                server_settings={"application_name": "verba-rag", "jit": "off"},
            )

            # Initialize database schema and pgvector
            async with self.pool.acquire() as conn:
                await register_vector(conn)
                await self._ensure_schema(conn)

            end_time = asyncio.get_event_loop().time()
            msg.info(f"PostgreSQL connection time: {end_time - start_time:.2f} seconds")
            return self.pool

        except Exception as e:
            msg.fail(f"PostgreSQL connection failed: {str(e)}")
            raise e

    def _build_database_url(self) -> Optional[str]:
        """Build database URL from individual environment variables."""
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "verba")
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")

        if host and user and password:
            return f"postgresql://{user}:{password}@{host}:{port}/{db}"
        return None

    async def _ensure_schema(self, conn: asyncpg.Connection):
        """Ensure all required tables and functions exist."""
        try:
            # Create extensions
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

            # Create tables
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

        -- Chunks table with vector embeddings
        CREATE TABLE IF NOT EXISTS chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
            content TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB DEFAULT '{}',
            chunk_index INTEGER,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- Configurations table
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

        -- Query suggestions table
        CREATE TABLE IF NOT EXISTS query_suggestions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            query TEXT UNIQUE NOT NULL,
            frequency INTEGER DEFAULT 1,
            last_used TIMESTAMPTZ DEFAULT NOW(),
            created_at TIMESTAMPTZ DEFAULT NOW()
        );

        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops);
        CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
        CREATE INDEX IF NOT EXISTS idx_documents_name ON documents(name);
        CREATE INDEX IF NOT EXISTS idx_configurations_type_active ON configurations(config_type, is_active);
        """

            await conn.execute(schema_sql)
            msg.good("PostgreSQL schema initialized successfully")

        except Exception as e:
            msg.warn(f"Schema initialization warning: {str(e)}")
            # Continue anyway - basic tables might still work

    async def disconnect(self, pool: Optional[asyncpg.Pool] = None) -> None:
        """Disconnect from PostgreSQL database."""
        start_time = asyncio.get_event_loop().time()
        
        if pool or self.pool:
            target_pool = pool or self.pool
            await target_pool.close()
            if target_pool == self.pool:
                self.pool = None
        
        end_time = asyncio.get_event_loop().time()
        msg.info(f"PostgreSQL disconnection time: {end_time - start_time:.2f} seconds")

    async def get_deployments(self) -> Dict[str, Any]:
        """Get available PostgreSQL deployment configurations"""
        deployments = {
            "DATABASE_URL": os.getenv("DATABASE_URL", ""),
            "POSTGRES_HOST": os.getenv("POSTGRES_HOST", ""),
            "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
        }
        return deployments

    async def health_check(self, pool: Optional[asyncpg.Pool] = None) -> Dict[str, Any]:
        """Perform health check on PostgreSQL connection."""
        try:
            target_pool = pool or self.pool
            if not target_pool:
                return {
                    "status": "unhealthy",
                    "error": "No database connection",
                    "backend": "postgresql",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            async with target_pool.acquire() as conn:
                # Test basic query
                result = await conn.fetchval("SELECT 1")
                
                # Test pgvector extension
                await conn.fetchval("SELECT vector_dims('[1,2,3]'::vector)")

            return {
                "status": "healthy",
                "backend": "postgresql",
                "timestamp": datetime.utcnow().isoformat(),
                "database_url": self.database_url[:50] + "..." if self.database_url else "unknown"
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "backend": "postgresql",
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_document_stats(self, pool: Optional[asyncpg.Pool] = None) -> Dict[str, Any]:
        """Get document statistics from PostgreSQL."""
        try:
            target_pool = pool or self.pool
            if not target_pool:
                return {}

            async with target_pool.acquire() as conn:
                # Get document count
                doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
                
                # Get chunk count
                chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks")
                
                # Get vector dimensions (if any chunks exist)
                vector_dims = None
                if chunk_count > 0:
                    vector_dims = await conn.fetchval(
                        "SELECT vector_dims(embedding) FROM chunks WHERE embedding IS NOT NULL LIMIT 1"
                    )

            return {
                "total_documents": doc_count,
                "total_chunks": chunk_count,
                "vector_dimensions": vector_dims,
            }

        except Exception as e:
            msg.warn(f"Failed to get document stats: {str(e)}")
            return {}


class ClientManager:
    """PostgreSQL Client Manager for connection pooling."""

    def __init__(self) -> None:
        self.pools: Dict[str, Dict] = {}
        self.manager: VerbaManager = VerbaManager()
        self.max_time: int = 30  # 30 minutes
        self.last_cleanup: datetime = datetime.now()
        self.cleanup_interval: int = 5  # 5 minutes

    def hash_credentials(self, credentials: Credentials) -> str:
        """Create hash for credential caching."""
        return f"{credentials.deployment}:{credentials.url}:{credentials.key}"

    async def connect(self, credentials: Credentials) -> asyncpg.Pool:
        """Connect to PostgreSQL with connection pooling."""
        cred_hash = self.hash_credentials(credentials)
        
        if cred_hash in self.pools:
            msg.info("Found existing PostgreSQL connection pool")
            return self.pools[cred_hash]["pool"]
        else:
            msg.good("Creating new PostgreSQL connection pool")
            try:
                pool = await self.manager.connect(credentials)
                self.pools[cred_hash] = {
                    "pool": pool,
                    "timestamp": datetime.now(),
                }
                return pool
            except Exception as e:
                raise e

    async def disconnect(self):
        """Disconnect all PostgreSQL pools."""
        msg.warn("Disconnecting PostgreSQL pools!")
        for cred_hash, pool_data in self.pools.items():
            await self.manager.disconnect(pool_data["pool"])
        self.pools.clear()
