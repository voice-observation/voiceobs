"""Tests for run comparison and regression detection."""


from voiceobs.analyzer import AnalysisResult
from voiceobs.compare import (
    ComparisonResult,
    MetricDelta,
    Regression,
    RegressionSeverity,
    RegressionThresholds,
    compare_runs,
)


class TestMetricDelta:
    """Tests for MetricDelta class."""

    def test_delta_calculation(self) -> None:
        """Should calculate delta correctly."""
        delta = MetricDelta(
            name="Test",
            baseline=100.0,
            current=120.0,
        )
        assert delta.delta == 20.0

    def test_delta_percent_calculation(self) -> None:
        """Should calculate percentage change correctly."""
        delta = MetricDelta(
            name="Test",
            baseline=100.0,
            current=120.0,
        )
        assert delta.delta_percent == 20.0

    def test_delta_with_none_baseline(self) -> None:
        """Should handle None baseline."""
        delta = MetricDelta(
            name="Test",
            baseline=None,
            current=100.0,
        )
        assert delta.delta is None
        assert delta.delta_percent is None

    def test_delta_with_none_current(self) -> None:
        """Should handle None current."""
        delta = MetricDelta(
            name="Test",
            baseline=100.0,
            current=None,
        )
        assert delta.delta is None
        assert delta.delta_percent is None

    def test_delta_with_zero_baseline(self) -> None:
        """Should handle zero baseline (avoid division by zero)."""
        delta = MetricDelta(
            name="Test",
            baseline=0.0,
            current=100.0,
        )
        assert delta.delta == 100.0
        assert delta.delta_percent is None

    def test_is_regression_higher_is_worse(self) -> None:
        """Should detect regression when higher is worse."""
        delta = MetricDelta(
            name="Test",
            baseline=100.0,
            current=120.0,
            higher_is_worse=True,
        )
        assert delta.is_regression is True

        delta_better = MetricDelta(
            name="Test",
            baseline=100.0,
            current=80.0,
            higher_is_worse=True,
        )
        assert delta_better.is_regression is False

    def test_is_regression_lower_is_worse(self) -> None:
        """Should detect regression when lower is worse."""
        delta = MetricDelta(
            name="Test",
            baseline=100.0,
            current=80.0,
            higher_is_worse=False,
        )
        assert delta.is_regression is True

        delta_better = MetricDelta(
            name="Test",
            baseline=100.0,
            current=120.0,
            higher_is_worse=False,
        )
        assert delta_better.is_regression is False

    def test_format_with_data(self) -> None:
        """Should format delta with data correctly."""
        delta = MetricDelta(
            name="ASR p95",
            baseline=100.0,
            current=120.0,
            unit="ms",
            higher_is_worse=True,
        )
        formatted = delta.format()
        assert "ASR p95" in formatted
        assert "100.00" in formatted
        assert "120.00" in formatted
        assert "+20.0%" in formatted
        assert "↑" in formatted

    def test_format_no_data(self) -> None:
        """Should format delta with no data correctly."""
        delta = MetricDelta(
            name="Test",
            baseline=None,
            current=None,
        )
        formatted = delta.format()
        assert "no data" in formatted

    def test_format_no_baseline(self) -> None:
        """Should format delta with no baseline correctly."""
        delta = MetricDelta(
            name="Test",
            baseline=None,
            current=100.0,
            unit="ms",
        )
        formatted = delta.format()
        assert "no baseline" in formatted

    def test_format_no_current(self) -> None:
        """Should format delta with no current correctly."""
        delta = MetricDelta(
            name="Test",
            baseline=100.0,
            current=None,
            unit="ms",
        )
        formatted = delta.format()
        assert "no data" in formatted
        assert "baseline" in formatted


