import pytest
from unittest.mock import Mock, patch
from goldenverba.verba_manager import VerbaManager
from goldenverba.server.types import Credentials, FileConfig

@pytest.fixture
def verba_manager():
    return VerbaManager()

def test_verba_manager_initialization(verba_manager):
    assert verba_manager.reader_manager is not None
    assert verba_manager.chunker_manager is not None
    assert verba_manager.embedder_manager is not None
    assert verba_manager.retriever_manager is not None
    assert verba_manager.generator_manager is not None
    assert verba_manager.weaviate_manager is not None

@pytest.mark.asyncio
async def test_connect(verba_manager):
    credentials = Credentials(
        url="http://localhost:8080",
        username="admin",
        password="password"
    )
    
    with patch('weaviate.client.WeaviateAsyncClient') as mock_client:
        client = await verba_manager.connect(credentials)
        assert client is not None

@pytest.mark.asyncio
async def test_disconnect(verba_manager):
    mock_client = Mock()
    await verba_manager.disconnect(mock_client)
    mock_client.close.assert_called_once()

def test_verify_config(verba_manager):
    config_a = {"key1": "value1", "key2": "value2"}
    config_b = {"key1": "value1", "key2": "value2"}
    assert verba_manager.verify_config(config_a, config_b) == True

    config_b = {"key1": "different", "key2": "value2"}
    assert verba_manager.verify_config(config_a, config_b) == False
