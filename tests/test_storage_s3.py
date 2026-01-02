"""Tests for S3Storage provider."""

# ruff: noqa: N803

import os
import sys

import pytest

from voiceobs.server.storage import S3Storage


class MockS3Client:  # noqa: N803
    """Mock S3 client for testing."""

    def __init__(self):
        """Initialize mock S3 client."""
        self.objects: dict[str, bytes] = {}
        self.put_object_called = False
        self.put_object_key: str | None = None
        self.put_object_body: bytes | None = None

    def put_object(  # noqa: N803
        self,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,  # noqa: N803
    ) -> None:
        """Mock put_object."""
        self.put_object_called = True
        self.put_object_key = Key
        self.put_object_body = Body
        self.objects[Key] = Body

    def get_object(self, Bucket: str, Key: str) -> dict:  # noqa: N803
        """Mock get_object."""
        if Key not in self.objects:
            raise Exception("NoSuchKey")
        return {"Body": MockS3Body(self.objects[Key])}

    def head_object(self, Bucket: str, Key: str) -> None:  # noqa: N803
        """Mock head_object."""
        if Key not in self.objects:
            raise Exception("NoSuchKey")

    def delete_object(self, Bucket: str, Key: str) -> None:  # noqa: N803
        """Mock delete_object."""
        if Key in self.objects:
            del self.objects[Key]

    def generate_presigned_url(  # noqa: N803
        self,
        ClientMethod: str,
        Params: dict,
        ExpiresIn: int,  # noqa: N803
    ) -> str:
        """Mock generate_presigned_url."""
        key = Params.get("Key", "")
        return f"https://s3.amazonaws.com/test-bucket/{key}?signature=mock"


class MockS3Body:
    """Mock S3 body object."""

    def __init__(self, data: bytes):
        """Initialize mock body."""
        self._data = data

    def read(self) -> bytes:
        """Read data."""
        return self._data


class TestS3Storage:
    """Tests for S3Storage provider."""

    def test_init_raises_import_error_without_boto3(self, monkeypatch):
        """Test that init raises ImportError if boto3 is not available."""
        # Mock import to raise ImportError
        original_import = __import__

        def mock_import(name, *args, **kwargs):
            if name == "boto3":
                raise ImportError("No module named 'boto3'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(ImportError, match="boto3 is required"):
            S3Storage(bucket_name="test-bucket")

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_save_uploads_to_s3(self, monkeypatch):
        """Test that save uploads to S3."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        # Mock boto3 client
        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        url = await storage.save(audio_data, conversation_id)

        assert url == "s3://test-bucket/conv-123.wav"
        assert mock_client.put_object_called
        assert mock_client.put_object_key == "conv-123.wav"
        assert mock_client.put_object_body == audio_data

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_save_with_audio_type(self, monkeypatch):
        """Test that save uploads to S3 with audio type."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        audio_data = b"fake audio data"
        conversation_id = "conv-123"

        url = await storage.save(audio_data, conversation_id, audio_type="tts")

        assert url == "s3://test-bucket/conv-123-tts.wav"
        assert mock_client.put_object_key == "conv-123-tts.wav"

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_get_retrieves_from_s3(self, monkeypatch):
        """Test that get retrieves from S3."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        audio_data = b"fake audio data"
        conversation_id = "conv-123"
        mock_client.objects["conv-123.wav"] = audio_data

        retrieved = await storage.get(conversation_id)

        assert retrieved == audio_data

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_get_returns_none_for_missing_file(self, monkeypatch):
        """Test that get returns None for non-existent S3 object."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        retrieved = await storage.get("nonexistent")

        assert retrieved is None

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_exists_checks_s3(self, monkeypatch):
        """Test that exists checks S3."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        mock_client.objects["conv-123.wav"] = b"data"

        exists = await storage.exists("conv-123")
        assert exists is True

        exists = await storage.exists("nonexistent")
        assert exists is False

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_delete_removes_from_s3(self, monkeypatch):
        """Test that delete removes from S3."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        mock_client.objects["conv-123.wav"] = b"data"

        deleted = await storage.delete("conv-123")
        assert deleted is True
        assert "conv-123.wav" not in mock_client.objects

    @pytest.mark.skipif(
        os.environ.get("SKIP_S3_TESTS") == "1", reason="S3 tests require AWS credentials"
    )
    async def test_get_presigned_url(self, monkeypatch):
        """Test that get_presigned_url generates presigned URL."""
        # Mock boto3 import
        mock_boto3 = type(sys)("boto3")
        monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

        mock_client = MockS3Client()
        storage = S3Storage(bucket_name="test-bucket")
        storage._s3_client = mock_client

        url = await storage.get_presigned_url("conv-123")

        assert url.startswith("https://")
        assert "conv-123.wav" in url
