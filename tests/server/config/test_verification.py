"""Tests for verification settings."""

import os
from unittest.mock import patch

from voiceobs.server.config.verification import VerificationSettings, get_verification_settings


def test_initial_wait_timeout_default():
    """Test that initial_wait_timeout has a sensible default."""
    with patch.dict(
        os.environ,
        {
            "LIVEKIT_URL": "wss://test.livekit.cloud",
            "LIVEKIT_API_KEY": "test_key",
            "LIVEKIT_API_SECRET": "test_secret",
            "SIP_OUTBOUND_TRUNK_ID": "trunk_123",
        },
        clear=True,
    ):
        settings = VerificationSettings()
        assert settings.verification_initial_wait_timeout == 4.5


class TestVerificationSettings:
    """Tests for VerificationSettings class."""

    def test_default_values(self):
        """Test default configuration values."""
        with patch.dict(
            os.environ,
            {
                "LIVEKIT_URL": "wss://test.livekit.io",
                "LIVEKIT_API_KEY": "test_key",
                "LIVEKIT_API_SECRET": "test_secret",
                "SIP_OUTBOUND_TRUNK_ID": "trunk_123",
            },
            clear=False,
        ):
            settings = VerificationSettings()
            assert settings.verification_max_turns == 3
            assert settings.verification_max_retries == 3
            assert settings.verification_call_timeout == 30
            assert settings.verification_retry_base_delay == 30

    def test_custom_values_from_env(self):
        """Test loading custom values from environment."""
        with patch.dict(
            os.environ,
            {
                "LIVEKIT_URL": "wss://test.livekit.io",
                "LIVEKIT_API_KEY": "test_key",
                "LIVEKIT_API_SECRET": "test_secret",
                "SIP_OUTBOUND_TRUNK_ID": "trunk_123",
                "VERIFICATION_MAX_TURNS": "5",
                "VERIFICATION_MAX_RETRIES": "5",
                "VERIFICATION_CALL_TIMEOUT": "60",
            },
            clear=False,
        ):
            settings = VerificationSettings()
            assert settings.verification_max_turns == 5
            assert settings.verification_max_retries == 5
            assert settings.verification_call_timeout == 60

    def test_get_retry_delay_exponential_backoff(self):
        """Test exponential backoff calculation."""
        with patch.dict(
            os.environ,
            {
                "LIVEKIT_URL": "wss://test.livekit.io",
                "LIVEKIT_API_KEY": "test_key",
                "LIVEKIT_API_SECRET": "test_secret",
                "SIP_OUTBOUND_TRUNK_ID": "trunk_123",
            },
            clear=False,
        ):
            settings = VerificationSettings()
            assert settings.get_retry_delay(attempt=1) == 30
            assert settings.get_retry_delay(attempt=2) == 60
            assert settings.get_retry_delay(attempt=3) == 120

    def test_get_verification_settings_helper(self):
        """Test get_verification_settings helper function."""
        with patch.dict(
            os.environ,
            {
                "LIVEKIT_URL": "wss://test.livekit.io",
                "LIVEKIT_API_KEY": "test_key",
                "LIVEKIT_API_SECRET": "test_secret",
                "SIP_OUTBOUND_TRUNK_ID": "trunk_123",
            },
            clear=False,
        ):
            settings = get_verification_settings()
            assert isinstance(settings, VerificationSettings)
            assert settings.livekit_url == "wss://test.livekit.io"
