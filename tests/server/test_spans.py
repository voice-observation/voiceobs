"""Tests for the spans endpoints."""

from uuid import UUID


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
