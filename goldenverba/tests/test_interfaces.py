import pytest
from goldenverba.components.interfaces import Retriever

def test_retriever_interface():
    # Test that Retriever is properly defined
    assert hasattr(Retriever, 'name')
    assert hasattr(Retriever, 'retrieve')
