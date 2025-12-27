"""Tests for decorator-based API."""

from __future__ import annotations

import asyncio

import pytest

from voiceobs.decorators import (
    voice_conversation_decorator,
    voice_stage_decorator,
    voice_turn_decorator,
)


class TestVoiceConversationDecorator:
    """Tests for @voice_conversation_decorator."""

    def test_decorator_wraps_sync_function(self):
        """Test that decorator works with sync functions."""

        @voice_conversation_decorator()
        def my_conversation():
            return "result"

        result = my_conversation()
        assert result == "result"

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves __name__."""

        @voice_conversation_decorator()
        def my_conversation():
            pass

        assert my_conversation.__name__ == "my_conversation"

    def test_decorator_preserves_docstring(self):
        """Test that decorator preserves __doc__."""

        @voice_conversation_decorator()
        def my_conversation():
            """My docstring."""
            pass

        assert my_conversation.__doc__ == "My docstring."

    def test_decorator_creates_conversation_context(self):
        """Test that decorator creates conversation context."""
        from voiceobs import get_current_conversation

        context_inside = None

        @voice_conversation_decorator()
        def my_conversation():
            nonlocal context_inside
            context_inside = get_current_conversation()
            return context_inside

        my_conversation()
        assert context_inside is not None
        assert context_inside.conversation_id is not None

    def test_decorator_with_custom_conversation_id(self):
        """Test that decorator accepts custom conversation_id."""
        from voiceobs import get_current_conversation

        @voice_conversation_decorator(conversation_id="custom-123")
        def my_conversation():
            return get_current_conversation()

        ctx = my_conversation()
        assert ctx.conversation_id == "custom-123"

    def test_decorator_with_args_and_kwargs(self):
        """Test that decorator passes args and kwargs to function."""

        @voice_conversation_decorator()
        def my_conversation(a, b, c=None):
            return (a, b, c)

        result = my_conversation(1, 2, c=3)
        assert result == (1, 2, 3)

    @pytest.mark.asyncio
    async def test_decorator_wraps_async_function(self):
        """Test that decorator works with async functions."""

        @voice_conversation_decorator()
        async def my_async_conversation():
            await asyncio.sleep(0.001)
            return "async_result"

        result = await my_async_conversation()
        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_async_decorator_creates_context(self):
        """Test that async decorator creates conversation context."""
        from voiceobs import get_current_conversation

        @voice_conversation_decorator()
        async def my_async_conversation():
            return get_current_conversation()

        ctx = await my_async_conversation()
        assert ctx is not None
        assert ctx.conversation_id is not None


class TestVoiceTurnDecorator:
    """Tests for @voice_turn_decorator."""

    def test_decorator_wraps_sync_function(self):
        """Test that decorator works with sync functions."""

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="user")
            def user_turn():
                return "user_said"

            return user_turn()

        result = conversation()
        assert result == "user_said"

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves __name__."""

        @voice_turn_decorator(actor="agent")
        def agent_response():
            pass

        assert agent_response.__name__ == "agent_response"

    def test_decorator_creates_turn_context(self):
        """Test that decorator creates turn context."""
        from voiceobs import get_current_turn

        turn_inside = None

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="user")
            def user_turn():
                nonlocal turn_inside
                turn_inside = get_current_turn()

            user_turn()

        conversation()
        assert turn_inside is not None
        assert turn_inside.actor == "user"

    def test_decorator_with_agent_actor(self):
        """Test decorator with agent actor."""
        from voiceobs import get_current_turn

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="agent")
            def agent_turn():
                return get_current_turn()

            return agent_turn()

        turn = conversation()
        assert turn.actor == "agent"

    def test_decorator_increments_turn_index(self):
        """Test that turn index increments correctly."""
        from voiceobs import get_current_turn

        indices = []

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="user")
            def turn1():
                indices.append(get_current_turn().turn_index)

            @voice_turn_decorator(actor="agent")
            def turn2():
                indices.append(get_current_turn().turn_index)

            turn1()
            turn2()

        conversation()
        assert indices == [0, 1]

    @pytest.mark.asyncio
    async def test_decorator_wraps_async_function(self):
        """Test that decorator works with async functions."""

        @voice_conversation_decorator()
        async def conversation():
            @voice_turn_decorator(actor="user")
            async def async_turn():
                await asyncio.sleep(0.001)
                return "async_turn_result"

            return await async_turn()

        result = await conversation()
        assert result == "async_turn_result"


