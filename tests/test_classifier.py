"""Tests for the failure classifier module."""

from pathlib import Path

from voiceobs.classifier import (
    ClassificationResult,
    FailureClassifier,
    classify_file,
    classify_spans,
)
from voiceobs.failures import (
    FailureThresholds,
    FailureType,
    Severity,
)


def make_stage_span(
    stage_type: str,
    duration_ms: float,
    conv_id: str = "conv-1",
    confidence: float | None = None,
) -> dict:
    """Create a synthetic stage span."""
    attrs = {
        "voice.conversation.id": conv_id,
        "voice.stage.type": stage_type,
    }
    if confidence is not None:
        attrs["voice.asr.confidence"] = confidence

    return {
        "name": f"voice.{stage_type}",
        "duration_ms": duration_ms,
        "attributes": attrs,
    }


def make_turn_span(
    actor: str,
    conv_id: str = "conv-1",
    turn_id: str = "turn-1",
    turn_index: int = 0,
    silence_ms: float | None = None,
    overlap_ms: float | None = None,
    interrupted: bool = False,
) -> dict:
    """Create a synthetic turn span."""
    attrs = {
        "voice.conversation.id": conv_id,
        "voice.turn.id": turn_id,
        "voice.turn.index": turn_index,
        "voice.actor": actor,
    }
    if silence_ms is not None:
        attrs["voice.silence.after_user_ms"] = silence_ms
    if overlap_ms is not None:
        attrs["voice.turn.overlap_ms"] = overlap_ms
    if interrupted:
        attrs["voice.interruption.detected"] = True

    return {
        "name": "voice.turn",
        "duration_ms": 1000.0,
        "attributes": attrs,
    }


class TestClassificationResult:
    """Tests for ClassificationResult dataclass."""

    def test_empty_result(self) -> None:
        """Empty result should have zero failures."""
        result = ClassificationResult()
        assert result.failure_count == 0
        assert result.failures_by_type == {}
        assert result.failures_by_severity == {}
        assert result.summary() == {}

    def test_failure_count(self) -> None:
        """failure_count should return length of failures list."""
        from voiceobs.failures import Failure

        result = ClassificationResult()
        result.failures = [
            Failure(type=FailureType.INTERRUPTION, severity=Severity.LOW, message="test"),
            Failure(type=FailureType.SLOW_RESPONSE, severity=Severity.HIGH, message="test"),
        ]
        assert result.failure_count == 2

    def test_failures_by_type(self) -> None:
        """failures_by_type should group failures correctly."""
        from voiceobs.failures import Failure

        result = ClassificationResult()
        result.failures = [
            Failure(type=FailureType.INTERRUPTION, severity=Severity.LOW, message="int1"),
            Failure(type=FailureType.INTERRUPTION, severity=Severity.MEDIUM, message="int2"),
            Failure(type=FailureType.SLOW_RESPONSE, severity=Severity.HIGH, message="slow1"),
        ]

        by_type = result.failures_by_type
        assert len(by_type[FailureType.INTERRUPTION]) == 2
        assert len(by_type[FailureType.SLOW_RESPONSE]) == 1

    def test_summary(self) -> None:
        """summary should return counts by type."""
        from voiceobs.failures import Failure

        result = ClassificationResult()
        result.failures = [
            Failure(type=FailureType.INTERRUPTION, severity=Severity.LOW, message="int1"),
            Failure(type=FailureType.INTERRUPTION, severity=Severity.LOW, message="int2"),
            Failure(type=FailureType.EXCESSIVE_SILENCE, severity=Severity.MEDIUM, message="sil1"),
        ]

        summary = result.summary()
        assert summary == {"interruption": 2, "excessive_silence": 1}


