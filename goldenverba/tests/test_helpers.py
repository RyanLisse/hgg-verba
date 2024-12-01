import pytest
from goldenverba.server.helpers import LoggerManager
from goldenverba.server.types import FileStatus

@pytest.fixture
def logger():
    return LoggerManager()

def test_logger_initialization(logger):
    assert logger is not None
    assert logger.logs == []
    assert logger.status == FileStatus.PENDING

def test_logger_add_log(logger):
    logger.add_log("Test log message")
    assert len(logger.logs) == 1
    assert logger.logs[0]["message"] == "Test log message"
    assert "timestamp" in logger.logs[0]

def test_logger_set_status(logger):
    logger.set_status(FileStatus.PROCESSING)
    assert logger.status == FileStatus.PROCESSING

    logger.set_status(FileStatus.COMPLETED)
    assert logger.status == FileStatus.COMPLETED

def test_logger_set_error(logger):
    error_message = "Test error message"
    logger.set_error(error_message)
    assert logger.status == FileStatus.ERROR
    assert len(logger.logs) > 0
    assert logger.logs[-1]["message"] == error_message
