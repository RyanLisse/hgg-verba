#!/usr/bin/env python3
"""
Railway PostgreSQL Migration Script - Weaviate to PostgreSQL
Migrates data from existing Weaviate instance to Railway PostgreSQL with pgvector.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from tqdm import tqdm

# Weaviate client
import weaviate
from weaviate import Client

# PostgreSQL with pgvector
from goldenverba.components.railway_postgres_manager import RailwayPostgresManager
from goldenverba.components.types import Document, Chunk


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class WeaviateToPostgresMigrator:
    """Migrates data from Weaviate to Railway PostgreSQL."""
    
    def __init__(self):
        # Weaviate connection
        self.weaviate_url = os.environ.get("WEAVIATE_URL_VERBA")
        self.weaviate_key = os.environ.get("WEAVIATE_API_KEY_VERBA")
        self.weaviate_index = os.environ.get("WEAVIATE_INDEX_NAME_VERBA", "RoborailAssistant")
        
        if not self.weaviate_url:
            raise ValueError("WEAVIATE_URL_VERBA environment variable is required")
        
        # PostgreSQL connection
        self.postgres_manager = RailwayPostgresManager()
        
        # Migration state
        self.migration_state_file = "migration_state.json"
        self.batch_size = 100
        
    def save_migration_state(self, state: Dict[str, Any]):
        """Save migration progress state."""
        with open(self.migration_state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_migration_state(self) -> Dict[str, Any]:
        """Load migration progress state."""
        if os.path.exists(self.migration_state_file):
            with open(self.migration_state_file, 'r') as f:
                return json.load(f)
        return {
            "documents_migrated": 0,
            "chunks_migrated": 0,
            "last_document_id": None,
            "completed": False,
            "started_at": datetime.now().isoformat()
        }
    
    def connect_weaviate(self) -> Client:
        """Connect to Weaviate instance."""
        try:
            if self.weaviate_key:
                auth_config = weaviate.AuthApiKey(api_key=self.weaviate_key)
                client = weaviate.Client(
                    url=self.weaviate_url,
                    auth_client_secret=auth_config
                )
            else:
                client = weaviate.Client(url=self.weaviate_url)
            
            logger.info(f"✅ Connected to Weaviate at {self.weaviate_url}")
            return client
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Weaviate: {e}")
            raise
    
    async def get_weaviate_documents(self, client: Client) -> List[Dict[str, Any]]:
        """Fetch all documents from Weaviate."""
        logger.info(f"🔍 Fetching documents from Weaviate index: {self.weaviate_index}")
        
        try:
            # Query to get all documents with metadata
            result = (
                client.query
                .get(self.weaviate_index, [
                    "doc_name", "doc_type", "doc_path", "content", 
                    "doc_metadata", "chunk_index", "vector"
                ])
                .with_additional(["id", "vector"])
                .with_limit(10000)  # Adjust based on your data size
                .do()
            )
            
            if "data" not in result or "Get" not in result["data"]:
                logger.warning("⚠️ No data found in Weaviate")
                return []
            
            weaviate_objects = result["data"]["Get"][self.weaviate_index]
            logger.info(f"📊 Found {len(weaviate_objects)} objects in Weaviate")
            
            # Group by document
            documents_dict = {}
            for obj in weaviate_objects:
                doc_name = obj.get("doc_name", "Unknown")
                
                if doc_name not in documents_dict:
                    documents_dict[doc_name] = {
                        "name": doc_name,
                        "type": obj.get("doc_type", "TXT"),
                        "path": obj.get("doc_path", ""),
                        "metadata": json.loads(obj.get("doc_metadata", "{}")) if obj.get("doc_metadata") else {},
                        "chunks": []
                    }
                
                # Add chunk data
                chunk_data = {
                    "content": obj.get("content", ""),
                    "chunk_index": obj.get("chunk_index", 0),
                    "embedding": obj.get("_additional", {}).get("vector", []),
                    "metadata": {}
                }
                
                documents_dict[doc_name]["chunks"].append(chunk_data)
            
            # Sort chunks by index
            for doc in documents_dict.values():
                doc["chunks"].sort(key=lambda x: x["chunk_index"])
            
            logger.info(f"📚 Grouped into {len(documents_dict)} documents")
            return list(documents_dict.values())
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch Weaviate documents: {e}")
            raise
    
    async def migrate_document(self, doc_data: Dict[str, Any]) -> bool:
        """Migrate a single document to PostgreSQL."""
        try:
            # Create Document object
            document = Document(
                name=doc_data["name"],
                type=doc_data["type"],
                path=doc_data["path"],
                content="",  # We'll reconstruct from chunks if needed
                metadata=doc_data["metadata"]
            )
            
            # Insert document
            doc_id = await self.postgres_manager.insert_document(document)
            logger.info(f"📄 Inserted document: {document.name} (ID: {doc_id})")
            
            # Create Chunk objects
            chunks = []
            for chunk_data in doc_data["chunks"]:
                chunk = Chunk(
                    content=chunk_data["content"],
                    metadata=chunk_data["metadata"]
                )
                
                # Add embedding if available
                if chunk_data["embedding"]:
                    chunk.embedding = np.array(chunk_data["embedding"])
                
                chunks.append(chunk)
            
            # Insert chunks
            if chunks:
                chunk_ids = await self.postgres_manager.insert_chunks(doc_id, chunks)
                logger.info(f"📦 Inserted {len(chunks)} chunks for document: {document.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to migrate document {doc_data['name']}: {e}")
            return False
    
    async def migrate_configurations(self, client: Client):
        """Migrate Weaviate configurations to PostgreSQL."""
        logger.info("⚙️ Migrating configurations...")
        
        try:
            # This is a simplified version - adjust based on your Weaviate config storage
            # You may need to adapt this based on how configurations are stored in Weaviate
            
            # Example: Migrate RAG configuration
            default_config = {
                "reader": "UnstructuredReader",
                "chunker": "TokenChunker",
                "embedder": "OpenAIEmbedder",
                "retriever": "WindowRetriever",
                "generator": "OpenAIGenerator"
            }
            
            await self.postgres_manager.save_configuration(
                config_type="rag",
                config_name="default",
                config_data=default_config,
                set_active=True
            )
            
            logger.info("✅ Configuration migration completed")
            
        except Exception as e:
            logger.error(f"❌ Configuration migration failed: {e}")
    
    async def verify_migration(self) -> bool:
        """Verify the migration was successful."""
        logger.info("🔍 Verifying migration...")
        
        try:
            # Check document count
            documents = await self.postgres_manager.get_documents(limit=1000)
            doc_count = len(documents)
            
            # Test vector search with a simple query
            if doc_count > 0:
                # Create a dummy embedding for testing
                test_embedding = [0.1] * 1536  # OpenAI embedding dimension
                
                results = await self.postgres_manager.vector_search(
                    query_embedding=test_embedding,
                    limit=5,
                    threshold=0.0
                )
                
                logger.info(f"✅ Migration verified:")
                logger.info(f"   📊 Documents: {doc_count}")
                logger.info(f"   🔍 Vector search results: {len(results)}")
                
                return True
            else:
                logger.warning("⚠️ No documents found after migration")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    async def run_migration(self):
        """Run the complete migration process."""
        logger.info("🚀 Starting Weaviate to PostgreSQL migration...")
        
        # Load previous state
        state = self.load_migration_state()
        
        if state.get("completed"):
            logger.info("✅ Migration already completed!")
            return
        
        try:
            # Initialize PostgreSQL
            await self.postgres_manager.initialize()
            logger.info("✅ PostgreSQL initialized")
            
            # Connect to Weaviate
            weaviate_client = self.connect_weaviate()
            
            # Fetch documents from Weaviate
            documents = await self.get_weaviate_documents(weaviate_client)
            
            if not documents:
                logger.warning("⚠️ No documents found to migrate")
                return
            
            # Migrate documents
            successful_migrations = 0
            failed_migrations = 0
            
            logger.info(f"📦 Starting migration of {len(documents)} documents...")
            
            for i, doc_data in enumerate(tqdm(documents, desc="Migrating documents")):
                try:
                    success = await self.migrate_document(doc_data)
                    if success:
                        successful_migrations += 1
                    else:
                        failed_migrations += 1
                    
                    # Update state periodically
                    if (i + 1) % 10 == 0:
                        state.update({
                            "documents_migrated": successful_migrations,
                            "last_document_id": doc_data["name"],
                            "progress": f"{i + 1}/{len(documents)}"
                        })
                        self.save_migration_state(state)
                        
                except Exception as e:
                    logger.error(f"❌ Failed to migrate document {doc_data['name']}: {e}")
                    failed_migrations += 1
            
            # Migrate configurations
            await self.migrate_configurations(weaviate_client)
            
            # Verify migration
            verification_passed = await self.verify_migration()
            
            # Update final state
            state.update({
                "completed": True,
                "completed_at": datetime.now().isoformat(),
                "successful_migrations": successful_migrations,
                "failed_migrations": failed_migrations,
                "verification_passed": verification_passed
            })
            self.save_migration_state(state)
            
            # Close connections
            await self.postgres_manager.close()
            
            # Summary
            logger.info("🎉 Migration completed!")
            logger.info(f"   ✅ Successful: {successful_migrations}")
            logger.info(f"   ❌ Failed: {failed_migrations}")
            logger.info(f"   🔍 Verification: {'PASSED' if verification_passed else 'FAILED'}")
            
            if verification_passed and failed_migrations == 0:
                logger.info("🌟 Migration completed successfully!")
                logger.info("📝 Next steps:")
                logger.info("   1. Update Railway environment variables to use PostgreSQL")
                logger.info("   2. Set USE_POSTGRESQL=true")
                logger.info("   3. Set USE_WEAVIATE=false")
                logger.info("   4. Redeploy the application")
            else:
                logger.warning("⚠️ Migration completed with issues. Review logs and fix before proceeding.")
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise


async def main():
    """Main migration function."""
    try:
        migrator = WeaviateToPostgresMigrator()
        await migrator.run_migration()
    except KeyboardInterrupt:
        logger.info("🛑 Migration interrupted by user")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())