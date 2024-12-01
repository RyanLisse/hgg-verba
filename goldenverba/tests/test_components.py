import pytest
from unittest.mock import Mock, patch
from goldenverba.components.document import Document
from goldenverba.components.managers import (
    ReaderManager,
    ChunkerManager,
    EmbeddingManager,
    RetrieverManager,
    GeneratorManager,
    WeaviateManager,
)

@pytest.fixture
def sample_document():
    return Document(
        name="test.txt",
        content="This is a test document content.",
        file_type="txt",
        uuid="test-uuid"
    )

@pytest.fixture
def reader_manager():
    return ReaderManager()

@pytest.fixture
def chunker_manager():
    return ChunkerManager()

@pytest.fixture
def embedding_manager():
    return EmbeddingManager()

def test_document_initialization(sample_document):
    assert sample_document.name == "test.txt"
    assert sample_document.content == "This is a test document content."
    assert sample_document.file_type == "txt"
    assert sample_document.uuid == "test-uuid"

def test_reader_manager_initialization(reader_manager):
    assert reader_manager is not None
    assert hasattr(reader_manager, 'read_file')

def test_chunker_manager_initialization(chunker_manager):
    assert chunker_manager is not None
    assert hasattr(chunker_manager, 'chunk_text')

def test_embedding_manager_initialization(embedding_manager):
    assert embedding_manager is not None
    assert hasattr(embedding_manager, 'embed_text')

@pytest.mark.asyncio
async def test_chunker_manager_chunk_text(chunker_manager, sample_document):
    chunks = chunker_manager.chunk_text(
        text=sample_document.content,
        chunk_size=10,
        chunk_overlap=2
    )
    assert isinstance(chunks, list)
    assert len(chunks) > 0

@pytest.mark.asyncio
async def test_embedding_manager_embed_text(embedding_manager):
    with patch('goldenverba.components.managers.embedding_manager.OpenAIEmbeddings') as mock_embeddings:
        mock_embeddings.return_value.embed_query.return_value = [0.1, 0.2, 0.3]
        embedding = await embedding_manager.embed_text("test text")
        assert isinstance(embedding, list)
        assert len(embedding) > 0
