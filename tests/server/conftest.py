"""Shared fixtures for server tests."""

import pytest
from fastapi.testclient import TestClient

from voiceobs.server.app import create_app
from voiceobs.server.store import get_span_store, reset_span_store


@pytest.fixture
def client():
    """Create a test client for the server."""
    reset_span_store()
    app = create_app()
    with TestClient(app) as client:
        yield client
    reset_span_store()


@pytest.fixture
def span_store():
    """Create a clean span store for testing."""
    reset_span_store()
    store = get_span_store()
    yield store
    reset_span_store()
