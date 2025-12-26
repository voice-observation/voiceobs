"""voiceobs - Open, vendor-neutral observability for voice AI conversations."""

from voiceobs._version import __version__
from voiceobs.context import (
    VOICE_SCHEMA_VERSION,
    ConversationContext,
    TurnContext,
    get_current_conversation,
    get_current_turn,
    mark_speech_end,
    mark_speech_start,
    voice_conversation,
    voice_turn,
)
from voiceobs.exporters import JSONLSpanExporter
from voiceobs.failures import (
    Failure,
    FailureThresholds,
    FailureType,
    Severity,
)
from voiceobs.stages import (
    StageContext,
    StageType,
    voice_stage,
)
from voiceobs.tracing import (
    ensure_tracing_initialized,
    get_tracer_provider_info,
)
from voiceobs.types import Actor

__all__ = [
    "__version__",
    "VOICE_SCHEMA_VERSION",
    "Actor",
    "ConversationContext",
    "Failure",
    "FailureThresholds",
    "FailureType",
    "JSONLSpanExporter",
    "Severity",
    "StageContext",
    "StageType",
    "TurnContext",
    "ensure_tracing_initialized",
    "get_current_conversation",
    "get_current_turn",
    "get_tracer_provider_info",
    "mark_speech_end",
    "mark_speech_start",
    "voice_conversation",
    "voice_stage",
    "voice_turn",
]
