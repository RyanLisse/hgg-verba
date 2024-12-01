import pytest
from goldenverba.components.chunk import Chunk

@pytest.fixture
def sample_chunk():
    return Chunk(
        content="This is a chunk of text.",
        content_without_overlap="This is a chunk of text.",
        chunk_id="chunk-123",
        start_i=0,
        end_i=23
    )

def test_chunk_initialization(sample_chunk):
    assert sample_chunk.content == "This is a chunk of text."
    assert sample_chunk.chunk_id == "chunk-123"
    assert sample_chunk.start_i == 0
    assert sample_chunk.end_i == 23
    assert sample_chunk.content_without_overlap == "This is a chunk of text."

def test_chunk_representation(sample_chunk):
    chunk_dict = sample_chunk.to_json()
    assert isinstance(chunk_dict, dict)
    assert chunk_dict["content"] == "This is a chunk of text."
    assert chunk_dict["chunk_id"] == "chunk-123"
