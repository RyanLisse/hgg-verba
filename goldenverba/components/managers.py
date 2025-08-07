import asyncio
import os

from wasabi import msg

from goldenverba.components.chunking.CodeChunker import CodeChunker
from goldenverba.components.chunking.HTMLChunker import HTMLChunker
from goldenverba.components.chunking.JSONChunker import JSONChunker
from goldenverba.components.chunking.MarkdownChunker import MarkdownChunker
from goldenverba.components.chunking.RecursiveChunker import RecursiveChunker
from goldenverba.components.chunking.SemanticChunker import SemanticChunker
from goldenverba.components.chunking.SentenceChunker import SentenceChunker

# Import Chunkers
from goldenverba.components.chunking.TokenChunker import TokenChunker
from goldenverba.components.document import Document
from goldenverba.components.embedding.CohereEmbedder import CohereEmbedder

# Import Embedders
from goldenverba.components.embedding.OpenAIEmbedder import OpenAIEmbedder
from goldenverba.components.embedding.SentenceTransformersEmbedder import (
    SentenceTransformersEmbedder,
)
from goldenverba.components.embedding.VoyageAIEmbedder import VoyageAIEmbedder
from goldenverba.components.generation.AnthrophicGenerator import AnthropicGenerator

# Import Generators
from goldenverba.components.generation.CohereGenerator import CohereGenerator
from goldenverba.components.generation.GeminiGenerator import GeminiGenerator
from goldenverba.components.generation.LiteLLMGenerator import LiteLLMGenerator
from goldenverba.components.generation.OpenAIGenerator import OpenAIGenerator
from goldenverba.components.interfaces import (
    Chunker,
    Embedding,
    Generator,
    Reader,
    Retriever,
)

# Import Readers
from goldenverba.components.reader.BasicReader import BasicReader
from goldenverba.components.reader.FirecrawlReader import FirecrawlReader
from goldenverba.components.reader.GitReader import GitReader
from goldenverba.components.reader.HTMLReader import HTMLReader
from goldenverba.components.reader.UnstructuredAPI import UnstructuredReader

# Import Retrievers
from goldenverba.components.retriever.WindowRetriever import WindowRetriever
from goldenverba.server.helpers import LoggerManager
from goldenverba.server.types import FileConfig, FileStatus

try:
    pass
except Exception:
    msg.warn("tiktoken not installed, your base installation might be corrupted.")

### Add new components here ###

production = os.getenv("VERBA_PRODUCTION")
if production != "Production":
    readers = [
        BasicReader(),
        HTMLReader(),
        GitReader(),
        UnstructuredReader(),
        FirecrawlReader(),
    ]
    chunkers = [
        TokenChunker(),
        SentenceChunker(),
        RecursiveChunker(),
        SemanticChunker(),
        HTMLChunker(),
        MarkdownChunker(),
        CodeChunker(),
        JSONChunker(),
    ]
    embedders = [
        SentenceTransformersEmbedder(),
        VoyageAIEmbedder(),
        CohereEmbedder(),
        OpenAIEmbedder(),
    ]
    retrievers = [WindowRetriever()]
    generators = [
        LiteLLMGenerator(),
        OpenAIGenerator(),
        AnthropicGenerator(),
        CohereGenerator(),
        GeminiGenerator(),
    ]
else:
    readers = [
        BasicReader(),
        HTMLReader(),
        GitReader(),
        UnstructuredReader(),
        FirecrawlReader(),
    ]
    chunkers = [
        TokenChunker(),
        SentenceChunker(),
        RecursiveChunker(),
        SemanticChunker(),
        HTMLChunker(),
        MarkdownChunker(),
        CodeChunker(),
        JSONChunker(),
    ]
    embedders = [
        VoyageAIEmbedder(),
        CohereEmbedder(),
        OpenAIEmbedder(),
    ]
    retrievers = [WindowRetriever()]
    generators = [
        LiteLLMGenerator(),
        OpenAIGenerator(),
        AnthropicGenerator(),
        CohereGenerator(),
        GeminiGenerator(),
    ]

### ----------------------- ###

# Constants
ALPHANUMERIC_REGEX_PATTERN = r"[^a-zA-Z0-9]"

# WeaviateManager class removed - migrated to PostgreSQL with pgvector


