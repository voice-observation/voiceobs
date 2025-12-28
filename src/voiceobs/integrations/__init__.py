"""Framework integrations for voiceobs.

This module provides auto-instrumentation for popular voice AI frameworks:
- LiveKit Agents SDK
- Vocode

Example usage with LiveKit:
    from livekit.agents import AgentSession
    from voiceobs.integrations import instrument_livekit_session

    session = AgentSession(...)
    instrumented = instrument_livekit_session(session)

    # Use the session normally - spans are created automatically
    await instrumented.start(room=ctx.room, agent=MyAgent())

Example usage with Vocode:
    from vocode.streaming.streaming_conversation import StreamingConversation
    from voiceobs.integrations import instrument_vocode_conversation

    conversation = StreamingConversation(...)
    instrumented = instrument_vocode_conversation(conversation)
"""

from voiceobs.integrations.base import BaseIntegration, InstrumentedConversation
from voiceobs.integrations.livekit import (
    LiveKitSessionWrapper,
    instrument_livekit_session,
)
from voiceobs.integrations.vocode import (
    VocodeConversationWrapper,
    instrument_vocode_conversation,
)

__all__ = [
    "BaseIntegration",
    "InstrumentedConversation",
    "LiveKitSessionWrapper",
    "VocodeConversationWrapper",
    "instrument_livekit_session",
    "instrument_vocode_conversation",
]
