"""LiveKit Agents SDK integration for voiceobs.

This module provides auto-instrumentation for LiveKit's AgentSession.

Example:
    from livekit.agents import AgentSession, Agent
    from voiceobs.integrations import instrument_livekit_session

    session = AgentSession(
        stt=deepgram.STT(),
        llm="openai/gpt-4.1-mini",
        tts=openai.TTS(),
        vad=silero.VAD.load(),
    )

    # Instrument the session
    instrumented_session = instrument_livekit_session(session)

    # Use the session normally - spans are created automatically
    await instrumented_session.start(room=ctx.room, agent=MyAgent())
"""

from __future__ import annotations

import uuid
from typing import Any

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind

# Check if livekit-agents is installed
try:
    import livekit.agents  # noqa: F401

    HAS_LIVEKIT = True
except ImportError:
    HAS_LIVEKIT = False


VOICE_SCHEMA_VERSION = "0.0.2"


def _get_tracer() -> trace.Tracer:
    """Get the tracer for voice observability."""
    return trace.get_tracer("voiceobs", VOICE_SCHEMA_VERSION)


class LiveKitSessionWrapper:
    """Wrapper that adds voiceobs instrumentation to a LiveKit AgentSession.

    This wrapper hooks into LiveKit session events to automatically create
    voiceobs spans for conversations, turns, and pipeline stages.
    """

    def __init__(self, session: Any) -> None:
        """Initialize the wrapper.

        Args:
            session: The LiveKit AgentSession to instrument.
        """
        self._session = session
        self._conversation_id = str(uuid.uuid4())
        self._conversation_span: Span | None = None
        self._turn_counter = 0
        self._setup_event_handlers()

    @property
    def session(self) -> Any:
        """Get the wrapped session."""
        return self._session

    @property
    def conversation_id(self) -> str:
        """Get the conversation ID."""
        return self._conversation_id

    def _setup_event_handlers(self) -> None:
        """Set up event handlers on the session."""

        @self._session.on("user_input_transcribed")
        def on_user_input(event: Any) -> None:
            """Handle user input transcribed event."""
            if getattr(event, "is_final", False):
                self._record_turn("user")

        @self._session.on("speech_created")
        def on_speech_created(event: Any) -> None:
            """Handle speech created event (agent starts speaking)."""
            self._record_turn("agent")

        @self._session.on("metrics_collected")
        def on_metrics(event: Any) -> None:
            """Handle metrics collected event for STT/LLM/TTS tracking."""
            metrics = getattr(event, "metrics", None)
            if metrics is None:
                return

            metrics_type = getattr(metrics, "type", None)
            if metrics_type == "stt_metrics":
                # For streaming STT, duration is 0.0; use audio_duration instead
                stt_duration = (
                    metrics.duration if metrics.duration else getattr(metrics, "audio_duration", 0)
                )
                self._record_stage(
                    stage="asr",
                    provider=getattr(metrics.metadata, "model_provider", None)
                    if metrics.metadata
                    else None,
                    model=getattr(metrics.metadata, "model_name", None)
                    if metrics.metadata
                    else None,
                    duration_ms=stt_duration * 1000 if stt_duration else None,
                )
            elif metrics_type == "llm_metrics":
                self._record_stage(
                    stage="llm",
                    provider=getattr(metrics.metadata, "model_provider", None)
                    if metrics.metadata
                    else None,
                    model=getattr(metrics.metadata, "model_name", None)
                    if metrics.metadata
                    else None,
                    duration_ms=metrics.duration * 1000 if metrics.duration else None,
                    input_tokens=getattr(metrics, "prompt_tokens", None),
                    output_tokens=getattr(metrics, "completion_tokens", None),
                )
            elif metrics_type == "tts_metrics":
                self._record_stage(
                    stage="tts",
                    provider=getattr(metrics.metadata, "model_provider", None)
                    if metrics.metadata
                    else None,
                    model=getattr(metrics.metadata, "model_name", None)
                    if metrics.metadata
                    else None,
                    duration_ms=metrics.duration * 1000 if metrics.duration else None,
                    ttfb_ms=metrics.ttfb * 1000 if metrics.ttfb else None,
                )

        @self._session.on("close")
        def on_close(event: Any) -> None:
            """Handle session close event."""
            self._stop_conversation()

    def _start_conversation(self) -> None:
        """Start the conversation span."""
        if self._conversation_span is not None:
            return

        tracer = _get_tracer()
        self._conversation_span = tracer.start_span(
            "voice.conversation",
            kind=SpanKind.INTERNAL,
        )
        self._conversation_span.set_attribute("voice.schema.version", VOICE_SCHEMA_VERSION)
        self._conversation_span.set_attribute("voice.conversation.id", self._conversation_id)

    def _stop_conversation(self) -> None:
        """Stop the conversation span."""
        if self._conversation_span is not None:
            self._conversation_span.end()
            self._conversation_span = None

    def _record_turn(self, actor: str) -> None:
        """Record a conversation turn."""
        if self._conversation_span is None:
            self._start_conversation()

        turn_id = str(uuid.uuid4())
        turn_index = self._turn_counter
        self._turn_counter += 1

        tracer = _get_tracer()
        # Create turn span as child of conversation span
        ctx = trace.set_span_in_context(self._conversation_span)
        with tracer.start_as_current_span(
            "voice.turn",
            context=ctx,
            kind=SpanKind.INTERNAL,
        ) as span:
            span.set_attribute("voice.schema.version", VOICE_SCHEMA_VERSION)
            span.set_attribute("voice.conversation.id", self._conversation_id)
            span.set_attribute("voice.turn.id", turn_id)
            span.set_attribute("voice.turn.index", turn_index)
            span.set_attribute("voice.actor", actor)

    def _record_stage(
        self,
        stage: str,
        provider: str | None = None,
        model: str | None = None,
        duration_ms: float | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        ttfb_ms: float | None = None,
    ) -> None:
        """Record a pipeline stage."""
        if self._conversation_span is None:
            self._start_conversation()

        tracer = _get_tracer()
        # Create stage span as child of conversation span
        ctx = trace.set_span_in_context(self._conversation_span)
        with tracer.start_as_current_span(
            f"voice.stage.{stage}",
            context=ctx,
            kind=SpanKind.INTERNAL,
        ) as span:
            span.set_attribute("voice.schema.version", VOICE_SCHEMA_VERSION)
            span.set_attribute("voice.conversation.id", self._conversation_id)
            span.set_attribute("voice.stage.type", stage)
            if provider:
                span.set_attribute("voice.stage.provider", provider)
            if model:
                span.set_attribute("voice.stage.model", model)
            if duration_ms is not None:
                span.set_attribute("voice.stage.duration_ms", duration_ms)
            if input_tokens is not None:
                span.set_attribute("voice.stage.input_tokens", input_tokens)
            if output_tokens is not None:
                span.set_attribute("voice.stage.output_tokens", output_tokens)
            if ttfb_ms is not None:
                span.set_attribute("voice.stage.ttfb_ms", ttfb_ms)

    async def start(self, *args: Any, **kwargs: Any) -> Any:
        """Start the session and begin voiceobs conversation tracking."""
        self._start_conversation()
        return await self._session.start(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the wrapped session."""
        return getattr(self._session, name)


def instrument_livekit_session(session: Any) -> LiveKitSessionWrapper:
    """Instrument a LiveKit AgentSession with voiceobs tracing.

    This function wraps a LiveKit session to automatically create voiceobs
    spans for voice conversations. It hooks into the session's event system
    to track user and agent turns, as well as STT/LLM/TTS metrics.

    Args:
        session: A LiveKit AgentSession instance.

    Returns:
        A LiveKitSessionWrapper that proxies to the original session
        while adding voiceobs instrumentation.

    Raises:
        ImportError: If livekit-agents is not installed.

    Example:
        from livekit.agents import AgentSession
        from voiceobs.integrations import instrument_livekit_session

        session = AgentSession(...)
        instrumented = instrument_livekit_session(session)

        # The session now creates voiceobs spans automatically
        await instrumented.start(room=ctx.room, agent=MyAgent())
    """
    if not HAS_LIVEKIT:
        raise ImportError(
            "livekit-agents is required for LiveKit integration. "
            "Install it with: pip install livekit-agents"
        )

    return LiveKitSessionWrapper(session)
