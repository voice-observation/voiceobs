"""Tests for the failure taxonomy module."""

from voiceobs.failures import (
    DEFAULT_THRESHOLDS,
    FAILURE_DEFINITIONS,
    Failure,
    FailureThresholds,
    FailureType,
    Severity,
    compute_interruption_severity,
    compute_silence_severity,
    compute_slow_response_severity,
    get_failure_definition,
)


class TestFailureType:
    """Tests for FailureType enum."""

    def test_all_failure_types_exist(self) -> None:
        """Verify all canonical failure types are defined."""
        expected = {
            "interruption",
            "excessive_silence",
            "slow_response",
            "asr_low_confidence",
            "llm_incorrect_intent",
            "unknown",
        }
        actual = {ft.value for ft in FailureType}
        assert actual == expected

    def test_failure_type_is_string_enum(self) -> None:
        """FailureType values should be usable as strings."""
        assert FailureType.INTERRUPTION == "interruption"
        assert FailureType.INTERRUPTION.value == "interruption"


class TestSeverity:
    """Tests for Severity enum."""

    def test_all_severity_levels_exist(self) -> None:
        """Verify all severity levels are defined."""
        expected = {"low", "medium", "high"}
        actual = {s.value for s in Severity}
        assert actual == expected

    def test_severity_is_string_enum(self) -> None:
        """Severity values should be usable as strings."""
        assert Severity.LOW == "low"
        assert Severity.HIGH == "high"


class TestFailureDefinitions:
    """Tests for FAILURE_DEFINITIONS."""

    def test_all_failure_types_have_definitions(self) -> None:
        """Every FailureType should have a definition."""
        for ft in FailureType:
            assert ft in FAILURE_DEFINITIONS

    def test_definition_has_description(self) -> None:
        """Each definition should have a non-empty description."""
        for ft, defn in FAILURE_DEFINITIONS.items():
            assert defn.description, f"{ft} missing description"
            assert len(defn.description) > 10

    def test_definition_has_type_matching_key(self) -> None:
        """Definition type should match the dictionary key."""
        for ft, defn in FAILURE_DEFINITIONS.items():
            assert defn.type == ft

    def test_interruption_has_triggering_signals(self) -> None:
        """Interruption should have overlap_ms as triggering signal."""
        defn = FAILURE_DEFINITIONS[FailureType.INTERRUPTION]
        assert "voice.turn.overlap_ms" in defn.triggering_signals

    def test_excessive_silence_threshold(self) -> None:
        """Excessive silence should have 3000ms default threshold."""
        defn = FAILURE_DEFINITIONS[FailureType.EXCESSIVE_SILENCE]
        assert defn.default_threshold == 3000.0
        assert defn.threshold_unit == "ms"

    def test_asr_confidence_threshold(self) -> None:
        """ASR confidence should have 0.7 default threshold."""
        defn = FAILURE_DEFINITIONS[FailureType.ASR_LOW_CONFIDENCE]
        assert defn.default_threshold == 0.7
        assert defn.threshold_unit == "ratio"


class TestFailureThresholds:
    """Tests for FailureThresholds dataclass."""

    def test_default_values(self) -> None:
        """Default thresholds should match documented defaults."""
        t = FailureThresholds()
        assert t.interruption_overlap_ms == 0.0
        assert t.excessive_silence_ms == 3000.0
        assert t.slow_asr_ms == 2000.0
        assert t.slow_llm_ms == 2000.0
        assert t.slow_tts_ms == 2000.0
        assert t.asr_min_confidence == 0.7
        assert t.llm_min_relevance == 0.5

    def test_severity_thresholds_defaults(self) -> None:
        """Severity thresholds should have correct defaults."""
        t = FailureThresholds()
        assert t.interruption_low_max_ms == 200.0
        assert t.interruption_medium_max_ms == 500.0
        assert t.silence_low_max_ms == 5000.0
        assert t.silence_medium_max_ms == 8000.0
        assert t.slow_low_max_ms == 3000.0
        assert t.slow_medium_max_ms == 5000.0

    def test_custom_thresholds(self) -> None:
        """Should be able to create custom thresholds."""
        t = FailureThresholds(
            excessive_silence_ms=5000.0,
            slow_llm_ms=4000.0,
            asr_min_confidence=0.5,
        )
        assert t.excessive_silence_ms == 5000.0
        assert t.slow_llm_ms == 4000.0
        assert t.asr_min_confidence == 0.5
        # Other values should remain default
        assert t.slow_asr_ms == 2000.0

    def test_default_thresholds_singleton(self) -> None:
        """DEFAULT_THRESHOLDS should be a usable singleton."""
        assert DEFAULT_THRESHOLDS.excessive_silence_ms == 3000.0


