"""Tests for S3Storage delete_by_url functionality."""

from unittest.mock import MagicMock, patch

import pytest


class TestS3DeleteByUrl:
    """Tests for S3Storage.delete_by_url method."""

    @pytest.mark.asyncio
    async def test_s3_delete_by_url(self):
        """Test delete_by_url for S3 storage."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            from voiceobs.server.storage.s3 import S3Storage

            storage = S3Storage(bucket_name="test-bucket")

            # Test valid S3 URL
            result = await storage.delete_by_url(
                "s3://test-bucket/personas/preview/test-id/file.mp3"
            )
            assert result is True
            mock_client.delete_object.assert_called_once_with(
                Bucket="test-bucket", Key="personas/preview/test-id/file.mp3"
            )

    @pytest.mark.asyncio
    async def test_s3_delete_by_url_wrong_bucket(self):
        """Test delete_by_url returns False for wrong bucket."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            from voiceobs.server.storage.s3 import S3Storage

            storage = S3Storage(bucket_name="test-bucket")

            result = await storage.delete_by_url("s3://wrong-bucket/key.mp3")
            assert result is False
            mock_client.delete_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_s3_delete_by_url_invalid_format(self):
        """Test delete_by_url returns False for invalid URL."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            from voiceobs.server.storage.s3 import S3Storage

            storage = S3Storage(bucket_name="test-bucket")

            result = await storage.delete_by_url("invalid-url")
            assert result is False
            mock_client.delete_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_s3_delete_by_url_non_s3_url(self):
        """Test delete_by_url returns False for non-S3 URL formats."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            from voiceobs.server.storage.s3 import S3Storage

            storage = S3Storage(bucket_name="test-bucket")

            # HTTP URL should fail
            result = await storage.delete_by_url("https://example.com/file.mp3")
            assert result is False
            mock_client.delete_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_s3_delete_by_url_empty_key(self):
        """Test delete_by_url returns False for S3 URL with no key."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_session.return_value.client.return_value = mock_client

            from voiceobs.server.storage.s3 import S3Storage

            storage = S3Storage(bucket_name="test-bucket")

            # S3 URL with just bucket, no key
            result = await storage.delete_by_url("s3://test-bucket")
            assert result is False
            mock_client.delete_object.assert_not_called()

    @pytest.mark.asyncio
    async def test_s3_delete_by_url_handles_exception(self):
        """Test delete_by_url returns False when S3 delete fails."""
        with patch("boto3.Session") as mock_session:
            mock_client = MagicMock()
            mock_client.delete_object.side_effect = Exception("S3 error")
            mock_session.return_value.client.return_value = mock_client

            from voiceobs.server.storage.s3 import S3Storage

            storage = S3Storage(bucket_name="test-bucket")

            result = await storage.delete_by_url(
                "s3://test-bucket/personas/preview/test-id/file.mp3"
            )
            assert result is False
