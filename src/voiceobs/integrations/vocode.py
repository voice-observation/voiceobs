"""Vocode integration for voiceobs.

This module provides auto-instrumentation for Vocode's StreamingConversation.

Example:
    from vocode.streaming.streaming_conversation import StreamingConversation
    from voiceobs.integrations import instrument_vocode_conversation

    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=DeepgramTranscriber(...),
        agent=ChatGPTAgent(...),
        synthesizer=ElevenLabsSynthesizer(...),
    )

    # Instrument the conversation
    instrumented = instrument_vocode_conversation(conversation)

    # Use the conversation normally - spans are created automatically
    await instrumented.start()
"""

from __future__ import annotations

from typing import Any

from voiceobs.integrations.base import InstrumentedConversation

# Check if vocode is installed
try:
    import vocode  # noqa: F401

    HAS_VOCODE = True
except ImportError:
    HAS_VOCODE = False


class VocodeConversationWrapper:
    """Wrapper that adds voiceobs instrumentation to a Vocode StreamingConversation.

    This wrapper intercepts Vocode conversation lifecycle methods to
    automatically create voiceobs spans.
    """

    def __init__(self, conversation: Any) -> None:
        """Initialize the wrapper.

        Args:
            conversation: The Vocode StreamingConversation to instrument.
        """
        self._conversation = conversation
        self._instrumented = InstrumentedConversation()
        self._wrap_methods()

    @property
    def conversation(self) -> Any:
        """Get the wrapped conversation."""
        return self._conversation

    @property
    def instrumented(self) -> InstrumentedConversation:
        """Get the instrumented conversation tracker."""
        return self._instrumented

    def _wrap_methods(self) -> None:
        """Wrap conversation methods to add instrumentation."""
        original_start = getattr(self._conversation, "start", None)
        original_terminate = getattr(self._conversation, "terminate", None)

        if original_start is not None:

            async def instrumented_start(*args: Any, **kwargs: Any) -> Any:
                self._instrumented.start()
                return await original_start(*args, **kwargs)

            self._conversation.start = instrumented_start

        if original_terminate is not None:

            async def instrumented_terminate(*args: Any, **kwargs: Any) -> Any:
                result = await original_terminate(*args, **kwargs)
                self._instrumented.stop()
                return result

            self._conversation.terminate = instrumented_terminate

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the wrapped conversation."""
        return getattr(self._conversation, name)


def instrument_vocode_conversation(conversation: Any) -> VocodeConversationWrapper:
    """Instrument a Vocode StreamingConversation with voiceobs tracing.

    This function wraps a Vocode conversation to automatically create
    voiceobs spans for voice conversations. It intercepts the start()
    and terminate() methods to track conversation lifecycle.

    Args:
        conversation: A Vocode StreamingConversation instance.

    Returns:
        A VocodeConversationWrapper that proxies to the original conversation
        while adding voiceobs instrumentation.

    Raises:
        ImportError: If vocode is not installed.

    Example:
        from vocode.streaming.streaming_conversation import StreamingConversation
        from voiceobs.integrations import instrument_vocode_conversation

        conversation = StreamingConversation(...)
        instrumented = instrument_vocode_conversation(conversation)

        # The conversation now creates voiceobs spans automatically
        await instrumented.start()
        # ... conversation runs ...
        await instrumented.terminate()
    """
    if not HAS_VOCODE:
        raise ImportError(
            "vocode is required for Vocode integration. Install it with: pip install vocode"
        )

    return VocodeConversationWrapper(conversation)
