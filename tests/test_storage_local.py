"""Tests for LocalFileStorage provider."""

# ruff: noqa: N803

from voiceobs.server.storage import LocalFileStorage


class TestLocalFileStorage:
    """Tests for LocalFileStorage provider."""

    async def test_save_creates_file(self, tmp_path):
        """Test that save creates a .wav file."""
        storage = LocalFileStorage(base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        url = await storage.save(audio_data, conversation_id)

        assert url == "/audio/conv-123"
        file_path = tmp_path / "conv-123.wav"
        assert file_path.exists()
        assert file_path.read_bytes() == audio_data

    async def test_save_creates_directory(self, tmp_path):
        """Test that save creates parent directories if needed."""
        nested_path = tmp_path / "nested" / "audio"
        storage = LocalFileStorage(base_path=str(nested_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        await storage.save(audio_data, conversation_id)

        assert nested_path.exists()
        assert (nested_path / "conv-123.wav").exists()

    async def test_save_with_audio_type(self, tmp_path):
        """Test that save creates file with audio type suffix."""
        storage = LocalFileStorage(base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        url = await storage.save(audio_data, conversation_id, audio_type="asr")

        assert url == "/audio/conv-123?type=asr"
        file_path = tmp_path / "conv-123-asr.wav"
        assert file_path.exists()
        assert file_path.read_bytes() == audio_data

    async def test_get_retrieves_file(self, tmp_path):
        """Test that get retrieves saved audio data."""
        storage = LocalFileStorage(base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        await storage.save(audio_data, conversation_id)
        retrieved = await storage.get(conversation_id)

        assert retrieved == audio_data

    async def test_get_with_audio_type(self, tmp_path):
        """Test that get retrieves file with audio type."""
        storage = LocalFileStorage(base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        await storage.save(audio_data, conversation_id, audio_type="tts")
        retrieved = await storage.get(f"{conversation_id}-tts")

        assert retrieved == audio_data

    async def test_get_returns_none_for_missing_file(self, tmp_path):
        """Test that get returns None for non-existent file."""
        storage = LocalFileStorage(base_path=str(tmp_path))

        retrieved = await storage.get("nonexistent")

        assert retrieved is None

    async def test_exists_returns_true_for_saved_file(self, tmp_path):
        """Test that exists returns True for saved file."""
        storage = LocalFileStorage(base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        await storage.save(audio_data, conversation_id)
        exists = await storage.exists(conversation_id)

        assert exists is True

    async def test_exists_returns_false_for_missing_file(self, tmp_path):
        """Test that exists returns False for non-existent file."""
        storage = LocalFileStorage(base_path=str(tmp_path))

        exists = await storage.exists("nonexistent")

        assert exists is False

    async def test_delete_removes_file(self, tmp_path):
        """Test that delete removes the file."""
        storage = LocalFileStorage(base_path=str(tmp_path))
        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        await storage.save(audio_data, conversation_id)
        deleted = await storage.delete(conversation_id)

        assert deleted is True
        assert not (tmp_path / "conv-123.wav").exists()

    async def test_delete_returns_false_for_missing_file(self, tmp_path):
        """Test that delete returns False for non-existent file."""
        storage = LocalFileStorage(base_path=str(tmp_path))

        deleted = await storage.delete("nonexistent")

        assert deleted is False
