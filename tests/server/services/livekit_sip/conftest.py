"""Shared fixtures for LiveKit SIP tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_settings():
    """Create mock verification settings."""
    settings = MagicMock()
    settings.livekit_url = "wss://test.livekit.cloud"
    settings.livekit_api_key = "test_key"
    settings.livekit_api_secret = "test_secret"
    settings.sip_outbound_trunk_id = "trunk_123"
    settings.verification_call_timeout = 30
    return settings
