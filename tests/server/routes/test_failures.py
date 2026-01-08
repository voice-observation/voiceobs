"""Tests for the failures endpoints."""


class TestFailuresEndpoints:
    """Tests for the /failures endpoints."""

    def test_list_failures_empty(self, client):
        """Test listing failures when none exist."""
        response = client.get("/failures")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["failures"] == []

    def test_list_failures_with_slow_response(self, client):
        """Test that slow responses are detected as failures."""
        # Ingest a slow LLM span (above default threshold)
        spans = {
            "spans": [
                {
                    "name": "voice.llm",
                    "duration_ms": 5000.0,  # 5 seconds - should trigger failure
                    "attributes": {
                        "voice.stage.type": "llm",
                        "voice.conversation.id": "conv-1",
                    },
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/failures")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1
        # Check that we have a slow_response failure
        failure_types = [f["type"] for f in data["failures"]]
        assert "slow_response" in failure_types

    def test_list_failures_filter_by_severity(self, client):
        """Test filtering failures by severity."""
        # Ingest spans that will trigger failures of different severities
        spans = {
            "spans": [
                {
                    "name": "voice.llm",
                    "duration_ms": 10000.0,  # Very slow - critical
                    "attributes": {"voice.stage.type": "llm"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Get all failures first
        all_response = client.get("/failures")
        all_data = all_response.json()

        if all_data["count"] > 0:
            # Get the severity of the first failure
            first_severity = all_data["failures"][0]["severity"]

            # Filter by that severity
            filtered_response = client.get(f"/failures?severity={first_severity}")
            filtered_data = filtered_response.json()

            # All returned failures should have the requested severity
            for failure in filtered_data["failures"]:
                assert failure["severity"] == first_severity

    def test_list_failures_filter_by_type(self, client):
        """Test filtering failures by type."""
        spans = {
            "spans": [
                {
                    "name": "voice.llm",
                    "duration_ms": 5000.0,
                    "attributes": {"voice.stage.type": "llm"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/failures?type=slow_response")

        assert response.status_code == 200
        data = response.json()
        for failure in data["failures"]:
            assert failure["type"] == "slow_response"

    def test_failures_by_severity_counts(self, client):
        """Test that by_severity counts are returned."""
        spans = {
            "spans": [
                {
                    "name": "voice.llm",
                    "duration_ms": 5000.0,
                    "attributes": {"voice.stage.type": "llm"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        response = client.get("/failures")

        assert response.status_code == 200
        data = response.json()
        assert "by_severity" in data
        assert "by_type" in data

    def test_filter_excludes_non_matching_severity(self, client):
        """Test that severity filter excludes failures with different severities."""
        # Create a slow LLM span that triggers a failure
        spans = {
            "spans": [
                {
                    "name": "voice.llm",
                    "duration_ms": 5000.0,
                    "attributes": {"voice.stage.type": "llm", "voice.conversation.id": "c1"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Verify we have at least one failure
        all_response = client.get("/failures")
        all_data = all_response.json()
        assert all_data["count"] >= 1, "Expected at least one failure"

        # Filter by a severity that doesn't exist - should exclude all failures
        filtered = client.get("/failures?severity=nonexistent_severity")
        filtered_data = filtered.json()
        # All failures should be filtered out (continue executed for each)
        assert filtered_data["count"] == 0

    def test_filter_excludes_non_matching_type(self, client):
        """Test that type filter excludes failures with different types."""
        # Create a slow LLM failure
        spans = {
            "spans": [
                {
                    "name": "voice.llm",
                    "duration_ms": 5000.0,
                    "attributes": {"voice.stage.type": "llm"},
                },
            ]
        }
        client.post("/ingest", json=spans)

        # Filter by a type that doesn't exist - should exclude everything
        response = client.get("/failures?type=nonexistent_type")

        assert response.status_code == 200
        data = response.json()
        # The slow_response failures should be excluded
        assert data["count"] == 0
        assert len(data["failures"]) == 0