class TestVoiceStageDecorator:
    """Tests for @voice_stage_decorator."""

    def test_decorator_wraps_sync_function(self):
        """Test that decorator works with sync functions."""

        @voice_stage_decorator(stage="llm")
        def call_llm():
            return "llm_response"

        result = call_llm()
        assert result == "llm_response"

    def test_decorator_preserves_function_name(self):
        """Test that decorator preserves __name__."""

        @voice_stage_decorator(stage="asr")
        def transcribe_audio():
            pass

        assert transcribe_audio.__name__ == "transcribe_audio"

    def test_decorator_with_provider_and_model(self):
        """Test decorator with provider and model parameters."""

        @voice_stage_decorator(stage="tts", provider="cartesia", model="sonic-3")
        def synthesize_speech():
            return "audio_bytes"

        result = synthesize_speech()
        assert result == "audio_bytes"

    def test_decorator_asr_stage(self):
        """Test decorator with ASR stage."""

        @voice_stage_decorator(stage="asr", provider="deepgram", model="nova-2")
        def transcribe():
            return "transcript"

        result = transcribe()
        assert result == "transcript"

    def test_decorator_llm_stage(self):
        """Test decorator with LLM stage."""

        @voice_stage_decorator(stage="llm", provider="openai", model="gpt-4")
        def generate_response():
            return "response"

        result = generate_response()
        assert result == "response"

    def test_decorator_tts_stage(self):
        """Test decorator with TTS stage."""

        @voice_stage_decorator(stage="tts", provider="elevenlabs")
        def text_to_speech():
            return b"audio"

        result = text_to_speech()
        assert result == b"audio"

    @pytest.mark.asyncio
    async def test_decorator_wraps_async_function(self):
        """Test that decorator works with async functions."""

        @voice_stage_decorator(stage="llm")
        async def async_llm_call():
            await asyncio.sleep(0.001)
            return "async_llm_response"

        result = await async_llm_call()
        assert result == "async_llm_response"

    def test_decorator_within_turn_context(self):
        """Test decorator within turn context."""

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="agent")
            def agent_turn():
                @voice_stage_decorator(stage="llm", provider="openai")
                def call_llm():
                    return "llm_output"

                return call_llm()

            return agent_turn()

        result = conversation()
        assert result == "llm_output"


class TestDecoratorExceptionHandling:
    """Tests for exception handling in decorators."""

    def test_conversation_decorator_propagates_exception(self):
        """Test that exceptions propagate through conversation decorator."""

        @voice_conversation_decorator()
        def failing_conversation():
            raise ValueError("test error")

        with pytest.raises(ValueError, match="test error"):
            failing_conversation()

    def test_turn_decorator_propagates_exception(self):
        """Test that exceptions propagate through turn decorator."""

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="user")
            def failing_turn():
                raise RuntimeError("turn error")

            failing_turn()

        with pytest.raises(RuntimeError, match="turn error"):
            conversation()

    def test_stage_decorator_propagates_exception(self):
        """Test that exceptions propagate through stage decorator."""

        @voice_stage_decorator(stage="llm")
        def failing_stage():
            raise ConnectionError("llm error")

        with pytest.raises(ConnectionError, match="llm error"):
            failing_stage()


class TestDecoratorReturnValues:
    """Tests for return value handling in decorators."""

    def test_conversation_returns_none(self):
        """Test decorator with function returning None."""

        @voice_conversation_decorator()
        def no_return():
            pass

        result = no_return()
        assert result is None

    def test_conversation_returns_complex_type(self):
        """Test decorator with function returning complex type."""

        @voice_conversation_decorator()
        def return_dict():
            return {"key": "value", "nested": {"a": 1}}

        result = return_dict()
        assert result == {"key": "value", "nested": {"a": 1}}

    def test_turn_returns_tuple(self):
        """Test turn decorator with function returning tuple."""

        @voice_conversation_decorator()
        def conversation():
            @voice_turn_decorator(actor="user")
            def return_tuple():
                return (1, 2, 3)

            return return_tuple()

        result = conversation()
        assert result == (1, 2, 3)