class TestFailure:
    """Tests for Failure dataclass."""

    def test_create_basic_failure(self) -> None:
        """Should be able to create a basic failure."""
        f = Failure(
            type=FailureType.INTERRUPTION,
            severity=Severity.MEDIUM,
            message="Agent interrupted user",
        )
        assert f.type == FailureType.INTERRUPTION
        assert f.severity == Severity.MEDIUM
        assert f.message == "Agent interrupted user"

    def test_create_failure_with_context(self) -> None:
        """Should be able to create a failure with full context."""
        f = Failure(
            type=FailureType.SLOW_RESPONSE,
            severity=Severity.HIGH,
            message="LLM took 6000ms",
            conversation_id="conv-123",
            turn_id="turn-456",
            turn_index=3,
            signal_name="voice.llm.duration_ms",
            signal_value=6000.0,
            threshold=2000.0,
        )
        assert f.conversation_id == "conv-123"
        assert f.turn_id == "turn-456"
        assert f.turn_index == 3
        assert f.signal_value == 6000.0
        assert f.threshold == 2000.0

    def test_to_dict(self) -> None:
        """to_dict should serialize failure correctly."""
        f = Failure(
            type=FailureType.EXCESSIVE_SILENCE,
            severity=Severity.LOW,
            message="4 second silence",
            conversation_id="conv-1",
            signal_value=4000.0,
        )
        d = f.to_dict()
        assert d["type"] == "excessive_silence"
        assert d["severity"] == "low"
        assert d["message"] == "4 second silence"
        assert d["conversation_id"] == "conv-1"
        assert d["signal_value"] == 4000.0


class TestGetFailureDefinition:
    """Tests for get_failure_definition function."""

    def test_get_known_type(self) -> None:
        """Should return correct definition for known types."""
        defn = get_failure_definition(FailureType.INTERRUPTION)
        assert defn.type == FailureType.INTERRUPTION

    def test_get_unknown_type(self) -> None:
        """Should return UNKNOWN definition for unknown type."""
        defn = get_failure_definition(FailureType.UNKNOWN)
        assert defn.type == FailureType.UNKNOWN


class TestComputeInterruptionSeverity:
    """Tests for compute_interruption_severity function."""

    def test_low_severity(self) -> None:
        """Overlap <= 200ms should be LOW severity."""
        assert compute_interruption_severity(0.0) == Severity.LOW
        assert compute_interruption_severity(100.0) == Severity.LOW
        assert compute_interruption_severity(200.0) == Severity.LOW

    def test_medium_severity(self) -> None:
        """Overlap > 200ms and <= 500ms should be MEDIUM severity."""
        assert compute_interruption_severity(201.0) == Severity.MEDIUM
        assert compute_interruption_severity(350.0) == Severity.MEDIUM
        assert compute_interruption_severity(500.0) == Severity.MEDIUM

    def test_high_severity(self) -> None:
        """Overlap > 500ms should be HIGH severity."""
        assert compute_interruption_severity(501.0) == Severity.HIGH
        assert compute_interruption_severity(1000.0) == Severity.HIGH

    def test_custom_thresholds(self) -> None:
        """Should respect custom thresholds."""
        strict = FailureThresholds(
            interruption_low_max_ms=100.0,
            interruption_medium_max_ms=250.0,
        )
        # 150ms is MEDIUM with strict thresholds, LOW with default
        assert compute_interruption_severity(150.0) == Severity.LOW
        assert compute_interruption_severity(150.0, strict) == Severity.MEDIUM


class TestComputeSilenceSeverity:
    """Tests for compute_silence_severity function."""

    def test_low_severity(self) -> None:
        """Silence <= 5000ms should be LOW severity."""
        assert compute_silence_severity(3000.0) == Severity.LOW
        assert compute_silence_severity(4000.0) == Severity.LOW
        assert compute_silence_severity(5000.0) == Severity.LOW

    def test_medium_severity(self) -> None:
        """Silence > 5000ms and <= 8000ms should be MEDIUM severity."""
        assert compute_silence_severity(5001.0) == Severity.MEDIUM
        assert compute_silence_severity(6500.0) == Severity.MEDIUM
        assert compute_silence_severity(8000.0) == Severity.MEDIUM

    def test_high_severity(self) -> None:
        """Silence > 8000ms should be HIGH severity."""
        assert compute_silence_severity(8001.0) == Severity.HIGH
        assert compute_silence_severity(12000.0) == Severity.HIGH

    def test_custom_thresholds(self) -> None:
        """Should respect custom thresholds."""
        lenient = FailureThresholds(
            silence_low_max_ms=7000.0,
            silence_medium_max_ms=12000.0,
        )
        # 6000ms is MEDIUM with default thresholds, LOW with lenient
        assert compute_silence_severity(6000.0) == Severity.MEDIUM
        assert compute_silence_severity(6000.0, lenient) == Severity.LOW


class TestComputeSlowResponseSeverity:
    """Tests for compute_slow_response_severity function."""

    def test_low_severity(self) -> None:
        """Duration <= 3000ms should be LOW severity."""
        assert compute_slow_response_severity(2000.0) == Severity.LOW
        assert compute_slow_response_severity(2500.0) == Severity.LOW
        assert compute_slow_response_severity(3000.0) == Severity.LOW

    def test_medium_severity(self) -> None:
        """Duration > 3000ms and <= 5000ms should be MEDIUM severity."""
        assert compute_slow_response_severity(3001.0) == Severity.MEDIUM
        assert compute_slow_response_severity(4200.0) == Severity.MEDIUM
        assert compute_slow_response_severity(5000.0) == Severity.MEDIUM

    def test_high_severity(self) -> None:
        """Duration > 5000ms should be HIGH severity."""
        assert compute_slow_response_severity(5001.0) == Severity.HIGH
        assert compute_slow_response_severity(10000.0) == Severity.HIGH

    def test_custom_thresholds(self) -> None:
        """Should respect custom thresholds."""
        strict = FailureThresholds(
            slow_low_max_ms=2000.0,
            slow_medium_max_ms=3500.0,
        )
        # 2500ms is LOW with default thresholds, MEDIUM with strict
        assert compute_slow_response_severity(2500.0) == Severity.LOW
        assert compute_slow_response_severity(2500.0, strict) == Severity.MEDIUM
