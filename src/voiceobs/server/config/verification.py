"""Verification configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class VerificationSettings(BaseSettings):
    """Settings for agent verification.

    All settings can be configured via environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LiveKit settings
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    sip_outbound_trunk_id: str

    # Verification behavior
    verification_max_turns: int = 3
    verification_max_retries: int = 3
    verification_call_timeout: int = 30
    verification_retry_base_delay: int = 30
    verification_initial_wait_timeout: float = 4.5

    def get_retry_delay(self, attempt: int) -> int:
        """Calculate retry delay with exponential backoff.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds before next retry
        """
        return self.verification_retry_base_delay * (2 ** (attempt - 1))


def get_verification_settings() -> VerificationSettings:
    """Get verification settings instance.

    Returns:
        VerificationSettings instance
    """
    return VerificationSettings()
