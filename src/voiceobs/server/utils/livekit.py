"""LiveKit utilities for the voiceobs server."""

from __future__ import annotations

import time
from uuid import uuid4

from livekit import api


def generate_room_name(prefix: str = "room") -> str:
    """Generate a unique room name with timestamp and UUID.

    Args:
        prefix: Prefix for the room name (default: "room")

    Returns:
        Unique room name in format: prefix-timestamp-uuid8

    Examples:
        >>> name = generate_room_name()  # "room-1706123456-a1b2c3d4"
        >>> name = generate_room_name(prefix="verify")  # "verify-1706123456-a1b2c3d4"
    """
    timestamp = int(time.time())
    uuid_suffix = str(uuid4())[:8]
    return f"{prefix}-{timestamp}-{uuid_suffix}"


def create_room_token(
    api_key: str,
    api_secret: str,
    room_name: str,
    identity: str,
) -> str:
    """Create a LiveKit room access token.

    Args:
        api_key: LiveKit API key
        api_secret: LiveKit API secret
        room_name: Name of the room to create token for
        identity: Identity for the participant

    Returns:
        JWT token string for room access

    Examples:
        >>> token = create_room_token(
        ...     api_key="key",
        ...     api_secret="secret",
        ...     room_name="my-room",
        ...     identity="my-agent",
        ... )
    """
    token = api.AccessToken(api_key, api_secret)
    token.with_identity(identity)
    token.with_grants(
        api.VideoGrants(
            room_join=True,
            room=room_name,
        )
    )
    return token.to_jwt()
