"""Tests for storage utility functions."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGetAudioStorageFromEnv:
    """Tests for get_audio_storage_from_env function."""

    @patch.dict(os.environ, {}, clear=True)
    @patch("voiceobs.server.utils.storage.AudioStorage")
    def test_default_local_storage(self, mock_audio_storage):
        """Should return local storage with defaults when no env vars set."""
        from voiceobs.server.utils.storage import get_audio_storage_from_env

        get_audio_storage_from_env()

        mock_audio_storage.assert_called_once_with(
            provider="local",
            base_path="/tmp/voiceobs-audio",
        )

    @patch.dict(
        os.environ,
        {"VOICEOBS_AUDIO_STORAGE_PROVIDER": "local", "VOICEOBS_AUDIO_STORAGE_PATH": "/custom/path"},
        clear=True,
    )
    @patch("voiceobs.server.utils.storage.AudioStorage")
    def test_custom_local_storage_path(self, mock_audio_storage):
        """Should use custom path for local storage."""
        from voiceobs.server.utils.storage import get_audio_storage_from_env

        get_audio_storage_from_env()

        mock_audio_storage.assert_called_once_with(
            provider="local",
            base_path="/custom/path",
        )

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3",
            "VOICEOBS_AUDIO_STORAGE_PATH": "my-bucket",
        },
        clear=True,
    )
    @patch("voiceobs.server.utils.storage.AudioStorage")
    def test_s3_storage_with_bucket_from_path(self, mock_audio_storage):
        """Should use VOICEOBS_AUDIO_STORAGE_PATH as bucket name for S3."""
        from voiceobs.server.utils.storage import get_audio_storage_from_env

        get_audio_storage_from_env()

        mock_audio_storage.assert_called_once_with(
            provider="s3",
            base_path="my-bucket",
            aws_region="us-east-1",
        )

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3",
            "VOICEOBS_AUDIO_STORAGE_PATH": "default-bucket",
            "VOICEOBS_AUDIO_S3_BUCKET": "explicit-bucket",
        },
        clear=True,
    )
    @patch("voiceobs.server.utils.storage.AudioStorage")
    def test_s3_storage_with_explicit_bucket(self, mock_audio_storage):
        """Should prefer VOICEOBS_AUDIO_S3_BUCKET over VOICEOBS_AUDIO_STORAGE_PATH."""
        from voiceobs.server.utils.storage import get_audio_storage_from_env

        get_audio_storage_from_env()

        mock_audio_storage.assert_called_once_with(
            provider="s3",
            base_path="explicit-bucket",
            aws_region="us-east-1",
        )

    @patch.dict(
        os.environ,
        {
            "VOICEOBS_AUDIO_STORAGE_PROVIDER": "s3",
            "VOICEOBS_AUDIO_STORAGE_PATH": "my-bucket",
            "VOICEOBS_AUDIO_S3_REGION": "eu-west-1",
        },
        clear=True,
    )
    @patch("voiceobs.server.utils.storage.AudioStorage")
    def test_s3_storage_with_custom_region(self, mock_audio_storage):
        """Should use custom AWS region for S3."""
        from voiceobs.server.utils.storage import get_audio_storage_from_env

        get_audio_storage_from_env()

        mock_audio_storage.assert_called_once_with(
            provider="s3",
            base_path="my-bucket",
            aws_region="eu-west-1",
        )


class TestGetPresignedUrlIfS3:
    """Tests for get_presigned_url_if_s3 function."""

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_url(self):
        """Should return empty string for empty URL."""
        from voiceobs.server.utils.storage import get_presigned_url_if_s3

        mock_storage = MagicMock()
        result = await get_presigned_url_if_s3(mock_storage, "")
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_none_for_none_url(self):
        """Should return falsy value for None URL."""
        from voiceobs.server.utils.storage import get_presigned_url_if_s3

        mock_storage = MagicMock()
        result = await get_presigned_url_if_s3(mock_storage, None)
        assert not result

    @pytest.mark.asyncio
    async def test_returns_original_for_non_s3_url(self):
        """Should return original URL for non-S3 URLs."""
        from voiceobs.server.utils.storage import get_presigned_url_if_s3

        mock_storage = MagicMock()
        mock_storage._provider_name = "local"

        result = await get_presigned_url_if_s3(mock_storage, "https://example.com/audio.wav")
        assert result == "https://example.com/audio.wav"

    @pytest.mark.asyncio
    async def test_returns_original_when_storage_not_s3(self):
        """Should return original S3 URL when storage provider is not S3."""
        from voiceobs.server.utils.storage import get_presigned_url_if_s3

        mock_storage = MagicMock()
        mock_storage._provider_name = "local"

        result = await get_presigned_url_if_s3(mock_storage, "s3://bucket/key.wav")
        assert result == "s3://bucket/key.wav"

    @pytest.mark.asyncio
    async def test_returns_presigned_url_for_s3(self):
        """Should return presigned URL for S3 URLs when storage is S3."""
        from voiceobs.server.utils.storage import get_presigned_url_if_s3

        mock_storage = MagicMock()
        mock_storage._provider_name = "s3"

        mock_s3_provider = MagicMock()
        mock_s3_provider.get_presigned_url_from_s3_url = AsyncMock(
            return_value="https://bucket.s3.amazonaws.com/key.wav?signed=xyz"
        )
        mock_storage._provider = mock_s3_provider

        result = await get_presigned_url_if_s3(mock_storage, "s3://bucket/key.wav")
        assert result == "https://bucket.s3.amazonaws.com/key.wav?signed=xyz"
        mock_s3_provider.get_presigned_url_from_s3_url.assert_called_once_with(
            "s3://bucket/key.wav", expiry=None
        )

    @pytest.mark.asyncio
    async def test_passes_expiry_to_s3_provider(self):
        """Should pass expiry parameter to S3 provider."""
        from voiceobs.server.utils.storage import get_presigned_url_if_s3

        mock_storage = MagicMock()
        mock_storage._provider_name = "s3"

        mock_s3_provider = MagicMock()
        mock_s3_provider.get_presigned_url_from_s3_url = AsyncMock(
            return_value="https://signed.url"
        )
        mock_storage._provider = mock_s3_provider

        await get_presigned_url_if_s3(mock_storage, "s3://bucket/key.wav", expiry=3600)
        mock_s3_provider.get_presigned_url_from_s3_url.assert_called_once_with(
            "s3://bucket/key.wav", expiry=3600
        )


class TestGetPresignedUrlForAudio:
    """Tests for get_presigned_url_for_audio function."""

    @pytest.mark.asyncio
    async def test_returns_none_for_none_url(self):
        """Should return None for None URL."""
        from voiceobs.server.utils.storage import get_presigned_url_for_audio

        result = await get_presigned_url_for_audio(None)
        assert result is None

    @pytest.mark.asyncio
    @patch("voiceobs.server.dependencies.get_audio_storage")
    async def test_calls_get_presigned_url_if_s3(self, mock_get_storage):
        """Should call get_presigned_url_if_s3 with storage and URL."""
        from voiceobs.server.utils.storage import get_presigned_url_for_audio

        mock_storage = MagicMock()
        mock_storage._provider_name = "s3"
        mock_s3_provider = MagicMock()
        mock_s3_provider.get_presigned_url_from_s3_url = AsyncMock(
            return_value="https://signed.url"
        )
        mock_storage._provider = mock_s3_provider
        mock_get_storage.return_value = mock_storage

        result = await get_presigned_url_for_audio("s3://bucket/key.wav", expiry=7200)

        mock_get_storage.assert_called_once()
        assert result == "https://signed.url"

    @pytest.mark.asyncio
    @patch("voiceobs.server.dependencies.get_audio_storage")
    async def test_returns_original_for_non_s3_url(self, mock_get_storage):
        """Should return original URL for non-S3 URLs."""
        from voiceobs.server.utils.storage import get_presigned_url_for_audio

        mock_storage = MagicMock()
        mock_storage._provider_name = "local"
        mock_get_storage.return_value = mock_storage

        result = await get_presigned_url_for_audio("https://example.com/audio.wav")

        assert result == "https://example.com/audio.wav"
