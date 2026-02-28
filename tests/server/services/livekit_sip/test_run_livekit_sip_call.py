"""Unit tests for run_livekit_sip_call async context manager."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.services.livekit_sip import run_livekit_sip_call


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


class TestRunLiveKitSIPCall:
    """Tests for run_livekit_sip_call async context manager."""

    @pytest.mark.asyncio
    async def test_creates_room_dials_connects_and_yields(self, mock_settings):
        """Test that run_livekit_sip_call creates room, dials, connects, yields."""
        mock_room = _make_mock_room()
        mock_session = _make_mock_session()

        with (
            patch("voiceobs.server.services.livekit_sip.runner.api.LiveKitAPI") as mock_api_class,
            patch(
                "voiceobs.server.services.livekit_sip.runner.rtc.Room",
                return_value=mock_room,
            ),
            patch(
                "voiceobs.server.services.livekit_sip.runner.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.livekit_sip.runner.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.livekit_sip.runner.generate_room_name",
                return_value="exec-12345-abcd",
            ),
        ):
            mock_api = MagicMock()
            mock_api.room.create_room = AsyncMock()
            mock_api.room.delete_room = AsyncMock()
            mock_api.sip.create_sip_participant = AsyncMock()
            mock_api.aclose = AsyncMock()
            mock_api_class.return_value = mock_api

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            call_order = []

            async with run_livekit_sip_call(
                phone_number="+1234567890",
                identity="execution-bot",
                room_prefix="exec-",
                settings=mock_settings,
            ) as (room, session, room_name):
                assert room is mock_room
                assert session is mock_session
                assert room_name == "exec-12345-abcd"
                call_order.append("inside_context")

            assert "inside_context" in call_order
            mock_api.room.create_room.assert_called_once()
            mock_api.sip.create_sip_participant.assert_called_once()
            mock_room.connect.assert_called_once()
            mock_room.aclose.assert_called_once()
            mock_api.room.delete_room.assert_called_once()

    @pytest.mark.asyncio
    async def test_before_dial_hook_called_after_room_creation(self, mock_settings):
        """Test that before_dial hook is called after room creation, before SIP dial."""
        call_order = []
        mock_room = _make_mock_room()
        mock_session = _make_mock_session()

        with (
            patch("voiceobs.server.services.livekit_sip.runner.api.LiveKitAPI") as mock_api_class,
            patch(
                "voiceobs.server.services.livekit_sip.runner.rtc.Room",
                return_value=mock_room,
            ),
            patch(
                "voiceobs.server.services.livekit_sip.runner.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.livekit_sip.runner.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.livekit_sip.runner.generate_room_name",
                return_value="exec-12345-abcd",
            ),
        ):
            mock_api = MagicMock()
            mock_api.room.create_room = AsyncMock(
                side_effect=lambda *a, **k: call_order.append("create_room")
            )
            mock_api.room.delete_room = AsyncMock()
            mock_api.sip.create_sip_participant = AsyncMock(
                side_effect=lambda *a, **k: call_order.append("dial_sip")
            )
            mock_api.aclose = AsyncMock()
            mock_api_class.return_value = mock_api

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            async def before_dial(room_name):
                call_order.append(("before_dial", room_name))

            async with run_livekit_sip_call(
                phone_number="+1234567890",
                identity="execution-bot",
                room_prefix="exec-",
                settings=mock_settings,
                before_dial=before_dial,
            ) as (room, session, room_name):
                pass

            assert "create_room" in call_order
            assert ("before_dial", "exec-12345-abcd") in call_order
            assert "dial_sip" in call_order
            create_idx = call_order.index("create_room")
            before_idx = call_order.index(("before_dial", "exec-12345-abcd"))
            dial_idx = call_order.index("dial_sip")
            assert create_idx < before_idx < dial_idx

    @pytest.mark.asyncio
    async def test_after_conversation_hook_called_before_cleanup(self, mock_settings):
        """Test that after_conversation hook is called after context exit, before cleanup."""
        call_order = []
        mock_room = _make_mock_room()
        mock_session = _make_mock_session()

        with (
            patch("voiceobs.server.services.livekit_sip.runner.api.LiveKitAPI") as mock_api_class,
            patch(
                "voiceobs.server.services.livekit_sip.runner.rtc.Room",
                return_value=mock_room,
            ),
            patch(
                "voiceobs.server.services.livekit_sip.runner.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.livekit_sip.runner.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.livekit_sip.runner.generate_room_name",
                return_value="exec-12345-abcd",
            ),
        ):
            mock_api = MagicMock()
            mock_api.room.create_room = AsyncMock()
            mock_api.room.delete_room = AsyncMock(
                side_effect=lambda *a, **k: call_order.append("delete_room")
            )
            mock_api.sip.create_sip_participant = AsyncMock()
            mock_api.aclose = AsyncMock()
            mock_api_class.return_value = mock_api

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            async def after_conversation(room_name):
                call_order.append(("after_conversation", room_name))

            async with run_livekit_sip_call(
                phone_number="+1234567890",
                identity="execution-bot",
                room_prefix="exec-",
                settings=mock_settings,
                after_conversation=after_conversation,
            ) as (room, session, room_name):
                pass

            assert ("after_conversation", "exec-12345-abcd") in call_order
            after_idx = call_order.index(("after_conversation", "exec-12345-abcd"))
            delete_idx = call_order.index("delete_room")
            assert after_idx < delete_idx
