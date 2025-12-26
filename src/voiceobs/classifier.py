"""Deterministic failure classifier for voice conversations.

This module implements a rule-based classifier that analyzes parsed JSONL
spans and detects failures based on configurable thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from voiceobs.analyzer import parse_jsonl
from voiceobs.failures import (
    DEFAULT_THRESHOLDS,
    Failure,
    FailureThresholds,
    FailureType,
    Severity,
    compute_interruption_severity,
    compute_silence_severity,
    compute_slow_response_severity,
)


@dataclass
class ClassificationResult:
    """Result of classifying failures in a set of spans."""

    failures: list[Failure] = field(default_factory=list)
    total_spans: int = 0
    total_turns: int = 0
    total_agent_turns: int = 0

    @property
    def failure_count(self) -> int:
        """Total number of failures detected."""
        return len(self.failures)

    @property
    def failures_by_type(self) -> dict[FailureType, list[Failure]]:
        """Group failures by type."""
        result: dict[FailureType, list[Failure]] = {}
        for f in self.failures:
            if f.type not in result:
                result[f.type] = []
            result[f.type].append(f)
        return result

    @property
    def failures_by_severity(self) -> dict[Severity, list[Failure]]:
        """Group failures by severity."""
        result: dict[Severity, list[Failure]] = {}
        for f in self.failures:
            if f.severity not in result:
                result[f.severity] = []
            result[f.severity].append(f)
        return result

    def summary(self) -> dict[str, int]:
        """Return a summary of failure counts by type."""
        return {ft.value: len(failures) for ft, failures in self.failures_by_type.items()}


class FailureClassifier:
    """Rule-based failure classifier for voice conversation spans.

    The classifier analyzes spans from a JSONL trace file and detects
    failures based on configurable thresholds.

    Example:
        classifier = FailureClassifier()
        result = classifier.classify_file("traces.jsonl")

        for failure in result.failures:
            print(f"{failure.type}: {failure.message}")
    """

    def __init__(self, thresholds: FailureThresholds | None = None) -> None:
        """Initialize the classifier with thresholds.

        Args:
            thresholds: Custom thresholds for failure detection.
                       Uses DEFAULT_THRESHOLDS if not provided.
        """
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def classify(self, spans: list[dict]) -> ClassificationResult:
        """Classify failures in a list of span dictionaries.

        Args:
            spans: List of span dictionaries (from parse_jsonl).

        Returns:
            ClassificationResult with detected failures.
        """
        result = ClassificationResult(total_spans=len(spans))

        for span in spans:
            name = span.get("name", "")
            attrs = span.get("attributes", {})
            duration_ms = span.get("duration_ms")

            # Extract common context
            conv_id = attrs.get("voice.conversation.id")
            turn_id = attrs.get("voice.turn.id")
            turn_index = attrs.get("voice.turn.index")

            # Check stage spans for slow response
            if name in ("voice.asr", "voice.llm", "voice.tts"):
                stage_type = attrs.get("voice.stage.type", name.replace("voice.", ""))
                if duration_ms is not None:
                    failure = self._check_slow_response(
                        stage_type=stage_type,
                        duration_ms=duration_ms,
                        conv_id=conv_id,
                        turn_id=turn_id,
                        turn_index=turn_index,
                    )
                    if failure:
                        result.failures.append(failure)

                # Check ASR confidence
                if stage_type == "asr":
                    confidence = attrs.get("voice.asr.confidence")
                    if confidence is not None:
                        failure = self._check_asr_confidence(
                            confidence=confidence,
                            conv_id=conv_id,
                            turn_id=turn_id,
                            turn_index=turn_index,
                        )
                        if failure:
                            result.failures.append(failure)

            # Check turn spans
            elif name == "voice.turn":
                result.total_turns += 1
                actor = attrs.get("voice.actor")

                if actor == "agent":
                    result.total_agent_turns += 1

                    # Check for excessive silence
                    silence = attrs.get("voice.silence.after_user_ms")
                    if silence is not None:
                        failure = self._check_excessive_silence(
                            silence_ms=silence,
                            conv_id=conv_id,
                            turn_id=turn_id,
                            turn_index=turn_index,
                        )
                        if failure:
                            result.failures.append(failure)

                    # Check for interruption
                    overlap = attrs.get("voice.turn.overlap_ms")
                    interrupted = attrs.get("voice.interruption.detected", False)

                    if overlap is not None and overlap > self.thresholds.interruption_overlap_ms:
                        failure = self._check_interruption(
                            overlap_ms=overlap,
                            conv_id=conv_id,
                            turn_id=turn_id,
                            turn_index=turn_index,
                        )
                        if failure:
                            result.failures.append(failure)
                    elif interrupted:
                        # Boolean flag without overlap value
                        result.failures.append(
                            Failure(
                                type=FailureType.INTERRUPTION,
                                severity=Severity.LOW,
                                message="Agent interrupted user (detected via flag)",
                                conversation_id=conv_id,
                                turn_id=turn_id,
                                turn_index=turn_index,
                                signal_name="voice.interruption.detected",
                                signal_value=1.0,
                                threshold=0.0,
                            )
                        )

        return result

    def classify_file(self, file_path: str | Path) -> ClassificationResult:
        """Classify failures in a JSONL file.

        Args:
            file_path: Path to the JSONL file.

        Returns:
            ClassificationResult with detected failures.
        """
        spans = parse_jsonl(file_path)
        return self.classify(spans)

    def _check_slow_response(
        self,
        stage_type: str,
        duration_ms: float,
        conv_id: str | None,
        turn_id: str | None,
        turn_index: int | None,
    ) -> Failure | None:
        """Check if a stage duration exceeds the slow response threshold."""
        # Get threshold for this stage type
        if stage_type == "asr":
            threshold = self.thresholds.slow_asr_ms
        elif stage_type == "llm":
            threshold = self.thresholds.slow_llm_ms
        elif stage_type == "tts":
            threshold = self.thresholds.slow_tts_ms
        else:
            threshold = self.thresholds.slow_llm_ms  # Default to LLM threshold

        if duration_ms <= threshold:
            return None

        severity = compute_slow_response_severity(duration_ms, self.thresholds)

        return Failure(
            type=FailureType.SLOW_RESPONSE,
            severity=severity,
            message=f"{stage_type.upper()} took {duration_ms:.0f}ms (threshold: {threshold:.0f}ms)",
            conversation_id=conv_id,
            turn_id=turn_id,
            turn_index=turn_index,
            signal_name=f"voice.{stage_type}.duration_ms",
            signal_value=duration_ms,
            threshold=threshold,
        )

    def _check_excessive_silence(
        self,
        silence_ms: float,
        conv_id: str | None,
        turn_id: str | None,
        turn_index: int | None,
    ) -> Failure | None:
        """Check if silence duration exceeds the threshold."""
        if silence_ms <= self.thresholds.excessive_silence_ms:
            return None

        severity = compute_silence_severity(silence_ms, self.thresholds)

        return Failure(
            type=FailureType.EXCESSIVE_SILENCE,
            severity=severity,
            message=(
                f"Silence of {silence_ms:.0f}ms "
                f"(threshold: {self.thresholds.excessive_silence_ms:.0f}ms)"
            ),
            conversation_id=conv_id,
            turn_id=turn_id,
            turn_index=turn_index,
            signal_name="voice.silence.after_user_ms",
            signal_value=silence_ms,
            threshold=self.thresholds.excessive_silence_ms,
        )

    def _check_interruption(
        self,
        overlap_ms: float,
        conv_id: str | None,
        turn_id: str | None,
        turn_index: int | None,
    ) -> Failure | None:
        """Check if overlap indicates an interruption."""
        if overlap_ms <= self.thresholds.interruption_overlap_ms:
            return None

        severity = compute_interruption_severity(overlap_ms, self.thresholds)

        return Failure(
            type=FailureType.INTERRUPTION,
            severity=severity,
            message=f"Agent interrupted user by {overlap_ms:.0f}ms",
            conversation_id=conv_id,
            turn_id=turn_id,
            turn_index=turn_index,
            signal_name="voice.turn.overlap_ms",
            signal_value=overlap_ms,
            threshold=self.thresholds.interruption_overlap_ms,
        )

    def _check_asr_confidence(
        self,
        confidence: float,
        conv_id: str | None,
        turn_id: str | None,
        turn_index: int | None,
    ) -> Failure | None:
        """Check if ASR confidence is below threshold."""
        if confidence >= self.thresholds.asr_min_confidence:
            return None

        # Determine severity based on confidence level
        if confidence >= 0.5:
            severity = Severity.LOW
        elif confidence >= 0.3:
            severity = Severity.MEDIUM
        else:
            severity = Severity.HIGH

        return Failure(
            type=FailureType.ASR_LOW_CONFIDENCE,
            severity=severity,
            message=(
                f"ASR confidence {confidence:.0%} "
                f"below threshold {self.thresholds.asr_min_confidence:.0%}"
            ),
            conversation_id=conv_id,
            turn_id=turn_id,
            turn_index=turn_index,
            signal_name="voice.asr.confidence",
            signal_value=confidence,
            threshold=self.thresholds.asr_min_confidence,
        )


def classify_file(
    file_path: str | Path,
    thresholds: FailureThresholds | None = None,
) -> ClassificationResult:
    """Convenience function to classify failures in a JSONL file.

    Args:
        file_path: Path to the JSONL file.
        thresholds: Optional custom thresholds.

    Returns:
        ClassificationResult with detected failures.
    """
    classifier = FailureClassifier(thresholds)
    return classifier.classify_file(file_path)


def classify_spans(
    spans: list[dict],
    thresholds: FailureThresholds | None = None,
) -> ClassificationResult:
    """Convenience function to classify failures in a list of spans.

    Args:
        spans: List of span dictionaries.
        thresholds: Optional custom thresholds.

    Returns:
        ClassificationResult with detected failures.
    """
    classifier = FailureClassifier(thresholds)
    return classifier.classify(spans)
