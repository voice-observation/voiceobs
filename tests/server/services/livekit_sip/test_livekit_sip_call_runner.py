"""Unit tests for LiveKitSIPCallRunner class."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.services.livekit_sip import LiveKitSIPCallRunner


def _make_mock_room():
    """Create a mock room with connect and aclose (safe_cleanup checks aclose first)."""
    mock_room = MagicMock()
    mock_room.connect = AsyncMock()
    mock_room.aclose = AsyncMock()
    return mock_room


def _make_mock_session():
    """Create a mock agent session with aclose."""
    mock_session = MagicMock()
    mock_session.aclose = AsyncMock()
    return mock_session


class TestLiveKitSIPCallRunner:
    """Tests for LiveKitSIPCallRunner class."""

    @pytest.mark.asyncio
    async def test_run_invokes_conversation_fn(self, mock_settings):
        """Test that runner.run invokes conversation_fn with room, session, room_name."""
        mock_room = _make_mock_room()
        mock_session = _make_mock_session()
        seen = {}

        async def conv_fn(room, session, room_name):
            seen["room"] = room
            seen["session"] = session
            seen["room_name"] = room_name

        @asynccontextmanager
        async def mock_cm():
            yield (mock_room, mock_session, "exec-abc-123")

        with patch(
            "voiceobs.server.services.livekit_sip.runner.run_livekit_sip_call",
            return_value=mock_cm(),
        ):
            runner = LiveKitSIPCallRunner(mock_settings)
            await runner.run(
                phone_number="+1234567890",
                identity="bot",
                room_prefix="exec-",
                conversation_fn=conv_fn,
            )

            assert seen["room"] is mock_room
            assert seen["session"] is mock_session
            assert seen["room_name"] == "exec-abc-123"

    @pytest.mark.asyncio
    async def test_run_passes_hooks_to_context_manager(self, mock_settings):
        """Test runner.run passes before_dial and after_conversation to run_livekit_sip_call."""
        mock_room = _make_mock_room()
        mock_session = _make_mock_session()

        @asynccontextmanager
        async def mock_cm():
            yield (mock_room, mock_session, "exec-xyz")

        with patch(
            "voiceobs.server.services.livekit_sip.runner.run_livekit_sip_call",
            return_value=mock_cm(),
        ) as mock_run:
            runner = LiveKitSIPCallRunner(mock_settings)

            async def before_dial(room_name):
                pass

            async def after_conversation(room_name):
                pass

            async def conv_fn(room, session, room_name):
                pass

            await runner.run(
                phone_number="+1234567890",
                identity="bot",
                room_prefix="exec-",
                conversation_fn=conv_fn,
                before_dial=before_dial,
                after_conversation=after_conversation,
            )

            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["before_dial"] is before_dial
            assert call_kwargs["after_conversation"] is after_conversation