class TestCompareRuns:
    """Tests for compare_runs function."""

    def _create_baseline_result(self) -> AnalysisResult:
        """Create a baseline analysis result for testing."""
        result = AnalysisResult()
        result.total_spans = 100
        result.total_conversations = 10
        result.total_turns = 50

        # Stage metrics
        result.asr_metrics.durations_ms = [100.0, 110.0, 120.0, 130.0, 140.0]
        result.llm_metrics.durations_ms = [200.0, 220.0, 240.0, 260.0, 280.0]
        result.tts_metrics.durations_ms = [50.0, 55.0, 60.0, 65.0, 70.0]

        # Turn metrics
        result.turn_metrics.silence_after_user_ms = [100.0, 150.0, 200.0, 250.0, 300.0]
        result.turn_metrics.total_agent_turns = 25
        result.turn_metrics.interruptions = 2

        # Eval metrics
        result.eval_metrics.total_evals = 20
        result.eval_metrics.intent_correct_count = 18
        result.eval_metrics.intent_incorrect_count = 2
        result.eval_metrics.relevance_scores = [0.8, 0.85, 0.9, 0.95]

        return result

    def test_compare_no_changes(self) -> None:
        """Should detect no regressions when runs are identical."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is False
        assert len(comparison.regressions) == 0

    def test_compare_latency_regression(self) -> None:
        """Should detect latency regressions."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Increase LLM latency by 30% (critical threshold is 25%)
        current.llm_metrics.durations_ms = [
            d * 1.30 for d in baseline.llm_metrics.durations_ms
        ]

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is True
        assert any("LLM" in r.description for r in comparison.regressions)

    def test_compare_latency_warning(self) -> None:
        """Should detect latency warnings."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Increase ASR latency by 15% (warning threshold is 10%)
        current.asr_metrics.durations_ms = [
            d * 1.15 for d in baseline.asr_metrics.durations_ms
        ]

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is True
        assert any(
            "ASR" in r.description and r.severity == RegressionSeverity.WARNING
            for r in comparison.regressions
        )

    def test_compare_silence_regression(self) -> None:
        """Should detect silence regressions."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Increase silence by 35% (critical threshold is 30%)
        current.turn_metrics.silence_after_user_ms = [
            s * 1.35 for s in baseline.turn_metrics.silence_after_user_ms
        ]

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is True
        assert any("Response latency" in r.description for r in comparison.regressions)

    def test_compare_interruption_regression(self) -> None:
        """Should detect interruption rate regressions."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Increase interruptions significantly (baseline: 2/25 = 8%, current: 10/25 = 40%)
        current.turn_metrics.interruptions = 10

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is True
        assert any("Interruption" in r.description for r in comparison.regressions)

    def test_compare_intent_regression(self) -> None:
        """Should detect intent correctness regressions."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Decrease intent correctness (baseline: 90%, current: 75%)
        current.eval_metrics.intent_correct_count = 15
        current.eval_metrics.intent_incorrect_count = 5

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is True
        assert any(
            "Intent correctness" in r.description for r in comparison.regressions
        )

    def test_compare_relevance_regression(self) -> None:
        """Should detect relevance score regressions."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Decrease relevance by ~25% (critical threshold is 20%)
        current.eval_metrics.relevance_scores = [0.6, 0.65, 0.68, 0.7]

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is True
        assert any("relevance" in r.description for r in comparison.regressions)

    def test_compare_with_custom_thresholds(self) -> None:
        """Should use custom thresholds when provided."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Increase latency by 15% (default warning is 10%, custom is 20%)
        current.llm_metrics.durations_ms = [
            d * 1.15 for d in baseline.llm_metrics.durations_ms
        ]

        # With custom thresholds, 15% shouldn't trigger regression
        lenient_thresholds = RegressionThresholds(
            latency_warning_pct=20.0,
            latency_critical_pct=40.0,
        )

        comparison = compare_runs(
            baseline, current, thresholds=lenient_thresholds
        )

        assert comparison.has_regressions is False

    def test_compare_improvement_not_regression(self) -> None:
        """Should not detect regression when metrics improve."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        # Improve latency (decrease)
        current.llm_metrics.durations_ms = [
            d * 0.8 for d in baseline.llm_metrics.durations_ms
        ]
        # Improve silence (decrease)
        current.turn_metrics.silence_after_user_ms = [
            s * 0.8 for s in baseline.turn_metrics.silence_after_user_ms
        ]
        # Improve interruptions (decrease)
        current.turn_metrics.interruptions = 1
        # Improve relevance (increase)
        current.eval_metrics.relevance_scores = [0.9, 0.92, 0.95, 0.98]

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is False

    def test_compare_empty_results(self) -> None:
        """Should handle empty analysis results."""
        baseline = AnalysisResult()
        current = AnalysisResult()

        comparison = compare_runs(baseline, current)

        assert comparison.has_regressions is False

    def test_compare_file_names_in_result(self) -> None:
        """Should include file names in comparison result."""
        baseline = self._create_baseline_result()
        current = self._create_baseline_result()

        comparison = compare_runs(
            baseline,
            current,
            baseline_file="baseline.jsonl",
            current_file="current.jsonl",
        )

        assert comparison.baseline_file == "baseline.jsonl"
        assert comparison.current_file == "current.jsonl"


class TestComparisonResult:
    """Tests for ComparisonResult class."""

    def test_has_critical_regressions(self) -> None:
        """Should detect critical regressions."""
        result = ComparisonResult(
            baseline_file="baseline",
            current_file="current",
        )
        result.regressions = [
            Regression(
                metric="test",
                baseline_value=100.0,
                current_value=130.0,
                delta=30.0,
                delta_percent=30.0,
                severity=RegressionSeverity.CRITICAL,
                description="Test critical regression",
            )
        ]

        assert result.has_critical_regressions is True

    def test_has_no_critical_regressions_with_warnings(self) -> None:
        """Should not report critical when only warnings exist."""
        result = ComparisonResult(
            baseline_file="baseline",
            current_file="current",
        )
        result.regressions = [
            Regression(
                metric="test",
                baseline_value=100.0,
                current_value=115.0,
                delta=15.0,
                delta_percent=15.0,
                severity=RegressionSeverity.WARNING,
                description="Test warning regression",
            )
        ]

        assert result.has_regressions is True
        assert result.has_critical_regressions is False

    def test_format_report(self) -> None:
        """Should format report correctly."""
        result = ComparisonResult(
            baseline_file="baseline.jsonl",
            current_file="current.jsonl",
        )
        result.asr_p95_delta = MetricDelta(
            name="ASR p95",
            baseline=100.0,
            current=120.0,
            unit="ms",
        )
        result.llm_p95_delta = MetricDelta(
            name="LLM p95",
            baseline=200.0,
            current=210.0,
            unit="ms",
        )
        result.tts_p95_delta = MetricDelta(
            name="TTS p95",
            baseline=50.0,
            current=55.0,
            unit="ms",
        )
        result.silence_mean_delta = MetricDelta(
            name="Silence mean",
            baseline=150.0,
            current=180.0,
            unit="ms",
        )
        result.silence_p95_delta = MetricDelta(
            name="Silence p95",
            baseline=300.0,
            current=350.0,
            unit="ms",
        )
        result.interruption_delta = MetricDelta(
            name="Interruptions",
            baseline=2.0,
            current=3.0,
            unit="",
        )
        result.interruption_rate_delta = MetricDelta(
            name="Interruption rate",
            baseline=8.0,
            current=12.0,
            unit="%",
        )
        result.intent_correct_rate_delta = MetricDelta(
            name="Intent correct",
            baseline=90.0,
            current=85.0,
            unit="%",
            higher_is_worse=False,
        )
        result.avg_relevance_delta = MetricDelta(
            name="Avg relevance",
            baseline=0.87,
            current=0.82,
            unit="",
            higher_is_worse=False,
        )

        report = result.format_report()

        assert "voiceobs Comparison Report" in report
        assert "baseline.jsonl" in report
        assert "current.jsonl" in report
        assert "ASR p95" in report
        assert "LLM p95" in report
        assert "TTS p95" in report
        assert "Silence mean" in report
        assert "Interruption" in report
        assert "Intent correct" in report
        assert "Avg relevance" in report

    def test_format_report_with_regressions(self) -> None:
        """Should show regressions in report."""
        result = ComparisonResult(
            baseline_file="baseline",
            current_file="current",
        )
        result.regressions = [
            Regression(
                metric="LLM p95",
                baseline_value=200.0,
                current_value=300.0,
                delta=100.0,
                delta_percent=50.0,
                severity=RegressionSeverity.CRITICAL,
                description="LLM latency increased by 50.0%",
            )
        ]

        report = result.format_report()

        assert "Regressions" in report
        assert "LLM latency increased by 50.0%" in report

    def test_format_report_no_regressions(self) -> None:
        """Should show success message when no regressions."""
        result = ComparisonResult(
            baseline_file="baseline",
            current_file="current",
        )

        report = result.format_report()

        assert "No regressions detected" in report


class TestRegressionThresholds:
    """Tests for RegressionThresholds defaults."""

    def test_default_thresholds(self) -> None:
        """Should have sensible default thresholds."""
        thresholds = RegressionThresholds()

        assert thresholds.latency_warning_pct == 10.0
        assert thresholds.latency_critical_pct == 25.0
        assert thresholds.silence_warning_pct == 15.0
        assert thresholds.silence_critical_pct == 30.0
        assert thresholds.interruption_rate_warning_pct == 5.0
        assert thresholds.interruption_rate_critical_pct == 15.0
        assert thresholds.intent_correct_warning_pct == 5.0
        assert thresholds.intent_correct_critical_pct == 15.0
        assert thresholds.relevance_warning_pct == 10.0
        assert thresholds.relevance_critical_pct == 20.0

    def test_custom_thresholds(self) -> None:
        """Should allow custom threshold values."""
        thresholds = RegressionThresholds(
            latency_warning_pct=5.0,
            latency_critical_pct=15.0,
        )

        assert thresholds.latency_warning_pct == 5.0
        assert thresholds.latency_critical_pct == 15.0