class TestFailureClassifierSlowResponse:
    """Tests for slow response detection."""

    def test_no_failure_when_under_threshold(self) -> None:
        """No failure when stage duration is under threshold."""
        spans = [make_stage_span("llm", 1500.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)
        assert result.failure_count == 0

    def test_failure_when_over_threshold(self) -> None:
        """Failure detected when stage duration exceeds threshold."""
        spans = [make_stage_span("llm", 2500.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 1
        failure = result.failures[0]
        assert failure.type == FailureType.SLOW_RESPONSE
        assert failure.severity == Severity.LOW
        assert "LLM" in failure.message
        assert failure.signal_value == 2500.0
        assert failure.threshold == 2000.0

    def test_medium_severity_slow_response(self) -> None:
        """Medium severity when duration is between low and medium thresholds."""
        spans = [make_stage_span("llm", 4000.0)]  # > 3000ms, <= 5000ms
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.MEDIUM

    def test_high_severity_slow_response(self) -> None:
        """High severity when duration exceeds medium threshold."""
        spans = [make_stage_span("llm", 6000.0)]  # > 5000ms
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.HIGH

    def test_asr_threshold(self) -> None:
        """ASR stage uses slow_asr_ms threshold."""
        thresholds = FailureThresholds(slow_asr_ms=1000.0)
        spans = [make_stage_span("asr", 1500.0)]
        classifier = FailureClassifier(thresholds)
        result = classifier.classify(spans)

        assert result.failure_count == 1
        assert result.failures[0].threshold == 1000.0

    def test_tts_threshold(self) -> None:
        """TTS stage uses slow_tts_ms threshold."""
        thresholds = FailureThresholds(slow_tts_ms=1500.0)
        spans = [make_stage_span("tts", 2000.0)]
        classifier = FailureClassifier(thresholds)
        result = classifier.classify(spans)

        assert result.failure_count == 1
        assert result.failures[0].threshold == 1500.0


class TestFailureClassifierExcessiveSilence:
    """Tests for excessive silence detection."""

    def test_no_failure_when_under_threshold(self) -> None:
        """No failure when silence is under threshold."""
        spans = [make_turn_span("agent", silence_ms=2000.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)
        assert result.failure_count == 0

    def test_failure_when_over_threshold(self) -> None:
        """Failure detected when silence exceeds threshold."""
        spans = [make_turn_span("agent", silence_ms=4000.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 1
        failure = result.failures[0]
        assert failure.type == FailureType.EXCESSIVE_SILENCE
        assert failure.severity == Severity.LOW  # 4000ms <= 5000ms
        assert failure.signal_value == 4000.0
        assert failure.threshold == 3000.0

    def test_medium_severity_silence(self) -> None:
        """Medium severity when silence is between low and medium thresholds."""
        spans = [make_turn_span("agent", silence_ms=6000.0)]  # > 5000ms, <= 8000ms
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.MEDIUM

    def test_high_severity_silence(self) -> None:
        """High severity when silence exceeds medium threshold."""
        spans = [make_turn_span("agent", silence_ms=10000.0)]  # > 8000ms
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.HIGH

    def test_custom_threshold(self) -> None:
        """Custom silence threshold is respected."""
        thresholds = FailureThresholds(excessive_silence_ms=5000.0)
        spans = [make_turn_span("agent", silence_ms=4000.0)]
        classifier = FailureClassifier(thresholds)
        result = classifier.classify(spans)

        assert result.failure_count == 0

    def test_user_turn_ignored(self) -> None:
        """User turns should not trigger silence failures."""
        spans = [make_turn_span("user", silence_ms=10000.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)
        assert result.failure_count == 0


class TestFailureClassifierInterruption:
    """Tests for interruption detection."""

    def test_no_failure_when_no_overlap(self) -> None:
        """No failure when there's no overlap."""
        spans = [make_turn_span("agent", overlap_ms=0.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)
        assert result.failure_count == 0

    def test_failure_when_overlap_detected(self) -> None:
        """Failure detected when overlap is positive."""
        spans = [make_turn_span("agent", overlap_ms=150.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 1
        failure = result.failures[0]
        assert failure.type == FailureType.INTERRUPTION
        assert failure.severity == Severity.LOW  # 150ms <= 200ms
        assert failure.signal_value == 150.0

    def test_medium_severity_interruption(self) -> None:
        """Medium severity when overlap is between low and medium thresholds."""
        spans = [make_turn_span("agent", overlap_ms=350.0)]  # > 200ms, <= 500ms
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.MEDIUM

    def test_high_severity_interruption(self) -> None:
        """High severity when overlap exceeds medium threshold."""
        spans = [make_turn_span("agent", overlap_ms=600.0)]  # > 500ms
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.HIGH

    def test_interruption_flag_without_overlap(self) -> None:
        """Interruption flag alone triggers LOW severity failure."""
        spans = [make_turn_span("agent", interrupted=True)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 1
        failure = result.failures[0]
        assert failure.type == FailureType.INTERRUPTION
        assert failure.severity == Severity.LOW

    def test_custom_overlap_threshold(self) -> None:
        """Custom overlap threshold is respected."""
        thresholds = FailureThresholds(interruption_overlap_ms=100.0)
        spans = [make_turn_span("agent", overlap_ms=50.0)]
        classifier = FailureClassifier(thresholds)
        result = classifier.classify(spans)

        assert result.failure_count == 0


class TestFailureClassifierASRConfidence:
    """Tests for ASR confidence detection."""

    def test_no_failure_when_confidence_above_threshold(self) -> None:
        """No failure when confidence is above threshold."""
        spans = [make_stage_span("asr", 500.0, confidence=0.85)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)
        assert result.failure_count == 0

    def test_failure_when_confidence_below_threshold(self) -> None:
        """Failure detected when confidence is below threshold."""
        spans = [make_stage_span("asr", 500.0, confidence=0.55)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 1
        failure = result.failures[0]
        assert failure.type == FailureType.ASR_LOW_CONFIDENCE
        assert failure.severity == Severity.LOW  # >= 0.5
        assert failure.signal_value == 0.55
        assert failure.threshold == 0.7

    def test_medium_severity_confidence(self) -> None:
        """Medium severity when confidence is between 0.3 and 0.5."""
        spans = [make_stage_span("asr", 500.0, confidence=0.4)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.MEDIUM

    def test_high_severity_confidence(self) -> None:
        """High severity when confidence is below 0.3."""
        spans = [make_stage_span("asr", 500.0, confidence=0.2)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].severity == Severity.HIGH

    def test_custom_confidence_threshold(self) -> None:
        """Custom confidence threshold is respected."""
        thresholds = FailureThresholds(asr_min_confidence=0.5)
        spans = [make_stage_span("asr", 500.0, confidence=0.55)]
        classifier = FailureClassifier(thresholds)
        result = classifier.classify(spans)

        assert result.failure_count == 0


class TestFailureClassifierMultipleFailures:
    """Tests for multiple failures in a single run."""

    def test_multiple_failures_same_type(self) -> None:
        """Multiple failures of the same type are detected."""
        spans = [
            make_turn_span("agent", turn_id="t1", overlap_ms=100.0),
            make_turn_span("agent", turn_id="t2", overlap_ms=200.0),
            make_turn_span("agent", turn_id="t3", overlap_ms=300.0),
        ]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 3
        assert all(f.type == FailureType.INTERRUPTION for f in result.failures)

    def test_multiple_failures_different_types(self) -> None:
        """Multiple failures of different types are detected."""
        spans = [
            make_stage_span("llm", 3000.0),  # slow response
            make_turn_span("agent", silence_ms=5000.0),  # excessive silence
            make_turn_span("agent", turn_id="t2", overlap_ms=300.0),  # interruption
        ]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failure_count == 3
        types = {f.type for f in result.failures}
        assert types == {
            FailureType.SLOW_RESPONSE,
            FailureType.EXCESSIVE_SILENCE,
            FailureType.INTERRUPTION,
        }

    def test_failures_grouped_by_type(self) -> None:
        """failures_by_type correctly groups failures."""
        spans = [
            make_turn_span("agent", turn_id="t1", overlap_ms=100.0),
            make_turn_span("agent", turn_id="t2", overlap_ms=200.0),
            make_stage_span("llm", 3000.0),
        ]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        by_type = result.failures_by_type
        assert len(by_type[FailureType.INTERRUPTION]) == 2
        assert len(by_type[FailureType.SLOW_RESPONSE]) == 1


class TestFailureClassifierContext:
    """Tests for context tracking in failures."""

    def test_conversation_id_preserved(self) -> None:
        """Conversation ID is preserved in failure."""
        spans = [make_turn_span("agent", conv_id="my-conv-123", overlap_ms=100.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].conversation_id == "my-conv-123"

    def test_turn_id_preserved(self) -> None:
        """Turn ID is preserved in failure."""
        spans = [make_turn_span("agent", turn_id="my-turn-456", overlap_ms=100.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].turn_id == "my-turn-456"

    def test_turn_index_preserved(self) -> None:
        """Turn index is preserved in failure."""
        spans = [make_turn_span("agent", turn_index=5, overlap_ms=100.0)]
        classifier = FailureClassifier()
        result = classifier.classify(spans)

        assert result.failures[0].turn_index == 5


class TestClassifyFile:
    """Tests for file-based classification."""

    def test_classify_file(self, tmp_path: Path) -> None:
        """classify_file reads and classifies a JSONL file."""
        import json

        jsonl_path = tmp_path / "traces.jsonl"
        spans = [
            make_stage_span("llm", 3000.0),
            make_turn_span("agent", overlap_ms=100.0),
        ]
        with jsonl_path.open("w") as f:
            for span in spans:
                f.write(json.dumps(span) + "\n")

        result = classify_file(jsonl_path)

        assert result.failure_count == 2
        assert result.total_spans == 2

    def test_classify_file_with_custom_thresholds(self, tmp_path: Path) -> None:
        """classify_file accepts custom thresholds."""
        import json

        jsonl_path = tmp_path / "traces.jsonl"
        spans = [make_stage_span("llm", 3000.0)]
        with jsonl_path.open("w") as f:
            for span in spans:
                f.write(json.dumps(span) + "\n")

        # With default thresholds, 3000ms is a failure
        result_default = classify_file(jsonl_path)
        assert result_default.failure_count == 1

        # With custom threshold, 3000ms is not a failure
        thresholds = FailureThresholds(slow_llm_ms=4000.0)
        result_custom = classify_file(jsonl_path, thresholds)
        assert result_custom.failure_count == 0


class TestClassifySpans:
    """Tests for span-based classification."""

    def test_classify_spans_convenience(self) -> None:
        """classify_spans is a convenience function."""
        spans = [make_turn_span("agent", overlap_ms=100.0)]
        result = classify_spans(spans)

        assert result.failure_count == 1

    def test_classify_spans_with_thresholds(self) -> None:
        """classify_spans accepts custom thresholds."""
        spans = [make_turn_span("agent", overlap_ms=50.0)]

        # With default thresholds (0ms), 50ms is a failure
        result_default = classify_spans(spans)
        assert result_default.failure_count == 1

        # With custom threshold, 50ms is not a failure
        thresholds = FailureThresholds(interruption_overlap_ms=100.0)
        result_custom = classify_spans(spans, thresholds)
        assert result_custom.failure_count == 0


class TestSyntheticRuns:
    """Integration tests with synthetic conversation runs."""

    def test_good_conversation_no_failures(self) -> None:
        """A well-behaved conversation has no failures."""
        spans = [
            # User turn
            make_turn_span("user", turn_index=0),
            make_stage_span("asr", 150.0, confidence=0.95),
            # Agent turn - responds promptly, no interruption
            make_turn_span("agent", turn_index=1, silence_ms=500.0, overlap_ms=-500.0),
            make_stage_span("llm", 800.0),
            make_stage_span("tts", 200.0),
            # User turn
            make_turn_span("user", turn_index=2),
            make_stage_span("asr", 120.0, confidence=0.92),
            # Agent turn
            make_turn_span("agent", turn_index=3, silence_ms=400.0, overlap_ms=-400.0),
            make_stage_span("llm", 600.0),
            make_stage_span("tts", 180.0),
        ]

        result = classify_spans(spans)
        assert result.failure_count == 0
        assert result.total_turns == 4
        assert result.total_agent_turns == 2

    def test_problematic_conversation_multiple_failures(self) -> None:
        """A problematic conversation has multiple failures."""
        spans = [
            # User turn
            make_turn_span("user", turn_index=0),
            make_stage_span("asr", 150.0, confidence=0.45),  # Low confidence
            # Agent turn - interrupts user
            make_turn_span("agent", turn_index=1, silence_ms=500.0, overlap_ms=350.0),
            make_stage_span("llm", 4500.0),  # Slow LLM
            make_stage_span("tts", 200.0),
            # User turn
            make_turn_span("user", turn_index=2),
            make_stage_span("asr", 120.0, confidence=0.88),
            # Agent turn - excessive silence
            make_turn_span("agent", turn_index=3, silence_ms=6500.0, overlap_ms=-100.0),
            make_stage_span("llm", 600.0),
            make_stage_span("tts", 180.0),
        ]

        result = classify_spans(spans)

        assert result.failure_count == 4
        summary = result.summary()
        assert summary["asr_low_confidence"] == 1
        assert summary["interruption"] == 1
        assert summary["slow_response"] == 1
        assert summary["excessive_silence"] == 1

    def test_strict_thresholds_more_failures(self) -> None:
        """Strict thresholds catch more failures."""
        spans = [
            make_turn_span("user", turn_index=0),
            make_stage_span("asr", 150.0, confidence=0.75),
            make_turn_span("agent", turn_index=1, silence_ms=2000.0, overlap_ms=0.0),
            make_stage_span("llm", 1800.0),
            make_stage_span("tts", 200.0),
        ]

        # Default thresholds - no failures
        result_default = classify_spans(spans)
        assert result_default.failure_count == 0

        # Strict thresholds - multiple failures
        strict = FailureThresholds(
            excessive_silence_ms=1500.0,
            slow_llm_ms=1500.0,
            asr_min_confidence=0.8,
        )
        result_strict = classify_spans(spans, strict)

        assert result_strict.failure_count == 3
        types = {f.type for f in result_strict.failures}
        assert types == {
            FailureType.EXCESSIVE_SILENCE,
            FailureType.SLOW_RESPONSE,
            FailureType.ASR_LOW_CONFIDENCE,
        }
