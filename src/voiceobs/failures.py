"""Failure taxonomy for voice conversations.

This module defines the canonical failure types that can occur in voice
conversations, along with their descriptions, triggering signals, and
default thresholds.

Failure Types:
- interruption: Agent started speaking before user finished
- excessive_silence: Too long pause between user and agent
- slow_response: Individual stage took too long
- asr_low_confidence: Speech recognition confidence below threshold
- llm_incorrect_intent: LLM misunderstood or gave wrong response
- unknown: Unclassified failure
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal


class FailureType(str, Enum):
    """Canonical failure types for voice conversations."""

    INTERRUPTION = "interruption"
    EXCESSIVE_SILENCE = "excessive_silence"
    SLOW_RESPONSE = "slow_response"
    ASR_LOW_CONFIDENCE = "asr_low_confidence"
    LLM_INCORRECT_INTENT = "llm_incorrect_intent"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Severity levels for failures."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class FailureDefinition:
    """Definition of a failure type with its attributes."""

    type: FailureType
    description: str
    triggering_signals: tuple[str, ...]
    default_threshold: float | None = None
    threshold_unit: str | None = None
    severity_rules: dict[str, Severity] = field(default_factory=dict)


# Canonical failure definitions
FAILURE_DEFINITIONS: dict[FailureType, FailureDefinition] = {
    FailureType.INTERRUPTION: FailureDefinition(
        type=FailureType.INTERRUPTION,
        description="Agent started speaking before the user finished speaking. "
        "This indicates the agent interrupted the user, which can be jarring "
        "and indicates a turn-taking issue.",
        triggering_signals=(
            "voice.turn.overlap_ms",
            "voice.interruption.detected",
        ),
        default_threshold=0.0,  # Any positive overlap is an interruption
        threshold_unit="ms",
        severity_rules={
            "low": Severity.LOW,  # overlap_ms > 0 and <= 200
            "medium": Severity.MEDIUM,  # overlap_ms > 200 and <= 500
            "high": Severity.HIGH,  # overlap_ms > 500
        },
    ),
    FailureType.EXCESSIVE_SILENCE: FailureDefinition(
        type=FailureType.EXCESSIVE_SILENCE,
        description="Too long of a pause between user finishing and agent responding. "
        "This makes the conversation feel slow and unresponsive.",
        triggering_signals=(
            "voice.silence.after_user_ms",
            "voice.silence.before_agent_ms",
        ),
        default_threshold=3000.0,  # 3 seconds is considered excessive
        threshold_unit="ms",
        severity_rules={
            "low": Severity.LOW,  # silence > 3000 and <= 5000
            "medium": Severity.MEDIUM,  # silence > 5000 and <= 8000
            "high": Severity.HIGH,  # silence > 8000
        },
    ),
    FailureType.SLOW_RESPONSE: FailureDefinition(
        type=FailureType.SLOW_RESPONSE,
        description="An individual stage (ASR, LLM, or TTS) took too long to complete. "
        "This indicates a performance bottleneck in the pipeline.",
        triggering_signals=(
            "voice.asr.duration_ms",
            "voice.llm.duration_ms",
            "voice.tts.duration_ms",
        ),
        default_threshold=2000.0,  # 2 seconds for any single stage
        threshold_unit="ms",
        severity_rules={
            "low": Severity.LOW,  # duration > 2000 and <= 3000
            "medium": Severity.MEDIUM,  # duration > 3000 and <= 5000
            "high": Severity.HIGH,  # duration > 5000
        },
    ),
    FailureType.ASR_LOW_CONFIDENCE: FailureDefinition(
        type=FailureType.ASR_LOW_CONFIDENCE,
        description="Speech recognition confidence is below the acceptable threshold. "
        "This may indicate poor audio quality, background noise, or unclear speech.",
        triggering_signals=("voice.asr.confidence",),
        default_threshold=0.7,  # 70% confidence threshold
        threshold_unit="ratio",
        severity_rules={
            "low": Severity.LOW,  # confidence < 0.7 and >= 0.5
            "medium": Severity.MEDIUM,  # confidence < 0.5 and >= 0.3
            "high": Severity.HIGH,  # confidence < 0.3
        },
    ),
    FailureType.LLM_INCORRECT_INTENT: FailureDefinition(
        type=FailureType.LLM_INCORRECT_INTENT,
        description="The LLM misunderstood the user's intent or provided an incorrect "
        "or irrelevant response. This is determined by semantic evaluation.",
        triggering_signals=(
            "eval.intent_correct",
            "eval.relevance_score",
        ),
        default_threshold=0.5,  # Relevance below 50% is incorrect
        threshold_unit="ratio",
        severity_rules={
            "low": Severity.LOW,  # relevance < 0.5 and >= 0.3
            "medium": Severity.MEDIUM,  # relevance < 0.3 and >= 0.1
            "high": Severity.HIGH,  # relevance < 0.1 or intent_correct=False
        },
    ),
    FailureType.UNKNOWN: FailureDefinition(
        type=FailureType.UNKNOWN,
        description="An unclassified failure that doesn't match known patterns. "
        "This may indicate a new type of issue that needs investigation.",
        triggering_signals=(),
        default_threshold=None,
        threshold_unit=None,
    ),
}


# Default thresholds that can be overridden
@dataclass
class FailureThresholds:
    """Configurable thresholds for failure detection."""

    # Interruption: overlap in ms that triggers failure (0 = any interruption)
    interruption_overlap_ms: float = 0.0

    # Excessive silence: silence after user in ms
    excessive_silence_ms: float = 3000.0

    # Slow response: max duration for any single stage
    slow_asr_ms: float = 2000.0
    slow_llm_ms: float = 2000.0
    slow_tts_ms: float = 2000.0

    # ASR confidence: minimum acceptable confidence
    asr_min_confidence: float = 0.7

    # LLM intent: minimum relevance score
    llm_min_relevance: float = 0.5

    # Severity thresholds for interruption
    interruption_low_max_ms: float = 200.0
    interruption_medium_max_ms: float = 500.0

    # Severity thresholds for excessive silence
    silence_low_max_ms: float = 5000.0
    silence_medium_max_ms: float = 8000.0

    # Severity thresholds for slow response
    slow_low_max_ms: float = 3000.0
    slow_medium_max_ms: float = 5000.0


# Singleton default thresholds
DEFAULT_THRESHOLDS = FailureThresholds()


@dataclass
class Failure:
    """A detected failure in a voice conversation."""

    type: FailureType
    severity: Severity
    message: str
    conversation_id: str | None = None
    turn_id: str | None = None
    turn_index: int | None = None
    signal_name: str | None = None
    signal_value: float | None = None
    threshold: float | None = None

    def to_dict(self) -> dict:
        """Convert failure to a dictionary."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "message": self.message,
            "conversation_id": self.conversation_id,
            "turn_id": self.turn_id,
            "turn_index": self.turn_index,
            "signal_name": self.signal_name,
            "signal_value": self.signal_value,
            "threshold": self.threshold,
        }


