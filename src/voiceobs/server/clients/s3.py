"""S3 storage client for audio files."""

from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

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
            from botocore.config import Config

            session = boto3.Session(
                aws_access_key_id=self._aws_access_key_id,
                aws_secret_access_key=self._aws_secret_access_key,
                region_name=self.aws_region,
            )
            # Use SigV4 explicitly - SigV2 (AWSAccessKeyId/Signature/Expires) is deprecated
            # and fails for many buckets/regions. SigV4 uses X-Amz-* params and works everywhere.
            config = Config(signature_version="s3v4")
            self._s3_client = session.client("s3", config=config)
        return self._s3_client

    def _get_s3_key(self, conversation_id: str, audio_type: str | None = None) -> str:
        """Generate S3 key for a conversation ID."""
        if audio_type:
            return f"{conversation_id}-{audio_type}.wav"
        return f"{conversation_id}.wav"

    def _get_s3_url(self, conversation_id: str, audio_type: str | None = None) -> str:
        """Generate S3 URL for a conversation ID."""
        return f"s3://{self.bucket_name}/{self._get_s3_key(conversation_id, audio_type)}"

    async def save(
        self, audio_data: bytes, conversation_id: str, audio_type: str | None = None
    ) -> str:
        """Save audio data to S3."""
        import asyncio

        s3_key = self._get_s3_key(conversation_id, audio_type)

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
        """Retrieve audio data from S3."""
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
            return None

    async def exists(self, audio_id: str) -> bool:
        """Check if audio file exists in S3."""
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
            return False

    async def delete(self, audio_id: str) -> bool:
        """Delete audio file from S3."""
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
            return False

    async def get_presigned_url(self, audio_id: str, expiry: int | None = None) -> str:
        """Generate a presigned URL for accessing audio file."""
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

    async def get_presigned_url_from_s3_url(self, s3_url: str, expiry: int | None = None) -> str:
        """Generate a presigned URL from an S3 URL."""
        import asyncio

        if not s3_url.startswith("s3://"):
            raise ValueError(f"Invalid S3 URL format: {s3_url}")

        url_parts = s3_url[5:].split("/", 1)
        if len(url_parts) != 2:
            raise ValueError(f"Invalid S3 URL format: {s3_url}")

        bucket_name, s3_key = url_parts

        if bucket_name != self.bucket_name:
            raise ValueError(
                f"S3 URL bucket '{bucket_name}' does not match configured bucket "
                f"'{self.bucket_name}'"
            )

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
        """Store audio data with a custom prefix pattern."""
        import asyncio

        from voiceobs.server.utils.media import get_extension_from_content_type

        extension = get_extension_from_content_type(content_type)
        if content_type is None:
            content_type = "audio/wav"

        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}{extension}"
        s3_key = f"{prefix}/{filename}"

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

        return f"s3://{self.bucket_name}/{s3_key}"

    async def get_by_s3_url(self, s3_url: str) -> bytes | None:
        """Retrieve audio data from S3 by s3:// URL."""
        import asyncio

        if not s3_url.startswith("s3://"):
            return None

        url_parts = s3_url[5:].split("/", 1)
        if len(url_parts) != 2:
            return None

        bucket_name, s3_key = url_parts

        if bucket_name != self.bucket_name:
            return None

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key),
            )
            return response["Body"].read()
        except Exception:
            return None

    async def delete_by_url(self, url: str) -> bool:
        """Delete audio file by its S3 URL."""
        import asyncio

        if not url.startswith("s3://"):
            return False

        url_parts = url[5:].split("/", 1)
        if len(url_parts) != 2:
            return False

        bucket_name, s3_key = url_parts

        if bucket_name != self.bucket_name:
            return False

        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key),
            )
            return True
        except Exception:
            return False
