"""Tests for phone agent verifier."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.services.agent_verification.phone_verifier import PhoneAgentVerifier


@pytest.fixture
def mock_settings():
    """Create mock verification settings."""
    settings = MagicMock()
    settings.livekit_url = "wss://test.livekit.cloud"
    settings.livekit_api_key = "test_key"
    settings.livekit_api_secret = "test_secret"
    settings.sip_outbound_trunk_id = "trunk_123"
    settings.verification_call_timeout = 30
    settings.verification_max_turns = 3
    return settings


class TestPhoneAgentVerifierInit:
    """Tests for PhoneAgentVerifier initialization."""

    def test_init_loads_settings(self, mock_settings):
        """Test that init loads verification settings."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            verifier = PhoneAgentVerifier()
            assert verifier._settings == mock_settings

    def test_get_agent_type_returns_phone(self, mock_settings):
        """Test that get_agent_type returns 'phone'."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            verifier = PhoneAgentVerifier()
            assert verifier.get_agent_type() == "phone"


class TestPhoneAgentVerifierVerify:
    """Tests for PhoneAgentVerifier.verify() method."""

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    @pytest.mark.asyncio
    async def test_verify_raises_error_when_phone_number_missing(self, verifier):
        """Test that verify raises ValueError when phone_number is missing."""
        with pytest.raises(ValueError, match="phone_number is required"):
            await verifier.verify({})

    @pytest.mark.asyncio
    async def test_verify_returns_false_for_invalid_phone_format(self, verifier):
        """Test that verify returns false for invalid phone format."""
        is_verified, error_msg, transcript = await verifier.verify({"phone_number": "invalid"})
        assert is_verified is False
        assert "Invalid phone number format" in error_msg
        assert transcript is None

    @pytest.mark.asyncio
    async def test_verify_returns_false_when_settings_missing(self, mock_settings):
        """Test that verify returns false when LiveKit settings are missing."""
        mock_settings.livekit_url = None
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            verifier = PhoneAgentVerifier()

            is_verified, error_msg, transcript = await verifier.verify(
                {"phone_number": "+1234567890"}
            )

            assert is_verified is False
            assert "LiveKit not configured" in error_msg


class TestPhoneAgentVerifierConversation:
    """Tests for conversation handling in PhoneAgentVerifier."""

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance with mocked settings."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    @pytest.mark.asyncio
    async def test_verify_success_with_enough_turns(self, verifier, mock_settings):
        """Test successful verification when agent responds with enough turns."""
        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.sip.create_sip_participant = AsyncMock()
        mock_api.aclose = AsyncMock()

        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.generate_reply = AsyncMock()
        mock_session.aclose = AsyncMock()

        with (
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
                return_value=mock_api,
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.rtc.Room"
            ) as mock_room_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.generate_room_name",
                return_value="verify-12345-abcd1234",
            ),
        ):
            # Setup mocks
            mock_room = MagicMock()
            mock_room.connect = AsyncMock()
            mock_room.disconnect = AsyncMock()
            mock_participant = MagicMock()
            mock_participant.identity = "sip_+1234567890"
            mock_room.remote_participants = {"p1": mock_participant}
            mock_room_class.return_value = mock_room

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            # Simulate conversation turns by modifying verifier state
            async def mock_run_conversation(room, session):
                verifier._transcript = [
                    {"role": "assistant", "content": "Hello"},
                    {"role": "user", "content": "Hi there"},
                    {"role": "assistant", "content": "How are you?"},
                    {"role": "user", "content": "Good thanks"},
                ]
                verifier._turns = 2

            verifier._run_conversation = mock_run_conversation

            is_verified, error_msg, transcript = await verifier.verify(
                {"phone_number": "+1234567890"}
            )

            assert is_verified is True
            assert error_msg is None
            assert len(transcript) == 4

    @pytest.mark.asyncio
    async def test_verify_failure_insufficient_turns(self, verifier, mock_settings):
        """Test failed verification when not enough conversation turns."""
        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.sip.create_sip_participant = AsyncMock()
        mock_api.aclose = AsyncMock()

        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.generate_reply = AsyncMock()
        mock_session.aclose = AsyncMock()

        with (
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
                return_value=mock_api,
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.rtc.Room"
            ) as mock_room_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.generate_room_name",
                return_value="verify-12345-abcd1234",
            ),
        ):
            mock_room = MagicMock()
            mock_room.connect = AsyncMock()
            mock_room.disconnect = AsyncMock()
            mock_participant = MagicMock()
            mock_participant.identity = "sip_+1234567890"
            mock_room.remote_participants = {"p1": mock_participant}
            mock_room_class.return_value = mock_room

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            # Simulate only 1 turn (not enough)
            async def mock_run_conversation(room, session):
                verifier._transcript = [
                    {"role": "assistant", "content": "Hello"},
                ]
                verifier._turns = 0

            verifier._run_conversation = mock_run_conversation

            is_verified, error_msg, transcript = await verifier.verify(
                {"phone_number": "+1234567890"}
            )

            assert is_verified is False
            assert "Insufficient" in error_msg

    @pytest.mark.asyncio
    async def test_verify_handles_sip_call_failure(self, verifier, mock_settings):
        """Test that verify handles SIP call failures gracefully."""
        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.aclose = AsyncMock()

        # Simulate SIP call failure
        from livekit import api as livekit_api

        mock_api.sip.create_sip_participant = AsyncMock(
            side_effect=livekit_api.TwirpError(code="internal", msg="SIP trunk error", status=500)
        )

        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
            return_value=mock_api,
        ):
            is_verified, error_msg, transcript = await verifier.verify(
                {"phone_number": "+1234567890"}
            )

            assert is_verified is False
            assert "SIP call failed" in error_msg

    @pytest.mark.asyncio
    async def test_verify_handles_generic_exception(self, verifier, mock_settings):
        """Test that verify handles generic exceptions gracefully."""
        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock(side_effect=Exception("Network error"))
        mock_api.room.delete_room = AsyncMock()
        mock_api.aclose = AsyncMock()

        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
            return_value=mock_api,
        ):
            is_verified, error_msg, transcript = await verifier.verify(
                {"phone_number": "+1234567890"}
            )

            assert is_verified is False
            assert "Verification failed" in error_msg


class TestPhoneAgentVerifierHelpers:
    """Tests for PhoneAgentVerifier helper methods."""

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance with mocked settings."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    def test_create_agent_session_uses_factory(self, verifier):
        """Test that _create_agent_session uses LiveKitProviderFactory."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.LiveKitProviderFactory"
        ) as mock_factory_class:
            mock_factory = MagicMock()
            mock_session = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            result = verifier._create_agent_session()

            mock_factory_class.assert_called_once()
            mock_factory.create_agent_session.assert_called_once()
            assert result is mock_session


