"""Tests for voiceobs analyzer."""

import io
import json
import textwrap

import pytest

from voiceobs.analyzer import (
    AnalysisResult,
    EvalMetrics,
    StageMetrics,
    TurnMetrics,
    analyze_file,
    analyze_spans,
    parse_jsonl,
    parse_jsonl_stream,
)


class TestStageMetrics:
    """Tests for StageMetrics class."""

    def test_empty_metrics(self):
        """Test metrics with no data."""
        metrics = StageMetrics("asr")
        assert metrics.count == 0
        assert metrics.mean_ms is None
        assert metrics.p50_ms is None
        assert metrics.p95_ms is None
        assert metrics.p99_ms is None

    def test_single_value(self):
        """Test metrics with a single value."""
        metrics = StageMetrics("asr", durations_ms=[100.0])
        assert metrics.count == 1
        assert metrics.mean_ms == 100.0
        assert metrics.p50_ms == 100.0
        assert metrics.p95_ms == 100.0  # Falls back to mean
        assert metrics.p99_ms == 100.0

    def test_multiple_values(self):
        """Test metrics with multiple values."""
        # 10 values from 100 to 1000
        durations = [100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0, 900.0, 1000.0]
        metrics = StageMetrics("llm", durations_ms=durations)

        assert metrics.count == 10
        assert metrics.mean_ms == 550.0
        assert metrics.p50_ms == 550.0  # median
        assert metrics.p95_ms == 1000.0  # 95th percentile
        assert metrics.p99_ms == 1000.0  # 99th percentile

    def test_percentiles_with_20_values(self):
        """Test percentile calculations with 20 values."""
        durations = list(range(100, 2100, 100))  # 100, 200, ..., 2000
        metrics = StageMetrics("tts", durations_ms=durations)

        assert metrics.count == 20
        assert metrics.p95_ms == 2000.0  # index 19


class TestTurnMetrics:
    """Tests for TurnMetrics class."""

    def test_empty_metrics(self):
        """Test metrics with no data."""
        metrics = TurnMetrics()
        assert metrics.silence_mean_ms is None
        assert metrics.silence_p95_ms is None
        assert metrics.interruption_rate is None

    def test_silence_metrics(self):
        """Test silence duration metrics."""
        metrics = TurnMetrics(
            silence_after_user_ms=[100.0, 200.0, 300.0, 400.0, 500.0],
        )
        assert metrics.silence_mean_ms == 300.0
        assert metrics.silence_p95_ms == 500.0

    def test_interruption_rate(self):
        """Test interruption rate calculation."""
        metrics = TurnMetrics(
            total_agent_turns=10,
            interruptions=2,
        )
        assert metrics.interruption_rate == 20.0

    def test_interruption_rate_zero(self):
        """Test interruption rate with no interruptions."""
        metrics = TurnMetrics(
            total_agent_turns=5,
            interruptions=0,
        )
        assert metrics.interruption_rate == 0.0


class TestEvalMetrics:
    """Tests for EvalMetrics class."""

    def test_empty_metrics(self):
        """Test empty eval metrics."""
        metrics = EvalMetrics()
        assert metrics.total_evals == 0
        assert metrics.intent_correct_rate is None
        assert metrics.intent_failure_rate is None
        assert metrics.avg_relevance_score is None
        assert metrics.min_relevance_score is None
        assert metrics.max_relevance_score is None

    def test_intent_rates(self):
        """Test intent correctness and failure rates."""
        metrics = EvalMetrics(
            total_evals=10,
            intent_correct_count=8,
            intent_incorrect_count=2,
        )
        assert metrics.intent_correct_rate == 80.0
        assert metrics.intent_failure_rate == 20.0

    def test_relevance_scores(self):
        """Test relevance score aggregation."""
        metrics = EvalMetrics(
            total_evals=3,
            relevance_scores=[0.5, 0.8, 0.9],
        )
        assert metrics.avg_relevance_score == pytest.approx(0.7333, rel=0.01)
        assert metrics.min_relevance_score == 0.5
        assert metrics.max_relevance_score == 0.9


