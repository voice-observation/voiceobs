"""Execution configuration settings for scenario calls and egress."""

import os

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExecutionSettings(BaseSettings):
    """Settings for scenario execution and LiveKit Egress.

    Egress recordings are uploaded to S3. LiveKit egress requires explicit
    AWS credentials. Uses VOICEOBS_AUDIO_S3_ACCESS_KEY/SECRET, or falls back
    to AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VOICEOBS_",
        extra="ignore",
    )

    # Egress S3 config
    # Env: VOICEOBS_AUDIO_STORAGE_PROVIDER, VOICEOBS_AUDIO_STORAGE_PATH,
    # VOICEOBS_AUDIO_S3_REGION, VOICEOBS_AUDIO_S3_ACCESS_KEY, VOICEOBS_AUDIO_S3_SECRET
    # Fallback: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    audio_storage_provider: str = "local"
    audio_storage_path: str = ""
    audio_s3_region: str = "us-east-1"
    audio_s3_access_key: str = ""
    audio_s3_secret: str = ""

    @model_validator(mode="after")
    def _fallback_aws_credentials(self) -> "ExecutionSettings":
        """Fall back to standard AWS env vars when VOICEOBS-specific ones are unset."""
        if not self.audio_s3_access_key:
            self.audio_s3_access_key = os.environ.get("AWS_ACCESS_KEY_ID", "")
        if not self.audio_s3_secret:
            self.audio_s3_secret = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
        return self


def get_execution_settings() -> ExecutionSettings:
    """Get execution settings instance.

    Returns:
        ExecutionSettings instance
    """
    return ExecutionSettings()
