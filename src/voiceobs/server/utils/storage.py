"""Storage utility functions for the voiceobs server."""

import os

from voiceobs.server.storage import AudioStorage


def get_audio_storage_from_env() -> AudioStorage:
    """Get audio storage instance from environment configuration.

    This is a utility function that creates a new AudioStorage instance
    based on environment variables. For a singleton instance in the application,
    use `voiceobs.server.dependencies.get_audio_storage()` instead.

    Environment variables:
        VOICEOBS_AUDIO_STORAGE_PROVIDER: Storage provider ("local" or "s3", default: "local")
        VOICEOBS_AUDIO_STORAGE_PATH: Base path for local storage or bucket name for S3
        VOICEOBS_AUDIO_S3_BUCKET: S3 bucket name (optional, uses VOICEOBS_AUDIO_STORAGE_PATH if not set)
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