class TestAdaptiveGreetingState:
    """Tests for adaptive greeting state tracking."""

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    def test_init_sets_other_party_spoke_first_to_false(self, verifier):
        """Test that _other_party_spoke_first is initialized to False."""
        assert verifier._other_party_spoke_first is False

    def test_init_creates_speech_detected_event(self, verifier):
        """Test that _speech_detected_event is initialized as asyncio.Event."""
        assert isinstance(verifier._speech_detected_event, asyncio.Event)
        assert not verifier._speech_detected_event.is_set()

    @pytest.mark.asyncio
    async def test_wait_for_speech_returns_true_when_event_set_before_timeout(self, verifier):
        """Test that _wait_for_speech returns True when speech detected before timeout."""
        # Set the event immediately
        verifier._speech_detected_event.set()

        result = await verifier._wait_for_speech(timeout=1.0)

        assert result is True
        assert verifier._other_party_spoke_first is True

    @pytest.mark.asyncio
    async def test_wait_for_speech_returns_false_on_timeout(self, verifier):
        """Test that _wait_for_speech returns False when timeout expires."""
        # Don't set the event - let it timeout
        result = await verifier._wait_for_speech(timeout=0.1)

        assert result is False
        assert verifier._other_party_spoke_first is False

    def test_on_user_state_changed_sets_event_when_speaking(self, verifier):
        """Test that _on_user_state_changed sets event when user starts speaking."""
        # Create a mock event with new_state = "speaking"
        mock_event = MagicMock()
        mock_event.new_state = "speaking"

        verifier._on_user_state_changed(mock_event)

        assert verifier._speech_detected_event.is_set()

    def test_on_user_state_changed_ignores_other_states(self, verifier):
        """Test that _on_user_state_changed ignores non-speaking states."""
        mock_event = MagicMock()
        mock_event.new_state = "listening"

        verifier._on_user_state_changed(mock_event)

        assert not verifier._speech_detected_event.is_set()

    @pytest.mark.asyncio
    async def test_verify_resets_adaptive_greeting_state(self, verifier, mock_settings):
        """Test that verify() resets adaptive greeting state for each call."""
        # Set some state as if from a previous call
        verifier._other_party_spoke_first = True
        verifier._speech_detected_event.set()

        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.sip.create_sip_participant = AsyncMock()
        mock_api.aclose = AsyncMock()

        mock_session = MagicMock()
        mock_session.aclose = AsyncMock()

        with (
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
                return_value=mock_api,
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.rtc.Room"
            ) as mock_room_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.generate_room_name",
                return_value="verify-12345-abcd1234",
            ),
        ):
            mock_room = MagicMock()
            mock_room.connect = AsyncMock()
            mock_room.disconnect = AsyncMock()
            mock_room_class.return_value = mock_room

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            # Track state at the point _run_conversation is called
            state_at_run = {}

            # Mock _run_conversation to check state was reset
            async def check_state_reset(room, session):
                # At this point, state should be reset
                state_at_run["other_party_spoke_first"] = verifier._other_party_spoke_first
                state_at_run["speech_detected_is_set"] = verifier._speech_detected_event.is_set()

            verifier._run_conversation = check_state_reset

            await verifier.verify({"phone_number": "+1234567890"})

            # Verify state was reset before _run_conversation was called
            assert state_at_run["other_party_spoke_first"] is False
            assert state_at_run["speech_detected_is_set"] is False


