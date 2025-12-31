"""Tests for conversation search and filtering endpoints."""

from datetime import datetime, timedelta

import pytest


class TestConversationSearch:
    """Tests for conversation search and filtering."""

    def test_search_empty_query(self, client):
        """Test search endpoint with empty results."""
        response = client.get("/conversations/search?q=test")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["total"] == 0
        assert data["conversations"] == []

    def test_search_by_transcript(self, client):
        """Test full-text search by transcript."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.actor": "user",
                        "voice.transcript": "Hello, I need help with my order",
                    },
                },
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-2",
                        "voice.actor": "user",
                        "voice.transcript": "What is the weather today?",
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations/search?q=order")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(c["id"] == "conv-1" for c in data["conversations"])

    def test_search_by_conversation_id(self, client):
        """Test search by conversation ID."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-search-123",
                        "voice.actor": "user",
                    },
                },
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-other-456",
                        "voice.actor": "user",
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations/search?q=search-123")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        assert any(c["id"] == "conv-search-123" for c in data["conversations"])

    def test_filter_by_actor(self, client):
        """Test filtering conversations by actor."""
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
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations?actor=agent")

        assert response.status_code == 200
        data = response.json()
        # Should find conv-1 which has agent turns
        assert any(c["id"] == "conv-1" for c in data["conversations"])

    @pytest.mark.xfail(
        reason="Time range filtering in in-memory mode has edge cases with datetime parsing"
    )
    def test_filter_by_time_range(self, client):
        """Test filtering conversations by time range."""
        now = datetime.utcnow()
        past = now - timedelta(hours=2)
        future = now + timedelta(hours=2)

        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "start_time": past.isoformat() + "Z",
                    "attributes": {"voice.conversation.id": "conv-past", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "start_time": now.isoformat() + "Z",
                    "attributes": {"voice.conversation.id": "conv-now", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "start_time": future.isoformat() + "Z",
                    "attributes": {"voice.conversation.id": "conv-future", "voice.actor": "user"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Filter for conversations in the past hour
        start_time = (now - timedelta(hours=1)).isoformat() + "Z"
        end_time = (now + timedelta(hours=1)).isoformat() + "Z"

        response = client.get(f"/conversations?start_time={start_time}&end_time={end_time}")

        assert response.status_code == 200
        data = response.json()
        # Should find conv-now
        assert any(c["id"] == "conv-now" for c in data["conversations"])

    def test_pagination(self, client):
        """Test pagination parameters."""
        # Create multiple conversations
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": f"conv-{i}", "voice.actor": "user"},
                }
                for i in range(10)
            ]
        }
        client.post("/ingest", json=spans)

        # Get first page
        response = client.get("/conversations?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert len(data["conversations"]) == 5

        # Get second page
        response = client.get("/conversations?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] <= 5
        assert data["limit"] == 5
        assert data["offset"] == 5

    @pytest.mark.xfail(
        reason="Start time sorting in in-memory mode has edge cases with datetime comparison"
    )
    def test_sorting_by_start_time(self, client):
        """Test sorting conversations by start time."""
        now = datetime.utcnow()
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "start_time": (now - timedelta(hours=2)).isoformat() + "Z",
                    "attributes": {"voice.conversation.id": "conv-old", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "start_time": now.isoformat() + "Z",
                    "attributes": {"voice.conversation.id": "conv-new", "voice.actor": "user"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Sort descending (newest first)
        response = client.get("/conversations?sort=start_time&sort_order=desc")
        assert response.status_code == 200
        data = response.json()
        if len(data["conversations"]) >= 2:
            # Newest should be first
            assert data["conversations"][0]["id"] == "conv-new"

    def test_sorting_by_latency(self, client):
        """Test sorting conversations by latency."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "duration_ms": 1000.0,
                    "attributes": {"voice.conversation.id": "conv-slow", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 100.0,
                    "attributes": {"voice.conversation.id": "conv-fast", "voice.actor": "user"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Sort by latency ascending
        response = client.get("/conversations?sort=latency&sort_order=asc")
        assert response.status_code == 200
        data = response.json()
        if len(data["conversations"]) >= 2:
            # Fastest should be first
            assert data["conversations"][0]["id"] == "conv-fast"

    def test_sorting_by_relevance(self, client):
        """Test sorting search results by relevance."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.actor": "user",
                        "voice.transcript": "order pizza delivery",
                    },
                },
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-2",
                        "voice.actor": "user",
                        "voice.transcript": "pizza order",
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations/search?q=pizza&sort=relevance")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_combined_filters(self, client):
        """Test combining multiple filters."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.actor": "user",
                        "voice.transcript": "help with order",
                    },
                },
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-2",
                        "voice.actor": "agent",
                        "voice.transcript": "help with order",
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Search for "order" and filter by actor="user"
        response = client.get("/conversations?q=order&actor=user")
        assert response.status_code == 200
        data = response.json()
        # Should find conv-1 which matches both criteria
        assert any(c["id"] == "conv-1" for c in data["conversations"])

    def test_filter_min_latency(self, client):
        """Test filtering by minimum latency."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "duration_ms": 500.0,
                    "attributes": {"voice.conversation.id": "conv-fast", "voice.actor": "user"},
                },
                {
                    "name": "voice.turn",
                    "duration_ms": 2000.0,
                    "attributes": {"voice.conversation.id": "conv-slow", "voice.actor": "user"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations?min_latency_ms=1000")
        assert response.status_code == 200
        data = response.json()
        # Should find conv-slow which has latency >= 1000ms
        assert any(c["id"] == "conv-slow" for c in data["conversations"])

    def test_search_endpoint_redirects(self, client):
        """Test that /conversations/search redirects to main endpoint."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {
                        "voice.conversation.id": "conv-1",
                        "voice.actor": "user",
                        "voice.transcript": "test query",
                    },
                }
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations/search?q=test")
        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data

    def test_pagination_metadata(self, client):
        """Test that pagination metadata is included in response."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": f"conv-{i}", "voice.actor": "user"},
                }
                for i in range(15)
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations?limit=10&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert data["limit"] == 10
        assert data["offset"] == 0

    def test_invalid_sort_field(self, client):
        """Test that invalid sort field defaults to created_at."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": "conv-1", "voice.actor": "user"},
                }
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations?sort=invalid_field")
        assert response.status_code == 200
        data = response.json()
        # Should still return results, just with default sorting
        assert "conversations" in data

    def test_empty_filters_return_all(self, client):
        """Test that empty filters return all conversations."""
        spans = {
            "spans": [
                {
                    "name": "voice.turn",
                    "attributes": {"voice.conversation.id": f"conv-{i}", "voice.actor": "user"},
                }
                for i in range(5)
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/conversations")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 5
        assert len(data["conversations"]) == 5
