"""Tests for storage utility functions."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.storage import AudioStorage
from voiceobs.server.utils.storage import (
    get_audio_storage_from_env,
    get_presigned_url_for_audio,
    get_presigned_url_if_s3,
)


class TestGetAudioStorageFromEnv:
    """Tests for get_audio_storage_from_env function."""

    @patch.dict(os.environ, {}, clear=True)
    def test_default_local_storage(self):
        """Test default is local storage."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "local"
        # Check that it's a LocalFileStorage instance
        from voiceobs.server.storage.local import LocalFileStorage

        assert isinstance(storage._provider, LocalFileStorage)

    @patch.dict(os.environ, {"VOICEOBS_AUDIO_STORAGE_PROVIDER": "local"})
    def test_explicit_local_storage(self):
        """Test explicit local storage."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "local"

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "local",
            "VOICEOBS_AUDIO_STORAGE_PATH": "/tmp/test-custom-path",
        },
    )
    def test_local_storage_custom_path(self):
        """Test local storage with custom path."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "local"
        from voiceobs.server.storage.local import LocalFileStorage

        assert isinstance(storage._provider, LocalFileStorage)
        assert str(storage._provider.base_path) == "/tmp/test-custom-path"

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3",
            "VOICEOBS_AUDIO_STORAGE_PATH": "my-bucket",
            "VOICEOBS_AUDIO_S3_REGION": "us-west-2",
        },
    )
    def test_s3_storage_with_path(self):
        """Test S3 storage using VOICEOBS_AUDIO_STORAGE_PATH as bucket."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "s3"
        from voiceobs.server.storage.s3 import S3Storage

        assert isinstance(storage._provider, S3Storage)

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3",
            "VOICEOBS_AUDIO_S3_BUCKET": "custom-bucket",
            "VOICEOBS_AUDIO_S3_REGION": "eu-west-1",
        },
    )
    def test_s3_storage_with_bucket_env_var(self):
        """Test S3 storage using VOICEOBS_AUDIO_S3_BUCKET."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "s3"
        from voiceobs.server.storage.s3 import S3Storage

        assert isinstance(storage._provider, S3Storage)

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3",
            "VOICEOBS_AUDIO_S3_BUCKET": "bucket1",
            "VOICEOBS_AUDIO_STORAGE_PATH": "bucket2",
        },
    )
    def test_s3_storage_bucket_precedence(self):
        """Test S3_BUCKET takes precedence over STORAGE_PATH."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "s3"
        # The bucket should be bucket1 (S3_BUCKET takes precedence)
        from voiceobs.server.storage.s3 import S3Storage

        assert isinstance(storage._provider, S3Storage)

    @patch.dict(
        os.environ,
        {"VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3", "VOICEOBS_AUDIO_STORAGE_PATH": "test-bucket"},
    )
    def test_s3_storage_default_region(self):
        """Test S3 storage defaults to us-east-1."""
        storage = get_audio_storage_from_env()

        assert storage._provider_name == "s3"
        from voiceobs.server.storage.s3 import S3Storage

        assert isinstance(storage._provider, S3Storage)


class TestGetPresignedUrlIfS3:
    """Tests for get_presigned_url_if_s3 function."""

    @pytest.mark.asyncio
    async def test_non_s3_url_returns_as_is(self):
        """Test non-S3 URL is returned as-is."""
        mock_storage = MagicMock(spec=AudioStorage)
        mock_storage._provider_name = "local"

        result = await get_presigned_url_if_s3(mock_storage, "https://example.com/audio.mp3")

        assert result == "https://example.com/audio.mp3"

    @pytest.mark.asyncio
    async def test_none_url_returns_none(self):
        """Test None URL returns None."""
        mock_storage = MagicMock(spec=AudioStorage)

        result = await get_presigned_url_if_s3(mock_storage, None)

        assert result is None

    @pytest.mark.asyncio
    async def test_empty_string_returns_empty(self):
        """Test empty string URL returns empty string."""
        mock_storage = MagicMock(spec=AudioStorage)

        result = await get_presigned_url_if_s3(mock_storage, "")

        assert result == ""

    @pytest.mark.asyncio
    async def test_s3_url_with_local_storage_returns_as_is(self):
        """Test S3 URL with local storage returns as-is."""
        mock_storage = MagicMock(spec=AudioStorage)
        mock_storage._provider_name = "local"

        result = await get_presigned_url_if_s3(mock_storage, "s3://bucket/key")

        assert result == "s3://bucket/key"

    @pytest.mark.asyncio
    async def test_s3_url_with_s3_storage_generates_presigned(self):
        """Test S3 URL with S3 storage generates presigned URL."""
        mock_storage = MagicMock(spec=AudioStorage)
        mock_storage._provider_name = "s3"
        mock_s3_provider = AsyncMock()
        mock_s3_provider.get_presigned_url_from_s3_url.return_value = (
            "https://presigned-url.com/audio"
        )
        mock_storage._provider = mock_s3_provider

        result = await get_presigned_url_if_s3(mock_storage, "s3://bucket/key")

        assert result == "https://presigned-url.com/audio"
        mock_s3_provider.get_presigned_url_from_s3_url.assert_called_once_with(
            "s3://bucket/key", expiry=None
        )

    @pytest.mark.asyncio
    async def test_s3_url_with_custom_expiry(self):
        """Test S3 URL with custom expiry."""
        mock_storage = MagicMock(spec=AudioStorage)
        mock_storage._provider_name = "s3"
        mock_s3_provider = AsyncMock()
        mock_s3_provider.get_presigned_url_from_s3_url.return_value = (
            "https://presigned-url.com/audio"
        )
        mock_storage._provider = mock_s3_provider

        result = await get_presigned_url_if_s3(mock_storage, "s3://bucket/key", expiry=3600)

        assert result == "https://presigned-url.com/audio"
        mock_s3_provider.get_presigned_url_from_s3_url.assert_called_once_with(
            "s3://bucket/key", expiry=3600
        )


class TestGetPresignedUrlForAudio:
    """Tests for get_presigned_url_for_audio function."""

    @pytest.mark.asyncio
    async def test_none_url_returns_none(self):
        """Test None URL returns None."""
        result = await get_presigned_url_for_audio(None)

        assert result is None

    @pytest.mark.asyncio
    @patch("voiceobs.server.dependencies.get_audio_storage")
    @patch("voiceobs.server.utils.storage.get_presigned_url_if_s3")
    async def test_delegates_to_get_presigned_url_if_s3(self, mock_get_presigned, mock_get_storage):
        """Test function delegates to get_presigned_url_if_s3."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_get_presigned.return_value = "https://presigned-url.com/audio"

        result = await get_presigned_url_for_audio("s3://bucket/key", expiry=3600)

        assert result == "https://presigned-url.com/audio"
        mock_get_storage.assert_called_once()
        mock_get_presigned.assert_called_once_with(mock_storage, "s3://bucket/key", expiry=3600)

    @pytest.mark.asyncio
    @patch("voiceobs.server.dependencies.get_audio_storage")
    @patch("voiceobs.server.utils.storage.get_presigned_url_if_s3")
    async def test_with_default_expiry(self, mock_get_presigned, mock_get_storage):
        """Test function with default expiry."""
        mock_storage = MagicMock()
        mock_get_storage.return_value = mock_storage
        mock_get_presigned.return_value = "https://presigned-url.com/audio"

        result = await get_presigned_url_for_audio("s3://bucket/key")

        assert result == "https://presigned-url.com/audio"
        mock_get_storage.assert_called_once()
        mock_get_presigned.assert_called_once_with(mock_storage, "s3://bucket/key", expiry=None)
