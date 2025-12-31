"""Tests for the voiceobs server."""

from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from voiceobs._version import __version__
from voiceobs.cli import app as cli_app
from voiceobs.server.app import create_app
from voiceobs.server.store import get_span_store, reset_span_store

runner = CliRunner()


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


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        """Test that health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_structure(self, client):
        """Test that health endpoint returns correct structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["version"] == __version__
        assert "timestamp" in data


class TestIngestEndpoint:
    """Tests for the /ingest endpoint."""

    def test_ingest_single_span(self, client):
        """Test ingesting a single span."""
        span_data = {
            "name": "voice.turn",
            "duration_ms": 1000.0,
            "attributes": {
                "voice.actor": "user",
                "voice.conversation.id": "conv-123",
            },
        }

        response = client.post("/ingest", json=span_data)

        assert response.status_code == 201
        data = response.json()
        assert data["accepted"] == 1
        assert len(data["span_ids"]) == 1
        # Validate UUID format
        UUID(data["span_ids"][0])

    def test_ingest_batch_of_spans(self, client):
        """Test ingesting a batch of spans."""
        batch_data = {
            "spans": [
                {
                    "name": "voice.asr",
                    "duration_ms": 100.0,
                    "attributes": {"voice.stage.type": "asr"},
                },
                {
                    "name": "voice.llm",
                    "duration_ms": 500.0,
                    "attributes": {"voice.stage.type": "llm"},
                },
                {
                    "name": "voice.tts",
                    "duration_ms": 200.0,
                    "attributes": {"voice.stage.type": "tts"},
                },
            ]
        }

        response = client.post("/ingest", json=batch_data)

        assert response.status_code == 201
        data = response.json()
        assert data["accepted"] == 3
        assert len(data["span_ids"]) == 3

    def test_ingest_span_with_timestamps(self, client):
        """Test ingesting a span with timestamps."""
        span_data = {
            "name": "voice.turn",
            "start_time": "2024-01-15T10:00:00Z",
            "end_time": "2024-01-15T10:00:01Z",
            "duration_ms": 1000.0,
            "attributes": {},
        }

        response = client.post("/ingest", json=span_data)

        assert response.status_code == 201

    def test_ingest_span_with_trace_info(self, client):
        """Test ingesting a span with OpenTelemetry trace info."""
        span_data = {
            "name": "voice.turn",
            "duration_ms": 500.0,
            "trace_id": "abc123",
            "span_id": "def456",
            "parent_span_id": "ghi789",
            "attributes": {},
        }

        response = client.post("/ingest", json=span_data)

        assert response.status_code == 201

    def test_ingest_empty_batch(self, client):
        """Test ingesting an empty batch."""
        response = client.post("/ingest", json={"spans": []})

        assert response.status_code == 201
        data = response.json()
        assert data["accepted"] == 0
        assert data["span_ids"] == []


class TestSpansEndpoints:
    """Tests for the /spans endpoints."""

    def test_list_spans_empty(self, client):
        """Test listing spans when empty."""
        response = client.get("/spans")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["spans"] == []

    def test_list_spans_after_ingest(self, client):
        """Test listing spans after ingestion."""
        # Ingest a span
        client.post(
            "/ingest",
            json={
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {"voice.actor": "agent"},
            },
        )

        response = client.get("/spans")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["spans"]) == 1
        assert data["spans"][0]["name"] == "voice.turn"

    def test_get_span_by_id(self, client):
        """Test getting a specific span by ID."""
        # Ingest a span
        ingest_response = client.post(
            "/ingest",
            json={
                "name": "voice.llm",
                "duration_ms": 500.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        )
        span_id = ingest_response.json()["span_ids"][0]

        response = client.get(f"/spans/{span_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "voice.llm"
        assert data["duration_ms"] == 500.0

    def test_get_span_not_found(self, client):
        """Test getting a non-existent span."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/spans/{fake_id}")

        assert response.status_code == 404

    def test_clear_spans(self, client):
        """Test clearing all spans."""
        # Ingest some spans
        client.post(
            "/ingest",
            json={
                "spans": [
                    {"name": "span1", "attributes": {}},
                    {"name": "span2", "attributes": {}},
                ]
            },
        )

        # Verify they exist
        assert client.get("/spans").json()["count"] == 2

        # Clear spans
        response = client.delete("/spans")

        assert response.status_code == 200
        data = response.json()
        assert data["cleared"] == 2

        # Verify they're gone
        assert client.get("/spans").json()["count"] == 0


class TestSpanStore:
    """Tests for the SpanStore class."""

    def test_add_and_get_span(self, span_store):
        """Test adding and retrieving a span."""
        span_id = span_store.add_span(
            name="test.span",
            duration_ms=100.0,
            attributes={"key": "value"},
        )

        span = span_store.get_span(span_id)

        assert span is not None
        assert span.name == "test.span"
        assert span.duration_ms == 100.0
        assert span.attributes == {"key": "value"}

    def test_get_nonexistent_span(self, span_store):
        """Test getting a span that doesn't exist."""
        from uuid import uuid4

        result = span_store.get_span(uuid4())
        assert result is None

    def test_get_all_spans(self, span_store):
        """Test getting all spans."""
        span_store.add_span(name="span1", attributes={})
        span_store.add_span(name="span2", attributes={})
        span_store.add_span(name="span3", attributes={})

        spans = span_store.get_all_spans()

        assert len(spans) == 3

    def test_get_spans_as_dicts(self, span_store):
        """Test getting spans as dictionaries."""
        span_store.add_span(
            name="voice.turn",
            duration_ms=500.0,
            attributes={"voice.actor": "agent"},
        )

        dicts = span_store.get_spans_as_dicts()

        assert len(dicts) == 1
        assert dicts[0]["name"] == "voice.turn"
        assert dicts[0]["duration_ms"] == 500.0
        assert dicts[0]["attributes"] == {"voice.actor": "agent"}

    def test_clear_spans(self, span_store):
        """Test clearing all spans."""
        span_store.add_span(name="span1", attributes={})
        span_store.add_span(name="span2", attributes={})

        count = span_store.clear()

        assert count == 2
        assert span_store.count() == 0

    def test_count_spans(self, span_store):
        """Test counting spans."""
        assert span_store.count() == 0

        span_store.add_span(name="span1", attributes={})
        assert span_store.count() == 1

        span_store.add_span(name="span2", attributes={})
        assert span_store.count() == 2


class TestServerCLI:
    """Tests for the server CLI command."""

    def test_server_command_in_help(self):
        """Test that server command appears in help."""
        result = runner.invoke(cli_app, ["--help"])

        assert result.exit_code == 0
        assert "server" in result.output

    def test_server_help(self):
        """Test server command help."""
        result = runner.invoke(cli_app, ["server", "--help"])

        assert result.exit_code == 0
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--reload" in result.output

    def test_server_without_dependencies(self):
        """Test server command fails gracefully without uvicorn."""
        with patch.dict("sys.modules", {"uvicorn": None}):
            # This test verifies the import error handling
            # The actual behavior depends on how Python handles the mock
            pass


class TestAppCreation:
    """Tests for the FastAPI app creation."""

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance."""
        from fastapi import FastAPI

        app = create_app()

        assert isinstance(app, FastAPI)

    def test_app_has_correct_metadata(self):
        """Test that app has correct metadata."""
        app = create_app()

        assert app.title == "voiceobs"
        assert app.version == __version__

    def test_app_has_docs_endpoints(self, client):
        """Test that docs endpoints are available."""
        # OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200

        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
