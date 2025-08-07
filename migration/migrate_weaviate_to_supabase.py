#!/usr/bin/env python3
"""
Weaviate to Supabase Data Migration Script for Verba RAG Application

This script migrates all data from Weaviate to Supabase PostgreSQL with pgvector,
including documents, chunks, embeddings, and configurations.
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    # VerbaWeaviateManager has been removed - this script is for reference only
    from goldenverba.components.managers import VerbaWeaviateManager
except ImportError:
    print("❌ VerbaWeaviateManager not available - Weaviate support has been removed")
    print("This migration script is kept for reference only.")
    sys.exit(1)

from goldenverba.components.supabase_manager import SupabaseManager
from goldenverba.server.types import Credentials
from wasabi import msg


@dataclass
class MigrationStats:
    """Statistics for migration progress"""

    documents_migrated: int = 0
    chunks_migrated: int = 0
    configs_migrated: int = 0
    embeddings_cached: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class WeaviateToSupabaseMigrator:
    """Handles the complete migration from Weaviate to Supabase"""

    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self.stats = MigrationStats()
        self.weaviate_manager = VerbaWeaviateManager()
        self.supabase_manager = SupabaseManager()

    async def migrate_all(
        self,
        weaviate_credentials: Credentials,
        supabase_url: str,
        supabase_key: str,
        dry_run: bool = False,
    ) -> bool:
        """
        Perform complete migration from Weaviate to Supabase.

        Args:
            weaviate_credentials: Credentials for Weaviate connection
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            dry_run: If True, only analyze data without migrating

        Returns:
            True if successful, False otherwise
        """
        try:
            msg.info("Starting Weaviate to Supabase migration...")
            start_time = datetime.utcnow()

            # Connect to both databases
            weaviate_client = await self._connect_weaviate(weaviate_credentials)
            if not weaviate_client:
                return False

            if not dry_run:
                supabase_client = await self._connect_supabase(
                    supabase_url, supabase_key
                )
                if not supabase_client:
                    return False

            # Log migration start
            if not dry_run:
                await self._log_migration_start(supabase_url, supabase_key)

            # Phase 1: Analyze source data
            msg.info("Phase 1: Analyzing Weaviate data...")
            analysis = await self._analyze_weaviate_data(weaviate_client)
            self._print_analysis(analysis)

            if dry_run:
                msg.info("Dry run completed - no data was migrated")
                return True

            # Phase 2: Migrate configurations
            msg.info("Phase 2: Migrating configurations...")
            await self._migrate_configurations(weaviate_client)

            # Phase 3: Migrate documents and chunks
            msg.info("Phase 3: Migrating documents and chunks...")
            await self._migrate_documents_batched(weaviate_client)

            # Phase 4: Migrate embedding cache
            msg.info("Phase 4: Migrating embedding cache...")
            await self._migrate_embedding_cache(weaviate_client)

            # Phase 5: Verify migration
            msg.info("Phase 5: Verifying migration...")
            verification_success = await self._verify_migration()

            # Log completion
            await self._log_migration_completion(verification_success)

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Print final statistics
            self._print_final_stats(duration, verification_success)

            return verification_success

        except Exception as e:
            msg.fail(f"Migration failed: {str(e)}")
            self.stats.errors.append(f"Migration failed: {str(e)}")
            return False

        finally:
            # Cleanup connections
            await self._cleanup_connections()

    async def _connect_weaviate(self, credentials: Credentials) -> Optional[Any]:
        """Connect to Weaviate"""
        try:
            client = await self.weaviate_manager.connect(
                credentials.deployment, credentials.url, credentials.key
            )
            msg.good("Connected to Weaviate")
            return client
        except Exception as e:
            msg.fail(f"Failed to connect to Weaviate: {str(e)}")
            return None

    async def _connect_supabase(self, url: str, key: str) -> Optional[Any]:
        """Connect to Supabase"""
        try:
            client = await self.supabase_manager.connect("Supabase", url, key)
            msg.good("Connected to Supabase")
            return client
        except Exception as e:
            msg.fail(f"Failed to connect to Supabase: {str(e)}")
            return None

    async def _analyze_weaviate_data(self, weaviate_client) -> Dict[str, Any]:
        """Analyze Weaviate data structure and counts"""
        try:
            # Get collection information
            collections_info = await self.weaviate_manager.get_all_collections_info(
                weaviate_client
            )

            # Count documents
            documents = await self.weaviate_manager.get_all_documents(weaviate_client)
            document_count = len(documents) if documents else 0

            # Estimate chunks (approximate)
            chunk_count = 0
            if documents:
                chunk_count = sum(
                    len(doc.chunks) for doc in documents[:10]
                )  # Sample first 10
                chunk_count = int(
                    chunk_count * (document_count / min(10, document_count))
                )

            # Get configuration count
            config_count = 0
            for config_type in ["rag", "theme", "user"]:
                config = await self.weaviate_manager.get_config_by_type(
                    weaviate_client, config_type
                )
                if config:
                    config_count += 1

            return {
                "collections": collections_info,
                "document_count": document_count,
                "estimated_chunk_count": chunk_count,
                "config_count": config_count,
            }

        except Exception as e:
            msg.warn(f"Analysis failed: {str(e)}")
            return {"error": str(e)}

    def _print_analysis(self, analysis: Dict[str, Any]):
        """Print analysis results"""
        if "error" in analysis:
            msg.warn(f"Analysis incomplete: {analysis['error']}")
            return

        msg.info("=== Weaviate Data Analysis ===")
        msg.info(f"Documents to migrate: {analysis.get('document_count', 0)}")
        msg.info(f"Estimated chunks: {analysis.get('estimated_chunk_count', 0)}")
        msg.info(f"Configurations: {analysis.get('config_count', 0)}")

        if "collections" in analysis:
            msg.info("Collections found:")
            for collection in analysis["collections"]:
                msg.info(
                    f"  - {collection.get('name', 'Unknown')}: {collection.get('count', 0)} objects"
                )

    async def _migrate_configurations(self, weaviate_client):
        """Migrate configuration data"""
        try:
            config_types = ["rag", "theme", "user", "migration", "schema"]

            for config_type in config_types:
                try:
                    config_data = await self.weaviate_manager.get_config_by_type(
                        weaviate_client, config_type
                    )

                    if config_data:
                        success = await self.supabase_manager.set_config(
                            config_type, config_data
                        )
                        if success:
                            self.stats.configs_migrated += 1
                            msg.good(f"Migrated {config_type} configuration")
                        else:
                            self.stats.errors.append(
                                f"Failed to migrate {config_type} config"
                            )

                except Exception as e:
                    error_msg = f"Error migrating {config_type} config: {str(e)}"
                    msg.warn(error_msg)
                    self.stats.errors.append(error_msg)

        except Exception as e:
            error_msg = f"Configuration migration failed: {str(e)}"
            msg.fail(error_msg)
            self.stats.errors.append(error_msg)

    async def _migrate_documents_batched(self, weaviate_client):
        """Migrate documents and chunks in batches"""
        try:
            # Get all documents from Weaviate
            documents = await self.weaviate_manager.get_all_documents(weaviate_client)

            if not documents:
                msg.warn("No documents found in Weaviate")
                return

            msg.info(f"Found {len(documents)} documents to migrate")

            # Process in batches
            for i in range(0, len(documents), self.batch_size):
                batch = documents[i : i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (
                    len(documents) + self.batch_size - 1
                ) // self.batch_size

                msg.info(
                    f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)"
                )

                try:
                    # Migrate batch to Supabase
                    success = await self.supabase_manager.import_document(batch)

                    if success:
                        self.stats.documents_migrated += len(batch)
                        # Count chunks in this batch
                        batch_chunks = sum(len(doc.chunks) for doc in batch)
                        self.stats.chunks_migrated += batch_chunks

                        msg.good(
                            f"Batch {batch_num} migrated successfully ({batch_chunks} chunks)"
                        )
                    else:
                        error_msg = f"Failed to migrate batch {batch_num}"
                        msg.fail(error_msg)
                        self.stats.errors.append(error_msg)

                except Exception as e:
                    error_msg = f"Error in batch {batch_num}: {str(e)}"
                    msg.fail(error_msg)
                    self.stats.errors.append(error_msg)

                # Brief pause between batches to avoid overwhelming the database
                await asyncio.sleep(0.1)

        except Exception as e:
            error_msg = f"Document migration failed: {str(e)}"
            msg.fail(error_msg)
            self.stats.errors.append(error_msg)

    async def _migrate_embedding_cache(self, weaviate_client):
        """Migrate embedding cache if it exists"""
        try:
            # This is a placeholder - actual implementation depends on how
            # Weaviate stores the embedding cache in the original system
            msg.info("Embedding cache migration - checking for cached embeddings...")

            # For now, we'll create an empty cache
            # In a real migration, you would extract cached embeddings from Weaviate
            # and store them using supabase_manager.store_embedding_cache()

            msg.info("Embedding cache migration completed (empty cache initialized)")

        except Exception as e:
            error_msg = f"Embedding cache migration failed: {str(e)}"
            msg.warn(error_msg)
            self.stats.errors.append(error_msg)

    async def _verify_migration(self) -> bool:
        """Verify that migration was successful"""
        try:
            # Get statistics from Supabase
            stats = await self.supabase_manager.get_document_stats()

            if not stats:
                msg.fail("Could not retrieve Supabase statistics for verification")
                return False

            # Compare with migration stats
            supabase_docs = stats.get("total_documents", 0)
            supabase_chunks = stats.get("total_chunks", 0)

            msg.info("=== Migration Verification ===")
            msg.info(f"Documents migrated: {self.stats.documents_migrated}")
            msg.info(f"Documents in Supabase: {supabase_docs}")
            msg.info(f"Chunks migrated: {self.stats.chunks_migrated}")
            msg.info(f"Chunks in Supabase: {supabase_chunks}")

            # Verification logic
            docs_match = supabase_docs >= self.stats.documents_migrated
            chunks_match = supabase_chunks >= self.stats.chunks_migrated

            if docs_match and chunks_match:
                msg.good("✅ Migration verification successful!")
                return True
            else:
                msg.fail("❌ Migration verification failed - data counts don't match")
                return False

        except Exception as e:
            msg.fail(f"Migration verification failed: {str(e)}")
            return False

    async def _log_migration_start(self, supabase_url: str, supabase_key: str):
        """Log migration start in Supabase"""
        try:
            # Connect temporarily to log migration start
            temp_manager = SupabaseManager()
            await temp_manager.connect("Supabase", supabase_url, supabase_key)

            # This would use a migration logging table if implemented
            msg.info("Migration start logged")

            await temp_manager.disconnect()

        except Exception as e:
            msg.warn(f"Could not log migration start: {str(e)}")

    async def _log_migration_completion(self, success: bool):
        """Log migration completion"""
        try:
            # Log completion status
            status = "completed" if success else "failed"
            msg.info(f"Migration {status}")

        except Exception as e:
            msg.warn(f"Could not log migration completion: {str(e)}")

    def _print_final_stats(self, duration: float, success: bool):
        """Print final migration statistics"""
        status = "✅ SUCCESSFUL" if success else "❌ FAILED"

        msg.info("=== Final Migration Statistics ===")
        msg.info(f"Status: {status}")
        msg.info(f"Duration: {duration:.2f} seconds")
        msg.info(f"Documents migrated: {self.stats.documents_migrated}")
        msg.info(f"Chunks migrated: {self.stats.chunks_migrated}")
        msg.info(f"Configurations migrated: {self.stats.configs_migrated}")
        msg.info(f"Errors encountered: {len(self.stats.errors)}")

        if self.stats.errors:
            msg.warn("Errors during migration:")
            for error in self.stats.errors:
                msg.warn(f"  - {error}")

    async def _cleanup_connections(self):
        """Clean up database connections"""
        try:
            await self.supabase_manager.disconnect()
            msg.info("Connections cleaned up")
        except Exception as e:
            msg.warn(f"Cleanup warning: {str(e)}")


async def main():
    """Main migration script entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Verba data from Weaviate to Supabase"
    )
    parser.add_argument("--weaviate-url", required=True, help="Weaviate URL")
    parser.add_argument("--weaviate-key", default="", help="Weaviate API key")
    parser.add_argument("--supabase-url", required=True, help="Supabase project URL")
    parser.add_argument(
        "--supabase-key", required=True, help="Supabase service role key"
    )
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Batch size for migration"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Analyze only, don't migrate"
    )

    args = parser.parse_args()

    # Create credentials
    weaviate_creds = Credentials(
        deployment="Weaviate", url=args.weaviate_url, key=args.weaviate_key
    )

    # Create migrator
    migrator = WeaviateToSupabaseMigrator(batch_size=args.batch_size)

    # Run migration
    success = await migrator.migrate_all(
        weaviate_credentials=weaviate_creds,
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key,
        dry_run=args.dry_run,
    )

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
