"""Run comparison and regression detection for voiceobs.

.. warning::
    **EXPERIMENTAL**: This module is experimental and its API may change
    in future versions. Use with caution in production environments.

This module provides functions to compare two analysis results and detect
regressions in latency, silence, failure counts, and semantic scores.

See docs/ci-workflow.md for usage examples and best practices.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from voiceobs.analyzer import AnalysisResult


class RegressionSeverity(Enum):
    """Severity level for detected regressions."""

    NONE = "none"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricDelta:
    """A delta between two metric values."""

    name: str
    baseline: float | None
    current: float | None
    unit: str = "ms"
    higher_is_worse: bool = True

    @property
    def delta(self) -> float | None:
        """Calculate the delta (current - baseline)."""
        if self.baseline is None or self.current is None:
            return None
        return self.current - self.baseline

    @property
    def delta_percent(self) -> float | None:
        """Calculate the percentage change."""
        if self.baseline is None or self.current is None:
            return None
        if self.baseline == 0:
            return None
        return ((self.current - self.baseline) / self.baseline) * 100

    @property
    def is_regression(self) -> bool:
        """Check if this metric shows a regression."""
        delta = self.delta
        if delta is None:
            return False
        if self.higher_is_worse:
            return delta > 0
        return delta < 0

    def format(self) -> str:
        """Format the delta for display."""
        if self.baseline is None and self.current is None:
            return f"{self.name}: no data"
        if self.baseline is None:
            return f"{self.name}: {self.current:.2f}{self.unit} (no baseline)"
        if self.current is None:
            return f"{self.name}: no data (baseline: {self.baseline:.2f}{self.unit})"

        delta = self.delta
        delta_pct = self.delta_percent

        # Format direction indicator
        if delta > 0:
            direction = "↑" if self.higher_is_worse else "↓"
            sign = "+"
        elif delta < 0:
            direction = "↓" if self.higher_is_worse else "↑"
            sign = ""
        else:
            direction = "="
            sign = ""

        # Format the line
        pct_str = f" ({sign}{delta_pct:.1f}%)" if delta_pct is not None else ""
        return (
            f"{self.name}: {self.baseline:.2f} → {self.current:.2f}{self.unit} "
            f"({sign}{delta:.2f}{self.unit}{pct_str}) {direction}"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "baseline": self.baseline,
            "current": self.current,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "unit": self.unit,
            "is_regression": self.is_regression,
        }


@dataclass
class Regression:
    """A detected regression between runs."""

    metric: str
    baseline_value: float | None
    current_value: float | None
    delta: float
    delta_percent: float | None
    severity: RegressionSeverity
    description: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "metric": self.metric,
            "baseline_value": self.baseline_value,
            "current_value": self.current_value,
            "delta": self.delta,
            "delta_percent": self.delta_percent,
            "severity": self.severity.value,
            "description": self.description,
        }


@dataclass
class ComparisonResult:
    """Result of comparing two analysis runs."""

    baseline_file: str
    current_file: str

    # Latency deltas
    asr_p95_delta: MetricDelta | None = None
    llm_p95_delta: MetricDelta | None = None
    tts_p95_delta: MetricDelta | None = None

    # Silence deltas
    silence_mean_delta: MetricDelta | None = None
    silence_p95_delta: MetricDelta | None = None

    # Failure count deltas
    interruption_delta: MetricDelta | None = None
    interruption_rate_delta: MetricDelta | None = None

    # Semantic score deltas
    intent_correct_rate_delta: MetricDelta | None = None
    avg_relevance_delta: MetricDelta | None = None

    # Detected regressions
    regressions: list[Regression] = field(default_factory=list)

    @property
    def has_regressions(self) -> bool:
        """Check if any regressions were detected."""
        return len(self.regressions) > 0

    @property
    def has_critical_regressions(self) -> bool:
        """Check if any critical regressions were detected."""
        return any(r.severity == RegressionSeverity.CRITICAL for r in self.regressions)

    def format_report(self) -> str:
        """Format the comparison result as a plain text report."""
        lines = []
        lines.append("voiceobs Comparison Report")
        lines.append("=" * 50)
        lines.append("")

        # Files
        lines.append("Files")
        lines.append("-" * 30)
        lines.append(f"  Baseline: {self.baseline_file}")
        lines.append(f"  Current:  {self.current_file}")
        lines.append("")

        # Stage Latency Deltas
        lines.append("Stage Latency Deltas (p95)")
        lines.append("-" * 30)
        for delta in [self.asr_p95_delta, self.llm_p95_delta, self.tts_p95_delta]:
            if delta:
                lines.append(f"  {delta.format()}")
        lines.append("")

        # Response Latency Deltas
        lines.append("Response Latency Deltas")
        lines.append("-" * 30)
        for delta in [self.silence_mean_delta, self.silence_p95_delta]:
            if delta:
                lines.append(f"  {delta.format()}")
        lines.append("")

        # Interruption Deltas
        lines.append("Interruption Deltas")
        lines.append("-" * 30)
        for delta in [self.interruption_delta, self.interruption_rate_delta]:
            if delta:
                lines.append(f"  {delta.format()}")
        lines.append("")

        # Semantic Score Deltas
        lines.append("Semantic Score Deltas (probabilistic)")
        lines.append("-" * 30)
        lines.append("  Note: Semantic metrics may vary between runs")
        lines.append("")
        for delta in [self.intent_correct_rate_delta, self.avg_relevance_delta]:
            if delta:
                lines.append(f"  {delta.format()}")
        lines.append("")

        # Regressions Summary
        lines.append("Regressions")
        lines.append("-" * 30)
        if self.regressions:
            for reg in self.regressions:
                severity_marker = (
                    "⚠️ " if reg.severity == RegressionSeverity.WARNING else "🔴 "
                )
                lines.append(f"  {severity_marker}{reg.description}")
        else:
            lines.append("  ✅ No regressions detected")
        lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        deltas = {}

        # Stage latency deltas
        if self.asr_p95_delta:
            deltas["asr_p95"] = self.asr_p95_delta.to_dict()
        if self.llm_p95_delta:
            deltas["llm_p95"] = self.llm_p95_delta.to_dict()
        if self.tts_p95_delta:
            deltas["tts_p95"] = self.tts_p95_delta.to_dict()

        # Silence deltas
        if self.silence_mean_delta:
            deltas["silence_mean"] = self.silence_mean_delta.to_dict()
        if self.silence_p95_delta:
            deltas["silence_p95"] = self.silence_p95_delta.to_dict()

        # Interruption deltas
        if self.interruption_delta:
            deltas["interruptions"] = self.interruption_delta.to_dict()
        if self.interruption_rate_delta:
            deltas["interruption_rate"] = self.interruption_rate_delta.to_dict()

        # Semantic deltas
        if self.intent_correct_rate_delta:
            deltas["intent_correct_rate"] = self.intent_correct_rate_delta.to_dict()
        if self.avg_relevance_delta:
            deltas["avg_relevance"] = self.avg_relevance_delta.to_dict()

        return {
            "files": {
                "baseline": self.baseline_file,
                "current": self.current_file,
            },
            "deltas": deltas,
            "regressions": [r.to_dict() for r in self.regressions],
            "has_regressions": self.has_regressions,
            "has_critical_regressions": self.has_critical_regressions,
        }


@dataclass
class RegressionThresholds:
    """Thresholds for detecting regressions.

    Values represent the percentage increase (for latency/silence/interruptions)
    or decrease (for semantic scores) that triggers a regression.
    """

    # Latency thresholds (% increase)
    latency_warning_pct: float = 10.0
    latency_critical_pct: float = 25.0

    # Silence thresholds (% increase)
    silence_warning_pct: float = 15.0
    silence_critical_pct: float = 30.0

    # Interruption thresholds (absolute increase or % increase)
    interruption_rate_warning_pct: float = 5.0
    interruption_rate_critical_pct: float = 15.0

    # Semantic score thresholds (% decrease)
    intent_correct_warning_pct: float = 5.0
    intent_correct_critical_pct: float = 15.0

    relevance_warning_pct: float = 10.0
    relevance_critical_pct: float = 20.0


def compare_runs(
    baseline: AnalysisResult,
    current: AnalysisResult,
    baseline_file: str = "baseline",
    current_file: str = "current",
    thresholds: RegressionThresholds | None = None,
) -> ComparisonResult:
    """Compare two analysis results and detect regressions.

    Args:
        baseline: The baseline analysis result.
        current: The current analysis result to compare.
        baseline_file: Name/path of baseline file for display.
        current_file: Name/path of current file for display.
        thresholds: Optional custom regression thresholds.

    Returns:
        ComparisonResult with deltas and detected regressions.
    """
    if thresholds is None:
        thresholds = RegressionThresholds()

    result = ComparisonResult(
        baseline_file=baseline_file,
        current_file=current_file,
    )

    regressions = []

    # Stage latency deltas (p95)
    result.asr_p95_delta = MetricDelta(
        name="ASR p95",
        baseline=baseline.asr_metrics.p95_ms,
        current=current.asr_metrics.p95_ms,
        unit="ms",
        higher_is_worse=True,
    )
    _check_latency_regression(
        result.asr_p95_delta, "ASR", thresholds, regressions
    )

    result.llm_p95_delta = MetricDelta(
        name="LLM p95",
        baseline=baseline.llm_metrics.p95_ms,
        current=current.llm_metrics.p95_ms,
        unit="ms",
        higher_is_worse=True,
    )
    _check_latency_regression(
        result.llm_p95_delta, "LLM", thresholds, regressions
    )

    result.tts_p95_delta = MetricDelta(
        name="TTS p95",
        baseline=baseline.tts_metrics.p95_ms,
        current=current.tts_metrics.p95_ms,
        unit="ms",
        higher_is_worse=True,
    )
    _check_latency_regression(
        result.tts_p95_delta, "TTS", thresholds, regressions
    )

    # Silence deltas
    result.silence_mean_delta = MetricDelta(
        name="Silence mean",
        baseline=baseline.turn_metrics.silence_mean_ms,
        current=current.turn_metrics.silence_mean_ms,
        unit="ms",
        higher_is_worse=True,
    )
    _check_silence_regression(
        result.silence_mean_delta, "mean", thresholds, regressions
    )

    result.silence_p95_delta = MetricDelta(
        name="Silence p95",
        baseline=baseline.turn_metrics.silence_p95_ms,
        current=current.turn_metrics.silence_p95_ms,
        unit="ms",
        higher_is_worse=True,
    )
    _check_silence_regression(
        result.silence_p95_delta, "p95", thresholds, regressions
    )

    # Interruption deltas
    result.interruption_delta = MetricDelta(
        name="Interruptions",
        baseline=float(baseline.turn_metrics.interruptions),
        current=float(current.turn_metrics.interruptions),
        unit="",
        higher_is_worse=True,
    )

    result.interruption_rate_delta = MetricDelta(
        name="Interruption rate",
        baseline=baseline.turn_metrics.interruption_rate,
        current=current.turn_metrics.interruption_rate,
        unit="%",
        higher_is_worse=True,
    )
    _check_interruption_regression(
        result.interruption_rate_delta, thresholds, regressions
    )

    # Semantic score deltas
    result.intent_correct_rate_delta = MetricDelta(
        name="Intent correct",
        baseline=baseline.eval_metrics.intent_correct_rate,
        current=current.eval_metrics.intent_correct_rate,
        unit="%",
        higher_is_worse=False,  # Lower is worse for correctness
    )
    _check_intent_regression(
        result.intent_correct_rate_delta, thresholds, regressions
    )

    result.avg_relevance_delta = MetricDelta(
        name="Avg relevance",
        baseline=baseline.eval_metrics.avg_relevance_score,
        current=current.eval_metrics.avg_relevance_score,
        unit="",
        higher_is_worse=False,  # Lower is worse for relevance
    )
    _check_relevance_regression(
        result.avg_relevance_delta, thresholds, regressions
    )

    result.regressions = regressions

    return result


def _check_latency_regression(
    delta: MetricDelta,
    stage: str,
    thresholds: RegressionThresholds,
    regressions: list[Regression],
) -> None:
    """Check for latency regression and add to list if found."""
    pct = delta.delta_percent
    if pct is None:
        return

    if pct >= thresholds.latency_critical_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=delta.delta,
                delta_percent=pct,
                severity=RegressionSeverity.CRITICAL,
                description=f"{stage} latency increased by {pct:.1f}%",
            )
        )
    elif pct >= thresholds.latency_warning_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=delta.delta,
                delta_percent=pct,
                severity=RegressionSeverity.WARNING,
                description=f"{stage} latency increased by {pct:.1f}%",
            )
        )


def _check_silence_regression(
    delta: MetricDelta,
    stat_type: str,
    thresholds: RegressionThresholds,
    regressions: list[Regression],
) -> None:
    """Check for silence regression and add to list if found."""
    pct = delta.delta_percent
    if pct is None:
        return

    if pct >= thresholds.silence_critical_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=delta.delta,
                delta_percent=pct,
                severity=RegressionSeverity.CRITICAL,
                description=f"Response latency ({stat_type}) increased by {pct:.1f}%",
            )
        )
    elif pct >= thresholds.silence_warning_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=delta.delta,
                delta_percent=pct,
                severity=RegressionSeverity.WARNING,
                description=f"Response latency ({stat_type}) increased by {pct:.1f}%",
            )
        )


def _check_interruption_regression(
    delta: MetricDelta,
    thresholds: RegressionThresholds,
    regressions: list[Regression],
) -> None:
    """Check for interruption rate regression and add to list if found."""
    d = delta.delta
    if d is None:
        return

    # Use absolute delta for interruption rate (already a percentage)
    if d >= thresholds.interruption_rate_critical_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=d,
                delta_percent=delta.delta_percent,
                severity=RegressionSeverity.CRITICAL,
                description=f"Interruption rate increased by {d:.1f}pp",
            )
        )
    elif d >= thresholds.interruption_rate_warning_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=d,
                delta_percent=delta.delta_percent,
                severity=RegressionSeverity.WARNING,
                description=f"Interruption rate increased by {d:.1f}pp",
            )
        )


def _check_intent_regression(
    delta: MetricDelta,
    thresholds: RegressionThresholds,
    regressions: list[Regression],
) -> None:
    """Check for intent correctness regression and add to list if found."""
    d = delta.delta
    if d is None:
        return

    # Negative delta means decrease in correctness
    decrease = -d
    if decrease >= thresholds.intent_correct_critical_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=d,
                delta_percent=delta.delta_percent,
                severity=RegressionSeverity.CRITICAL,
                description=f"Intent correctness decreased by {decrease:.1f}pp",
            )
        )
    elif decrease >= thresholds.intent_correct_warning_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=d,
                delta_percent=delta.delta_percent,
                severity=RegressionSeverity.WARNING,
                description=f"Intent correctness decreased by {decrease:.1f}pp",
            )
        )


def _check_relevance_regression(
    delta: MetricDelta,
    thresholds: RegressionThresholds,
    regressions: list[Regression],
) -> None:
    """Check for relevance score regression and add to list if found."""
    pct = delta.delta_percent
    if pct is None:
        return

    # Negative percentage means decrease in relevance
    decrease_pct = -pct
    if decrease_pct >= thresholds.relevance_critical_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=delta.delta,
                delta_percent=pct,
                severity=RegressionSeverity.CRITICAL,
                description=f"Avg relevance decreased by {decrease_pct:.1f}%",
            )
        )
    elif decrease_pct >= thresholds.relevance_warning_pct:
        regressions.append(
            Regression(
                metric=delta.name,
                baseline_value=delta.baseline,
                current_value=delta.current,
                delta=delta.delta,
                delta_percent=pct,
                severity=RegressionSeverity.WARNING,
                description=f"Avg relevance decreased by {decrease_pct:.1f}%",
            )
        )
