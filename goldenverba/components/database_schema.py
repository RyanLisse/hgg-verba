"""
PostgreSQL Schema definitions and migration utilities for Verba RAG application.
This module provides schema management for Railway PostgreSQL with pgvector extension.
"""

import asyncio
import asyncpg
from typing import Optional
from wasabi import msg


class VerbaPostgreSQLSchema:
    """Database schema manager for Verba PostgreSQL implementation."""
    
    @staticmethod
    async def create_schema(connection: asyncpg.Connection, vector_dimension: int = 1536):
        """Create the complete database schema with pgvector extension."""
        
        try:
            # Enable pgvector extension
            await connection.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            msg.good("pgvector extension enabled")
            
            # Create config table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS verba_config (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    config JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create documents table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS verba_documents (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    title TEXT NOT NULL,
                    content TEXT,
                    extension TEXT,
                    file_size BIGINT,
                    source TEXT,
                    labels TEXT[] DEFAULT '{}',
                    meta JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}',
                    embedder TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create chunks table with dynamic vector dimension
            await connection.execute(f"""
                CREATE TABLE IF NOT EXISTS verba_chunks (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    document_uuid UUID NOT NULL REFERENCES verba_documents(uuid) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    content_without_overlap TEXT,
                    chunk_id INTEGER NOT NULL,
                    chunk_index INTEGER DEFAULT 0,
                    vector vector({vector_dimension}),
                    embedder TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    
                    -- Ensure chunk_id is unique per document
                    UNIQUE(document_uuid, chunk_id)
                );
            """)
            
            # Create suggestions table
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS verba_suggestions (
                    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    query TEXT NOT NULL UNIQUE,
                    count INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            msg.good("Database tables created successfully")
            
        except Exception as e:
            msg.fail(f"Failed to create schema: {str(e)}")
            raise e
    
    @staticmethod
    async def create_indexes(connection: asyncpg.Connection):
        """Create performance indexes for the database."""
        
        indexes = [
            # Vector similarity search index (HNSW for better performance)
            ("idx_chunks_vector_hnsw", "verba_chunks", "vector vector_cosine_ops", "hnsw"),
            
            # Regular B-tree indexes
            ("idx_chunks_document_uuid", "verba_chunks", "document_uuid", "btree"),
            ("idx_chunks_embedder", "verba_chunks", "embedder", "btree"),
            ("idx_chunks_chunk_id", "verba_chunks", "chunk_id", "btree"),
            ("idx_documents_title", "verba_documents", "title", "btree"),
            ("idx_documents_embedder", "verba_documents", "embedder", "btree"),
            ("idx_documents_labels", "verba_documents", "labels", "gin"),
            ("idx_suggestions_query", "verba_suggestions", "query", "btree"),
            ("idx_suggestions_count", "verba_suggestions", "count DESC", "btree"),
            ("idx_config_uuid", "verba_config", "uuid", "btree"),
            
            # Composite indexes for common queries
            ("idx_chunks_doc_embedder", "verba_chunks", "(document_uuid, embedder)", "btree"),
            ("idx_documents_embedder_created", "verba_documents", "(embedder, created_at DESC)", "btree"),
        ]
        
        for index_name, table_name, columns, index_type in indexes:
            try:
                if index_type == "hnsw":
                    # HNSW index for vector similarity
                    await connection.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} USING hnsw ({columns})
                        WITH (m = 16, ef_construction = 64);
                    """)
                elif index_type == "gin":
                    # GIN index for array operations
                    await connection.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} USING gin ({columns});
                    """)
                else:
                    # Regular B-tree index
                    await connection.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON {table_name} USING btree ({columns});
                    """)
                
                msg.good(f"Created index: {index_name}")
                
            except Exception as e:
                msg.warn(f"Failed to create index {index_name}: {str(e)}")
    
    @staticmethod
    async def create_functions(connection: asyncpg.Connection):
        """Create useful PostgreSQL functions for Verba operations."""
        
        # Function to update the updated_at timestamp
        await connection.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        # Triggers for automatic updated_at updates
        triggers = [
            ("verba_config", "config_updated_at"),
            ("verba_documents", "documents_updated_at"),
            ("verba_suggestions", "suggestions_updated_at"),
        ]
        
        for table_name, trigger_name in triggers:
            await connection.execute(f"""
                DROP TRIGGER IF EXISTS {trigger_name} ON {table_name};
                CREATE TRIGGER {trigger_name}
                    BEFORE UPDATE ON {table_name}
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
            """)
        
        # Function for cosine similarity search with metadata
        await connection.execute("""
            CREATE OR REPLACE FUNCTION similarity_search(
                search_vector vector,
                search_embedder text,
                search_limit integer DEFAULT 10,
                filter_labels text[] DEFAULT NULL,
                filter_doc_uuids uuid[] DEFAULT NULL
            )
            RETURNS TABLE (
                chunk_uuid uuid,
                chunk_content text,
                chunk_id integer,
                doc_uuid uuid,
                doc_title text,
                similarity_score float
            ) AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    c.uuid,
                    c.content,
                    c.chunk_id,
                    d.uuid,
                    d.title,
                    1.0 - (c.vector <=> search_vector) as score
                FROM verba_chunks c
                JOIN verba_documents d ON c.document_uuid = d.uuid
                WHERE c.embedder = search_embedder
                    AND c.vector IS NOT NULL
                    AND (filter_labels IS NULL OR d.labels && filter_labels)
                    AND (filter_doc_uuids IS NULL OR d.uuid = ANY(filter_doc_uuids))
                ORDER BY c.vector <=> search_vector
                LIMIT search_limit;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        msg.good("Database functions and triggers created")
    
    @staticmethod
    async def verify_schema(connection: asyncpg.Connection) -> dict:
        """Verify schema integrity and return status."""
        
        status = {
            "pgvector_enabled": False,
            "tables_exist": {},
            "indexes_exist": {},
            "functions_exist": {},
            "vector_dimension": None
        }
        
        try:
            # Check pgvector extension
            result = await connection.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'vector'
                );
            """)
            status["pgvector_enabled"] = result
            
            # Check tables
            tables = ["verba_config", "verba_documents", "verba_chunks", "verba_suggestions"]
            for table in tables:
                exists = await connection.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = $1
                    );
                """, table)
                status["tables_exist"][table] = exists
            
            # Check vector dimension
            if status["tables_exist"]["verba_chunks"]:
                dim_result = await connection.fetchval("""
                    SELECT atttypmod FROM pg_attribute 
                    WHERE attrelid = 'verba_chunks'::regclass 
                    AND attname = 'vector';
                """)
                if dim_result and dim_result > 0:
                    status["vector_dimension"] = dim_result
            
            # Check key indexes
            key_indexes = ["idx_chunks_vector_hnsw", "idx_chunks_document_uuid", "idx_documents_title"]
            for index in key_indexes:
                exists = await connection.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_indexes WHERE indexname = $1
                    );
                """, index)
                status["indexes_exist"][index] = exists
            
            # Check functions
            functions = ["similarity_search", "update_updated_at_column"]
            for func in functions:
                exists = await connection.fetchval("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_proc WHERE proname = $1
                    );
                """, func)
                status["functions_exist"][func] = exists
            
        except Exception as e:
            msg.fail(f"Schema verification failed: {str(e)}")
            status["error"] = str(e)
        
        return status
    
    @staticmethod
    async def init_database(database_url: str, vector_dimension: int = 1536) -> bool:
        """Initialize complete database schema with all components."""
        
        try:
            # Connect to database
            conn = await asyncpg.connect(database_url)
            
            msg.info("Initializing Verba PostgreSQL schema...")
            
            # Create schema
            await VerbaPostgreSQLSchema.create_schema(conn, vector_dimension)
            
            # Create indexes
            await VerbaPostgreSQLSchema.create_indexes(conn)
            
            # Create functions and triggers
            await VerbaPostgreSQLSchema.create_functions(conn)
            
            # Verify everything was created
            status = await VerbaPostgreSQLSchema.verify_schema(conn)
            
            await conn.close()
            
            if all(status["tables_exist"].values()) and status["pgvector_enabled"]:
                msg.good("Database schema initialized successfully")
                return True
            else:
                msg.fail("Schema initialization incomplete")
                return False
                
        except Exception as e:
            msg.fail(f"Database initialization failed: {str(e)}")
            return False