class ReaderManager:
    def __init__(self) -> None:
        self.readers: dict[str, Reader] = {reader.name: reader for reader in readers}

    async def load(
        self, reader: str, fileConfig: FileConfig, logger: LoggerManager
    ) -> list[Document]:
        try:
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            if reader in self.readers:
                config = fileConfig.rag_config["Reader"].components[reader].config
                documents: list[Document] = await self.readers[reader].load(
                    config, fileConfig
                )
                for document in documents:
                    document.meta["Reader"] = (
                        fileConfig.rag_config["Reader"].components[reader].model_dump()
                    )
                elapsed_time = round(loop.time() - start_time, 2)
                if len(documents) == 1:
                    await logger.send_report(
                        fileConfig.fileID,
                        FileStatus.LOADING,
                        f"Loaded {fileConfig.filename}",
                        took=elapsed_time,
                    )
                else:
                    await logger.send_report(
                        fileConfig.fileID,
                        FileStatus.LOADING,
                        f"Loaded {fileConfig.filename} with {len(documents)} documents",
                        took=elapsed_time,
                    )
                return documents
            else:
                raise Exception(f"Reader {reader} not found")

        except Exception as e:
            raise Exception(f"Reader {reader} failed with: {str(e)}")


class ChunkerManager:
    def __init__(self) -> None:
        self.chunkers: dict[str, Chunker] = {
            chunker.name: chunker for chunker in chunkers
        }

    async def chunk(
        self,
        chunker: str,
        config: dict,
        documents: list[Document],
        logger: LoggerManager,
        fileID: str,
    ) -> list[Document]:
        try:
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            if chunker in self.chunkers:
                chunked_documents: list[Document] = await self.chunkers[chunker].chunk(
                    config, documents
                )
                for document in chunked_documents:
                    document.meta["Chunker"] = {
                        "name": chunker,
                        "config": config,
                    }
                elapsed_time = round(loop.time() - start_time, 2)
                total_chunks = sum(len(doc.chunks) for doc in chunked_documents)
                await logger.send_report(
                    fileID,
                    FileStatus.CHUNKING,
                    f"Chunked into {total_chunks} chunks",
                    took=elapsed_time,
                )
                return chunked_documents
            else:
                raise Exception(f"{chunker} Chunker not found")
        except Exception as e:
            raise e


class EmbeddingManager:
    def __init__(self) -> None:
        self.embedders: dict[str, Embedding] = {
            embedder.name: embedder for embedder in embedders
        }

    async def embed(
        self,
        embedder: str,
        config: dict,
        documents: list[Document],
        logger: LoggerManager,
        fileID: str,
    ) -> list[Document]:
        try:
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            if embedder in self.embedders:
                embedded_documents: list[Document] = await self.embedders[
                    embedder
                ].embed(config, documents)
                for document in embedded_documents:
                    document.meta["Embedder"] = {
                        "name": embedder,
                        "config": config,
                    }
                elapsed_time = round(loop.time() - start_time, 2)
                total_chunks = sum(len(doc.chunks) for doc in embedded_documents)
                await logger.send_report(
                    fileID,
                    FileStatus.EMBEDDING,
                    f"Embedded {total_chunks} chunks",
                    took=elapsed_time,
                )
                return embedded_documents
            else:
                raise Exception(f"{embedder} Embedder not found")
        except Exception as e:
            raise e


class RetrieverManager:
    def __init__(self) -> None:
        self.retrievers: dict[str, Retriever] = {
            retriever.name: retriever for retriever in retrievers
        }

    async def retrieve(
        self,
        retriever: str,
        config: dict,
        query: str,
        chunks: list,
        logger: LoggerManager,
    ) -> list:
        try:
            if retriever in self.retrievers:
                retrieved_chunks: list = await self.retrievers[retriever].retrieve(
                    config, query, chunks
                )
                return retrieved_chunks
            else:
                raise Exception(f"{retriever} Retriever not found")

        except Exception as e:
            raise e


class GeneratorManager:
    def __init__(self) -> None:
        self.generators: dict[str, Generator] = {
            generator.name: generator for generator in generators
        }

    async def generate(
        self,
        generator: str,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict],
        logger: LoggerManager,
    ) -> str:
        try:
            if generator in self.generators:
                generated_text: str = await self.generators[generator].generate(
                    config, query, context, conversation
                )
                return generated_text
            else:
                raise Exception(f"{generator} Generator not found")

        except Exception as e:
            raise e

    async def generate_stream(
        self,
        generator: str,
        config: dict,
        query: str,
        context: str,
        conversation: list[dict],
        logger: LoggerManager,
    ):
        try:
            if generator in self.generators:
                async for chunk in self.generators[generator].generate_stream(
                    config, query, context, conversation
                ):
                    yield chunk
            else:
                raise Exception(f"{generator} Generator not found")

        except Exception as e:
            raise e
