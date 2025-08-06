"""Supabase manager for Verba - handles all database operations with pgvector."""

import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import numpy as np
from datetime import datetime, timedelta

from supabase import create_client, Client
from supabase.client import AsyncClient
from postgrest import AsyncPostgrestClient
import asyncpg
from pgvector.asyncpg import register_vector

from goldenverba.components.types import Document, Chunk
from goldenverba.components.managers import Manager


class SupabaseManager:
    """Manages all Supabase operations including vector search with pgvector."""
    
    def __init__(self, url: str = None, key: str = None):
        """Initialize Supabase client.
        
        Args:
            url: Supabase project URL
            key: Supabase anon/service key
        """
        self.url = url or os.environ.get("SUPABASE_URL")
        self.key = key or os.environ.get("SUPABASE_KEY")
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required")
        
        # Sync client for simple operations
        self.client: Client = create_client(self.url, self.key)
        
        # Async connection pool for vector operations
        self.pool: Optional[asyncpg.Pool] = None
        self.db_url = self._get_db_url()
        
    def _get_db_url(self) -> str:
        """Extract database URL from Supabase URL."""
        # Supabase URLs follow pattern: https://[project-ref].supabase.co
        # DB connection: postgresql://postgres.[project-ref]:password@aws-0-[region].pooler.supabase.com:5432/postgres
        
        db_host = os.environ.get("SUPABASE_DB_HOST")
        db_password = os.environ.get("SUPABASE_DB_PASSWORD", self.key)
        db_name = os.environ.get("SUPABASE_DB_NAME", "postgres")
        db_port = os.environ.get("SUPABASE_DB_PORT", "5432")
        
        if not db_host:
            # Extract from Supabase URL
            import re
            match = re.search(r'https://([^.]+)\.supabase\.co', self.url)
            if match:
                project_ref = match.group(1)
                db_host = f"aws-0-us-west-1.pooler.supabase.com"  # Default, should be configured
                
        return f"postgresql://postgres.{project_ref}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    async def initialize(self):
        """Initialize async connection pool."""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            
            # Register pgvector type
            async with self.pool.acquire() as conn:
                await register_vector(conn)
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def insert_document(self, document: Document) -> str:
        """Insert a document into the database.
        
        Args:
            document: Document object to insert
            
        Returns:
            Document ID
        """
        doc_id = str(uuid4())
        
        data = {
            "id": doc_id,
            "name": document.name,
            "type": document.type.upper(),
            "path": document.path,
            "content": document.content[:1000000] if document.content else None,  # Limit content size
            "metadata": document.metadata or {},
            "file_size": len(document.content) if document.content else 0,
            "status": "PENDING"
        }
        
        response = self.client.table("documents").insert(data).execute()
        return doc_id
    
    async def insert_chunks(self, document_id: str, chunks: List[Chunk]) -> List[str]:
        """Insert document chunks with embeddings.
        
        Args:
            document_id: Parent document ID
            chunks: List of chunk objects with embeddings
            
        Returns:
            List of chunk IDs
        """
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
                """, chunk_id, document_id, i, chunk.content, json.dumps(chunk.metadata or {}), embedding)
                
                chunk_ids.append(chunk_id)
        
        # Update document status and chunk count
        self.client.table("documents").update({
            "status": "COMPLETED",
            "total_chunks": len(chunks)
        }).eq("id", document_id).execute()
        
        return chunk_ids
    
    async def vector_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        filter_metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search.
        
        Args:
            query_embedding: Query vector
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching chunks with similarity scores
        """
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
        """Perform hybrid search combining vector and text search.
        
        Args:
            query_text: Text query
            query_embedding: Query vector
            limit: Maximum number of results
            alpha: Weight for vector search (0-1)
            
        Returns:
            List of matching chunks with combined scores
        """
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
        """Retrieve documents from database.
        
        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of documents
        """
        query = self.client.table("documents").select("*")
        
        if status:
            query = query.eq("status", status)
        
        query = query.order("created_at", desc=True)
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        return response.data
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Success status
        """
        try:
            self.client.table("documents").delete().eq("id", document_id).execute()
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
        """Save configuration to database.
        
        Args:
            config_type: Type of configuration (e.g., 'rag', 'theme')
            config_name: Name of configuration
            config_data: Configuration data
            set_active: Whether to set as active configuration
            
        Returns:
            Configuration ID
        """
        config_id = str(uuid4())
        
        # Deactivate other configs of same type if setting active
        if set_active:
            self.client.table("configurations").update({
                "is_active": False
            }).eq("config_type", config_type).execute()
        
        data = {
            "id": config_id,
            "config_type": config_type,
            "config_name": config_name,
            "config_data": config_data,
            "is_active": set_active
        }
        
        self.client.table("configurations").upsert(data).execute()
        return config_id
    
    async def get_configuration(
        self,
        config_type: str,
        config_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve configuration from database.
        
        Args:
            config_type: Type of configuration
            config_name: Optional specific configuration name
            
        Returns:
            Configuration data or None
        """
        query = self.client.table("configurations").select("*").eq("config_type", config_type)
        
        if config_name:
            query = query.eq("config_name", config_name)
        else:
            query = query.eq("is_active", True)
        
        response = query.execute()
        
        if response.data:
            return response.data[0]["config_data"]
        return None
    
    async def add_to_cache(
        self,
        query: str,
        query_embedding: List[float],
        response: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add entry to semantic cache.
        
        Args:
            query: Query text
            query_embedding: Query vector
            response: Cached response
            metadata: Optional metadata
            
        Returns:
            Cache entry ID
        """
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
        """Search semantic cache for similar queries.
        
        Args:
            query_embedding: Query vector
            threshold: Similarity threshold for cache hit
            
        Returns:
            Cached response if found, None otherwise
        """
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
    
    async def add_suggestion(self, query: str) -> None:
        """Add or update query suggestion.
        
        Args:
            query: Query text to add to suggestions
        """
        # Check if query exists
        existing = self.client.table("query_suggestions").select("*").eq("query", query).execute()
        
        if existing.data:
            # Update frequency and last used
            self.client.table("query_suggestions").update({
                "frequency": existing.data[0]["frequency"] + 1,
                "last_used": datetime.now().isoformat()
            }).eq("query", query).execute()
        else:
            # Insert new suggestion
            self.client.table("query_suggestions").insert({
                "query": query,
                "frequency": 1
            }).execute()
    
    async def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Get query suggestions based on prefix.
        
        Args:
            prefix: Query prefix
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested queries
        """
        response = self.client.table("query_suggestions").select("query").ilike("query", f"{prefix}%").order("frequency", desc=True).limit(limit).execute()
        
        return [row["query"] for row in response.data]