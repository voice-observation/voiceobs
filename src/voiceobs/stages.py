"""Stage-level spans for voice pipeline components (ASR, LLM, TTS)."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Literal

from opentelemetry.trace import SpanKind

from voiceobs.context import VOICE_SCHEMA_VERSION, _get_tracer, get_current_conversation

# Canonical stage names
StageType = Literal["asr", "llm", "tts"]

# Stage span names
_STAGE_SPAN_NAMES = {
    "asr": "voice.asr",
    "llm": "voice.llm",
    "tts": "voice.tts",
}


@contextmanager
def voice_stage(
    stage: StageType,
    *,
    provider: str | None = None,
    model: str | None = None,
    input_size: int | None = None,
) -> Generator[StageContext, None, None]:
    """Context manager for a voice pipeline stage (ASR, LLM, or TTS).

    Creates an OpenTelemetry span for the stage operation. Should be called
    within a voice_turn context for proper span hierarchy.

    Args:
        stage: The stage type - "asr", "llm", or "tts".
        provider: The service provider (e.g., "deepgram", "openai", "cartesia").
        model: The model identifier (e.g., "nova-2", "gpt-4", "sonic-3").
        input_size: Size of the input in bytes or characters.

    Yields:
        A StageContext that can be used to set output_size or error.

    Example:
        with voice_turn("user"):
            with voice_stage("asr", provider="deepgram", model="nova-2") as asr:
                transcript = transcribe(audio)
                asr.set_output(len(transcript))
    """
    span_name = _STAGE_SPAN_NAMES.get(stage, f"voice.{stage}")

    ctx = StageContext(stage=stage)

    with _get_tracer().start_as_current_span(
        span_name,
        kind=SpanKind.CLIENT,  # CLIENT since we're calling external services
    ) as span:
        # Set schema version
        span.set_attribute("voice.schema.version", VOICE_SCHEMA_VERSION)

        # Set conversation ID if available
        conversation = get_current_conversation()
        if conversation:
            span.set_attribute("voice.conversation.id", conversation.conversation_id)

        # Set stage type
        span.set_attribute("voice.stage.type", stage)

        # Set optional attributes if provided
        if provider is not None:
            span.set_attribute("voice.stage.provider", provider)
        if model is not None:
            span.set_attribute("voice.stage.model", model)
        if input_size is not None:
            span.set_attribute("voice.stage.input_size", input_size)

        # Store span reference in context for later updates
        ctx._span = span

        try:
            yield ctx
        except Exception as e:
            # Record error on the span
            span.set_attribute("voice.stage.error", str(e))
            span.record_exception(e)
            raise


class StageContext:
    """Context object for a voice stage, allowing updates during execution."""

    def __init__(self, stage: StageType) -> None:
        self.stage = stage
        self._span = None
        self._output_size: int | None = None

    def set_output(self, size: int) -> None:
        """Set the output size for this stage.

        Args:
            size: Size of the output in bytes or characters.
        """
        self._output_size = size
        if self._span is not None:
            self._span.set_attribute("voice.stage.output_size", size)

    def set_error(self, error: str) -> None:
        """Set an error message for this stage.

        Args:
            error: Error message or description.
        """
        if self._span is not None:
            self._span.set_attribute("voice.stage.error", error)
