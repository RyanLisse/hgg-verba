import os
import importlib
import math
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import asyncpg
from copy import deepcopy

from dotenv import load_dotenv
from wasabi import msg

from goldenverba.server.helpers import LoggerManager
from goldenverba.components.document import Document
from goldenverba.components.postgresql_manager import PostgreSQLManager
from goldenverba.server.types import (
    FileConfig,
    FileStatus,
    ChunkScore,
    Credentials,
)

from goldenverba.components.managers import (
    ReaderManager,
    ChunkerManager,
    EmbeddingManager,
    RetrieverManager,
    GeneratorManager,
)

load_dotenv()


class PostgreSQLVerbaManager:
    """PostgreSQL-based Verba Manager for Railway deployment."""

    def __init__(self) -> None:
        self.reader_manager = ReaderManager()
        self.chunker_manager = ChunkerManager()
        self.embedder_manager = EmbeddingManager()
        self.retriever_manager = RetrieverManager()
        self.generator_manager = GeneratorManager()
        self.postgresql_manager = PostgreSQLManager()
        self.rag_config_uuid = "e0adcc12-9bad-4588-8a1e-bab0af6ed485"
        self.theme_config_uuid = "baab38a7-cb51-4108-acd8-6edeca222820"
        self.user_config_uuid = "f53f7738-08be-4d5a-b003-13eb4bf03ac7"
        self.environment_variables = {}
        self.installed_libraries = {}

        self.verify_installed_libraries()
        self.verify_variables()

    async def connect(self, credentials: Credentials):
        """Connect to Railway PostgreSQL database."""
        start_time = asyncio.get_event_loop().time()
        try:
            pool = await self.postgresql_manager.connect(
                credentials.deployment, credentials.url, credentials.key
            )
        except Exception as e:
            raise e
        if pool:
            initialized = await self.postgresql_manager.verify_collection(
                pool, self.postgresql_manager.config_collection_name
            )
            if initialized:
                end_time = asyncio.get_event_loop().time()
                msg.info(f"Connection time: {end_time - start_time:.2f} seconds")
                return pool

    async def disconnect(self, pool):
        """Disconnect from PostgreSQL database."""
        start_time = asyncio.get_event_loop().time()
        result = await self.postgresql_manager.disconnect(pool)
        end_time = asyncio.get_event_loop().time()
        msg.info(f"Disconnection time: {end_time - start_time:.2f} seconds")
        return result

    async def get_deployments(self):
        """Get PostgreSQL deployment information."""
        deployments = {
            "RAILWAY_POSTGRES_URL": (
                os.getenv("RAILWAY_POSTGRES_URL")
                if os.getenv("RAILWAY_POSTGRES_URL")
                else ""
            ),
            "DATABASE_URL": (
                os.getenv("DATABASE_URL")
                if os.getenv("DATABASE_URL")
                else ""
            ),
            "RAILWAY_POSTGRES_HOST": (
                os.getenv("RAILWAY_POSTGRES_HOST")
                if os.getenv("RAILWAY_POSTGRES_HOST")
                else ""
            ),
        }
        return deployments

    # Import methods (adapted for PostgreSQL)
    async def import_document(
        self, pool, file_config: FileConfig, logger: LoggerManager = LoggerManager()
    ):
        """Import document into PostgreSQL database."""
        try:
            loop = asyncio.get_running_loop()
            start_time = loop.time()

            duplicate_uuid = await self.postgresql_manager.exist_document_name(
                pool, file_config.filename
            )
            if duplicate_uuid is not None and not file_config.overwrite:
                raise Exception(f"{file_config.filename} already exists in Verba")
            elif duplicate_uuid is not None and file_config.overwrite:
                await self.postgresql_manager.delete_document(pool, duplicate_uuid)
                await logger.send_report(
                    file_config.fileID,
                    status=FileStatus.STARTING,
                    message=f"Overwriting {file_config.filename}",
                    took=0,
                )
            else:
                await logger.send_report(
                    file_config.fileID,
                    status=FileStatus.STARTING,
                    message="Starting Import",
                    took=0,
                )

            documents = await self.reader_manager.load(
                file_config.rag_config["Reader"].selected, file_config, logger
            )

            tasks = [
                self.process_single_document(pool, doc, file_config, logger)
                for doc in documents
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            successful_tasks = sum(
                1 for result in results if not isinstance(result, Exception)
            )

            if successful_tasks > 1:
                await logger.send_report(
                    file_config.fileID,
                    status=FileStatus.INGESTING,
                    message=f"Imported {file_config.filename} and its {successful_tasks} documents into PostgreSQL",
                    took=round(loop.time() - start_time, 2),
                )
            elif successful_tasks == 1:
                await logger.send_report(
                    file_config.fileID,
                    status=FileStatus.INGESTING,
                    message=f"Imported {file_config.filename} and {len(documents[0].chunks)} chunks into PostgreSQL",
                    took=round(loop.time() - start_time, 2),
                )
            elif (
                successful_tasks == 0
                and len(results) == 1
                and isinstance(results[0], Exception)
            ):
                msg.fail(
                    f"No documents imported {successful_tasks} of {len(results)} successful tasks"
                )
                raise results[0]
            else:
                raise Exception(
                    f"No documents imported {successful_tasks} of {len(results)} successful tasks"
                )

            await logger.send_report(
                file_config.fileID,
                status=FileStatus.DONE,
                message=f"Import for {file_config.filename} completed successfully",
                took=round(loop.time() - start_time, 2),
            )

        except Exception as e:
            await logger.send_report(
                file_config.fileID,
                status=FileStatus.ERROR,
                message=f"Import for {file_config.filename} failed: {str(e)}",
                took=0,
            )
            return

    async def process_single_document(
        self,
        pool,
        document: Document,
        file_config: FileConfig,
        logger: LoggerManager,
    ):
        """Process a single document for PostgreSQL storage."""
        loop = asyncio.get_running_loop()
        start_time = loop.time()

        if file_config.isURL:
            current_file_config = deepcopy(file_config)
            current_file_config.fileID = file_config.fileID + document.title
            current_file_config.isURL = False
            current_file_config.filename = document.title
            await logger.create_new_document(
                file_config.fileID + document.title,
                document.title,
                file_config.fileID,
            )
        else:
            current_file_config = file_config

        try:
            duplicate_uuid = await self.postgresql_manager.exist_document_name(
                pool, document.title
            )
            if duplicate_uuid is not None and not current_file_config.overwrite:
                raise Exception(f"{document.title} already exists in Verba")
            elif duplicate_uuid is not None and current_file_config.overwrite:
                await self.postgresql_manager.delete_document(pool, duplicate_uuid)

            chunk_task = asyncio.create_task(
                self.chunker_manager.chunk(
                    current_file_config.rag_config["Chunker"].selected,
                    current_file_config,
                    [document],
                    self.embedder_manager.embedders[
                        current_file_config.rag_config["Embedder"].selected
                    ],
                    logger,
                )
            )
            chunked_documents = await chunk_task

            embedding_task = asyncio.create_task(
                self.embedder_manager.vectorize(
                    current_file_config.rag_config["Embedder"].selected,
                    current_file_config,
                    chunked_documents,
                    logger,
                )
            )
            vectorized_documents = await embedding_task

            for document in vectorized_documents:
                ingesting_task = asyncio.create_task(
                    self.postgresql_manager.import_document(
                        pool,
                        document,
                        current_file_config.rag_config["Embedder"]
                        .components[file_config.rag_config["Embedder"].selected]
                        .config["Model"]
                        .value,
                    )
                )
                await ingesting_task

            await logger.send_report(
                current_file_config.fileID,
                status=FileStatus.INGESTING,
                message=f"Imported {current_file_config.filename} into PostgreSQL",
                took=round(loop.time() - start_time, 2),
            )

            await logger.send_report(
                current_file_config.fileID,
                status=FileStatus.DONE,
                message=f"Import for {current_file_config.filename} completed successfully",
                took=round(loop.time() - start_time, 2),
            )
        except Exception as e:
            await logger.send_report(
                current_file_config.fileID,
                status=FileStatus.ERROR,
                message=f"Import for {file_config.filename} failed: {str(e)}",
                took=round(loop.time() - start_time, 2),
            )
            raise Exception(f"Import for {file_config.filename} failed: {str(e)}")

    # Configuration methods (same as original but using PostgreSQL)
    def create_config(self) -> dict:
        """Creates the RAG Configuration."""
        available_environments = self.environment_variables
        available_libraries = self.installed_libraries

        readers = self.reader_manager.readers
        reader_config = {
            "components": {
                reader: readers[reader].get_meta(
                    available_environments, available_libraries
                )
                for reader in readers
            },
            "selected": list(readers.values())[0].name,
        }

        chunkers = self.chunker_manager.chunkers
        chunkers_config = {
            "components": {
                chunker: chunkers[chunker].get_meta(
                    available_environments, available_libraries
                )
                for chunker in chunkers
            },
            "selected": list(chunkers.values())[0].name,
        }

        embedders = self.embedder_manager.embedders
        embedder_config = {
            "components": {
                embedder: embedders[embedder].get_meta(
                    available_environments, available_libraries
                )
                for embedder in embedders
            },
            "selected": "OpenAIEmbedder" if "OpenAIEmbedder" in [e.name for e in embedders.values()] else list(embedders.values())[0].name,
        }

        retrievers = self.retriever_manager.retrievers
        retrievers_config = {
            "components": {
                retriever: retrievers[retriever].get_meta(
                    available_environments, available_libraries
                )
                for retriever in retrievers
            },
            "selected": list(retrievers.values())[0].name,
        }

        generators = self.generator_manager.generators
        generator_config = {
            "components": {
                generator: generators[generator].get_meta(
                    available_environments, available_libraries
                )
                for generator in generators
            },
            "selected": "OpenAIGenerator" if "OpenAIGenerator" in [g.name for g in generators.values()] else list(generators.values())[0].name,
        }

        return {
            "Reader": reader_config,
            "Chunker": chunkers_config,
            "Embedder": embedder_config,
            "Retriever": retrievers_config,
            "Generator": generator_config,
        }

    def create_user_config(self) -> dict:
        """Create user configuration."""
        return {"getting_started": False}

    async def set_theme_config(self, pool, config: dict):
        """Set theme configuration."""
        await self.postgresql_manager.set_config(pool, self.theme_config_uuid, config)

    async def set_rag_config(self, pool, config: dict):
        """Set RAG configuration."""
        await self.postgresql_manager.set_config(pool, self.rag_config_uuid, config)

    async def set_user_config(self, pool, config: dict):
        """Set user configuration."""
        await self.postgresql_manager.set_config(pool, self.user_config_uuid, config)

    async def load_rag_config(self, pool):
        """Load RAG configuration from PostgreSQL."""
        loaded_config = await self.postgresql_manager.get_config(
            pool, self.rag_config_uuid
        )
        new_config = self.create_config()
        if loaded_config is not None:
            if self.verify_config(loaded_config, new_config):
                msg.info("Using Existing RAG Configuration")
                return loaded_config
            else:
                msg.info("Using New RAG Configuration")
                await self.set_rag_config(pool, new_config)
                return new_config
        else:
            msg.info("Using New RAG Configuration")
            return new_config

    async def load_theme_config(self, pool):
        """Load theme configuration."""
        loaded_config = await self.postgresql_manager.get_config(
            pool, self.theme_config_uuid
        )

        if loaded_config is None:
            return None, None

        return loaded_config["theme"], loaded_config["themes"]

    async def load_user_config(self, pool):
        """Load user configuration."""
        loaded_config = await self.postgresql_manager.get_config(
            pool, self.user_config_uuid
        )

        if loaded_config is None:
            return self.create_user_config()

        return loaded_config

    def verify_config(self, a: dict, b: dict) -> bool:
        """Verify configuration compatibility."""
        try:
            if os.getenv("VERBA_PRODUCTION") == "Demo":
                return True
            for a_component_key, b_component_key in zip(a, b):
                if a_component_key != b_component_key:
                    msg.fail(
                        f"Config Validation Failed, component name mismatch: {a_component_key} != {b_component_key}"
                    )
                    return False

                a_component = a[a_component_key]["components"]
                b_component = b[b_component_key]["components"]

                if len(a_component) != len(b_component):
                    msg.fail(
                        f"Config Validation Failed, {a_component_key} component count mismatch: {len(a_component)} != {len(b_component)}"
                    )
                    return False

                for a_rag_component_key, b_rag_component_key in zip(
                    a_component, b_component
                ):
                    if a_rag_component_key != b_rag_component_key:
                        msg.fail(
                            f"Config Validation Failed, component name mismatch: {a_rag_component_key} != {b_rag_component_key}"
                        )
                        return False
                    a_rag_component = a_component[a_rag_component_key]
                    b_rag_component = b_component[b_rag_component_key]

                    a_config = a_rag_component["config"]
                    b_config = b_rag_component["config"]

                    if len(a_config) != len(b_config):
                        msg.fail(
                            f"Config Validation Failed, component config count mismatch: {len(a_config)} != {len(b_config)}"
                        )
                        return False

                    for a_config_key, b_config_key in zip(a_config, b_config):
                        if a_config_key != b_config_key:
                            msg.fail(
                                f"Config Validation Failed, component name mismatch: {a_config_key} != {b_config_key}"
                            )
                            return False

                        a_setting = a_config[a_config_key]
                        b_setting = b_config[b_config_key]

                        if a_setting["description"] != b_setting["description"]:
                            msg.fail(
                                f"Config Validation Failed, description mismatch: {a_setting['description']} != {b_setting['description']}"
                            )
                            return False

                        if sorted(a_setting["values"]) != sorted(b_setting["values"]):
                            msg.fail(
                                f"Config Validation Failed, values mismatch: {a_setting['values']} != {b_setting['values']}"
                            )
                            return False

            return True

        except Exception as e:
            msg.fail(f"Config Validation failed: {str(e)}")
            return False

    async def reset_rag_config(self, pool):
        """Reset RAG configuration."""
        msg.info("Resetting RAG Configuration")
        await self.postgresql_manager.reset_config(pool, self.rag_config_uuid)

    async def reset_theme_config(self, pool):
        """Reset theme configuration."""
        msg.info("Resetting Theme Configuration")
        await self.postgresql_manager.reset_config(pool, self.theme_config_uuid)

    async def reset_user_config(self, pool):
        """Reset user configuration."""
        msg.info("Resetting User Configuration")
        await self.postgresql_manager.reset_config(pool, self.user_config_uuid)

    # Library and environment verification (same as original)
    def verify_installed_libraries(self) -> None:
        """Check which libraries are installed."""
        reader = [
            lib
            for reader in self.reader_manager.readers
            for lib in self.reader_manager.readers[reader].requires_library
        ]
        chunker = [
            lib
            for chunker in self.chunker_manager.chunkers
            for lib in self.chunker_manager.chunkers[chunker].requires_library
        ]
        embedder = [
            lib
            for embedder in self.embedder_manager.embedders
            for lib in self.embedder_manager.embedders[embedder].requires_library
        ]
        retriever = [
            lib
            for retriever in self.retriever_manager.retrievers
            for lib in self.retriever_manager.retrievers[retriever].requires_library
        ]
        generator = [
            lib
            for generator in self.generator_manager.generators
            for lib in self.generator_manager.generators[generator].requires_library
        ]

        required_libraries = reader + chunker + embedder + retriever + generator
        unique_libraries = set(required_libraries)

        for lib in unique_libraries:
            try:
                importlib.import_module(lib)
                self.installed_libraries[lib] = True
            except Exception:
                self.installed_libraries[lib] = False

    def verify_variables(self) -> None:
        """Check which environment variables are available."""
        reader = [
            lib
            for reader in self.reader_manager.readers
            for lib in self.reader_manager.readers[reader].requires_env
        ]
        chunker = [
            lib
            for chunker in self.chunker_manager.chunkers
            for lib in self.chunker_manager.chunkers[chunker].requires_env
        ]
        embedder = [
            lib
            for embedder in self.embedder_manager.embedders
            for lib in self.embedder_manager.embedders[embedder].requires_env
        ]
        retriever = [
            lib
            for retriever in self.retriever_manager.retrievers
            for lib in self.retriever_manager.retrievers[retriever].requires_env
        ]
        generator = [
            lib
            for generator in self.generator_manager.generators
            for lib in self.generator_manager.generators[generator].requires_env
        ]

        required_envs = reader + chunker + embedder + retriever + generator
        unique_envs = set(required_envs)

        for env in unique_envs:
            if os.environ.get(env) is not None:
                self.environment_variables[env] = True
            else:
                self.environment_variables[env] = False

    # RAG operations
    async def retrieve_chunks(
        self,
        pool,
        query: str,
        rag_config: dict,
        labels: list[str] = None,
        document_uuids: list[str] = None,
    ):
        """Retrieve chunks using PostgreSQL vector search."""
        if labels is None:
            labels = []
        if document_uuids is None:
            document_uuids = []

        embedder = rag_config["Embedder"].selected

        await self.postgresql_manager.add_suggestion(pool, query)

        vector = await self.embedder_manager.vectorize_query(
            embedder, query, rag_config
        )

        # Get retriever config
        retriever_config = rag_config["Retriever"]
        limit = retriever_config.components[retriever_config.selected].config.get("Chunk Limit", {}).value or 10

        chunk_scores = await self.postgresql_manager.similarity_search(
            pool, vector, embedder, limit, labels, document_uuids
        )

        # Convert to expected format
        documents = []
        context = ""
        
        for chunk_score in chunk_scores:
            documents.append({
                "uuid": chunk_score.uuid,
                "score": chunk_score.score,
                "chunk_id": chunk_score.chunk_id,
                "doc_uuid": chunk_score.doc_uuid,
                "doc_name": chunk_score.doc_name,
                "embedder": chunk_score.embedder
            })
            context += f"Document: {chunk_score.doc_name}\n{chunk_score.uuid}\n\n"

        return (documents, context)

    async def generate_stream_answer(
        self,
        rag_config: dict,
        query: str,
        context: str,
        conversation: list[dict],
    ):
        """Generate streaming answer using configured generator."""
        full_text = ""
        async for result in self.generator_manager.generate_stream(
            rag_config, query, context, conversation
        ):
            full_text += result["message"]
            yield result

    # Content retrieval (adapted for PostgreSQL)
    async def get_content(
        self,
        pool,
        uuid: str,
        page: int,
        chunk_scores: list[ChunkScore],
    ):
        """Get content from PostgreSQL database."""
        chunks_per_page = 10
        content_pieces = []
        total_batches = 0

        # Return Chunks with surrounding context
        if len(chunk_scores) > 0:
            if page > len(chunk_scores):
                page = 0

            total_batches = len(chunk_scores)
            chunk = await self.postgresql_manager.get_chunk(
                pool, chunk_scores[page].uuid, chunk_scores[page].embedder
            )

            before_ids = [
                i
                for i in range(
                    max(0, chunk_scores[page].chunk_id - int(chunks_per_page / 2)),
                    chunk_scores[page].chunk_id,
                )
            ]
            if before_ids:
                chunks_before_chunk = await self.postgresql_manager.get_chunk_by_ids(
                    pool,
                    chunk_scores[page].embedder,
                    uuid,
                    ids=[
                        i
                        for i in range(
                            max(
                                0, chunk_scores[page].chunk_id - int(chunks_per_page / 2)
                            ),
                            chunk_scores[page].chunk_id,
                        )
                    ],
                )
                before_content = "".join(
                    [
                        chunk["properties"]["content_without_overlap"]
                        for chunk in chunks_before_chunk
                    ]
                )
            else:
                before_content = ""

            after_ids = [
                i
                for i in range(
                    chunk_scores[page].chunk_id + 1,
                    chunk_scores[page].chunk_id + int(chunks_per_page / 2),
                )
            ]
            if after_ids:
                chunks_after_chunk = await self.postgresql_manager.get_chunk_by_ids(
                    pool,
                    chunk_scores[page].embedder,
                    uuid,
                    ids=[
                        i
                        for i in range(
                            chunk_scores[page].chunk_id + 1,
                            chunk_scores[page].chunk_id + int(chunks_per_page / 2),
                        )
                    ],
                )
                after_content = "".join(
                    [
                        chunk["properties"]["content_without_overlap"]
                        for chunk in chunks_after_chunk
                    ]
                )
            else:
                after_content = ""

            content_pieces.append(
                {
                    "content": before_content,
                    "chunk_id": 0,
                    "score": 0,
                    "type": "text",
                }
            )
            content_pieces.append(
                {
                    "content": chunk["content_without_overlap"],
                    "chunk_id": chunk_scores[page].chunk_id,
                    "score": chunk_scores[page].score,
                    "type": "extract",
                }
            )
            content_pieces.append(
                {
                    "content": after_content,
                    "chunk_id": 0,
                    "score": 0,
                    "type": "text",
                }
            )

        # Return Content based on Page
        else:
            document = await self.postgresql_manager.get_document(
                pool, uuid, properties=["meta"]
            )
            config = json.loads(document["meta"])
            embedder = config["Embedder"]["config"]["Model"]["value"]
            request_chunk_ids = [
                i
                for i in range(
                    chunks_per_page * (page + 1) - chunks_per_page,
                    chunks_per_page * (page + 1),
                )
            ]

            chunks = await self.postgresql_manager.get_chunk_by_ids(
                pool, embedder, uuid, request_chunk_ids
            )

            total_chunks = await self.postgresql_manager.get_chunk_count(
                pool, embedder, uuid
            )
            total_batches = int(math.ceil(total_chunks / chunks_per_page))

            content = "".join(
                [chunk["properties"]["content_without_overlap"] for chunk in chunks]
            )

            content_pieces.append(
                {
                    "content": content,
                    "chunk_id": 0,
                    "score": 0,
                    "type": "text",
                }
            )

        return (content_pieces, total_batches)


class PostgreSQLClientManager:
    """PostgreSQL Client Manager for connection pooling."""
    def __init__(self) -> None:
        self.pools: dict[str, dict] = {}
        self.manager: PostgreSQLVerbaManager = PostgreSQLVerbaManager()
        self.max_time: int = 30  # 30 minutes
        self.last_cleanup: datetime = datetime.now()
        self.cleanup_interval: int = 5  # 5 minutes

    def hash_credentials(self, credentials: Credentials) -> str:
        """Create hash for credential caching."""
        return f"{credentials.deployment}:{credentials.url}:{credentials.key}"

    async def connect(self, credentials: Credentials) -> asyncpg.Pool:
        """Connect to PostgreSQL with connection pooling."""
        _credentials = credentials

        # Handle both None and empty string cases for environment variable fallback
        if not _credentials.url or _credentials.url.strip() == "":
            _credentials.url = os.environ.get("RAILWAY_POSTGRES_URL", "") or os.environ.get("DATABASE_URL", "")
        if not _credentials.key or _credentials.key.strip() == "":
            _credentials.key = os.environ.get("RAILWAY_POSTGRES_PASSWORD", "")

        cred_hash = self.hash_credentials(_credentials)
        if cred_hash in self.pools:
            msg.info("Found existing PostgreSQL connection pool")
            return self.pools[cred_hash]["pool"]
        else:
            msg.good("Creating new PostgreSQL connection pool")
            try:
                pool = await self.manager.connect(_credentials)
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

    async def clean_up(self):
        """Clean up old PostgreSQL connections."""
        current_time = datetime.now()
        time_since_cleanup = (current_time - self.last_cleanup).total_seconds() / 60
        
        if time_since_cleanup < self.cleanup_interval:
            return
            
        msg.info("Cleaning PostgreSQL Connection Pools")
        pools_to_remove = []

        for cred_hash, pool_data in self.pools.items():
            time_difference = current_time - pool_data["timestamp"]
            if time_difference.total_seconds() / 60 > self.max_time:
                pools_to_remove.append(cred_hash)
            pool: asyncpg.Pool = pool_data["pool"]
            if pool._closed:
                pools_to_remove.append(cred_hash)

        for cred_hash in pools_to_remove:
            await self.manager.disconnect(self.pools[cred_hash]["pool"])
            del self.pools[cred_hash]
            msg.warn(f"Removed pool: {cred_hash}")

        msg.info(f"Cleaned up {len(pools_to_remove)} pools")
        self.last_cleanup = current_time