"""Shared fixtures for server tests."""

import os

import pytest
from fastapi.testclient import TestClient

from voiceobs.server.app import create_app
from voiceobs.server.dependencies import reset_dependencies
from voiceobs.server.store import get_span_store, reset_span_store


@pytest.fixture(autouse=True)
def ensure_in_memory_storage(monkeypatch):
    """Ensure tests always use in-memory storage, not PostgreSQL.

    This fixture runs automatically for all tests in the server test suite.
    It removes the database URL from the environment to prevent tests from
    accidentally writing to a real PostgreSQL database.
    """
    # Remove database URL from environment if set
    monkeypatch.delenv("VOICEOBS_DATABASE_URL", raising=False)
    yield


@pytest.fixture
def client():
    """Create a test client for the server."""
    reset_span_store()
    reset_dependencies()
    app = create_app()
    with TestClient(app) as client:
        yield client
    reset_span_store()
    reset_dependencies()


@pytest.fixture
def span_store():
    """Create a clean span store for testing."""
    reset_span_store()
    store = get_span_store()
    yield store
    reset_span_store()
