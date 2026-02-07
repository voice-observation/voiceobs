"""Tests for the traits API endpoint."""


class TestTraitsEndpoint:
    """Tests for GET /api/v1/traits."""

    def test_get_traits_returns_vocabulary(self, client):
        """Test that GET /api/v1/traits returns the trait vocabulary."""
        response = client.get("/api/v1/traits")

        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "vocabulary" in data
        vocabulary = data["vocabulary"]

        # Check all categories exist
        assert "emotional_state" in vocabulary
        assert "communication_style" in vocabulary
        assert "patience_level" in vocabulary
        assert "cooperation" in vocabulary
        assert "expertise" in vocabulary

        # Check some specific traits
        assert "angry" in vocabulary["emotional_state"]
        assert "impatient" in vocabulary["patience_level"]
        assert "cooperative" in vocabulary["cooperation"]

    def test_get_traits_returns_all_traits(self, client):
        """Test that all expected traits are present."""
        response = client.get("/api/v1/traits")

        assert response.status_code == 200
        data = response.json()
        vocabulary = data["vocabulary"]

        # Flatten all traits
        all_traits = []
        for traits in vocabulary.values():
            all_traits.extend(traits)

        # Should have 32 traits total
        assert len(all_traits) == 32
