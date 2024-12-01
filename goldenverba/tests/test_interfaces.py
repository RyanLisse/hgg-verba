import pytest
from goldenverba.components.interfaces import Retriever

def test_retriever_interface():
    # Test that Retriever is properly defined
    retriever = Retriever()
    assert hasattr(retriever, 'name')
    assert hasattr(Retriever, 'retrieve')
