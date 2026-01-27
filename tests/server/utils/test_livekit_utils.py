"""Tests for LiveKit utilities."""

import re
import time
from unittest.mock import MagicMock, patch

from voiceobs.server.utils.livekit import create_room_token, generate_room_name


class TestGenerateRoomName:
    """Tests for room name generation."""

    def test_generates_unique_names(self):
        """Each call should generate a unique name."""
        name1 = generate_room_name()
        name2 = generate_room_name()
        assert name1 != name2

    def test_default_prefix(self):
        """Default prefix should be 'room'."""
        name = generate_room_name()
        assert name.startswith("room-")

    def test_custom_prefix(self):
        """Custom prefix should be used."""
        name = generate_room_name(prefix="verify")
        assert name.startswith("verify-")

    def test_contains_timestamp(self):
        """Room name should contain a timestamp component."""
        before = int(time.time())
        name = generate_room_name()
        after = int(time.time())

        # Extract timestamp from name (format: prefix-timestamp-uuid)
        parts = name.split("-")
        assert len(parts) >= 2
        timestamp = int(parts[1])
        assert before <= timestamp <= after

    def test_contains_uuid_suffix(self):
        """Room name should contain UUID suffix."""
        name = generate_room_name()
        # Format: prefix-timestamp-uuid (uuid is 8 chars)
        parts = name.split("-")
        assert len(parts) >= 3
        uuid_part = parts[2]
        assert len(uuid_part) == 8
        # UUID should be alphanumeric
        assert uuid_part.isalnum()

    def test_format_matches_pattern(self):
        """Room name should match expected pattern."""
        name = generate_room_name(prefix="test")
        # Pattern: prefix-timestamp-uuid8
        pattern = r"^test-\d+-[a-f0-9]{8}$"
        assert re.match(pattern, name) is not None


class TestCreateRoomToken:
    """Tests for room token creation."""

    @patch("voiceobs.server.utils.livekit.api.AccessToken")
    def test_creates_token_with_credentials(self, mock_access_token):
        """Token should be created with API key and secret."""
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "test-jwt-token"
        mock_access_token.return_value = mock_token

        result = create_room_token(
            api_key="test-key",
            api_secret="test-secret",
            room_name="test-room",
            identity="test-identity",
        )

        mock_access_token.assert_called_once_with("test-key", "test-secret")
        assert result == "test-jwt-token"

    @patch("voiceobs.server.utils.livekit.api.AccessToken")
    def test_sets_identity(self, mock_access_token):
        """Token should have identity set."""
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "test-jwt-token"
        mock_access_token.return_value = mock_token

        create_room_token(
            api_key="test-key",
            api_secret="test-secret",
            room_name="test-room",
            identity="my-agent",
        )

        mock_token.with_identity.assert_called_once_with("my-agent")

    @patch("voiceobs.server.utils.livekit.api.VideoGrants")
    @patch("voiceobs.server.utils.livekit.api.AccessToken")
    def test_sets_video_grants(self, mock_access_token, mock_video_grants):
        """Token should have video grants for room join."""
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "test-jwt-token"
        mock_access_token.return_value = mock_token
        mock_grants = MagicMock()
        mock_video_grants.return_value = mock_grants

        create_room_token(
            api_key="test-key",
            api_secret="test-secret",
            room_name="my-room",
            identity="test-identity",
        )

        mock_video_grants.assert_called_once_with(room_join=True, room="my-room")
        mock_token.with_grants.assert_called_once_with(mock_grants)

    @patch("voiceobs.server.utils.livekit.api.AccessToken")
    def test_returns_jwt_string(self, mock_access_token):
        """Should return JWT token string."""
        mock_token = MagicMock()
        mock_token.to_jwt.return_value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        mock_access_token.return_value = mock_token

        result = create_room_token(
            api_key="key",
            api_secret="secret",
            room_name="room",
            identity="identity",
        )

        assert isinstance(result, str)
        mock_token.to_jwt.assert_called_once()
