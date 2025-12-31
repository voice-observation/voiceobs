"""Decorator-based API for voice observability.

Provides function decorators as an alternative to context managers for
instrumenting voice conversations, turns, and stages.
"""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

from voiceobs.context import voice_conversation, voice_turn
from voiceobs.stages import StageType, voice_stage
from voiceobs.types import Actor

F = TypeVar("F", bound=Callable[..., Any])


def voice_conversation_decorator(
    conversation_id: str | None = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function in a voice conversation context.

    Creates a conversation context that tracks the conversation ID and
    turn counter. All voice turns within the decorated function will be
    associated with this conversation.

    Args:
        conversation_id: Optional conversation ID. If not provided, a UUID
            will be auto-generated.

    Returns:
        A decorator that wraps the function in a voice_conversation context.

    Example:
        @voice_conversation_decorator()
        def handle_call():
            # All turns here are part of the same conversation
            process_user_input()
            generate_response()

        @voice_conversation_decorator(conversation_id="call-123")
        def handle_specific_call():
            pass
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with voice_conversation(conversation_id=conversation_id):
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with voice_conversation(conversation_id=conversation_id):
                    return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def voice_turn_decorator(
    actor: Actor,
    *,
    audio_url: str | None = None,
    audio_duration_ms: float | None = None,
    audio_format: str | None = None,
    audio_sample_rate: int | None = None,
    audio_channels: int | None = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function in a voice turn context.

    Creates a turn span that represents a single turn in the conversation.
    Should be used within a voice_conversation context.

    Args:
        actor: The actor for this turn - "user", "agent", or "system".
        audio_url: Optional URL or path to the audio file for this turn.
        audio_duration_ms: Optional duration of the audio in milliseconds.
        audio_format: Optional audio format (e.g., "wav", "mp3", "ogg").
        audio_sample_rate: Optional sample rate in Hz (e.g., 16000, 44100).
        audio_channels: Optional number of audio channels (1=mono, 2=stereo).

    Returns:
        A decorator that wraps the function in a voice_turn context.

    Example:
        @voice_conversation_decorator()
        def handle_call():
            @voice_turn_decorator(actor="user", audio_url="s3://bucket/user.wav")
            def process_user():
                return transcribe_audio()

            @voice_turn_decorator(actor="agent")
            def respond():
                return generate_response()

            user_text = process_user()
            response = respond()
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with voice_turn(
                    actor,
                    audio_url=audio_url,
                    audio_duration_ms=audio_duration_ms,
                    audio_format=audio_format,
                    audio_sample_rate=audio_sample_rate,
                    audio_channels=audio_channels,
                ):
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with voice_turn(
                    actor,
                    audio_url=audio_url,
                    audio_duration_ms=audio_duration_ms,
                    audio_format=audio_format,
                    audio_sample_rate=audio_sample_rate,
                    audio_channels=audio_channels,
                ):
                    return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def voice_stage_decorator(
    stage: StageType,
    *,
    provider: str | None = None,
    model: str | None = None,
    input_size: int | None = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function in a voice stage context.

    Creates a stage span for a voice pipeline component (ASR, LLM, or TTS).
    Should be used within a voice_turn context for proper span hierarchy.

    Args:
        stage: The stage type - "asr", "llm", or "tts".
        provider: The service provider (e.g., "deepgram", "openai", "cartesia").
        model: The model identifier (e.g., "nova-2", "gpt-4", "sonic-3").
        input_size: Size of the input in bytes or characters.

    Returns:
        A decorator that wraps the function in a voice_stage context.

    Example:
        @voice_stage_decorator(stage="llm", provider="openai", model="gpt-4")
        def call_llm(prompt: str) -> str:
            return openai.chat(prompt)

        @voice_stage_decorator(stage="asr", provider="deepgram")
        async def transcribe(audio: bytes) -> str:
            return await deepgram.transcribe(audio)
    """

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with voice_stage(stage, provider=provider, model=model, input_size=input_size):
                    return await func(*args, **kwargs)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                with voice_stage(stage, provider=provider, model=model, input_size=input_size):
                    return func(*args, **kwargs)

            return sync_wrapper  # type: ignore[return-value]

    return decorator
