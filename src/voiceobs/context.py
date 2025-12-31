"""Context management for voice conversations and turns."""

from __future__ import annotations

import uuid
from collections.abc import Generator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind

from voiceobs.timeline import ConversationTimeline
from voiceobs.types import Actor

# Schema version for voice observability attributes
VOICE_SCHEMA_VERSION = "0.0.2"

# Audio attribute names
AUDIO_URL_ATTR = "voice.turn.audio_url"
AUDIO_DURATION_MS_ATTR = "voice.turn.audio_duration_ms"
AUDIO_FORMAT_ATTR = "voice.turn.audio_format"
AUDIO_SAMPLE_RATE_ATTR = "voice.turn.audio_sample_rate"
AUDIO_CHANNELS_ATTR = "voice.turn.audio_channels"


def _get_tracer() -> trace.Tracer:
    """Get the tracer for voice observability."""
    return trace.get_tracer("voiceobs", VOICE_SCHEMA_VERSION)


@dataclass
class ConversationContext:
    """Context for a voice conversation."""

    conversation_id: str
    turn_counter: int = 0
    timeline: ConversationTimeline = field(default_factory=ConversationTimeline)

    def next_turn_index(self) -> int:
        """Get the next turn index and increment the counter."""
        index = self.turn_counter
        self.turn_counter += 1
        return index


@dataclass
class TurnContext:
    """Context for a voice turn within a conversation."""

    turn_id: str
    turn_index: int
    actor: Actor


# Context variables for tracking conversation and turn state
_conversation_context: ContextVar[ConversationContext | None] = ContextVar(
    "voice_conversation_context", default=None
)
_turn_context: ContextVar[TurnContext | None] = ContextVar("voice_turn_context", default=None)


def get_current_conversation() -> ConversationContext | None:
    """Get the current conversation context, if any."""
    return _conversation_context.get()


def get_current_turn() -> TurnContext | None:
    """Get the current turn context, if any."""
    return _turn_context.get()


@contextmanager
def voice_conversation(
    conversation_id: str | None = None,
) -> Generator[ConversationContext, None, None]:
    """Context manager for a voice conversation.

    Creates a conversation context that tracks the conversation ID and
    turn counter. All voice turns within this context will be associated
    with this conversation and share the same trace_id.

    Args:
        conversation_id: Optional conversation ID. If not provided, a UUID
            will be auto-generated.

    Yields:
        The conversation context.

    Example:
        with voice_conversation() as conv:
            print(f"Conversation: {conv.conversation_id}")
            with voice_turn("user"):
                # Handle user speech
                pass
    """
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())

    ctx = ConversationContext(conversation_id=conversation_id)
    token = _conversation_context.set(ctx)

    # Create a parent span for the conversation so all turns share the same trace_id
    with _get_tracer().start_as_current_span(
        "voice.conversation",
        kind=SpanKind.INTERNAL,
    ) as span:
        span.set_attribute("voice.schema.version", VOICE_SCHEMA_VERSION)
        span.set_attribute("voice.conversation.id", conversation_id)
        try:
            yield ctx
        finally:
            _conversation_context.reset(token)


# Store the current span for updating attributes
_current_turn_span: ContextVar[Span | None] = ContextVar("voice_current_turn_span", default=None)


