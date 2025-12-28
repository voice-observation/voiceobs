"""Tests for voiceobs integrations base classes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from voiceobs.integrations import BaseIntegration, InstrumentedConversation


class TestBaseIntegration:
    """Tests for BaseIntegration class."""

    def test_base_integration_requires_implementation(self) -> None:
        """Test that BaseIntegration cannot be used directly."""
        integration = BaseIntegration()
        with pytest.raises(NotImplementedError):
            integration.instrument(MagicMock())

    def test_base_integration_has_name(self) -> None:
        """Test that BaseIntegration has a name property."""
        integration = BaseIntegration()
        assert integration.name == "base"


class TestInstrumentedConversation:
    """Tests for InstrumentedConversation wrapper."""

    def test_creates_conversation_context(self) -> None:
        """Test that InstrumentedConversation creates a conversation context."""
        conv = InstrumentedConversation(conversation_id="test-conv-123")
        assert conv.conversation_id == "test-conv-123"

    def test_auto_generates_conversation_id(self) -> None:
        """Test that conversation ID is auto-generated if not provided."""
        conv = InstrumentedConversation()
        assert conv.conversation_id is not None
        assert len(conv.conversation_id) > 0

    def test_start_creates_span(self) -> None:
        """Test that start() creates a conversation span."""
        with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
            mock_context = MagicMock()
            mock_conv.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_conv.return_value.__exit__ = MagicMock(return_value=None)

            conv = InstrumentedConversation(conversation_id="test-123")
            conv.start()

            mock_conv.assert_called_once_with(conversation_id="test-123")

    def test_stop_ends_span(self) -> None:
        """Test that stop() ends the conversation span."""
        with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
            mock_cm = MagicMock()
            mock_conv.return_value = mock_cm

            conv = InstrumentedConversation()
            conv.start()
            conv.stop()

            mock_cm.__exit__.assert_called_once()

    def test_record_turn_creates_turn_span(self) -> None:
        """Test that record_turn creates a turn span."""
        with patch("voiceobs.integrations.base.voice_conversation"):
            with patch("voiceobs.integrations.base.voice_turn") as mock_turn:
                mock_turn.return_value.__enter__ = MagicMock()
                mock_turn.return_value.__exit__ = MagicMock(return_value=None)

                conv = InstrumentedConversation()
                conv.start()
                conv.record_turn(actor="user", duration_ms=500.0)

                mock_turn.assert_called_once_with("user")

    def test_record_stage_creates_stage_span(self) -> None:
        """Test that record_stage creates a stage span."""
        with patch("voiceobs.integrations.base.voice_conversation"):
            with patch("voiceobs.integrations.base.voice_stage") as mock_stage:
                mock_stage.return_value.__enter__ = MagicMock()
                mock_stage.return_value.__exit__ = MagicMock(return_value=None)

                conv = InstrumentedConversation()
                conv.start()
                conv.record_stage(
                    stage="asr",
                    provider="deepgram",
                    model="nova-2",
                    duration_ms=150.0,
                )

                mock_stage.assert_called_once_with(
                    "asr", provider="deepgram", model="nova-2", input_size=None
                )

    def test_context_manager_usage(self) -> None:
        """Test that InstrumentedConversation works as context manager."""
        with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
            mock_cm = MagicMock()
            mock_conv.return_value = mock_cm

            with InstrumentedConversation() as conv:
                assert conv is not None

            mock_cm.__enter__.assert_called_once()
            mock_cm.__exit__.assert_called_once()


class TestIntegrationExports:
    """Tests for integration module exports."""

    def test_exports_base_integration(self) -> None:
        """Test that BaseIntegration is exported."""
        from voiceobs.integrations import BaseIntegration

        assert BaseIntegration is not None

    def test_exports_instrumented_conversation(self) -> None:
        """Test that InstrumentedConversation is exported."""
        from voiceobs.integrations import InstrumentedConversation

        assert InstrumentedConversation is not None


class TestInstrumentedConversationEdgeCases:
    """Edge case tests for InstrumentedConversation."""

    def test_start_is_idempotent(self) -> None:
        """Test that calling start() multiple times is safe."""
        with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
            mock_cm = MagicMock()
            mock_conv.return_value = mock_cm

            conv = InstrumentedConversation()
            conv.start()
            conv.start()  # Second call should be no-op

            # Should only be called once
            mock_conv.assert_called_once()

    def test_stop_without_start_is_safe(self) -> None:
        """Test that calling stop() without start() is safe."""
        conv = InstrumentedConversation()
        conv.stop()  # Should not raise

    def test_record_turn_auto_starts_conversation(self) -> None:
        """Test that record_turn starts conversation if not started."""
        with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
            with patch("voiceobs.integrations.base.voice_turn") as mock_turn:
                mock_conv.return_value.__enter__ = MagicMock()
                mock_conv.return_value.__exit__ = MagicMock(return_value=None)
                mock_turn.return_value.__enter__ = MagicMock()
                mock_turn.return_value.__exit__ = MagicMock(return_value=None)

                conv = InstrumentedConversation()
                # Don't call start() explicitly
                conv.record_turn(actor="user")

                # Conversation should have been started
                mock_conv.assert_called_once()

    def test_record_stage_auto_starts_conversation(self) -> None:
        """Test that record_stage starts conversation if not started."""
        with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
            with patch("voiceobs.integrations.base.voice_stage") as mock_stage:
                mock_conv.return_value.__enter__ = MagicMock()
                mock_conv.return_value.__exit__ = MagicMock(return_value=None)
                mock_stage.return_value.__enter__ = MagicMock()
                mock_stage.return_value.__exit__ = MagicMock(return_value=None)

                conv = InstrumentedConversation()
                # Don't call start() explicitly
                conv.record_stage(stage="asr")

                # Conversation should have been started
                mock_conv.assert_called_once()