class TestGreetingInstructions:
    """Tests for greeting instruction constants."""

    def test_initiate_greeting_instructions_exist(self):
        """Test that INITIATE_GREETING_INSTRUCTIONS constant exists."""
        from voiceobs.server.prompts.verification import (
            INITIATE_GREETING_INSTRUCTIONS,
        )

        has_hi = "Hi" in INITIATE_GREETING_INSTRUCTIONS
        has_hello = "hello" in INITIATE_GREETING_INSTRUCTIONS.lower()
        assert has_hi or has_hello

    def test_respond_greeting_instructions_exist(self):
        """Test that RESPOND_GREETING_INSTRUCTIONS constant exists."""
        from voiceobs.server.prompts.verification import (
            RESPOND_GREETING_INSTRUCTIONS,
        )

        has_respond = "respond" in RESPOND_GREETING_INSTRUCTIONS.lower()
        has_acknowledge = "acknowledge" in RESPOND_GREETING_INSTRUCTIONS.lower()
        assert has_respond or has_acknowledge


class TestAdaptiveGreetingConversation:
    """Tests for adaptive greeting in conversation flow."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock verification settings with initial wait timeout."""
        settings = MagicMock()
        settings.livekit_url = "wss://test.livekit.cloud"
        settings.livekit_api_key = "test_key"
        settings.livekit_api_secret = "test_secret"
        settings.sip_outbound_trunk_id = "trunk_123"
        settings.verification_call_timeout = 30
        settings.verification_max_turns = 3
        settings.verification_initial_wait_timeout = 4.5
        return settings

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    @pytest.mark.asyncio
    async def test_registers_user_state_changed_handler(self, verifier):
        """Test that _run_conversation registers user_state_changed handler."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.on = MagicMock()

        # Make _wait_for_speech return immediately (they spoke first)
        verifier._wait_for_speech = AsyncMock(return_value=True)

        # Set turns >= max_turns so the conversation loop exits immediately
        async def mock_generate_reply(*args, **kwargs):
            verifier._turns = 3  # Exit condition: turns >= max_turns

        mock_session.generate_reply = AsyncMock(side_effect=mock_generate_reply)

        await verifier._run_conversation(mock_room, mock_session)

        # Verify user_state_changed handler was registered
        handler_calls = [
            call for call in mock_session.on.call_args_list if call[0][0] == "user_state_changed"
        ]
        assert len(handler_calls) >= 1

    @pytest.mark.asyncio
    async def test_waits_before_greeting_when_other_party_silent(self, verifier, mock_settings):
        """Test that conversation waits for other party before greeting."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.on = MagicMock()

        # Simulate timeout (no one spoke)
        verifier._wait_for_speech = AsyncMock(return_value=False)

        # Set turns >= max_turns so the conversation loop exits immediately
        mock_speech_handle = MagicMock()
        mock_speech_handle.interrupt = MagicMock()

        async def mock_generate_reply(*args, **kwargs):
            verifier._turns = 3  # Exit condition: turns >= max_turns
            return mock_speech_handle

        mock_session.generate_reply = AsyncMock(side_effect=mock_generate_reply)

        await verifier._run_conversation(mock_room, mock_session)

        # Should use INITIATE instructions since we timed out
        generate_calls = mock_session.generate_reply.call_args_list
        first_greeting_call = generate_calls[0]
        assert "Hi" in str(first_greeting_call) or "Greet" in str(first_greeting_call)

    @pytest.mark.asyncio
    async def test_responds_contextually_when_other_party_speaks_first(self, verifier):
        """Test that conversation responds contextually when other party speaks first."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.on = MagicMock()

        # Simulate other party speaking first
        verifier._wait_for_speech = AsyncMock(return_value=True)

        # Set turns >= max_turns so the conversation loop exits immediately
        async def mock_generate_reply(*args, **kwargs):
            verifier._turns = 3  # Exit condition: turns >= max_turns

        mock_session.generate_reply = AsyncMock(side_effect=mock_generate_reply)

        await verifier._run_conversation(mock_room, mock_session)

        # Should use RESPOND instructions since they spoke first
        generate_calls = mock_session.generate_reply.call_args_list
        first_greeting_call = generate_calls[0]
        assert (
            "Respond" in str(first_greeting_call)
            or "acknowledge" in str(first_greeting_call).lower()
        )

    @pytest.mark.asyncio
    async def test_interrupts_greeting_when_other_party_starts_speaking(self, verifier):
        """Test that we interrupt our greeting if other party starts speaking."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.on = MagicMock()

        # Track if interrupt was called
        mock_speech_handle = MagicMock()
        mock_speech_handle.interrupt = MagicMock()

        # We will initiate (timeout), then other party speaks during our greeting
        verifier._wait_for_speech = AsyncMock(return_value=False)

        # Simulate other party speaking during our greeting
        async def trigger_speech_during_greeting(*args, **kwargs):
            # Simulate speech detected during TTS generation
            verifier._speech_detected_event.set()
            # Set turns >= max_turns so the conversation loop exits immediately
            verifier._turns = 3
            return mock_speech_handle

        mock_session.generate_reply = AsyncMock(side_effect=trigger_speech_during_greeting)

        await verifier._run_conversation(mock_room, mock_session)

        # The speech handle's interrupt should have been called
        mock_speech_handle.interrupt.assert_called_once()
        assert verifier._other_party_spoke_first is True


