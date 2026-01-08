"""S3 storage provider for audio files."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

from voiceobs.server.storage.base import get_extension_from_content_type

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class S3Storage:
    """S3 storage provider for audio files.

    Uploads audio files to S3 and generates presigned URLs for access.
    """

    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_region: str = "us-east-1",
        presigned_url_expiry: int = 3600,
    ) -> None:
        """Initialize S3 storage provider.

        Args:
            bucket_name: S3 bucket name.
            aws_access_key_id: AWS access key ID (optional, uses env/default).
            aws_secret_access_key: AWS secret access key (optional, uses env/default).
            aws_region: AWS region name.
            presigned_url_expiry: Presigned URL expiry time in seconds.
        """
        try:
            import boto3  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            ) from e

        self.bucket_name = bucket_name
        self.aws_region = aws_region
        self.presigned_url_expiry = presigned_url_expiry

        # Initialize S3 client
        self._s3_client: S3Client | None = None
        self._aws_access_key_id = aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
        self._aws_secret_access_key = aws_secret_access_key or os.environ.get(
            "AWS_SECRET_ACCESS_KEY"
        )

    @property
    def s3_client(self) -> S3Client:
        """Get or create S3 client."""
        if self._s3_client is None:
            import boto3

            session = boto3.Session(
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self.aws_region,
            )
            self._s3_client = session.client("s3")
        return self._s3_client

    def _get_s3_key(self, conversation_id: str, audio_type: str | None = None) -> str:
        """Generate S3 key for a conversation ID.

        Args:
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").

        Returns:
            S3 key string.
        """
        if audio_type:
            return f"{conversation_id}-{audio_type}.wav"
        return f"{conversation_id}.wav"

    def _get_s3_url(self, conversation_id: str, audio_type: str | None = None) -> str:
        """Generate S3 URL for a conversation ID.

        Args:
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier.

        Returns:
            S3 URL string.
        """
        return f"s3://{self.bucket_name}/{self._get_s3_key(conversation_id, audio_type)}"

    async def save(
        self, audio_data: bytes, conversation_id: str, audio_type: str | None = None
    ) -> str:
        """Save audio data to S3.

        Args:
            audio_data: Raw audio data bytes.
            conversation_id: Conversation identifier.
            audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").

        Returns:
            S3 URL to the stored file.
        """
        import asyncio

        s3_key = self._get_s3_key(conversation_id, audio_type)

        # Upload to S3 (boto3 is sync, so we run in executor)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=audio_data,
                ContentType="audio/wav",
            ),
        )

        return self._get_s3_url(conversation_id, audio_type)

    async def get(self, audio_id: str) -> bytes | None:
        """Retrieve audio data from S3.

        Args:
            audio_id: Conversation ID (S3 key without extension).

        Returns:
            Audio data bytes or None if not found.
        """
        import asyncio

        s3_key = self._get_s3_key(audio_id)

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key),
            )
            return response["Body"].read()
        except Exception:
            # Handle NoSuchKey and other client errors
            return None

    async def exists(self, audio_id: str) -> bool:
        """Check if audio file exists in S3.

        Args:
            audio_id: Conversation ID.

        Returns:
            True if file exists, False otherwise.
        """
        import asyncio

        s3_key = self._get_s3_key(audio_id)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key),
            )
            return True
        except Exception:
            # Handle NoSuchKey and other client errors
            return False

    async def delete(self, audio_id: str) -> bool:
        """Delete audio file from S3.

        Args:
            audio_id: Conversation ID.

        Returns:
            True if deleted, False if not found.
        """
        import asyncio

        s3_key = self._get_s3_key(audio_id)

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key),
            )
            return True
        except Exception:
            # Handle any errors (file may not exist)
            return False

    async def get_presigned_url(self, audio_id: str, expiry: int | None = None) -> str:
        """Generate a presigned URL for accessing audio file.

        Args:
            audio_id: Conversation ID.
            expiry: URL expiry time in seconds (defaults to configured value).

        Returns:
            Presigned URL string.
        """
        import asyncio

        s3_key = self._get_s3_key(audio_id)
        expiry_seconds = expiry or self.presigned_url_expiry

        loop = asyncio.get_event_loop()
        url = await loop.run_in_executor(
            None,
            lambda: self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expiry_seconds,
            ),
        )
        return url

    async def store_audio(
        self, audio_data: bytes, prefix: str, content_type: str | None = None
    ) -> str:
        """Store audio data with a custom prefix pattern.

        Args:
            audio_data: Raw audio data bytes.
            prefix: Prefix pattern for file storage (e.g., "personas/preview/persona-id").
            content_type: MIME type of the audio (e.g., "audio/mpeg", "audio/wav").
                Defaults to "audio/wav" if not provided.

        Returns:
            S3 URL to the stored file.
        """
        import asyncio

        # Determine file extension from content type
        extension = get_extension_from_content_type(content_type)

        # Default content type if not provided
        if content_type is None:
            content_type = "audio/wav"

        # Generate unique filename with prefix
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{extension}"

        # Create S3 key with prefix
        s3_key = f"{prefix}/{filename}"

        # Upload to S3
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=audio_data,
                ContentType=content_type,
            ),
        )

        # Return S3 URL
        return f"s3://{self.bucket_name}/{s3_key}"
