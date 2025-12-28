"""Tests for Vocode integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.integrations import instrument_vocode_conversation


class TestVocodeIntegration:
    """Tests for Vocode integration."""

    def test_instrument_vocode_returns_wrapper(self) -> None:
        """Test that instrument_vocode_conversation returns a wrapper."""
        mock_conversation = MagicMock()

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            result = instrument_vocode_conversation(mock_conversation)
            assert result is not None

    def test_instrument_vocode_raises_without_sdk(self) -> None:
        """Test that instrument_vocode_conversation raises if SDK not installed."""
        mock_conversation = MagicMock()

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", False):
            with pytest.raises(ImportError) as exc_info:
                instrument_vocode_conversation(mock_conversation)
            assert "vocode" in str(exc_info.value)

    def test_vocode_wrapper_has_conversation(self) -> None:
        """Test that Vocode wrapper has reference to original conversation."""
        mock_conversation = MagicMock()
        mock_conversation.start = AsyncMock()

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            wrapper = instrument_vocode_conversation(mock_conversation)
            assert wrapper.conversation is mock_conversation

    def test_vocode_wrapper_has_instrumented_conversation(self) -> None:
        """Test that Vocode wrapper provides InstrumentedConversation."""
        mock_conversation = MagicMock()

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            wrapper = instrument_vocode_conversation(mock_conversation)
            assert hasattr(wrapper, "instrumented")

    def test_vocode_wrapper_proxies_attributes(self) -> None:
        """Test that Vocode wrapper proxies attributes to original."""
        mock_conversation = MagicMock()
        mock_conversation.some_attribute = "test_value"

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            wrapper = instrument_vocode_conversation(mock_conversation)
            assert wrapper.some_attribute == "test_value"


class TestVocodeAsyncWrappers:
    """Tests for Vocode async method wrappers."""

    @pytest.mark.asyncio
    async def test_start_wrapper_calls_instrumented_start(self) -> None:
        """Test that calling start() triggers instrumented start."""
        mock_conversation = MagicMock()
        mock_conversation.start = AsyncMock(return_value="start_result")
        mock_conversation.terminate = AsyncMock()

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
                mock_conv.return_value.__enter__ = MagicMock()
                mock_conv.return_value.__exit__ = MagicMock(return_value=None)

                wrapper = instrument_vocode_conversation(mock_conversation)

                # Call the wrapped start method
                result = await wrapper.conversation.start()

                # Verify original start was called
                assert result == "start_result"
                # Verify instrumented.start was called (via voice_conversation)
                mock_conv.assert_called_once()

    @pytest.mark.asyncio
    async def test_terminate_wrapper_calls_instrumented_stop(self) -> None:
        """Test that calling terminate() triggers instrumented stop."""
        mock_conversation = MagicMock()
        mock_conversation.start = AsyncMock()
        mock_conversation.terminate = AsyncMock(return_value="terminate_result")

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            with patch("voiceobs.integrations.base.voice_conversation") as mock_conv:
                mock_conv.return_value.__enter__ = MagicMock()
                mock_conv.return_value.__exit__ = MagicMock(return_value=None)

                wrapper = instrument_vocode_conversation(mock_conversation)
                wrapper.instrumented.start()  # Start first

                # Call the wrapped terminate method
                result = await wrapper.conversation.terminate()

                # Verify original terminate was called
                assert result == "terminate_result"

    @pytest.mark.asyncio
    async def test_start_passes_args_and_kwargs(self) -> None:
        """Test that start wrapper passes arguments correctly."""
        mock_conversation = MagicMock()
        original_start = AsyncMock(return_value="result")
        mock_conversation.start = original_start
        mock_conversation.terminate = AsyncMock()

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            wrapper = instrument_vocode_conversation(mock_conversation)

            # Call with args and kwargs
            await wrapper.conversation.start("arg1", kwarg1="value1")

            # Verify args were passed through to the original
            original_start.assert_called_once_with("arg1", kwarg1="value1")

    @pytest.mark.asyncio
    async def test_terminate_passes_args_and_kwargs(self) -> None:
        """Test that terminate wrapper passes arguments correctly."""
        mock_conversation = MagicMock()
        mock_conversation.start = AsyncMock()
        original_terminate = AsyncMock(return_value="result")
        mock_conversation.terminate = original_terminate

        with patch("voiceobs.integrations.vocode.HAS_VOCODE", True):
            wrapper = instrument_vocode_conversation(mock_conversation)

            # Call with args and kwargs
            await wrapper.conversation.terminate("arg1", kwarg1="value1")

            # Verify args were passed through to the original
            original_terminate.assert_called_once_with("arg1", kwarg1="value1")


class TestVocodeExports:
    """Tests for Vocode integration exports."""

    def test_exports_instrument_vocode_conversation(self) -> None:
        """Test that instrument_vocode_conversation is exported."""
        from voiceobs.integrations import instrument_vocode_conversation

        assert instrument_vocode_conversation is not None
