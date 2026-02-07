"""Tests for AudioStorage delete_by_url functionality."""

import pytest

from voiceobs.server.storage.base import AudioStorage


class TestDeleteByUrl:
    """Tests for AudioStorage.delete_by_url method."""

    @pytest.mark.asyncio
    async def test_delete_by_url_local_storage(self, tmp_path):
        """Test delete_by_url for local storage."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        # Store a file
        audio_data = b"test audio content"
        url = await storage.store_audio(
            audio_data, prefix="personas/preview/test-id", content_type="audio/mpeg"
        )

        # Delete by URL
        result = await storage.delete_by_url(url)
        assert result is True

        # Verify file is deleted (second delete returns False)
        result = await storage.delete_by_url(url)
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_url_nonexistent_file(self, tmp_path):
        """Test delete_by_url returns False for nonexistent file."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        result = await storage.delete_by_url("/audio/nonexistent/file.mp3")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_url_invalid_format(self, tmp_path):
        """Test delete_by_url handles invalid URL format gracefully."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        result = await storage.delete_by_url("invalid-url")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_url_empty_string(self, tmp_path):
        """Test delete_by_url handles empty string gracefully."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        result = await storage.delete_by_url("")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_by_url_with_path_traversal_attempt(self, tmp_path):
        """Test delete_by_url rejects path traversal attempts."""
        storage = AudioStorage(provider="local", base_path=str(tmp_path))

        # Attempt path traversal
        result = await storage.delete_by_url("/audio/../../../etc/passwd")
        assert result is False
