"""
Pytest configuration and fixtures for Knapsack Lab test suite.
"""

import sys
from pathlib import Path
import pytest

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import config
from app import app

@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_items():
    """Standard 4-item classic textbook instance."""
    return [
        {"id": 1, "name": "Item 1", "weight": 10, "value": 60, "original_index": 0},
        {"id": 2, "name": "Item 2", "weight": 20, "value": 100, "original_index": 1},
        {"id": 3, "name": "Item 3", "weight": 30, "value": 120, "original_index": 2},
        {"id": 4, "name": "Item 4", "weight": 15, "value": 70, "original_index": 3}
    ]
