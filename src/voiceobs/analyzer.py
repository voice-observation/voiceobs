"""Analyzer for voiceobs JSONL trace files.

This module provides functions to parse JSONL span data and compute
observability metrics like latency percentiles, silence duration, and
interruption rates.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO


@dataclass
class StageMetrics:
    """Metrics for a stage type (ASR, LLM, TTS)."""

    stage_type: str
    durations_ms: list[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        """Number of spans for this stage."""
        return len(self.durations_ms)

    @property
    def mean_ms(self) -> float | None:
        """Mean duration in milliseconds."""
        if not self.durations_ms:
            return None
        return statistics.mean(self.durations_ms)

    @property
    def p50_ms(self) -> float | None:
        """Median (p50) duration in milliseconds."""
        if not self.durations_ms:
            return None
        return statistics.median(self.durations_ms)

    @property
    def p95_ms(self) -> float | None:
        """95th percentile duration in milliseconds."""
        if len(self.durations_ms) < 2:
            return self.mean_ms
        sorted_durations = sorted(self.durations_ms)
        index = int(len(sorted_durations) * 0.95)
        return sorted_durations[min(index, len(sorted_durations) - 1)]

    @property
    def p99_ms(self) -> float | None:
        """99th percentile duration in milliseconds."""
        if len(self.durations_ms) < 2:
            return self.mean_ms
        sorted_durations = sorted(self.durations_ms)
        index = int(len(sorted_durations) * 0.99)
        return sorted_durations[min(index, len(sorted_durations) - 1)]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "stage_type": self.stage_type,
            "count": self.count,
            "mean_ms": self.mean_ms,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
        }


@dataclass
class TurnMetrics:
    """Metrics for turn-level timing."""

    silence_after_user_ms: list[float] = field(default_factory=list)
    overlap_ms: list[float] = field(default_factory=list)
    interruptions: int = 0
    total_agent_turns: int = 0

    @property
    def silence_mean_ms(self) -> float | None:
        """Mean silence after user in milliseconds."""
        if not self.silence_after_user_ms:
            return None
        return statistics.mean(self.silence_after_user_ms)

    @property
    def silence_p95_ms(self) -> float | None:
        """95th percentile silence after user in milliseconds."""
        if len(self.silence_after_user_ms) < 2:
            return self.silence_mean_ms
        sorted_silence = sorted(self.silence_after_user_ms)
        index = int(len(sorted_silence) * 0.95)
        return sorted_silence[min(index, len(sorted_silence) - 1)]

    @property
    def interruption_rate(self) -> float | None:
        """Percentage of agent turns that were interruptions."""
        if self.total_agent_turns == 0:
            return None
        return (self.interruptions / self.total_agent_turns) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "silence_samples": len(self.silence_after_user_ms),
            "silence_mean_ms": self.silence_mean_ms,
            "silence_p95_ms": self.silence_p95_ms,
            "total_agent_turns": self.total_agent_turns,
            "interruptions": self.interruptions,
            "interruption_rate": self.interruption_rate,
        }


@dataclass
class EvalMetrics:
    """Metrics from semantic evaluation results.

    Note: These metrics are probabilistic since they come from LLM-as-judge
    evaluation. Results may vary slightly between runs.
    """

    total_evals: int = 0
    intent_correct_count: int = 0
    intent_incorrect_count: int = 0
    relevance_scores: list[float] = field(default_factory=list)

    @property
    def intent_correct_rate(self) -> float | None:
        """Percentage of turns with correct intent."""
        if self.total_evals == 0:
            return None
        return (self.intent_correct_count / self.total_evals) * 100

    @property
    def intent_failure_rate(self) -> float | None:
        """Percentage of turns with incorrect intent."""
        if self.total_evals == 0:
            return None
        return (self.intent_incorrect_count / self.total_evals) * 100

    @property
    def avg_relevance_score(self) -> float | None:
        """Average relevance score (0.0 to 1.0)."""
        if not self.relevance_scores:
            return None
        return statistics.mean(self.relevance_scores)

    @property
    def min_relevance_score(self) -> float | None:
        """Minimum relevance score."""
        if not self.relevance_scores:
            return None
        return min(self.relevance_scores)

    @property
    def max_relevance_score(self) -> float | None:
        """Maximum relevance score."""
        if not self.relevance_scores:
            return None
        return max(self.relevance_scores)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_evals": self.total_evals,
            "intent_correct_count": self.intent_correct_count,
            "intent_incorrect_count": self.intent_incorrect_count,
            "intent_correct_rate": self.intent_correct_rate,
            "intent_failure_rate": self.intent_failure_rate,
            "avg_relevance_score": self.avg_relevance_score,
            "min_relevance_score": self.min_relevance_score,
            "max_relevance_score": self.max_relevance_score,
        }


@dataclass
class AnalysisResult:
    """Complete analysis result from a JSONL file."""

    total_spans: int = 0
    total_conversations: int = 0
    total_turns: int = 0

    asr_metrics: StageMetrics = field(default_factory=lambda: StageMetrics("asr"))
    llm_metrics: StageMetrics = field(default_factory=lambda: StageMetrics("llm"))
    tts_metrics: StageMetrics = field(default_factory=lambda: StageMetrics("tts"))

    turn_metrics: TurnMetrics = field(default_factory=TurnMetrics)
    eval_metrics: EvalMetrics = field(default_factory=EvalMetrics)

    def format_report(self) -> str:
        """Format the analysis result as a plain text report."""
        lines = []
        lines.append("voiceobs Analysis Report")
        lines.append("=" * 50)
        lines.append("")

        # Summary
        lines.append("Summary")
        lines.append("-" * 30)
        lines.append(f"  Total spans: {self.total_spans}")
        lines.append(f"  Conversations: {self.total_conversations}")
        lines.append(f"  Turns: {self.total_turns}")
        lines.append("")

        # Stage Latencies
        lines.append("Stage Latencies (ms)")
        lines.append("-" * 30)

        for metrics in [self.asr_metrics, self.llm_metrics, self.tts_metrics]:
            if metrics.count > 0:
                lines.append(f"  {metrics.stage_type.upper()} (n={metrics.count}):")
                lines.append(f"    mean: {metrics.mean_ms:.3f}")
                lines.append(f"    p50:  {metrics.p50_ms:.3f}")
                lines.append(f"    p95:  {metrics.p95_ms:.3f}")
                lines.append(f"    p99:  {metrics.p99_ms:.3f}")
            else:
                lines.append(f"  {metrics.stage_type.upper()}: no data")

        lines.append("")

        # Response Latency (Silence after user)
        lines.append("Response Latency (silence after user)")
        lines.append("-" * 30)

        if self.turn_metrics.silence_after_user_ms:
            n = len(self.turn_metrics.silence_after_user_ms)
            lines.append(f"  Samples: {n}")
            lines.append(f"  mean: {self.turn_metrics.silence_mean_ms:.1f}ms")
            lines.append(f"  p95:  {self.turn_metrics.silence_p95_ms:.1f}ms")
        else:
            lines.append("  No silence data available")
            lines.append("  (Use mark_speech_end/mark_speech_start for accurate timing)")

        lines.append("")

        # Interruption Rate
        lines.append("Interruptions")
        lines.append("-" * 30)

        if self.turn_metrics.total_agent_turns > 0:
            lines.append(f"  Agent turns: {self.turn_metrics.total_agent_turns}")
            lines.append(f"  Interruptions: {self.turn_metrics.interruptions}")
            rate = self.turn_metrics.interruption_rate
            if rate is not None:
                lines.append(f"  Rate: {rate:.1f}%")
        else:
            lines.append("  No agent turn data available")

        lines.append("")

        # Semantic Evaluation (probabilistic)
        lines.append("Semantic Evaluation (probabilistic)")
        lines.append("-" * 30)
        lines.append("  Note: These metrics come from LLM-as-judge evaluation")
        lines.append("  and may vary slightly between runs.")
        lines.append("")

        if self.eval_metrics.total_evals > 0:
            lines.append(f"  Evaluated turns: {self.eval_metrics.total_evals}")

            if self.eval_metrics.intent_correct_rate is not None:
                lines.append(f"  Intent correct: {self.eval_metrics.intent_correct_rate:.1f}%")

            if self.eval_metrics.intent_failure_rate is not None:
                lines.append(f"  Intent failures: {self.eval_metrics.intent_failure_rate:.1f}%")

            if self.eval_metrics.avg_relevance_score is not None:
                lines.append(f"  Avg relevance: {self.eval_metrics.avg_relevance_score:.2f}")

            if self.eval_metrics.min_relevance_score is not None:
                lines.append(
                    f"  Relevance range: {self.eval_metrics.min_relevance_score:.2f} - "
                    f"{self.eval_metrics.max_relevance_score:.2f}"
                )
        else:
            lines.append("  No evaluation data available")
            lines.append("  (Run semantic evaluation to generate eval records)")

        lines.append("")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "summary": {
                "total_spans": self.total_spans,
                "total_conversations": self.total_conversations,
                "total_turns": self.total_turns,
            },
            "stages": {
                "asr": self.asr_metrics.to_dict(),
                "llm": self.llm_metrics.to_dict(),
                "tts": self.tts_metrics.to_dict(),
            },
            "turns": self.turn_metrics.to_dict(),
            "eval": self.eval_metrics.to_dict(),
        }


def parse_jsonl(file_path: str | Path) -> list[dict]:
    """Parse a JSONL file into a list of span dictionaries.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of span dictionaries.
    """
    spans = []
    path = Path(file_path)

    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                spans.append(json.loads(line))

    return spans


def parse_jsonl_stream(stream: TextIO) -> list[dict]:
    """Parse JSONL from a stream into a list of span dictionaries.

    Args:
        stream: Text stream to read from.

    Returns:
        List of span dictionaries.
    """
    spans = []
    for line in stream:
        line = line.strip()
        if line:
            spans.append(json.loads(line))
    return spans


def analyze_spans(spans: list[dict]) -> AnalysisResult:
    """Analyze a list of span dictionaries and compute metrics.

    Args:
        spans: List of span dictionaries (from parse_jsonl).

    Returns:
        AnalysisResult with computed metrics.
    """
    result = AnalysisResult()
    result.total_spans = len(spans)

    conversation_ids: set[str] = set()

    for span in spans:
        name = span.get("name", "")
        attrs = span.get("attributes", {})
        duration_ms = span.get("duration_ms")

        # Track conversations
        conv_id = attrs.get("voice.conversation.id")
        if conv_id:
            conversation_ids.add(conv_id)

        # Stage spans - support both voice.asr and voice.stage.asr naming
        stage_names = (
            "voice.asr",
            "voice.llm",
            "voice.tts",
            "voice.stage.asr",
            "voice.stage.llm",
            "voice.stage.tts",
        )
        if name in stage_names:
            stage_type = attrs.get(
                "voice.stage.type",
                name.replace("voice.stage.", "").replace("voice.", ""),
            )
            # Prefer voice.stage.duration_ms attribute (from metrics events)
            # Fall back to span duration (from context manager timing)
            stage_duration = attrs.get("voice.stage.duration_ms", duration_ms)
            if stage_duration is not None:
                if stage_type == "asr":
                    result.asr_metrics.durations_ms.append(stage_duration)
                elif stage_type == "llm":
                    result.llm_metrics.durations_ms.append(stage_duration)
                elif stage_type == "tts":
                    result.tts_metrics.durations_ms.append(stage_duration)

        # Turn spans
        elif name == "voice.turn":
            result.total_turns += 1
            actor = attrs.get("voice.actor")

            if actor == "agent":
                result.turn_metrics.total_agent_turns += 1

                # Silence after user
                silence = attrs.get("voice.silence.after_user_ms")
                if silence is not None:
                    result.turn_metrics.silence_after_user_ms.append(silence)

                # Overlap
                overlap = attrs.get("voice.turn.overlap_ms")
                if overlap is not None:
                    result.turn_metrics.overlap_ms.append(overlap)

                # Interruption
                interrupted = attrs.get("voice.interruption.detected")
                if interrupted:
                    result.turn_metrics.interruptions += 1

        # Evaluation records
        elif name == "voiceobs.eval":
            result.eval_metrics.total_evals += 1

            intent_correct = attrs.get("eval.intent_correct")
            if intent_correct is True:
                result.eval_metrics.intent_correct_count += 1
            elif intent_correct is False:
                result.eval_metrics.intent_incorrect_count += 1

            relevance_score = attrs.get("eval.relevance_score")
            if relevance_score is not None:
                result.eval_metrics.relevance_scores.append(relevance_score)

    result.total_conversations = len(conversation_ids)

    return result


def analyze_file(file_path: str | Path) -> AnalysisResult:
    """Analyze a JSONL file and return metrics.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        AnalysisResult with computed metrics.
    """
    spans = parse_jsonl(file_path)
    return analyze_spans(spans)