class TestParseJSONL:
    """Tests for JSONL parsing."""

    def test_parse_jsonl_file(self, tmp_path):
        """Test parsing a JSONL file."""
        file_path = tmp_path / "spans.jsonl"
        spans_data = [
            {"name": "voice.turn", "duration_ms": 100},
            {"name": "voice.asr", "duration_ms": 50},
        ]
        file_path.write_text("\n".join(json.dumps(s) for s in spans_data) + "\n")

        spans = parse_jsonl(file_path)
        assert len(spans) == 2
        assert spans[0]["name"] == "voice.turn"
        assert spans[1]["name"] == "voice.asr"

    def test_parse_jsonl_stream(self):
        """Test parsing JSONL from a stream."""
        data = '{"name": "voice.turn"}\n{"name": "voice.asr"}\n'
        stream = io.StringIO(data)

        spans = parse_jsonl_stream(stream)
        assert len(spans) == 2

    def test_parse_empty_lines(self):
        """Test that empty lines are skipped."""
        data = '{"name": "span1"}\n\n{"name": "span2"}\n\n'
        stream = io.StringIO(data)

        spans = parse_jsonl_stream(stream)
        assert len(spans) == 2


class TestAnalyzeSpans:
    """Tests for span analysis."""

    def test_count_spans(self):
        """Test counting total spans."""
        spans = [
            {"name": "voice.conversation", "attributes": {}},
            {"name": "voice.turn", "attributes": {}},
            {"name": "voice.asr", "attributes": {}},
        ]
        result = analyze_spans(spans)
        assert result.total_spans == 3

    def test_count_conversations(self):
        """Test counting unique conversations."""
        spans = [
            {"name": "voice.turn", "attributes": {"voice.conversation.id": "conv-1"}},
            {"name": "voice.turn", "attributes": {"voice.conversation.id": "conv-1"}},
            {"name": "voice.turn", "attributes": {"voice.conversation.id": "conv-2"}},
        ]
        result = analyze_spans(spans)
        assert result.total_conversations == 2

    def test_count_turns(self):
        """Test counting turns."""
        spans = [
            {"name": "voice.turn", "attributes": {"voice.actor": "user"}},
            {"name": "voice.turn", "attributes": {"voice.actor": "agent"}},
            {"name": "voice.asr", "attributes": {}},
        ]
        result = analyze_spans(spans)
        assert result.total_turns == 2

    def test_asr_metrics(self):
        """Test ASR stage metrics."""
        spans = [
            {"name": "voice.asr", "duration_ms": 100.0, "attributes": {"voice.stage.type": "asr"}},
            {"name": "voice.asr", "duration_ms": 200.0, "attributes": {"voice.stage.type": "asr"}},
        ]
        result = analyze_spans(spans)
        assert result.asr_metrics.count == 2
        assert result.asr_metrics.mean_ms == 150.0

    def test_llm_metrics(self):
        """Test LLM stage metrics."""
        spans = [
            {"name": "voice.llm", "duration_ms": 500.0, "attributes": {"voice.stage.type": "llm"}},
            {"name": "voice.llm", "duration_ms": 700.0, "attributes": {"voice.stage.type": "llm"}},
        ]
        result = analyze_spans(spans)
        assert result.llm_metrics.count == 2
        assert result.llm_metrics.mean_ms == 600.0

    def test_tts_metrics(self):
        """Test TTS stage metrics."""
        spans = [
            {"name": "voice.tts", "duration_ms": 200.0, "attributes": {"voice.stage.type": "tts"}},
        ]
        result = analyze_spans(spans)
        assert result.tts_metrics.count == 1
        assert result.tts_metrics.mean_ms == 200.0

    def test_silence_metrics(self):
        """Test silence after user metrics."""
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.silence.after_user_ms": 500.0,
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.silence.after_user_ms": 700.0,
                },
            },
        ]
        result = analyze_spans(spans)
        assert len(result.turn_metrics.silence_after_user_ms) == 2
        assert result.turn_metrics.silence_mean_ms == 600.0

    def test_interruption_metrics(self):
        """Test interruption detection metrics."""
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.interruption.detected": False,
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.interruption.detected": True,
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.interruption.detected": True,
                },
            },
        ]
        result = analyze_spans(spans)
        assert result.turn_metrics.total_agent_turns == 3
        assert result.turn_metrics.interruptions == 2
        assert result.turn_metrics.interruption_rate == pytest.approx(66.67, rel=0.01)

    def test_overlap_metrics(self):
        """Test overlap duration metrics."""
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.turn.overlap_ms": -500.0,  # Normal gap
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 100.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.turn.overlap_ms": 200.0,  # Interruption
                },
            },
        ]
        result = analyze_spans(spans)
        assert len(result.turn_metrics.overlap_ms) == 2

    def test_eval_metrics(self):
        """Test evaluation record parsing."""
        spans = [
            {
                "name": "voiceobs.eval",
                "attributes": {
                    "eval.intent_correct": True,
                    "eval.relevance_score": 0.9,
                    "voice.conversation.id": "conv-1",
                    "voice.turn.id": "turn-1",
                },
            },
            {
                "name": "voiceobs.eval",
                "attributes": {
                    "eval.intent_correct": False,
                    "eval.relevance_score": 0.3,
                    "voice.conversation.id": "conv-1",
                    "voice.turn.id": "turn-2",
                },
            },
            {
                "name": "voiceobs.eval",
                "attributes": {
                    "eval.intent_correct": True,
                    "eval.relevance_score": 0.8,
                    "voice.conversation.id": "conv-1",
                    "voice.turn.id": "turn-3",
                },
            },
        ]
        result = analyze_spans(spans)

        assert result.eval_metrics.total_evals == 3
        assert result.eval_metrics.intent_correct_count == 2
        assert result.eval_metrics.intent_incorrect_count == 1
        assert result.eval_metrics.intent_correct_rate == pytest.approx(66.67, rel=0.01)
        assert result.eval_metrics.intent_failure_rate == pytest.approx(33.33, rel=0.01)
        assert len(result.eval_metrics.relevance_scores) == 3
        assert result.eval_metrics.avg_relevance_score == pytest.approx(0.6667, rel=0.01)


