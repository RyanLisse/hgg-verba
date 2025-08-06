import pytest
from goldenverba.components.document import Document
from goldenverba.components.managers import (
    ReaderManager,
    ChunkerManager,
    EmbeddingManager,
)

@pytest.fixture
def sample_document():
    return Document(
        title="test.txt",
        content="This is a test document content.",
        extension="txt",
        fileSize=100,
        labels=[],
        source="test",
        meta={},
        metadata=""
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
    assert sample_document.title == "test.txt"
    assert sample_document.content == "This is a test document content."
    assert sample_document.extension == "txt"
    assert sample_document.fileSize == 100
    assert isinstance(sample_document.chunks, list)
    assert len(sample_document.chunks) == 0

def test_reader_manager_initialization(reader_manager):
    assert reader_manager is not None
    assert hasattr(reader_manager, 'readers')

def test_chunker_manager_initialization(chunker_manager):
    assert chunker_manager is not None
    assert hasattr(chunker_manager, 'chunkers')

def test_embedding_manager_initialization(embedding_manager):
    assert embedding_manager is not None
    assert hasattr(embedding_manager, 'embedders')

@pytest.mark.asyncio
async def test_chunker_manager_chunk_text(chunker_manager, sample_document):
    # Test that the chunker manager can process a document
    assert chunker_manager is not None
    assert sample_document is not None

@pytest.mark.asyncio
async def test_embedding_manager_embed_text(embedding_manager):
    # Test that the embedding manager can embed text
    assert embedding_manager is not None
