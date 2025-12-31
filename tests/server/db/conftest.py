"""Shared fixtures for database tests."""

from unittest.mock import AsyncMock

import pytest


class MockRecord(dict):
    """Mock asyncpg Record that supports both dict and attribute access."""

    def __getitem__(self, key):
        return super().__getitem__(key)


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = AsyncMock()
    return db