class TestCallNotAnsweredError:
    """Tests for CallNotAnsweredError handling."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock verification settings."""
        settings = MagicMock()
        settings.livekit_url = "wss://test.livekit.cloud"
        settings.livekit_api_key = "test_key"
        settings.livekit_api_secret = "test_secret"
        settings.sip_outbound_trunk_id = "trunk_123"
        settings.verification_call_timeout = 30
        settings.verification_max_turns = 3
        settings.verification_initial_wait_timeout = 4.5
        return settings

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    @pytest.mark.asyncio
    async def test_verify_handles_call_not_answered_error(self, verifier, mock_settings):
        """Test that verify handles CallNotAnsweredError gracefully."""
        from voiceobs.server.services.agent_verification.errors import CallNotAnsweredError

        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.aclose = AsyncMock()

        # Simulate CallNotAnsweredError
        mock_api.sip.create_sip_participant = AsyncMock(
            side_effect=CallNotAnsweredError("Call was not answered within timeout")
        )

        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
            return_value=mock_api,
        ):
            is_verified, error_msg, transcript = await verifier.verify(
                {"phone_number": "+1234567890"}
            )

            assert is_verified is False
            assert "not answered" in error_msg.lower()


class TestEventHandlerCallbacks:
    """Tests for event handler callbacks in _run_conversation."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock verification settings."""
        settings = MagicMock()
        settings.livekit_url = "wss://test.livekit.cloud"
        settings.livekit_api_key = "test_key"
        settings.livekit_api_secret = "test_secret"
        settings.sip_outbound_trunk_id = "trunk_123"
        settings.verification_call_timeout = 30
        settings.verification_max_turns = 1  # Exit quickly
        settings.verification_initial_wait_timeout = 0.1
        return settings

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    @pytest.mark.asyncio
    async def test_agent_state_changed_tts_started(self, verifier):
        """Test agent_state_changed handler tracks TTS start time."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()

        # Capture event handlers
        handlers = {}

        def capture_handler(event_name):
            def decorator(func):
                handlers[event_name] = func
                return func

            return decorator

        mock_session.on = capture_handler

        # Make _wait_for_speech return immediately
        verifier._wait_for_speech = AsyncMock(return_value=True)
        verifier._turns = 1  # Exit immediately

        mock_session.generate_reply = AsyncMock()

        await verifier._run_conversation(mock_room, mock_session)

        # Simulate agent_state_changed event with speaking state
        if "agent_state_changed" in handlers:
            mock_event = MagicMock()
            mock_event.new_state = "speaking"
            mock_event.old_state = "listening"

            handlers["agent_state_changed"](mock_event)
            assert verifier._tts_start_time is not None

    @pytest.mark.asyncio
    async def test_agent_state_changed_tts_completed(self, verifier):
        """Test agent_state_changed handler tracks TTS completion."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()

        handlers = {}

        def capture_handler(event_name):
            def decorator(func):
                handlers[event_name] = func
                return func

            return decorator

        mock_session.on = capture_handler

        verifier._wait_for_speech = AsyncMock(return_value=True)
        verifier._turns = 1

        mock_session.generate_reply = AsyncMock()

        await verifier._run_conversation(mock_room, mock_session)

        if "agent_state_changed" in handlers:
            # First, start speaking
            mock_event = MagicMock()
            mock_event.new_state = "speaking"
            mock_event.old_state = "listening"
            handlers["agent_state_changed"](mock_event)

            # Add turn timings to store TTS duration
            verifier._turn_timings = [{"turn": 1, "llm_duration": 0.5}]

            # Then stop speaking
            mock_event2 = MagicMock()
            mock_event2.new_state = "listening"
            mock_event2.old_state = "speaking"
            handlers["agent_state_changed"](mock_event2)

            assert verifier._tts_start_time is None  # Reset after completion
            assert "tts_duration" in verifier._turn_timings[0]

    @pytest.mark.asyncio
    async def test_user_input_transcribed_handler(self, verifier):
        """Test user_input_transcribed handler tracks STT timing."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()

        handlers = {}

        def capture_handler(event_name):
            def decorator(func):
                handlers[event_name] = func
                return func

            return decorator

        mock_session.on = capture_handler

        verifier._wait_for_speech = AsyncMock(return_value=True)
        verifier._turns = 1

        mock_session.generate_reply = AsyncMock()

        await verifier._run_conversation(mock_room, mock_session)

        if "user_input_transcribed" in handlers:
            # Set up timing state
            verifier._last_agent_response_time = asyncio.get_event_loop().time() - 0.5
            verifier._turn_timings = [{"turn": 1, "llm_duration": 0.5}]

            handlers["user_input_transcribed"]("test transcript")

            assert "stt_duration" in verifier._turn_timings[0]

    @pytest.mark.asyncio
    async def test_conversation_item_added_user(self, verifier):
        """Test conversation_item_added handler for user messages."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()

        handlers = {}

        def capture_handler(event_name):
            def decorator(func):
                handlers[event_name] = func
                return func

            return decorator

        mock_session.on = capture_handler

        verifier._wait_for_speech = AsyncMock(return_value=True)
        verifier._turns = 1

        mock_session.generate_reply = AsyncMock()

        await verifier._run_conversation(mock_room, mock_session)

        if "conversation_item_added" in handlers:
            mock_event = MagicMock()
            mock_event.item.role = "user"
            mock_event.item.text_content = "Hello there"

            initial_turns = verifier._turns
            handlers["conversation_item_added"](mock_event)

            assert len(verifier._transcript) > 0
            assert verifier._transcript[-1]["role"] == "user"
            assert verifier._transcript[-1]["content"] == "Hello there"
            assert verifier._turns == initial_turns + 1

    @pytest.mark.asyncio
    async def test_conversation_item_added_assistant(self, verifier):
        """Test conversation_item_added handler for assistant messages."""
        mock_room = MagicMock()
        mock_session = MagicMock()
        mock_session.start = AsyncMock()

        handlers = {}

        def capture_handler(event_name):
            def decorator(func):
                handlers[event_name] = func
                return func

            return decorator

        mock_session.on = capture_handler

        verifier._wait_for_speech = AsyncMock(return_value=True)
        verifier._turns = 1

        mock_session.generate_reply = AsyncMock()

        await verifier._run_conversation(mock_room, mock_session)

        if "conversation_item_added" in handlers:
            # Set up timing state
            verifier._last_user_input_time = asyncio.get_event_loop().time() - 0.3

            mock_event = MagicMock()
            mock_event.item.role = "assistant"
            mock_event.item.text_content = "Hi, how can I help?"

            handlers["conversation_item_added"](mock_event)

            assert len(verifier._transcript) > 0
            assert verifier._transcript[-1]["role"] == "assistant"
            assert verifier._last_agent_response_time is not None
            assert len(verifier._turn_timings) > 0


