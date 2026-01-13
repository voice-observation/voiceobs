"""Storage utility functions for the voiceobs server."""

import os
from typing import TYPE_CHECKING

from voiceobs.server.storage import AudioStorage

if TYPE_CHECKING:
    from voiceobs.server.storage.s3 import S3Storage


def get_audio_storage_from_env() -> AudioStorage:
    """Get audio storage instance from environment configuration.

    This is a utility function that creates a new AudioStorage instance
    based on environment variables. For a singleton instance in the application,
    use `voiceobs.server.dependencies.get_audio_storage()` instead.

    Environment variables:
        VOICEOBS_AUDIO_STORAGE_PROVIDER: Storage provider ("local" or "s3", default: "local")
        VOICEOBS_AUDIO_STORAGE_PATH: Base path for local storage or bucket name for S3
        VOICEOBS_AUDIO_S3_BUCKET: S3 bucket name (optional, uses
            VOICEOBS_AUDIO_STORAGE_PATH if not set)
        VOICEOBS_AUDIO_S3_REGION: AWS region for S3 (default: "us-east-1")

    For S3 storage, AWS credentials must be provided via one of:
        - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables
        - AWS credentials file (~/.aws/credentials)
        - IAM role (if running on EC2/ECS/Lambda)
        - AWS_PROFILE environment variable (to use a specific profile)

    Returns:
        AudioStorage instance configured from environment variables.

    Example:
        >>> storage = get_audio_storage_from_env()
        >>> url = await storage.store_audio(audio_data, prefix="personas/preview")
    """
    # Get configuration from environment
    provider = os.environ.get("VOICEOBS_AUDIO_STORAGE_PROVIDER", "local")
    base_path = os.environ.get("VOICEOBS_AUDIO_STORAGE_PATH", "/tmp/voiceobs-audio")

    if provider == "s3":
        bucket_name = os.environ.get("VOICEOBS_AUDIO_S3_BUCKET", base_path)
        aws_region = os.environ.get("VOICEOBS_AUDIO_S3_REGION", "us-east-1")
        return AudioStorage(
            provider="s3",
            base_path=bucket_name,
            aws_region=aws_region,
        )
    else:
        return AudioStorage(
            provider="local",
            base_path=base_path,
        )


async def get_presigned_url_if_s3(
    audio_storage: AudioStorage, url: str, expiry: int | None = None
) -> str:
    """Get a presigned URL if the URL is an S3 URL, otherwise return the URL as-is.

    Args:
        audio_storage: AudioStorage instance to use for generating presigned URLs.
        url: URL to check and potentially convert to presigned URL.
        expiry: URL expiry time in seconds (only used for S3 URLs).

    Returns:
        Presigned URL if the input is an S3 URL, otherwise the original URL.
    """
    # Check if URL is an S3 URL
    if not url or not url.startswith("s3://"):
        return url

    # Check if storage provider is S3
    if audio_storage._provider_name != "s3":
        # Not S3 storage, return URL as-is
        return url

    # Access the underlying S3Storage provider
    s3_provider: S3Storage = audio_storage._provider  # type: ignore[assignment]

    # Generate presigned URL
    return await s3_provider.get_presigned_url_from_s3_url(url, expiry=expiry)


async def get_presigned_url_for_audio(url: str | None, expiry: int | None = None) -> str | None:
    """Get a presigned URL for an audio URL if using S3 storage, otherwise return as-is.

    This is a convenience function that gets the audio storage from dependencies
    and converts S3 URLs to presigned URLs.

    Args:
        url: Audio URL to convert (can be None).
        expiry: URL expiry time in seconds (only used for S3 URLs).

    Returns:
        Presigned URL if the input is an S3 URL, None if input is None,
        otherwise the original URL.
    """
    if url is None:
        return None

    # Import here to avoid circular dependencies
    from voiceobs.server.dependencies import get_audio_storage

    audio_storage = get_audio_storage()
    return await get_presigned_url_if_s3(audio_storage, url, expiry=expiry)