class TestAnalyzeFile:
    """Tests for analyze_file function."""

    def test_analyze_file_end_to_end(self, tmp_path):
        """Test analyzing a complete JSONL file."""
        file_path = tmp_path / "spans.jsonl"
        spans = [
            {
                "name": "voice.conversation",
                "duration_ms": 5000.0,
                "attributes": {"voice.conversation.id": "conv-1"},
            },
            {
                "name": "voice.turn",
                "duration_ms": 1000.0,
                "attributes": {"voice.actor": "user", "voice.conversation.id": "conv-1"},
            },
            {
                "name": "voice.asr",
                "duration_ms": 150.0,
                "attributes": {"voice.stage.type": "asr", "voice.conversation.id": "conv-1"},
            },
            {
                "name": "voice.turn",
                "duration_ms": 2000.0,
                "attributes": {
                    "voice.actor": "agent",
                    "voice.conversation.id": "conv-1",
                    "voice.silence.after_user_ms": 1200.0,
                    "voice.interruption.detected": False,
                },
            },
            {
                "name": "voice.llm",
                "duration_ms": 800.0,
                "attributes": {"voice.stage.type": "llm", "voice.conversation.id": "conv-1"},
            },
            {
                "name": "voice.tts",
                "duration_ms": 300.0,
                "attributes": {"voice.stage.type": "tts", "voice.conversation.id": "conv-1"},
            },
        ]
        file_path.write_text("\n".join(json.dumps(s) for s in spans) + "\n")

        result = analyze_file(file_path)

        assert result.total_spans == 6
        assert result.total_conversations == 1
        assert result.total_turns == 2
        assert result.asr_metrics.count == 1
        assert result.llm_metrics.count == 1
        assert result.tts_metrics.count == 1
        assert result.turn_metrics.total_agent_turns == 1