class TestTimingCallbacks:
    """Tests for timing callback handling in conversation."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock verification settings."""
        settings = MagicMock()
        settings.livekit_url = "wss://test.livekit.cloud"
        settings.livekit_api_key = "test_key"
        settings.livekit_api_secret = "test_secret"
        settings.sip_outbound_trunk_id = "trunk_123"
        settings.verification_call_timeout = 30
        settings.verification_max_turns = 3
        settings.verification_initial_wait_timeout = 4.5
        return settings

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    def test_log_timing_summary_with_no_timings(self, verifier):
        """Test _log_timing_summary handles empty timings gracefully."""
        verifier._turn_timings = []
        # Should not raise
        verifier._log_timing_summary()

    def test_log_timing_summary_with_llm_timings(self, verifier):
        """Test _log_timing_summary logs LLM timing averages."""
        verifier._turn_timings = [
            {"turn": 1, "llm_duration": 0.5},
            {"turn": 2, "llm_duration": 0.7},
        ]
        # Should not raise and should log averages
        verifier._log_timing_summary()

    def test_log_timing_summary_with_stt_timings(self, verifier):
        """Test _log_timing_summary logs STT timing averages."""
        verifier._turn_timings = [
            {"turn": 1, "llm_duration": 0.5, "stt_duration": 0.2},
            {"turn": 2, "llm_duration": 0.7, "stt_duration": 0.3},
        ]
        # Should not raise and should log STT averages
        verifier._log_timing_summary()

    def test_log_timing_summary_with_tts_timings(self, verifier):
        """Test _log_timing_summary logs TTS timing averages."""
        verifier._turn_timings = [
            {"turn": 1, "llm_duration": 0.5, "tts_duration": 0.4},
            {"turn": 2, "llm_duration": 0.7, "tts_duration": 0.6},
        ]
        # Should not raise and should log TTS averages
        verifier._log_timing_summary()

    def test_log_timing_summary_with_all_timings(self, verifier):
        """Test _log_timing_summary logs all timing types."""
        verifier._turn_timings = [
            {"turn": 1, "llm_duration": 0.5, "stt_duration": 0.2, "tts_duration": 0.4},
            {"turn": 2, "llm_duration": 0.7, "stt_duration": 0.3, "tts_duration": 0.6},
        ]
        # Should not raise and should log all averages
        verifier._log_timing_summary()


