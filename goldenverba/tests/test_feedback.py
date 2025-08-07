from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from goldenverba.server.api import app


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_langsmith_client():
    with patch("goldenverba.server.api.LangSmithClient") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance


def test_submit_positive_feedback(test_client, mock_langsmith_client):
    mock_feedback = Mock()
    mock_feedback.id = "test-feedback-id"
    mock_langsmith_client.create_feedback.return_value = mock_feedback

    payload = {
        "runId": "test-run-123",
        "feedbackType": "positive",
        "additionalFeedback": "",
        "credentials": {
            "deployment": "Local",
            "url": "http://localhost:8080",
            "key": "test-key",
        },
    }

    headers = {"origin": "http://localhost:3000"}

    response = test_client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "feedback_id": "test-feedback-id"}

    mock_langsmith_client.create_feedback.assert_called_once_with(
        run_id="test-run-123", key="user_rating", score=1, comment="", value="positive"
    )


def test_submit_negative_feedback(test_client, mock_langsmith_client):
    mock_feedback = Mock()
    mock_feedback.id = "test-feedback-id"
    mock_langsmith_client.create_feedback.return_value = mock_feedback

    payload = {
        "runId": "test-run-123",
        "feedbackType": "negative",
        "additionalFeedback": "Test feedback comment",
        "credentials": {
            "deployment": "Local",
            "url": "http://localhost:8080",
            "key": "test-key",
        },
    }

    headers = {"origin": "http://localhost:3000"}

    response = test_client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "feedback_id": "test-feedback-id"}

    mock_langsmith_client.create_feedback.assert_called_once_with(
        run_id="test-run-123",
        key="user_rating",
        score=0,
        comment="Test feedback comment",
        value="negative",
    )


def test_submit_feedback_error(test_client, mock_langsmith_client):
    mock_langsmith_client.create_feedback.side_effect = Exception("Test error")

    payload = {
        "runId": "test-run-123",
        "feedbackType": "positive",
        "additionalFeedback": "",
        "credentials": {
            "deployment": "Local",
            "url": "http://localhost:8080",
            "key": "test-key",
        },
    }

    headers = {"origin": "http://localhost:3000"}

    response = test_client.post("/api/feedback", json=payload, headers=headers)
    assert response.status_code == 200  # API returns 200 even for errors
    assert response.json() == {"status": "error", "message": "Test error"}
