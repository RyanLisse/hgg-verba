from unittest.mock import Mock, patch

import pytest

from goldenverba.server.types import Credentials
from goldenverba.verba_manager_supabase import VerbaManagerSupabase


@pytest.fixture
def verba_manager():
    return VerbaManagerSupabase()


def test_verba_manager_initialization(verba_manager):
    assert verba_manager.reader_manager is not None
    assert verba_manager.chunker_manager is not None
    assert verba_manager.embedder_manager is not None
    assert verba_manager.retriever_manager is not None
    assert verba_manager.generator_manager is not None
    assert verba_manager.database_manager is not None


@pytest.mark.asyncio
async def test_connect(verba_manager):
    credentials = Credentials(
        deployment="Local", url="postgresql://localhost:5432/verba", key="test-key"
    )

    with patch(
        "goldenverba.components.supabase_manager.SupabaseManager.connect"
    ) as mock_connect:
        mock_connect.return_value = Mock()
        client = await verba_manager.connect(credentials)
        assert client is not None


@pytest.mark.asyncio
async def test_disconnect(verba_manager):
    mock_client = Mock()
    with patch(
        "goldenverba.components.supabase_manager.SupabaseManager.disconnect"
    ) as mock_disconnect:
        await verba_manager.disconnect(mock_client)
        mock_disconnect.assert_called_once()


def test_verify_config(verba_manager):
    config_a = {
        "Reader": {
            "selected": "TextReader",
            "components": {
                "TextReader": {
                    "config": {
                        "test": {
                            "description": "Test config",
                            "values": ["value1", "value2"],
                        }
                    }
                }
            },
        }
    }
    config_b = {
        "Reader": {
            "selected": "TextReader",
            "components": {
                "TextReader": {
                    "config": {
                        "test": {
                            "description": "Test config",
                            "values": ["value1", "value2"],
                        }
                    }
                }
            },
        }
    }
    assert verba_manager.verify_config(config_a, config_b)

    config_b = {
        "Reader": {
            "selected": "TextReader",
            "components": {
                "TextReader": {
                    "config": {
                        "test": {
                            "description": "Different config",
                            "values": ["value1", "value2"],
                        }
                    }
                }
            },
        }
    }
    assert not verba_manager.verify_config(config_a, config_b)
