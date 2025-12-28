"""Tests for LiveKit Agents SDK integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.integrations import (
    LiveKitSessionWrapper,
    instrument_livekit_session,
)


class TestLiveKitIntegration:
    """Tests for LiveKit Agents SDK integration."""

    def test_instrument_livekit_session_returns_wrapper(self) -> None:
        """Test that instrument_livekit_session returns a wrapper."""
        mock_session = MagicMock()
        mock_session.on = MagicMock(return_value=lambda f: f)

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            result = instrument_livekit_session(mock_session)
            assert result is not None
            assert isinstance(result, LiveKitSessionWrapper)

    def test_instrument_livekit_session_raises_without_sdk(self) -> None:
        """Test that instrument_livekit_session raises if SDK not installed."""
        mock_session = MagicMock()

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", False):
            with pytest.raises(ImportError) as exc_info:
                instrument_livekit_session(mock_session)
            assert "livekit-agents" in str(exc_info.value)

    def test_livekit_hooks_user_input_transcribed_events(self) -> None:
        """Test that LiveKit integration hooks user_input_transcribed events."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            instrument_livekit_session(mock_session)
            assert "user_input_transcribed" in event_handlers

    def test_livekit_hooks_speech_created_events(self) -> None:
        """Test that LiveKit integration hooks speech_created events."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            instrument_livekit_session(mock_session)
            assert "speech_created" in event_handlers

    def test_livekit_hooks_metrics_collected_events(self) -> None:
        """Test that LiveKit integration hooks metrics_collected events."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            instrument_livekit_session(mock_session)
            assert "metrics_collected" in event_handlers

    def test_livekit_hooks_close_events(self) -> None:
        """Test that LiveKit integration hooks close events."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            instrument_livekit_session(mock_session)
            assert "close" in event_handlers

    def test_livekit_wrapper_has_session(self) -> None:
        """Test that LiveKit wrapper has session property."""
        mock_session = MagicMock()
        mock_session.on = MagicMock(return_value=lambda f: f)

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)
            assert wrapper.session is mock_session

    def test_livekit_wrapper_has_conversation_id(self) -> None:
        """Test that LiveKit wrapper has conversation_id property."""
        mock_session = MagicMock()
        mock_session.on = MagicMock(return_value=lambda f: f)

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)
            assert wrapper.conversation_id is not None
            assert len(wrapper.conversation_id) > 0


class TestLiveKitEventHandlers:
    """Tests for LiveKit event handler execution."""

    def test_user_input_transcribed_handler_records_turn_on_final(self) -> None:
        """Test that user_input_transcribed handler records a turn on final."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            # Create mock event with is_final=True
            mock_event = MagicMock()
            mock_event.is_final = True

            with patch.object(wrapper, "_record_turn") as mock_record:
                event_handlers["user_input_transcribed"](mock_event)
                mock_record.assert_called_once_with("user")

    def test_user_input_transcribed_handler_ignores_non_final(self) -> None:
        """Test that user_input_transcribed handler ignores non-final."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            # Create mock event with is_final=False
            mock_event = MagicMock()
            mock_event.is_final = False

            with patch.object(wrapper, "_record_turn") as mock_record:
                event_handlers["user_input_transcribed"](mock_event)
                mock_record.assert_not_called()

    def test_speech_created_handler_records_agent_turn(self) -> None:
        """Test that speech_created handler records an agent turn."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            mock_event = MagicMock()

            with patch.object(wrapper, "_record_turn") as mock_record:
                event_handlers["speech_created"](mock_event)
                mock_record.assert_called_once_with("agent")

    def test_metrics_collected_handler_records_stt_metrics(self) -> None:
        """Test that metrics_collected handler records STT metrics."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            # Create mock STT metrics
            mock_event = MagicMock()
            mock_event.metrics.type = "stt_metrics"
            mock_event.metrics.duration = 0.5
            mock_event.metrics.metadata.model_provider = "deepgram"
            mock_event.metrics.metadata.model_name = "nova-2"

            with patch.object(wrapper, "_record_stage") as mock_record:
                event_handlers["metrics_collected"](mock_event)
                mock_record.assert_called_once_with(
                    stage="asr",
                    provider="deepgram",
                    model="nova-2",
                    duration_ms=500.0,
                )

    def test_metrics_collected_handler_records_llm_metrics(self) -> None:
        """Test that metrics_collected handler records LLM metrics."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            # Create mock LLM metrics
            mock_event = MagicMock()
            mock_event.metrics.type = "llm_metrics"
            mock_event.metrics.duration = 1.2
            mock_event.metrics.prompt_tokens = 100
            mock_event.metrics.completion_tokens = 50
            mock_event.metrics.metadata.model_provider = "openai"
            mock_event.metrics.metadata.model_name = "gpt-4"

            with patch.object(wrapper, "_record_stage") as mock_record:
                event_handlers["metrics_collected"](mock_event)
                mock_record.assert_called_once_with(
                    stage="llm",
                    provider="openai",
                    model="gpt-4",
                    duration_ms=1200.0,
                    input_tokens=100,
                    output_tokens=50,
                )

    def test_metrics_collected_handler_records_tts_metrics(self) -> None:
        """Test that metrics_collected handler records TTS metrics."""
        mock_session = MagicMock()
        event_handlers: dict = {}

        def mock_on(event_name: str):
            def decorator(func):
                event_handlers[event_name] = func
                return func

            return decorator

        mock_session.on = mock_on

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            # Create mock TTS metrics
            mock_event = MagicMock()
            mock_event.metrics.type = "tts_metrics"
            mock_event.metrics.duration = 0.8
            mock_event.metrics.ttfb = 0.15
            mock_event.metrics.metadata.model_provider = "openai"
            mock_event.metrics.metadata.model_name = "tts-1"

            with patch.object(wrapper, "_record_stage") as mock_record:
                event_handlers["metrics_collected"](mock_event)
                mock_record.assert_called_once_with(
                    stage="tts",
                    provider="openai",
                    model="tts-1",
                    duration_ms=800.0,
                    ttfb_ms=150.0,
                )

    def test_getattr_proxies_to_session(self) -> None:
        """Test that __getattr__ proxies attribute access to the session."""
        mock_session = MagicMock()
        mock_session.on = MagicMock(return_value=lambda f: f)
        mock_session.some_method = MagicMock(return_value="result")
        mock_session.some_attribute = "test_value"

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            # Access proxied attribute
            assert wrapper.some_attribute == "test_value"

            # Call proxied method
            result = wrapper.some_method()
            assert result == "result"
            mock_session.some_method.assert_called_once()


