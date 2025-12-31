"""Tests for the analysis endpoints."""


class TestAnalyzeEndpoints:
    """Tests for the /analyze endpoints."""

    def test_analyze_empty(self, client):
        """Test analyzing when no spans exist."""
        response = client.get("/analyze")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_spans"] == 0
        assert data["summary"]["total_conversations"] == 0
        assert data["summary"]["total_turns"] == 0

    def test_analyze_with_spans(self, client):
        """Test analyzing ingested spans."""
        # Ingest spans
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "duration_ms": 1000.0,
                    "attributes": {
                        "voice.actor": "user",
                        "voice.conversation.id": "conv-1",
                        "voice.turn.id": "turn-1",
                        "voice.turn.index": 0,
                    },
                },
                {
                    "name": "voice.asr",
                    "duration_ms": 100.0,
                    "attributes": {
                        "voice.stage.type": "asr",
                        "voice.conversation.id": "conv-1",
                    },
                },
                {
                    "name": "voice.llm",
                    "duration_ms": 500.0,
                    "attributes": {
                        "voice.stage.type": "llm",
                        "voice.conversation.id": "conv-1",
                    },
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 800.0,
                    "attributes": {
                        "voice.actor": "agent",
                        "voice.conversation.id": "conv-1",
                        "voice.turn.id": "turn-2",
                        "voice.turn.index": 1,
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/analyze")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_spans"] == 4
        assert data["summary"]["total_conversations"] == 1
        assert data["summary"]["total_turns"] == 2
        assert data["stages"]["asr"]["count"] == 1
        assert data["stages"]["llm"]["count"] == 1

    def test_analyze_conversation_found(self, client):
        """Test analyzing a specific conversation."""
        # Ingest spans for two conversations
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "duration_ms": 100.0,
                    "attributes": {"voice.conversation.id": "conv-1", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 200.0,
                    "attributes": {"voice.conversation.id": "conv-2", "voice.actor": "user"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/analyze/conv-1")

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_spans"] == 1
        assert data["summary"]["total_turns"] == 1

    def test_analyze_conversation_not_found(self, client):
        """Test analyzing a non-existent conversation."""
        response = client.get("/analyze/nonexistent")

        assert response.status_code == 404
