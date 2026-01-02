"""Tests for AudioStorage wrapper class."""

import sys

import pytest

from voiceobs.server.storage import AudioStorage, LocalFileStorage, S3Storage


class TestAudioStorage:
    """Tests for AudioStorage wrapper class."""

    def test_init_local_storage(self, tmp_path):
        """Test initializing AudioStorage with local provider."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        assert storage._provider_name == "local"
        assert isinstance(storage._provider, LocalFileStorage)

    def test_init_local_storage_requires_base_path(self):
        """Test that local storage requires base_path."""
        with pytest.raises(ValueError, match="base_path is required"):
            AudioStorage(provider="local")

    def test_init_s3_storage(self, monkeypatch):
        """Test initializing AudioStorage with S3 provider."""
        # Mock boto3 import
        sys.modules["boto3"] = type(sys)("boto3")

        storage = AudioStorage(provider="s3", base_path="test-bucket")

        assert storage._provider_name == "s3"
        assert isinstance(storage._provider, S3Storage)

    def test_init_s3_storage_requires_base_path(self, monkeypatch):
        """Test that S3 storage requires base_path."""
        sys.modules["boto3"] = type(sys)("boto3")

        with pytest.raises(ValueError, match="base_path.*bucket name"):
            AudioStorage(provider="s3")

    def test_init_unknown_provider(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown storage provider"):
            AudioStorage(provider="unknown")

    async def test_save_delegates_to_provider(self, tmp_path):
        """Test that save delegates to provider."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        url = await storage.save(audio_data, conversation_id)

        assert url == "/audio/conv-123"
        assert (tmp_path / "conv-123.wav").exists()

    async def test_save_with_audio_type(self, tmp_path):
        """Test that save with audio_type delegates to provider."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        url = await storage.save(audio_data, conversation_id, audio_type="asr")

        assert url == "/audio/conv-123?type=asr"
        assert (tmp_path / "conv-123-asr.wav").exists()

    async def test_get_delegates_to_provider(self, tmp_path):
        """Test that get delegates to provider."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        await storage.save(audio_data, conversation_id)
        retrieved = await storage.get(conversation_id)

        assert retrieved == audio_data

    async def test_exists_delegates_to_provider(self, tmp_path):
        """Test that exists delegates to provider."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))
        conversation_id = "conv-123"

        assert await storage.exists(conversation_id) is False

        await storage.save(b"data", conversation_id)
        assert await storage.exists(conversation_id) is True

    async def test_delete_delegates_to_provider(self, tmp_path):
        """Test that delete delegates to provider."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))
        conversation_id = "conv-123"

        await storage.save(b"data", conversation_id)
        deleted = await storage.delete(conversation_id)

        assert deleted is True
        assert not (tmp_path / "conv-123.wav").exists()
