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


class TestAudioStorageStoreAudio:
    """Tests for AudioStorage.store_audio() method."""

    def test_store_audio_with_prefix_and_content_type(self, audio_storage, audio_data):
        """Test that store_audio saves file with prefix pattern."""
        import asyncio
        import uuid

        persona_id = str(uuid.uuid4())
        prefix = f"personas/preview/{persona_id}"
        content_type = "audio/mpeg"

        # Store audio with prefix
        audio_url = asyncio.run(
            audio_storage.store_audio(audio_data, prefix=prefix, content_type=content_type)
        )

        # Verify URL is returned
        assert audio_url is not None
        assert isinstance(audio_url, str)
        assert len(audio_url) > 0

    def test_store_audio_local_creates_subdirectories(self, tmp_path, monkeypatch, audio_data):
        """Test that store_audio creates subdirectories for local storage."""
        import asyncio

        from voiceobs.server.dependencies import reset_dependencies
        from voiceobs.server.storage import AudioStorage

        reset_dependencies()
        monkeypatch.setenv("VOICEOBS_AUDIO_STORAGE_PROVIDER", "local")
        monkeypatch.setenv("VOICEOBS_AUDIO_STORAGE_PATH", str(tmp_path))

        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        persona_id = "test-persona-123"
        prefix = f"personas/preview/{persona_id}"

        # Store audio
        asyncio.run(storage.store_audio(audio_data, prefix=prefix))

        # Verify subdirectories were created
        expected_dir = tmp_path / "personas" / "preview" / persona_id
        assert expected_dir.exists()
        assert expected_dir.is_dir()

        # Verify file exists (defaults to .wav when content_type not specified)
        files = list(expected_dir.glob("*.wav"))
        assert len(files) >= 1

        reset_dependencies()

    def test_store_audio_returns_different_urls_for_different_prefixes(
        self, audio_storage, audio_data
    ):
        """Test that store_audio returns different URLs for different prefixes."""
        import asyncio

        prefix1 = "personas/preview/persona-1"
        prefix2 = "personas/preview/persona-2"

        url1 = asyncio.run(audio_storage.store_audio(audio_data, prefix=prefix1))
        url2 = asyncio.run(audio_storage.store_audio(audio_data, prefix=prefix2))

        # URLs should be different
        assert url1 != url2

    def test_store_audio_with_content_type_audio_mpeg(self, audio_storage, audio_data):
        """Test store_audio with audio/mpeg content type."""
        import asyncio

        prefix = "personas/preview/test"
        content_type = "audio/mpeg"

        url = asyncio.run(
            audio_storage.store_audio(audio_data, prefix=prefix, content_type=content_type)
        )

        assert url is not None
        # URL should indicate mp3 file
        assert ".mp3" in url or "audio/mpeg" in url or "mpeg" in url

    def test_store_audio_with_content_type_audio_wav(self, audio_storage, audio_data):
        """Test store_audio with audio/wav content type."""
        import asyncio

        prefix = "personas/preview/test"
        content_type = "audio/wav"

        url = asyncio.run(
            audio_storage.store_audio(audio_data, prefix=prefix, content_type=content_type)
        )

        assert url is not None
        # URL should indicate wav file
        assert ".wav" in url or "audio/wav" in url or "wav" in url

    def test_store_audio_defaults_to_audio_wav(self, audio_storage, audio_data):
        """Test that store_audio defaults to audio/wav when content_type not specified."""
        import asyncio

        prefix = "personas/preview/test"

        url = asyncio.run(audio_storage.store_audio(audio_data, prefix=prefix))

        assert url is not None
        # Should default to wav
        assert ".wav" in url or "audio/wav" in url or "wav" in url