def get_failure_definition(failure_type: FailureType) -> FailureDefinition:
    """Get the definition for a failure type.

    Args:
        failure_type: The type of failure.

    Returns:
        The failure definition.
    """
    return FAILURE_DEFINITIONS.get(
        failure_type,
        FAILURE_DEFINITIONS[FailureType.UNKNOWN],
    )


def compute_interruption_severity(
    overlap_ms: float,
    thresholds: FailureThresholds = DEFAULT_THRESHOLDS,
) -> Severity:
    """Compute severity for an interruption failure.

    Args:
        overlap_ms: The overlap duration in milliseconds.
        thresholds: Threshold configuration.

    Returns:
        The severity level.
    """
    if overlap_ms <= thresholds.interruption_low_max_ms:
        return Severity.LOW
    elif overlap_ms <= thresholds.interruption_medium_max_ms:
        return Severity.MEDIUM
    else:
        return Severity.HIGH


def compute_silence_severity(
    silence_ms: float,
    thresholds: FailureThresholds = DEFAULT_THRESHOLDS,
) -> Severity:
    """Compute severity for an excessive silence failure.

    Args:
        silence_ms: The silence duration in milliseconds.
        thresholds: Threshold configuration.

    Returns:
        The severity level.
    """
    if silence_ms <= thresholds.silence_low_max_ms:
        return Severity.LOW
    elif silence_ms <= thresholds.silence_medium_max_ms:
        return Severity.MEDIUM
    else:
        return Severity.HIGH


def compute_slow_response_severity(
    duration_ms: float,
    thresholds: FailureThresholds = DEFAULT_THRESHOLDS,
) -> Severity:
    """Compute severity for a slow response failure.

    Args:
        duration_ms: The stage duration in milliseconds.
        thresholds: Threshold configuration.

    Returns:
        The severity level.
    """
    if duration_ms <= thresholds.slow_low_max_ms:
        return Severity.LOW
    elif duration_ms <= thresholds.slow_medium_max_ms:
        return Severity.MEDIUM
    else:
        return Severity.HIGH
