#!/usr/bin/env python3
"""
Migration tool for transferring data from Weaviate to Railway PostgreSQL.
This script helps migrate existing Verba data to the new PostgreSQL backend.
"""

import asyncio
import json
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv
from wasabi import msg

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from goldenverba.components.postgresql_manager import PostgreSQLManager
from goldenverba.components.database_schema import VerbaPostgreSQLSchema
from goldenverba.components.document import Document, Chunk
from goldenverba.server.types import Credentials

# Load environment variables
load_dotenv()


class WeaviateToPostgreSQLMigration:
    """Migration utility for moving from Weaviate to PostgreSQL."""
    
    def __init__(self, weaviate_url: str, weaviate_api_key: str, postgres_url: str):
        self.weaviate_url = weaviate_url
        self.weaviate_api_key = weaviate_api_key
        self.postgres_url = postgres_url
        self.postgresql_manager = PostgreSQLManager()
        self.batch_size = 100
        
    async def initialize_postgresql(self, vector_dimension: int = 1536) -> bool:
        """Initialize PostgreSQL database with proper schema."""
        try:
            msg.info("Initializing PostgreSQL schema...")
            success = await VerbaPostgreSQLSchema.init_database(self.postgres_url, vector_dimension)
            
            if success:
                msg.good("PostgreSQL schema initialized successfully")
                return True
            else:
                msg.fail("Failed to initialize PostgreSQL schema")
                return False
                
        except Exception as e:
            msg.fail(f"PostgreSQL initialization error: {str(e)}")
            return False
    
    async def verify_weaviate_connection(self) -> bool:
        """Verify Weaviate connection and get basic info."""
        try:
            from weaviate import WeaviateClient
            import weaviate.classes as wvc
            
            # Create Weaviate client
            if self.weaviate_api_key:
                client = WeaviateClient(
                    url=self.weaviate_url,
                    auth_credentials=wvc.auth.ApiKey(self.weaviate_api_key)
                )
            else:
                client = WeaviateClient(url=self.weaviate_url)
            
            # Test connection
            if client.is_ready():
                msg.good(f"Successfully connected to Weaviate at {self.weaviate_url}")
                
                # Get schema info
                collections = client.collections.list_all()
                msg.info(f"Found {len(collections)} collections in Weaviate")
                
                for collection_name in collections.keys():
                    collection = client.collections.get(collection_name)
                    # Try to get count (some collections might not support this)
                    try:
                        count = len(collection.query.fetch_objects().objects)
                        msg.info(f"  - {collection_name}: ~{count} objects")
                    except:
                        msg.info(f"  - {collection_name}: count unavailable")
                
                client.close()
                return True
            else:
                msg.fail("Cannot connect to Weaviate")
                return False
                
        except Exception as e:
            msg.fail(f"Weaviate connection error: {str(e)}")
            return False
    
    async def get_weaviate_data(self) -> Dict[str, List[Dict]]:
        """Extract all data from Weaviate collections."""
        try:
            from weaviate import WeaviateClient
            import weaviate.classes as wvc
            
            # Create Weaviate client
            if self.weaviate_api_key:
                client = WeaviateClient(
                    url=self.weaviate_url,
                    auth_credentials=wvc.auth.ApiKey(self.weaviate_api_key)
                )
            else:
                client = WeaviateClient(url=self.weaviate_url)
            
            if not client.is_ready():
                raise Exception("Cannot connect to Weaviate")
            
            data = {
                "configs": [],
                "documents": [],
                "chunks": [],
                "suggestions": []
            }
            
            # Get all collections
            collections = client.collections.list_all()
            
            msg.info("Extracting data from Weaviate...")
            
            for collection_name, collection_config in collections.items():
                collection = client.collections.get(collection_name)
                
                # Determine collection type
                if "config" in collection_name.lower():
                    msg.info(f"Extracting configs from {collection_name}...")
                    objects = collection.query.fetch_objects().objects
                    for obj in objects:
                        data["configs"].append({
                            "uuid": str(obj.uuid),
                            "properties": obj.properties
                        })
                
                elif "document" in collection_name.lower():
                    msg.info(f"Extracting documents from {collection_name}...")
                    objects = collection.query.fetch_objects().objects
                    for obj in objects:
                        doc_data = obj.properties.copy()
                        doc_data["uuid"] = str(obj.uuid)
                        doc_data["collection_name"] = collection_name
                        data["documents"].append(doc_data)
                
                elif "chunk" in collection_name.lower():
                    msg.info(f"Extracting chunks from {collection_name}...")
                    objects = collection.query.fetch_objects(include_vector=True).objects
                    for obj in objects:
                        chunk_data = obj.properties.copy()
                        chunk_data["uuid"] = str(obj.uuid)
                        chunk_data["vector"] = obj.vector.get("default") if obj.vector else None
                        chunk_data["collection_name"] = collection_name
                        data["chunks"].append(chunk_data)
                
                elif "suggestion" in collection_name.lower():
                    msg.info(f"Extracting suggestions from {collection_name}...")
                    objects = collection.query.fetch_objects().objects
                    for obj in objects:
                        sugg_data = obj.properties.copy()
                        sugg_data["uuid"] = str(obj.uuid)
                        data["suggestions"].append(sugg_data)
            
            client.close()
            
            msg.good(f"Extracted {len(data['configs'])} configs, {len(data['documents'])} documents, "
                    f"{len(data['chunks'])} chunks, {len(data['suggestions'])} suggestions")
            
            return data
            
        except Exception as e:
            msg.fail(f"Failed to extract Weaviate data: {str(e)}")
            raise e
    
    async def migrate_data_to_postgresql(self, data: Dict[str, List[Dict]]) -> bool:
        """Migrate extracted data to PostgreSQL."""
        try:
            # Connect to PostgreSQL
            pool = await self.postgresql_manager.connect(url=self.postgres_url)
            
            if not pool:
                msg.fail("Failed to connect to PostgreSQL")
                return False
            
            msg.info("Starting data migration to PostgreSQL...")
            
            # Migrate configurations
            await self._migrate_configs(pool, data["configs"])
            
            # Migrate documents
            await self._migrate_documents(pool, data["documents"])
            
            # Migrate chunks
            await self._migrate_chunks(pool, data["chunks"])
            
            # Migrate suggestions
            await self._migrate_suggestions(pool, data["suggestions"])
            
            await self.postgresql_manager.disconnect(pool)
            
            msg.good("Data migration completed successfully!")
            return True
            
        except Exception as e:
            msg.fail(f"Migration failed: {str(e)}")
            return False
    
    async def _migrate_configs(self, pool: asyncpg.Pool, configs: List[Dict]) -> None:
        """Migrate configuration data."""
        if not configs:
            msg.info("No configurations to migrate")
            return
        
        msg.info(f"Migrating {len(configs)} configurations...")
        
        async with pool.acquire() as conn:
            for config in configs:
                try:
                    await conn.execute("""
                        INSERT INTO verba_config (uuid, config, created_at, updated_at)
                        VALUES ($1, $2, NOW(), NOW())
                        ON CONFLICT (uuid) DO UPDATE SET
                        config = $2, updated_at = NOW();
                    """, config["uuid"], json.dumps(config["properties"]))
                
                except Exception as e:
                    msg.warn(f"Failed to migrate config {config['uuid']}: {str(e)}")
        
        msg.good(f"Migrated {len(configs)} configurations")
    
    async def _migrate_documents(self, pool: asyncpg.Pool, documents: List[Dict]) -> None:
        """Migrate document data."""
        if not documents:
            msg.info("No documents to migrate")
            return
        
        msg.info(f"Migrating {len(documents)} documents...")
        
        async with pool.acquire() as conn:
            for doc in documents:
                try:
                    # Extract embedder from collection name or properties
                    embedder = self._extract_embedder_from_collection(doc.get("collection_name", ""))
                    
                    await conn.execute("""
                        INSERT INTO verba_documents 
                        (uuid, title, content, extension, file_size, source, labels, meta, metadata, embedder, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                        ON CONFLICT (uuid) DO UPDATE SET
                        title = $2, content = $3, extension = $4, file_size = $5, 
                        source = $6, labels = $7, meta = $8, metadata = $9, embedder = $10, updated_at = NOW();
                    """,
                    doc["uuid"],
                    doc.get("title", doc.get("doc_name", "Unknown")),
                    doc.get("content", doc.get("text", "")),
                    doc.get("extension", doc.get("doc_type", "")),
                    doc.get("file_size", doc.get("fileSize", 0)),
                    doc.get("source", doc.get("doc_link", "")),
                    doc.get("labels", []),
                    json.dumps(doc.get("meta", {})),
                    json.dumps(doc.get("metadata", {})),
                    embedder
                    )
                
                except Exception as e:
                    msg.warn(f"Failed to migrate document {doc['uuid']}: {str(e)}")
        
        msg.good(f"Migrated {len(documents)} documents")
    
    async def _migrate_chunks(self, pool: asyncpg.Pool, chunks: List[Dict]) -> None:
        """Migrate chunk data."""
        if not chunks:
            msg.info("No chunks to migrate")
            return
        
        msg.info(f"Migrating {len(chunks)} chunks...")
        
        async with pool.acquire() as conn:
            for chunk in chunks:
                try:
                    # Extract embedder from collection name
                    embedder = self._extract_embedder_from_collection(chunk.get("collection_name", ""))
                    
                    await conn.execute("""
                        INSERT INTO verba_chunks 
                        (uuid, document_uuid, content, content_without_overlap, chunk_id, chunk_index, vector, embedder, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
                        ON CONFLICT (uuid) DO UPDATE SET
                        document_uuid = $2, content = $3, content_without_overlap = $4, 
                        chunk_id = $5, chunk_index = $6, vector = $7, embedder = $8;
                    """,
                    chunk["uuid"],
                    chunk.get("doc_uuid", chunk.get("document_uuid")),
                    chunk.get("content", chunk.get("text", "")),
                    chunk.get("content_without_overlap", chunk.get("content", chunk.get("text", ""))),
                    chunk.get("chunk_id", 0),
                    chunk.get("chunk_index", 0),
                    chunk.get("vector"),
                    embedder
                    )
                
                except Exception as e:
                    msg.warn(f"Failed to migrate chunk {chunk['uuid']}: {str(e)}")
        
        msg.good(f"Migrated {len(chunks)} chunks")
    
    async def _migrate_suggestions(self, pool: asyncpg.Pool, suggestions: List[Dict]) -> None:
        """Migrate suggestion data."""
        if not suggestions:
            msg.info("No suggestions to migrate")
            return
        
        msg.info(f"Migrating {len(suggestions)} suggestions...")
        
        async with pool.acquire() as conn:
            for sugg in suggestions:
                try:
                    await conn.execute("""
                        INSERT INTO verba_suggestions (uuid, query, count, created_at, updated_at)
                        VALUES ($1, $2, $3, NOW(), NOW())
                        ON CONFLICT (query) DO UPDATE SET
                        count = $3, updated_at = NOW();
                    """,
                    sugg["uuid"],
                    sugg.get("query", ""),
                    sugg.get("count", 1)
                    )
                
                except Exception as e:
                    msg.warn(f"Failed to migrate suggestion {sugg['uuid']}: {str(e)}")
        
        msg.good(f"Migrated {len(suggestions)} suggestions")
    
    def _extract_embedder_from_collection(self, collection_name: str) -> str:
        """Extract embedder name from Weaviate collection name."""
        # Weaviate collections typically follow pattern: VERBA_Document_EmbedderName or VERBA_Chunk_EmbedderName
        if "_" in collection_name:
            parts = collection_name.split("_")
            if len(parts) >= 3:
                return parts[-1]  # Last part is usually the embedder name
        
        return "OpenAIEmbedder"  # Default fallback
    
    async def backup_weaviate_data(self, backup_file: str) -> bool:
        """Create a backup of Weaviate data to JSON file."""
        try:
            data = await self.get_weaviate_data()
            
            backup_path = Path(backup_file)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            msg.good(f"Backup saved to {backup_file}")
            return True
            
        except Exception as e:
            msg.fail(f"Backup failed: {str(e)}")
            return False
    
    async def restore_from_backup(self, backup_file: str) -> bool:
        """Restore data from JSON backup file."""
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                msg.fail(f"Backup file not found: {backup_file}")
                return False
            
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            return await self.migrate_data_to_postgresql(data)
            
        except Exception as e:
            msg.fail(f"Restore failed: {str(e)}")
            return False


