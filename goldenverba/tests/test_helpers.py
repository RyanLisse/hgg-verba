import pytest
from fastapi import WebSocket
from unittest.mock import AsyncMock
from goldenverba.server.helpers import LoggerManager
from goldenverba.server.types import FileStatus

@pytest.fixture
def logger():
    mock_socket = AsyncMock(spec=WebSocket)
    return LoggerManager(socket=mock_socket)

def test_logger_initialization(logger):
    assert logger is not None
    assert logger.socket is not None

@pytest.mark.asyncio
async def test_logger_send_report(logger):
    file_id = "test-file"
    status = FileStatus.LOADING
    message = "Test message"
    took = 1.5
    
    await logger.send_report(file_id, status, message, took)
    logger.socket.send_json.assert_called_once()

@pytest.mark.asyncio
async def test_logger_create_new_document(logger):
    new_file_id = "new-file"
    document_name = "test.txt"
    original_file_id = "original-file"
    
    await logger.create_new_document(new_file_id, document_name, original_file_id)
    logger.socket.send_json.assert_called_once()
