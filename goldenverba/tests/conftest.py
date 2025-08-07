import os
import sys

import pytest

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def test_client():
    # Import here to avoid circular imports
    from server.app import app

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