class TestLiveKitStartMethod:
    """Tests for the wrapped start method."""

    @pytest.mark.asyncio
    async def test_start_starts_conversation(self) -> None:
        """Test that start() starts the conversation span."""
        mock_session = MagicMock()
        mock_session.on = MagicMock(return_value=lambda f: f)
        mock_session.start = AsyncMock(return_value=None)

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            with patch.object(wrapper, "_start_conversation") as mock_start:
                await wrapper.start(room="test_room")
                mock_start.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_calls_session_start(self) -> None:
        """Test that start() calls the underlying session.start()."""
        mock_session = MagicMock()
        mock_session.on = MagicMock(return_value=lambda f: f)
        mock_session.start = AsyncMock(return_value=None)

        with patch("voiceobs.integrations.livekit.HAS_LIVEKIT", True):
            wrapper = instrument_livekit_session(mock_session)

            await wrapper.start(room="test_room", agent="test_agent")

            mock_session.start.assert_called_once_with(
                room="test_room", agent="test_agent"
            )


class TestLiveKitExports:
    """Tests for LiveKit integration exports."""

    def test_exports_instrument_livekit_session(self) -> None:
        """Test that instrument_livekit_session is exported."""
        from voiceobs.integrations import instrument_livekit_session

        assert instrument_livekit_session is not None

    def test_exports_livekit_session_wrapper(self) -> None:
        """Test that LiveKitSessionWrapper is exported."""
        from voiceobs.integrations import LiveKitSessionWrapper

        assert LiveKitSessionWrapper is not None
