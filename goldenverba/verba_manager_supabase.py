"""
Verba Manager with Supabase Support
Extended VerbaManager that can work with both Weaviate and Supabase backends
"""

import asyncio
from copy import deepcopy
from datetime import datetime
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv
from wasabi import msg

from goldenverba.components.managers import (
    ChunkerManager,
    EmbeddingManager,
    GeneratorManager,
    ReaderManager,
    RetrieverManager,
)
from goldenverba.components.supabase_manager import SupabaseManager
from goldenverba.server.helpers import LoggerManager
from goldenverba.server.types import ChunkScore, Credentials, FileConfig

load_dotenv()


class VerbaManagerSupabase:
    """
    Enhanced Verba Manager that supports both Weaviate and Supabase backends.
    Maintains compatibility with existing Verba interface while adding Supabase support.
    """

    def __init__(self, use_supabase: bool = True):
        """
        Initialize VerbaManager with optional Supabase support.

        Args:
            use_supabase: If True, use Supabase backend; if False, use Weaviate
        """
        self.reader_manager = ReaderManager()
        self.chunker_manager = ChunkerManager()
        self.embedder_manager = EmbeddingManager()
        self.retriever_manager = RetrieverManager()
        self.generator_manager = GeneratorManager()

        # Backend selection
        self.use_supabase = use_supabase
        if use_supabase:
            self.database_manager = SupabaseManager()
        else:
            from goldenverba.components.managers import VerbaWeaviateManager

            self.database_manager = VerbaWeaviateManager()

        # Configuration UUIDs (maintain compatibility)
        self.rag_config_uuid = "e0adcc12-9bad-4588-8a1e-bab0af6ed485"
        self.theme_config_uuid = "baab38a7-cb51-4108-acd8-6edeca222820"
        self.user_config_uuid = "f53f7738-08be-4d5a-b003-13eb4bf03ac7"

        self.environment_variables = {}
        self.installed_libraries = {}

        self.verify_installed_libraries()
        self.verify_variables()

    def verify_installed_libraries(self):
        """Verify that required libraries are installed"""
        # This method maintains compatibility with original VerbaManager
        try:
            import tiktoken

            self.installed_libraries["tiktoken"] = True
        except ImportError:
            self.installed_libraries["tiktoken"] = False
            msg.warn("tiktoken not installed")

        # Add Supabase-specific library checks
        if self.use_supabase:
            try:
                import supabase
                import asyncpg
                import pgvector

                self.installed_libraries["supabase"] = True
                self.installed_libraries["asyncpg"] = True
                self.installed_libraries["pgvector"] = True
            except ImportError as e:
                msg.warn(f"Supabase dependencies not installed: {e}")
                self.installed_libraries["supabase"] = False

    def verify_variables(self):
        """Verify that required environment variables are set"""
        import os

        if self.use_supabase:
            # Supabase environment variables
            self.environment_variables["SUPABASE_URL"] = bool(os.getenv("SUPABASE_URL"))
            self.environment_variables["SUPABASE_KEY"] = bool(os.getenv("SUPABASE_KEY"))
        else:
            # Weaviate environment variables
            self.environment_variables["WEAVIATE_URL_VERBA"] = bool(
                os.getenv("WEAVIATE_URL_VERBA")
            )
            self.environment_variables["WEAVIATE_API_KEY_VERBA"] = bool(
                os.getenv("WEAVIATE_API_KEY_VERBA")
            )

    async def connect(self, credentials: Credentials):
        """
        Connect to the configured backend (Supabase or Weaviate).

        Args:
            credentials: Connection credentials

        Returns:
            Connected client or None if failed
        """
        start_time = asyncio.get_event_loop().time()

        try:
            if self.use_supabase:
                # For Supabase, we expect deployment to be "Supabase"
                client = await self.database_manager.connect(
                    credentials.deployment, credentials.url, credentials.key
                )
            else:
                # For Weaviate, use original connection logic
                client = await self.database_manager.connect(
                    credentials.deployment, credentials.url, credentials.key
                )

            if client:
                # Verify configuration collection/table exists
                if self.use_supabase:
                    # For Supabase, we just verify the connection worked
                    initialized = True
                else:
                    # For Weaviate, verify the config collection
                    initialized = await self.database_manager.verify_collection(
                        client, self.database_manager.config_collection_name
                    )

                if initialized:
                    end_time = asyncio.get_event_loop().time()
                    msg.info(f"Connection time: {end_time - start_time:.2f} seconds")
                    return client

        except Exception as e:
            msg.fail(f"Connection failed: {str(e)}")
            raise e

        return None

    async def disconnect(self, client):
        """Disconnect from the backend"""
        start_time = asyncio.get_event_loop().time()
        result = await self.database_manager.disconnect()
        end_time = asyncio.get_event_loop().time()
        msg.info(f"Disconnection time: {end_time - start_time:.2f} seconds")
        return result

    async def get_deployments(self):
        """Get available deployment configurations"""
        import os

        if self.use_supabase:
            deployments = {
                "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
                "SUPABASE_KEY": os.getenv("SUPABASE_KEY", ""),
            }
        else:
            deployments = {
                "WEAVIATE_URL_VERBA": os.getenv("WEAVIATE_URL_VERBA", ""),
                "WEAVIATE_API_KEY_VERBA": os.getenv("WEAVIATE_API_KEY_VERBA", ""),
            }
        return deployments

    async def import_document(
        self, client, fileConfig: FileConfig, logger: LoggerManager = LoggerManager()
    ):
        """
        Import document using the configured backend.

        Args:
            client: Database client
            fileConfig: File configuration
            logger: Logger for progress updates
        """
        try:
            asyncio.get_running_loop()

            # Read document
            logger.log(f"Reading document: {fileConfig.filename}")
            reader = self.reader_manager.get_reader(fileConfig.reader)
            documents = await reader.aload(fileConfig.reader_config, fileConfig)

            if not documents:
                logger.error(f"No documents loaded from {fileConfig.filename}")
                return None

            # Process each document
            processed_documents = []
            for document in documents:
                logger.log(f"Processing document: {document.title}")

                # Chunk document
                chunker = self.chunker_manager.get_chunker(fileConfig.chunker)
                chunks = await chunker.achunk(
                    fileConfig.chunker_config, document.content, logger
                )

                if not chunks:
                    logger.warn(f"No chunks created for document: {document.title}")
                    continue

                # Embed chunks
                embedder = self.embedder_manager.get_embedder(fileConfig.embedder)
                embedded_chunks = await embedder.aembed(
                    fileConfig.embedder_config, chunks, logger, client
                )

                # Update document with embedded chunks
                document.chunks = embedded_chunks
                processed_documents.append(document)

            # Import to backend
            if self.use_supabase:
                success = await self.database_manager.import_document(
                    processed_documents, logger
                )
                if success:
                    logger.log(
                        f"Successfully imported {len(processed_documents)} documents to Supabase"
                    )
                else:
                    logger.error("Failed to import documents to Supabase")
                    return None
            else:
                # Use original Weaviate import logic
                success = await self.database_manager.import_document(
                    client, processed_documents, logger
                )
                if not success:
                    logger.error("Failed to import documents to Weaviate")
                    return None

            return processed_documents

        except Exception as e:
            logger.error(f"Document import failed: {str(e)}")
            return None

    async def retrieve_chunks(
        self,
        client,
        query: str,
        retriever_config: Dict[str, Any],
        logger: LoggerManager = LoggerManager(),
    ) -> List[ChunkScore]:
        """
        Retrieve relevant chunks using the configured retriever.

        Args:
            client: Database client
            query: Search query
            retriever_config: Retriever configuration
            logger: Logger for progress updates

        Returns:
            List of scored chunks
        """
        try:
            retriever = self.retriever_manager.get_retriever(
                retriever_config.get("retriever", "WindowRetriever")
            )

            # Create retrieval config
            retrieval_config = {
                "query": query,
                "limit": retriever_config.get("limit", 10),
                "doc_filter": retriever_config.get("doc_filter"),
                "similarity_threshold": retriever_config.get(
                    "similarity_threshold", 0.0
                ),
            }

            if self.use_supabase:
                # For Supabase, we pass the manager directly
                chunks = await retriever.aretrieve(
                    retrieval_config, self.database_manager
                )
            else:
                # For Weaviate, we pass the client
                chunks = await retriever.aretrieve(retrieval_config, client)

            logger.log(f"Retrieved {len(chunks)} relevant chunks")
            return chunks

        except Exception as e:
            logger.error(f"Chunk retrieval failed: {str(e)}")
            return []

    async def generate_response(
        self,
        client,
        query: str,
        chunks: List[ChunkScore],
        generator_config: Dict[str, Any],
        logger: LoggerManager = LoggerManager(),
    ) -> str:
        """
        Generate response using the configured generator.

        Args:
            client: Database client
            query: User query
            chunks: Retrieved chunks
            generator_config: Generator configuration
            logger: Logger for progress updates

        Returns:
            Generated response
        """
        try:
            generator = self.generator_manager.get_generator(
                generator_config.get("generator", "OpenAIGenerator")
            )

            # Create generation config
            generation_config = {
                "query": query,
                "chunks": chunks,
                "model": generator_config.get("model", "gpt-3.5-turbo"),
                "temperature": generator_config.get("temperature", 0.7),
                "max_tokens": generator_config.get("max_tokens", 1000),
            }

            response = await generator.agenerate(generation_config, logger)

            logger.log("Response generated successfully")
            return response

        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return f"Error generating response: {str(e)}"

    async def get_config(
        self, client, config_type: str = "rag"
    ) -> Optional[Dict[str, Any]]:
        """
        Get configuration from the backend.

        Args:
            client: Database client
            config_type: Type of configuration to retrieve

        Returns:
            Configuration data or None
        """
        try:
            if self.use_supabase:
                return await self.database_manager.get_config(config_type)
            else:
                # Use original Weaviate config retrieval
                return await self.database_manager.get_config_by_type(
                    client, config_type
                )

        except Exception as e:
            msg.warn(f"Failed to get {config_type} config: {str(e)}")
            return None

    async def set_config(
        self, client, config_type: str, config_data: Dict[str, Any]
    ) -> bool:
        """
        Set configuration in the backend.

        Args:
            client: Database client
            config_type: Type of configuration
            config_data: Configuration data

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_supabase:
                return await self.database_manager.set_config(config_type, config_data)
            else:
                # Use original Weaviate config storage
                return await self.database_manager.set_config_by_type(
                    client, config_type, config_data
                )

        except Exception as e:
            msg.warn(f"Failed to set {config_type} config: {str(e)}")
            return False

    async def reset_rag_config(self, client):
        """Reset RAG configuration to defaults"""
        default_config = {
            "reader": "BasicReader",
            "chunker": "TokenChunker",
            "embedder": "OpenAIEmbedder",
            "retriever": "WindowRetriever",
            "generator": "OpenAIGenerator",
        }
        return await self.set_config(client, "rag", default_config)

    async def reset_theme_config(self, client):
        """Reset theme configuration to defaults"""
        default_theme = {
            "theme": "WCD",
            "title": "Verba",
            "subtitle": "The Golden RAGtriever",
        }
        return await self.set_config(client, "theme", default_theme)

    async def reset_user_config(self, client):
        """Reset user configuration to defaults"""
        default_user_config = {"suggestions": True, "analytics": False}
        return await self.set_config(client, "user", default_user_config)

    async def delete_documents(self, client, document_ids: List[str]) -> bool:
        """
        Delete documents from the backend.

        Args:
            client: Database client
            document_ids: List of document IDs to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.use_supabase:
                return await self.database_manager.delete_documents(document_ids)
            else:
                # Use original Weaviate deletion
                return await self.database_manager.delete_documents(
                    client, document_ids
                )

        except Exception as e:
            msg.warn(f"Failed to delete documents: {str(e)}")
            return False

    async def get_document_stats(self, client) -> Dict[str, Any]:
        """
        Get document statistics from the backend.

        Args:
            client: Database client

        Returns:
            Statistics dictionary
        """
        try:
            if self.use_supabase:
                return await self.database_manager.get_document_stats()
            else:
                # Use original Weaviate stats retrieval
                return await self.database_manager.get_document_stats(client)

        except Exception as e:
            msg.warn(f"Failed to get document stats: {str(e)}")
            return {}

    async def health_check(self, client) -> Dict[str, Any]:
        """
        Perform health check on the backend.

        Args:
            client: Database client

        Returns:
            Health status information
        """
        try:
            if self.use_supabase:
                return await self.database_manager.health_check()
            else:
                # Use original Weaviate health check
                return await self.database_manager.health_check(client)

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "backend": "supabase" if self.use_supabase else "weaviate",
                "timestamp": datetime.utcnow().isoformat(),
            }