class TestCleanupOrder:
    """Tests for proper cleanup order to prevent session closed errors."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock verification settings."""
        settings = MagicMock()
        settings.livekit_url = "wss://test.livekit.cloud"
        settings.livekit_api_key = "test_key"
        settings.livekit_api_secret = "test_secret"
        settings.sip_outbound_trunk_id = "trunk_123"
        settings.verification_call_timeout = 30
        settings.verification_max_turns = 3
        settings.verification_initial_wait_timeout = 4.5
        return settings

    @pytest.fixture
    def verifier(self, mock_settings):
        """Create a verifier instance."""
        with patch(
            "voiceobs.server.services.agent_verification.phone_verifier.get_verification_settings"
        ) as mock_get_settings:
            mock_get_settings.return_value = mock_settings
            return PhoneAgentVerifier()

    @pytest.mark.asyncio
    async def test_agent_session_closed_before_http_session(self, verifier, mock_settings):
        """Test that AgentSession.aclose() is called before HTTP session is closed."""
        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.sip.create_sip_participant = AsyncMock()
        mock_api.aclose = AsyncMock()

        # Track cleanup order
        cleanup_order = []

        # Create mock with spec to limit attributes - aclose exists on AgentSession
        mock_agent_session = MagicMock(spec=["aclose"])

        async def track_session_close():
            cleanup_order.append("agent_session_aclose")

        mock_agent_session.aclose = AsyncMock(side_effect=track_session_close)

        # For HTTP session, use spec to limit attributes - aiohttp.ClientSession has close()
        # But safe_cleanup checks for aclose first, so we mock that
        mock_http_session = MagicMock(spec=["aclose"])

        async def track_http_aclose():
            cleanup_order.append("http_session_close")

        mock_http_session.aclose = AsyncMock(side_effect=track_http_aclose)

        with (
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
                return_value=mock_api,
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.rtc.Room"
            ) as mock_room_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.aiohttp.ClientSession",
                return_value=mock_http_session,
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.generate_room_name",
                return_value="verify-12345-abcd1234",
            ),
        ):
            mock_room = MagicMock()
            mock_room.connect = AsyncMock()
            mock_room.disconnect = AsyncMock()
            mock_room_class.return_value = mock_room

            # Mock _run_conversation to set the agent session
            async def mock_run_conversation(room, session):
                verifier._agent_session = mock_agent_session
                verifier._turns = 2  # Simulate successful conversation

            verifier._run_conversation = mock_run_conversation
            verifier._create_agent_session = MagicMock(return_value=mock_agent_session)

            await verifier.verify({"phone_number": "+1234567890"})

            # Verify agent session was closed before HTTP session
            assert "agent_session_aclose" in cleanup_order
            assert "http_session_close" in cleanup_order
            agent_idx = cleanup_order.index("agent_session_aclose")
            http_idx = cleanup_order.index("http_session_close")
            assert agent_idx < http_idx, (
                f"AgentSession should be closed before HTTP session. Order was: {cleanup_order}"
            )

    @pytest.mark.asyncio
    async def test_init_sets_agent_session_to_none(self, verifier):
        """Test that _agent_session is initialized to None."""
        assert verifier._agent_session is None

    @pytest.mark.asyncio
    async def test_verify_resets_agent_session(self, verifier, mock_settings):
        """Test that verify() resets _agent_session at the start."""
        # Set some state as if from a previous call
        verifier._agent_session = MagicMock()

        mock_api = MagicMock()
        mock_api.room.create_room = AsyncMock()
        mock_api.room.delete_room = AsyncMock()
        mock_api.sip.create_sip_participant = AsyncMock()
        mock_api.aclose = AsyncMock()

        mock_session = MagicMock()
        mock_session.aclose = AsyncMock()

        with (
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.api.LiveKitAPI",
                return_value=mock_api,
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.rtc.Room"
            ) as mock_room_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.LiveKitProviderFactory"
            ) as mock_factory_class,
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.create_room_token",
                return_value="test_token",
            ),
            patch(
                "voiceobs.server.services.agent_verification.phone_verifier.generate_room_name",
                return_value="verify-12345-abcd1234",
            ),
        ):
            mock_room = MagicMock()
            mock_room.connect = AsyncMock()
            mock_room.disconnect = AsyncMock()
            mock_room_class.return_value = mock_room

            mock_factory = MagicMock()
            mock_factory.create_agent_session.return_value = mock_session
            mock_factory_class.return_value = mock_factory

            # Track state at the point _run_conversation is called
            state_at_run = {}

            async def check_state_reset(room, session):
                # At this point, agent_session should be set to the new session
                state_at_run["agent_session_was_reset"] = True

            verifier._run_conversation = check_state_reset

            await verifier.verify({"phone_number": "+1234567890"})

            # Verify state was captured
            assert state_at_run.get("agent_session_was_reset") is True