class TestFormatReport:
    """Tests for report formatting (snapshot tests)."""

    def test_format_report_complete(self):
        """Test report format with complete data."""
        result = AnalysisResult(
            total_spans=20,
            total_conversations=2,
            total_turns=8,
            asr_metrics=StageMetrics("asr", durations_ms=[100.0, 120.0, 150.0, 180.0, 200.0]),
            llm_metrics=StageMetrics("llm", durations_ms=[500.0, 600.0, 700.0, 800.0, 1000.0]),
            tts_metrics=StageMetrics("tts", durations_ms=[200.0, 250.0, 300.0]),
            turn_metrics=TurnMetrics(
                silence_after_user_ms=[1000.0, 1200.0, 1100.0, 1500.0],
                total_agent_turns=4,
                interruptions=1,
            ),
        )

        report = result.format_report()

        # Snapshot test: verify expected structure
        expected = textwrap.dedent("""\
            voiceobs Analysis Report
            ==================================================

            Summary
            ------------------------------
              Total spans: 20
              Conversations: 2
              Turns: 8

            Stage Latencies (ms)
            ------------------------------
              ASR (n=5):
                mean: 150.0
                p50:  150.0
                p95:  200.0
                p99:  200.0
              LLM (n=5):
                mean: 720.0
                p50:  700.0
                p95:  1000.0
                p99:  1000.0
              TTS (n=3):
                mean: 250.0
                p50:  250.0
                p95:  300.0
                p99:  300.0

            Response Latency (silence after user)
            ------------------------------
              Samples: 4
              mean: 1200.0ms
              p95:  1500.0ms

            Interruptions
            ------------------------------
              Agent turns: 4
              Interruptions: 1
              Rate: 25.0%

            Semantic Evaluation (probabilistic)
            ------------------------------
              Note: These metrics come from LLM-as-judge evaluation
              and may vary slightly between runs.

              No evaluation data available
              (Run semantic evaluation to generate eval records)
        """)

        assert report == expected

    def test_format_report_empty_data(self):
        """Test report format with no data."""
        result = AnalysisResult()
        report = result.format_report()

        assert "voiceobs Analysis Report" in report
        assert "Total spans: 0" in report
        assert "ASR: no data" in report
        assert "LLM: no data" in report
        assert "TTS: no data" in report
        assert "No silence data available" in report
        assert "No agent turn data available" in report
        assert "Semantic Evaluation (probabilistic)" in report
        assert "No evaluation data available" in report

    def test_format_report_partial_data(self):
        """Test report format with partial stage data."""
        result = AnalysisResult(
            total_spans=5,
            total_conversations=1,
            total_turns=2,
            asr_metrics=StageMetrics("asr", durations_ms=[100.0, 150.0]),
            llm_metrics=StageMetrics("llm"),  # No LLM data
            tts_metrics=StageMetrics("tts", durations_ms=[200.0]),
        )

        report = result.format_report()

        assert "ASR (n=2):" in report
        assert "LLM: no data" in report
        assert "TTS (n=1):" in report

    def test_format_report_with_eval_data(self):
        """Test report format with evaluation data."""
        result = AnalysisResult(
            total_spans=5,
            total_conversations=1,
            total_turns=3,
            eval_metrics=EvalMetrics(
                total_evals=3,
                intent_correct_count=2,
                intent_incorrect_count=1,
                relevance_scores=[0.9, 0.3, 0.8],
            ),
        )

        report = result.format_report()

        assert "Semantic Evaluation (probabilistic)" in report
        assert "Evaluated turns: 3" in report
        assert "Intent correct: 66.7%" in report
        assert "Intent failures: 33.3%" in report
        assert "Avg relevance: 0.67" in report
        assert "Relevance range: 0.30 - 0.90" in report


class TestCLIIntegration:
    """Tests for CLI analyze command."""

    def test_analyze_command_help(self):
        """Test that analyze command has help text."""
        from typer.testing import CliRunner

        from voiceobs.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "--help"])

        assert result.exit_code == 0
        assert "Analyze a JSONL trace file" in result.output
        # Check for -i (short option) since --input may be split by ANSI codes
        assert "-i" in result.output

    def test_analyze_command_with_file(self, tmp_path):
        """Test analyze command with a valid file."""
        from typer.testing import CliRunner

        from voiceobs.cli import app

        # Create a test JSONL file
        file_path = tmp_path / "test.jsonl"
        spans = [
            {"name": "voice.turn", "duration_ms": 100.0, "attributes": {"voice.actor": "user"}},
            {
                "name": "voice.asr",
                "duration_ms": 150.0,
                "attributes": {"voice.stage.type": "asr"},
            },
        ]
        file_path.write_text("\n".join(json.dumps(s) for s in spans) + "\n")

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "--input", str(file_path)])

        assert result.exit_code == 0
        assert "voiceobs Analysis Report" in result.output
        assert "Total spans: 2" in result.output
        assert "ASR (n=1):" in result.output

    def test_analyze_command_file_not_found(self, tmp_path):
        """Test analyze command with non-existent file."""
        from typer.testing import CliRunner

        from voiceobs.cli import app

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "--input", str(tmp_path / "missing.jsonl")])

        # Typer validates file existence and should exit with error
        assert result.exit_code != 0

    def test_analyze_command_invalid_json(self, tmp_path):
        """Test analyze command with invalid JSON file."""
        from typer.testing import CliRunner

        from voiceobs.cli import app

        # Create a file with invalid JSON
        file_path = tmp_path / "invalid.jsonl"
        file_path.write_text("this is not valid json\n")

        runner = CliRunner()
        result = runner.invoke(app, ["analyze", "--input", str(file_path)])

        # Should exit with error code 1
        assert result.exit_code == 1
        assert "Error analyzing file" in result.output
