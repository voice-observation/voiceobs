"""Error handling tests for the voiceobs server.

Tests for HTTP error responses: 400 (bad request), 404 (not found), 503 (service unavailable).
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from voiceobs.server.app import create_app
from voiceobs.server.dependencies import reset_dependencies
from voiceobs.server.store import reset_span_store


@pytest.fixture
def client_no_raise():
    """Create a test client that doesn't raise server exceptions.

    This allows testing that unhandled exceptions return 500 status codes.
    """
    reset_span_store()
    reset_dependencies()
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    reset_span_store()
    reset_dependencies()


class TestBadRequestErrors:
    """Tests for 400 Bad Request errors."""

    def test_ingest_missing_name(self, client):
        """Test that missing span name returns 422."""
        response = client.post(
            "/ingest",
            json={
                "duration_ms": 100.0,
                "attributes": {},
            },
        )
        assert response.status_code == 422  # Pydantic validation error
        error = response.json()
        assert "detail" in error

    def test_ingest_invalid_duration(self, client):
        """Test that invalid duration type returns 422."""
        response = client.post(
            "/ingest",
            json={
                "name": "voice.turn",
                "duration_ms": "not_a_number",  # Should be float
                "attributes": {},
            },
        )
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_ingest_invalid_json(self, client):
        """Test that invalid JSON returns 422."""
        response = client.post(
            "/ingest",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_ingest_empty_batch(self, client):
        """Test that empty spans array returns 422."""
        response = client.post(
            "/ingest",
            json={"spans": []},
        )
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_ingest_batch_invalid_span(self, client):
        """Test that batch with invalid span returns 422."""
        response = client.post(
            "/ingest",
            json={
                "spans": [
                    {"name": "valid.span", "duration_ms": 100.0},
                    {"duration_ms": 200.0},  # Missing name
                ]
            },
        )
        assert response.status_code == 422

    def test_ingest_invalid_datetime(self, client):
        """Test that invalid datetime format returns 422."""
        response = client.post(
            "/ingest",
            json={
                "name": "voice.turn",
                "start_time": "not-a-datetime",
                "duration_ms": 100.0,
            },
        )
        assert response.status_code == 422

    def test_ingest_negative_duration(self, client):
        """Test that negative duration returns 422."""
        response = client.post(
            "/ingest",
            json={
                "name": "voice.turn",
                "duration_ms": -100.0,
            },
        )
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error


class TestNotFoundErrors:
    """Tests for 404 Not Found errors."""

    def test_get_nonexistent_span(self, client):
        """Test that getting non-existent span returns 404."""
        fake_id = str(uuid4())
        response = client.get(f"/spans/{fake_id}")
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert fake_id in error["detail"]

    def test_get_nonexistent_conversation(self, client):
        """Test that getting non-existent conversation returns 404."""
        response = client.get("/conversations/nonexistent-conv-id")
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert "nonexistent-conv-id" in error["detail"]

    def test_analyze_nonexistent_conversation(self, client):
        """Test that analyzing non-existent conversation returns 404."""
        response = client.get("/analyze/nonexistent-conv-id")
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error

    def test_get_span_invalid_uuid(self, client):
        """Test that invalid UUID format returns 422."""
        response = client.get("/spans/not-a-valid-uuid")
        assert response.status_code == 422

    def test_undefined_endpoint(self, client):
        """Test that undefined endpoint returns 404."""
        response = client.get("/undefined/endpoint")
        assert response.status_code == 404

    def test_undefined_method(self, client):
        """Test that undefined method returns 405."""
        response = client.patch("/spans")  # PATCH not defined
        assert response.status_code == 405


class TestServiceUnavailableErrors:
    """Tests for 500 Internal Server Error from storage failures."""

    def test_storage_failure_on_ingest(self, client_no_raise):
        """Test that storage failure on ingest returns 500."""
        with patch("voiceobs.server.routes.spans.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.add_span.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.post(
                "/ingest",
                json={"name": "voice.turn", "duration_ms": 100.0},
            )
            assert response.status_code == 500

    def test_storage_failure_on_list_spans(self, client_no_raise):
        """Test that storage failure on list spans returns 500."""
        with patch("voiceobs.server.routes.spans.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.get_all_spans.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.get("/spans")
            assert response.status_code == 500

    def test_storage_failure_on_get_span(self, client_no_raise):
        """Test that storage failure on get span returns 500."""
        fake_id = str(uuid4())
        with patch("voiceobs.server.routes.spans.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.get_span.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.get(f"/spans/{fake_id}")
            assert response.status_code == 500

    def test_storage_failure_on_clear(self, client_no_raise):
        """Test that storage failure on clear returns 500."""
        with patch("voiceobs.server.routes.spans.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.clear.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.delete("/spans")
            assert response.status_code == 500

    def test_storage_failure_on_analyze(self, client_no_raise):
        """Test that storage failure on analyze returns 500."""
        with patch("voiceobs.server.routes.analysis.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.get_spans_as_dicts.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.get("/analyze")
            assert response.status_code == 500

    def test_storage_failure_on_conversations_list(self, client_no_raise):
        """Test that storage failure on conversations list returns 500."""
        with patch("voiceobs.server.routes.conversations.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.get_spans_as_dicts.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.get("/conversations")
            assert response.status_code == 500

    def test_storage_failure_on_failures_list(self, client_no_raise):
        """Test that storage failure on failures list returns 500."""
        with patch("voiceobs.server.routes.failures.get_storage") as mock_get_storage:
            mock_storage = AsyncMock()
            mock_storage.get_spans_as_dicts.side_effect = Exception("Database connection failed")
            mock_get_storage.return_value = mock_storage

            response = client_no_raise.get("/failures")
            assert response.status_code == 500


class TestErrorResponseFormat:
    """Tests for error response format consistency."""

    def test_404_error_has_detail(self, client):
        """Test that 404 errors include detail message."""
        fake_id = str(uuid4())
        response = client.get(f"/spans/{fake_id}")
        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert isinstance(error["detail"], str)
        assert len(error["detail"]) > 0

    def test_422_error_has_detail(self, client):
        """Test that 422 errors include detail with validation info."""
        response = client.post(
            "/ingest",
            json={"invalid_field": "value"},
        )
        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    def test_405_error_response(self, client):
        """Test that 405 Method Not Allowed is returned correctly."""
        response = client.put("/health")  # PUT not allowed on health
        assert response.status_code == 405
