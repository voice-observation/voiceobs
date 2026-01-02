"""Tests for audio streaming endpoint."""

import pytest

from voiceobs.server.dependencies import get_audio_storage, reset_dependencies


@pytest.fixture
def audio_storage(tmp_path, monkeypatch):
    """Create audio storage for testing."""
    reset_dependencies()
    # Set environment to use local storage
    monkeypatch.setenv("VOICEOBS_AUDIO_STORAGE_PROVIDER", "local")
    monkeypatch.setenv("VOICEOBS_AUDIO_STORAGE_PATH", str(tmp_path))
    yield get_audio_storage()
    reset_dependencies()


@pytest.fixture
def audio_data():
    """Sample audio data for testing."""
    return b"fake wav audio data" * 100  # Make it large enough for range testing


class TestAudioEndpoint:
    """Tests for /api/v1/audio/{audio_id} endpoint."""

    def test_stream_audio_returns_200(self, client, audio_storage, audio_data):
        """Test that audio endpoint returns 200 for existing file."""
        conversation_id = "conv-123"
        # Save audio file first
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        response = client.get(f"/api/v1/audio/{conversation_id}")

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "audio/wav"
        assert response.headers["Accept-Ranges"] == "bytes"
        assert response.content == audio_data

    def test_stream_audio_returns_404_for_missing_file(self, client):
        """Test that audio endpoint returns 404 for non-existent file."""
        response = client.get("/api/v1/audio/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_stream_audio_supports_range_request_full(self, client, audio_storage, audio_data):
        """Test that audio endpoint supports full Range request."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        file_size = len(audio_data)
        headers = {"Range": f"bytes=0-{file_size - 1}"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        assert response.status_code == 206
        assert response.headers["Content-Type"] == "audio/wav"
        assert response.headers["Accept-Ranges"] == "bytes"
        assert "Content-Range" in response.headers
        assert response.content == audio_data

    def test_stream_audio_supports_range_request_partial(self, client, audio_storage, audio_data):
        """Test that audio endpoint supports partial Range request."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Request first 100 bytes
        headers = {"Range": "bytes=0-99"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        assert response.status_code == 206
        assert response.headers["Content-Type"] == "audio/wav"
        assert "Content-Range" in response.headers
        assert len(response.content) == 100
        assert response.content == audio_data[:100]

    def test_stream_audio_supports_range_request_middle(self, client, audio_storage, audio_data):
        """Test that audio endpoint supports Range request for middle portion."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Request bytes 100-199
        headers = {"Range": "bytes=100-199"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        assert response.status_code == 206
        assert len(response.content) == 100
        assert response.content == audio_data[100:200]

    def test_stream_audio_supports_range_request_from_start(
        self, client, audio_storage, audio_data
    ):
        """Test that audio endpoint supports Range request from start."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Request from start to end (no end specified)
        headers = {"Range": "bytes=0-"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        assert response.status_code == 206
        assert response.content == audio_data

    def test_stream_audio_supports_range_request_to_end(self, client, audio_storage, audio_data):
        """Test that audio endpoint supports Range request to end."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Request last 100 bytes
        file_size = len(audio_data)
        headers = {"Range": f"bytes={file_size - 100}-"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        assert response.status_code == 206
        assert len(response.content) == 100
        assert response.content == audio_data[-100:]

    def test_stream_audio_handles_invalid_range(self, client, audio_storage, audio_data):
        """Test that audio endpoint handles invalid Range header."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Invalid range (start > end)
        file_size = len(audio_data)
        headers = {"Range": f"bytes={file_size}-0"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        # Should return 416 Range Not Satisfiable
        assert response.status_code == 416

    def test_stream_audio_handles_range_beyond_file_size(self, client, audio_storage, audio_data):
        """Test that audio endpoint handles Range beyond file size."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Range beyond file size
        file_size = len(audio_data)
        headers = {"Range": f"bytes={file_size + 100}-{file_size + 200}"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        # Should clamp to file size or return 416
        assert response.status_code in [206, 416]

    def test_stream_audio_ignores_malformed_range(self, client, audio_storage, audio_data):
        """Test that audio endpoint ignores malformed Range header."""
        conversation_id = "conv-123"
        import asyncio

        asyncio.run(audio_storage.save(audio_data, conversation_id))

        # Malformed range header
        headers = {"Range": "invalid-range"}

        response = client.get(f"/api/v1/audio/{conversation_id}", headers=headers)

        # Should serve full file
        assert response.status_code == 200
        assert response.content == audio_data