async def main():
    """Main CLI function for migration tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate Verba data from Weaviate to Railway PostgreSQL")
    parser.add_argument("--weaviate-url", required=True, help="Weaviate URL")
    parser.add_argument("--weaviate-key", help="Weaviate API key")
    parser.add_argument("--postgres-url", required=True, help="PostgreSQL connection URL")
    parser.add_argument("--vector-dim", type=int, default=1536, help="Vector dimension (default: 1536)")
    parser.add_argument("--backup-only", action="store_true", help="Only create backup, don't migrate")
    parser.add_argument("--backup-file", default="weaviate_backup.json", help="Backup file path")
    parser.add_argument("--restore-from-backup", help="Restore from backup file instead of Weaviate")
    parser.add_argument("--init-only", action="store_true", help="Only initialize PostgreSQL schema")
    
    args = parser.parse_args()
    
    migration = WeaviateToPostgreSQLMigration(
        args.weaviate_url,
        args.weaviate_key,
        args.postgres_url
    )
    
    try:
        # Initialize PostgreSQL schema
        if not await migration.initialize_postgresql(args.vector_dim):
            return 1
        
        if args.init_only:
            msg.good("PostgreSQL schema initialization completed")
            return 0
        
        # Restore from backup
        if args.restore_from_backup:
            success = await migration.restore_from_backup(args.restore_from_backup)
            return 0 if success else 1
        
        # Verify Weaviate connection
        if not await migration.verify_weaviate_connection():
            return 1
        
        # Create backup
        if args.backup_only:
            success = await migration.backup_weaviate_data(args.backup_file)
            return 0 if success else 1
        
        # Full migration
        msg.info("Starting full migration process...")
        
        # Create backup first
        await migration.backup_weaviate_data(args.backup_file)
        
        # Extract and migrate data
        data = await migration.get_weaviate_data()
        success = await migration.migrate_data_to_postgresql(data)
        
        if success:
            msg.good("Migration completed successfully!")
            msg.info(f"Backup saved to: {args.backup_file}")
            return 0
        else:
            msg.fail("Migration failed")
            return 1
    
    except KeyboardInterrupt:
        msg.warn("Migration interrupted by user")
        return 1
    except Exception as e:
        msg.fail(f"Migration error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))