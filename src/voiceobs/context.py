"""Context management for voice conversations and turns."""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generator, Literal, Optional

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind

if TYPE_CHECKING:
    pass

# Schema version for voice observability attributes
VOICE_SCHEMA_VERSION = "0.0.1"


def _get_tracer() -> trace.Tracer:
    """Get the tracer for voice observability."""
    return trace.get_tracer("voiceobs", VOICE_SCHEMA_VERSION)

# Actor type for voice turns
Actor = Literal["user", "agent", "system"]


@dataclass
class ConversationContext:
    """Context for a voice conversation."""

    conversation_id: str
    turn_counter: int = 0

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
_conversation_context: ContextVar[Optional[ConversationContext]] = ContextVar(
    "voice_conversation_context", default=None
)
_turn_context: ContextVar[Optional[TurnContext]] = ContextVar(
    "voice_turn_context", default=None
)


def get_current_conversation() -> Optional[ConversationContext]:
    """Get the current conversation context, if any."""
    return _conversation_context.get()


def get_current_turn() -> Optional[TurnContext]:
    """Get the current turn context, if any."""
    return _turn_context.get()


@contextmanager
def voice_conversation(
    conversation_id: Optional[str] = None,
) -> Generator[ConversationContext, None, None]:
    """Context manager for a voice conversation.

    Creates a conversation context that tracks the conversation ID and
    turn counter. All voice turns within this context will be associated
    with this conversation.

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
    try:
        yield ctx
    finally:
        _conversation_context.reset(token)


@contextmanager
def voice_turn(actor: Actor) -> Generator[TurnContext, None, None]:
    """Context manager for a voice turn.

    Creates a turn context and emits an OpenTelemetry span for the turn.
    Must be called within a voice_conversation context.

    Args:
        actor: The actor for this turn - "user", "agent", or "system".

    Yields:
        The turn context.

    Raises:
        RuntimeError: If called outside of a voice_conversation context.

    Example:
        with voice_conversation():
            with voice_turn("user") as turn:
                print(f"Turn {turn.turn_index} by {turn.actor}")
                # Process user utterance
    """
    conversation = get_current_conversation()
    if conversation is None:
        raise RuntimeError(
            "voice_turn must be called within a voice_conversation context"
        )

    turn_id = str(uuid.uuid4())
    turn_index = conversation.next_turn_index()

    turn_ctx = TurnContext(turn_id=turn_id, turn_index=turn_index, actor=actor)
    token = _turn_context.set(turn_ctx)

    # Create OpenTelemetry span for this turn
    with _get_tracer().start_as_current_span(
        "voice.turn",
        kind=SpanKind.INTERNAL,
    ) as span:
        _set_turn_attributes(span, conversation, turn_ctx)
        try:
            yield turn_ctx
        finally:
            _turn_context.reset(token)


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
