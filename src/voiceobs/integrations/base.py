"""Base classes for voiceobs framework integrations."""

from __future__ import annotations

import uuid
from typing import Any

from voiceobs.context import voice_conversation, voice_turn
from voiceobs.stages import StageType, voice_stage
from voiceobs.types import Actor


class BaseIntegration:
    """Base class for framework integrations.

    Subclasses should implement the instrument() method to add
    voiceobs tracing to a specific framework.
    """

    @property
    def name(self) -> str:
        """Name of this integration."""
        return "base"

    def instrument(self, target: Any) -> Any:
        """Instrument a target object with voiceobs tracing.

        Args:
            target: The framework object to instrument.

        Returns:
            The instrumented object or a wrapper.

        Raises:
            NotImplementedError: If not implemented by subclass.
        """
        raise NotImplementedError("Subclasses must implement instrument()")


class InstrumentedConversation:
    """Wrapper for tracking a voice conversation with voiceobs spans.

    This class provides a simple interface for manually recording
    voice conversation events when auto-instrumentation is not available.

    Example:
        with InstrumentedConversation() as conv:
            conv.record_turn(actor="user", duration_ms=1500)
            conv.record_stage(stage="asr", provider="deepgram", duration_ms=200)
            conv.record_turn(actor="agent", duration_ms=2000)
            conv.record_stage(stage="llm", provider="openai", duration_ms=800)
            conv.record_stage(stage="tts", provider="elevenlabs", duration_ms=300)
    """

    def __init__(self, conversation_id: str | None = None) -> None:
        """Initialize an instrumented conversation.

        Args:
            conversation_id: Optional conversation ID. Auto-generated if not provided.
        """
        self._conversation_id = conversation_id or str(uuid.uuid4())
        self._context_manager: Any = None
        self._conversation_context: Any = None
        self._started = False

    @property
    def conversation_id(self) -> str:
        """Get the conversation ID."""
        return self._conversation_id

    def start(self) -> None:
        """Start the conversation span."""
        if self._started:
            return

        self._context_manager = voice_conversation(conversation_id=self._conversation_id)
        self._conversation_context = self._context_manager.__enter__()
        self._started = True

    def stop(self) -> None:
        """Stop the conversation span."""
        if not self._started or self._context_manager is None:
            return

        self._context_manager.__exit__(None, None, None)
        self._started = False
        self._context_manager = None
        self._conversation_context = None

    def record_turn(
        self,
        actor: Actor,
        duration_ms: float | None = None,
    ) -> None:
        """Record a conversation turn.

        Args:
            actor: The actor for this turn ("user", "agent", or "system").
            duration_ms: Optional duration in milliseconds (for logging).
        """
        if not self._started:
            self.start()

        with voice_turn(actor):
            pass  # The span is created and closed immediately

    def record_stage(
        self,
        stage: StageType,
        provider: str | None = None,
        model: str | None = None,
        duration_ms: float | None = None,
        input_size: int | None = None,
        output_size: int | None = None,
    ) -> None:
        """Record a pipeline stage execution.

        Args:
            stage: The stage type ("asr", "llm", or "tts").
            provider: The service provider name.
            model: The model identifier.
            duration_ms: Optional duration in milliseconds (for logging).
            input_size: Optional input size in bytes/characters.
            output_size: Optional output size in bytes/characters.
        """
        if not self._started:
            self.start()

        with voice_stage(stage, provider=provider, model=model, input_size=input_size):
            pass  # The span is created and closed immediately

    def __enter__(self) -> InstrumentedConversation:
        """Enter the context manager."""
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager."""
        self.stop()
