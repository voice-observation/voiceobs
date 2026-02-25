"""Test bypass configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    """Settings for e2e test account bypass.

    Controls which user email is recognized as a test account.
    When test_user_email is None (the default), no test bypass is possible.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_user_email: str | None = None


def get_test_settings() -> TestSettings:
    """Get test settings instance.

    Returns:
        TestSettings instance
    """
    return TestSettings()
