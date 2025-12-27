"""voiceobs - Open, vendor-neutral observability for voice AI conversations."""

from voiceobs._version import __version__
from voiceobs.classifier import (
    ClassificationResult,
    FailureClassifier,
    classify_file,
    classify_spans,
)
from voiceobs.config import (
    ConfigValidationError,
    EvalCacheConfig,
    EvalConfig,
    ExporterConsoleConfig,
    ExporterJsonlConfig,
    ExportersConfig,
    FailuresConfig,
    FailureSeverityConfig,
    RegressionConfig,
    VoiceobsConfig,
    generate_default_config,
    get_config,
    load_config,
    reload_config,
    set_config,
)
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
    "ClassificationResult",
    "ConfigValidationError",
    "ConversationContext",
    "EvalCacheConfig",
    "EvalConfig",
    "ExporterConsoleConfig",
    "ExporterJsonlConfig",
    "ExportersConfig",
    "Failure",
    "FailureClassifier",
    "FailuresConfig",
    "FailureSeverityConfig",
    "FailureThresholds",
    "FailureType",
    "JSONLSpanExporter",
    "RegressionConfig",
    "Severity",
    "StageContext",
    "StageType",
    "TurnContext",
    "VoiceobsConfig",
    "classify_file",
    "classify_spans",
    "ensure_tracing_initialized",
    "generate_default_config",
    "get_config",
    "get_current_conversation",
    "get_current_turn",
    "get_tracer_provider_info",
    "load_config",
    "mark_speech_end",
    "mark_speech_start",
    "reload_config",
    "set_config",
    "voice_conversation",
    "voice_stage",
    "voice_turn",
]
