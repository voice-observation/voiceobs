"""Tests for test bypass configuration."""

import os
from unittest.mock import patch

from voiceobs.server.config.testing import TestSettings, get_test_settings


class TestTestSettings:
    """Tests for TestSettings."""

    def test_default_test_user_email_is_none(self):
        """Test that test_user_email defaults to None when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Skip .env file so we test the true default
            settings = TestSettings(_env_file=None)
        assert settings.test_user_email is None

    def test_test_user_email_from_env(self):
        """Test that test_user_email reads from TEST_USER_EMAIL env var."""
        with patch.dict(os.environ, {"TEST_USER_EMAIL": "test@example.com"}):
            settings = TestSettings()
        assert settings.test_user_email == "test@example.com"

    def test_get_test_settings_returns_instance(self):
        """Test that get_test_settings returns a TestSettings instance."""
        settings = get_test_settings()
        assert isinstance(settings, TestSettings)
