import pytest
from goldenverba.components.chunk import Chunk

@pytest.fixture
def sample_chunk():
    return Chunk(
        content="This is a chunk of text.",
        index=0,
        document_id="doc-123"
    )

def test_chunk_initialization(sample_chunk):
    assert sample_chunk.content == "This is a chunk of text."
    assert sample_chunk.index == 0
    assert sample_chunk.document_id == "doc-123"

def test_chunk_representation(sample_chunk):
    assert repr(sample_chunk) == "Chunk(index=0, document_id='doc-123')"
