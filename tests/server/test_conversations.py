"""Tests for the conversations endpoints."""


class TestConversationsEndpoints:
    """Tests for the /conversations endpoints."""

    def test_list_conversations_empty(self, client):
        """Test listing conversations when empty."""
        response = client.get("/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["total"] == 0
        assert data["conversations"] == []

    def test_list_conversations_with_data(self, client):
        """Test listing conversations after ingestion."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": "conv-1", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": "conv-1", "voice.actor": "agent"},
                },
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": "conv-2", "voice.actor": "user"},
                },
                # Span without conversation ID - should be ignored
                {
                    "name": "voice.asr",
                    "duration_ms": 100.0,
                    "attributes": {"voice.stage.type": "asr"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert data["total"] == 2

        # Find conv-1 in the list
        conv1 = next((c for c in data["conversations"] if c["id"] == "conv-1"), None)
        assert conv1 is not None
        assert conv1["turn_count"] == 2
        assert conv1["span_count"] == 2

    def test_get_conversation_found(self, client):
        """Test getting a specific conversation."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "duration_ms": 100.0,
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.actor": "user",
                        "voice.turn.id": "turn-1",
                        "voice.turn.index": 0,
                    },
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 200.0,
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.actor": "agent",
                        "voice.turn.id": "turn-2",
                        "voice.turn.index": 1,
                    },
                },
                {
                    "name": "voice.llm",
                    "duration_ms": 500.0,
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.stage.type": "llm",
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations/conv-1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "conv-1"
        assert len(data["turns"]) == 2
        assert data["span_count"] == 3
        assert data["analysis"] is not None
        # Turns should be sorted by index
        assert data["turns"][0]["actor"] == "user"
        assert data["turns"][1]["actor"] == "agent"

    def test_get_conversation_not_found(self, client):
        """Test getting a non-existent conversation."""
        response = client.get("/conversations/nonexistent")

        assert response.status_code == 404