@contextmanager
def voice_turn(
    actor: Actor,
    *,
    audio_url: str | None = None,
    audio_duration_ms: float | None = None,
    audio_format: str | None = None,
    audio_sample_rate: int | None = None,
    audio_channels: int | None = None,
) -> Generator[TurnContext, None, None]:
    """Context manager for a voice turn.

    Creates a turn context and emits an OpenTelemetry span for the turn.
    Must be called within a voice_conversation context.

    Args:
        actor: The actor for this turn - "user", "agent", or "system".
        audio_url: Optional URL or path to the audio file for this turn.
        audio_duration_ms: Optional duration of the audio in milliseconds.
        audio_format: Optional audio format (e.g., "wav", "mp3", "ogg").
        audio_sample_rate: Optional sample rate in Hz (e.g., 16000, 44100).
        audio_channels: Optional number of audio channels (1=mono, 2=stereo).

    Yields:
        The turn context.

    Raises:
        RuntimeError: If called outside of a voice_conversation context.

    Example:
        with voice_conversation():
            with voice_turn("user", audio_url="s3://bucket/audio.wav") as turn:
                print(f"Turn {turn.turn_index} by {turn.actor}")
                # Process user utterance
    """
    conversation = get_current_conversation()
    if conversation is None:
        raise RuntimeError("voice_turn must be called within a voice_conversation context")

    turn_id = str(uuid.uuid4())
    turn_index = conversation.next_turn_index()

    turn_ctx = TurnContext(turn_id=turn_id, turn_index=turn_index, actor=actor)
    token = _turn_context.set(turn_ctx)

    # Track turn timing
    conversation.timeline.start_turn(turn_index, actor)

    # Create OpenTelemetry span for this turn
    with _get_tracer().start_as_current_span(
        "voice.turn",
        kind=SpanKind.INTERNAL,
    ) as span:
        span_token = _current_turn_span.set(span)
        _set_turn_attributes(span, conversation, turn_ctx)

        # Set audio metadata attributes if provided
        if audio_url is not None:
            span.set_attribute(AUDIO_URL_ATTR, audio_url)
        if audio_duration_ms is not None:
            span.set_attribute(AUDIO_DURATION_MS_ATTR, audio_duration_ms)
        if audio_format is not None:
            span.set_attribute(AUDIO_FORMAT_ATTR, audio_format)
        if audio_sample_rate is not None:
            span.set_attribute(AUDIO_SAMPLE_RATE_ATTR, audio_sample_rate)
        if audio_channels is not None:
            span.set_attribute(AUDIO_CHANNELS_ATTR, audio_channels)

        try:
            yield turn_ctx
        finally:
            # Set timing metrics at the end of agent turns
            # This allows mark_speech_start/mark_speech_end to be called first
            if actor == "agent":
                # Silence/latency metrics
                silence_ms = conversation.timeline.compute_silence_after_user_ms()
                if silence_ms is not None:
                    span.set_attribute("voice.silence.after_user_ms", silence_ms)
                    span.set_attribute("voice.silence.before_agent_ms", silence_ms)

                # Overlap/interruption metrics
                overlap_ms = conversation.timeline.compute_overlap_ms()
                if overlap_ms is not None:
                    span.set_attribute("voice.turn.overlap_ms", overlap_ms)
                    span.set_attribute(
                        "voice.interruption.detected",
                        conversation.timeline.is_interruption(),
                    )

            conversation.timeline.end_turn()
            _current_turn_span.reset(span_token)
            _turn_context.reset(token)


def mark_speech_end() -> None:
    """Mark when speech ends in the current turn.

    For user turns, call this when the user stops speaking
    (e.g., when VAD detects silence or recording stops).

    This enables accurate response latency measurement.

    Example:
        with voice_turn("user"):
            audio = record_audio()
            mark_speech_end()  # User stopped speaking
            transcript = transcribe(audio)
    """
    conversation = get_current_conversation()
    if conversation is not None:
        conversation.timeline.mark_speech_end()


def mark_speech_start(timestamp_ns: int | None = None) -> None:
    """Mark when speech starts in the current turn.

    For agent turns, call this when TTS audio playback begins.

    This enables accurate response latency measurement.

    Args:
        timestamp_ns: Optional timestamp in nanoseconds. If not provided,
            uses the current time. This can be used to backdate the speech
            start for barge-in scenarios where the agent logically started
            responding earlier than actual playback.

    Example:
        with voice_turn("agent"):
            response = generate_response(text)
            audio = synthesize(response)
            mark_speech_start()  # Agent starts speaking
            play_audio(audio)
    """
    conversation = get_current_conversation()
    if conversation is not None:
        conversation.timeline.mark_speech_start(timestamp_ns)


def _set_turn_attributes(
    span: Span,
    conversation: ConversationContext,
    turn: TurnContext,
) -> None:
    """Set OpenTelemetry attributes on a turn span."""
    span.set_attribute("voice.schema.version", VOICE_SCHEMA_VERSION)
    span.set_attribute("voice.conversation.id", conversation.conversation_id)
    span.set_attribute("voice.turn.id", turn.turn_id)
    span.set_attribute("voice.turn.index", turn.turn_index)
    span.set_attribute("voice.actor", turn.actor)
