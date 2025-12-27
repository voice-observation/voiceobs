"""End-to-end tests for the complete voiceobs workflow.

This module tests the full pipeline:
    pipeline → jsonl → analyze → eval → compare

These tests verify that all components work together correctly.
"""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from voiceobs import (
    JSONLSpanExporter,
)
from voiceobs.analyzer import analyze_file
from voiceobs.compare import compare_runs


class TestEndToEndPipeline:
    """End-to-end tests for the full voiceobs pipeline."""

    def test_pipeline_to_jsonl_to_analyze(self, tmp_path: Path) -> None:
        """Test: pipeline → jsonl → analyze."""
        jsonl_file = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(jsonl_file))

        # Create a fresh provider with our exporter
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer("test")

        # Simulate a conversation with stages
        with tracer.start_as_current_span("voice.conversation") as conv_span:
            conv_span.set_attribute("voice.conversation.id", "conv-e2e-1")

            # User turn
            with tracer.start_as_current_span("voice.turn") as turn_span:
                turn_span.set_attribute("voice.actor", "user")
                turn_span.set_attribute("voice.conversation.id", "conv-e2e-1")

            # Agent turn with stages
            with tracer.start_as_current_span("voice.turn") as turn_span:
                turn_span.set_attribute("voice.actor", "agent")
                turn_span.set_attribute("voice.conversation.id", "conv-e2e-1")
                turn_span.set_attribute("voice.silence.after_user_ms", 150.0)

                # ASR stage
                with tracer.start_as_current_span("voice.asr") as asr_span:
                    asr_span.set_attribute("voice.stage.type", "asr")
                    time.sleep(0.01)

                # LLM stage
                with tracer.start_as_current_span("voice.llm") as llm_span:
                    llm_span.set_attribute("voice.stage.type", "llm")
                    time.sleep(0.02)

                # TTS stage
                with tracer.start_as_current_span("voice.tts") as tts_span:
                    tts_span.set_attribute("voice.stage.type", "tts")
                    time.sleep(0.01)

        # Verify JSONL was created
        assert jsonl_file.exists()

        # Analyze the JSONL
        result = analyze_file(jsonl_file)

        # Verify analysis results
        assert result.total_spans > 0
        assert result.total_conversations == 1
        assert result.total_turns == 2
        assert result.asr_metrics.count > 0
        assert result.llm_metrics.count > 0
        assert result.tts_metrics.count > 0
        assert len(result.turn_metrics.silence_after_user_ms) > 0

    def test_pipeline_to_jsonl_to_compare(self, tmp_path: Path) -> None:
        """Test: pipeline → jsonl → compare."""
        baseline_file = tmp_path / "baseline.jsonl"
        current_file = tmp_path / "current.jsonl"

        def create_run(file_path: Path, llm_duration: float) -> None:
            """Create a run with specified LLM duration."""
            exporter = JSONLSpanExporter(str(file_path))
            provider = TracerProvider()
            provider.add_span_processor(SimpleSpanProcessor(exporter))
            tracer = provider.get_tracer("test")

            with tracer.start_as_current_span("voice.conversation") as conv_span:
                conv_span.set_attribute("voice.conversation.id", "conv-compare")

                with tracer.start_as_current_span("voice.turn") as turn_span:
                    turn_span.set_attribute("voice.actor", "agent")
                    turn_span.set_attribute("voice.conversation.id", "conv-compare")

                    with tracer.start_as_current_span("voice.llm") as llm_span:
                        llm_span.set_attribute("voice.stage.type", "llm")
                        time.sleep(llm_duration)

        # Create baseline (fast)
        create_run(baseline_file, 0.01)

        # Create current (slow - should trigger regression)
        create_run(current_file, 0.05)

        # Analyze both
        baseline_result = analyze_file(baseline_file)
        current_result = analyze_file(current_file)

        # Compare
        comparison = compare_runs(
            baseline_result,
            current_result,
            baseline_file=str(baseline_file),
            current_file=str(current_file),
        )

        # Verify comparison detected the latency increase
        assert comparison.llm_p95_delta is not None
        assert comparison.llm_p95_delta.current > comparison.llm_p95_delta.baseline

    def test_full_workflow_no_regression(self, tmp_path: Path) -> None:
        """Test full workflow with no regressions."""
        baseline_file = tmp_path / "baseline.jsonl"
        current_file = tmp_path / "current.jsonl"

        # Create identical baseline data
        spans = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.stage.type": "llm",
                },
            },
            {
                "name": "voice.turn",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.actor": "agent",
                    "voice.silence.after_user_ms": 100.0,
                },
            },
        ]

        baseline_file.write_text("\n".join(json.dumps(s) for s in spans))
        current_file.write_text("\n".join(json.dumps(s) for s in spans))

        # Analyze and compare
        baseline_result = analyze_file(baseline_file)
        current_result = analyze_file(current_file)

        comparison = compare_runs(baseline_result, current_result)

        # No regressions expected
        assert not comparison.has_regressions
        assert len(comparison.regressions) == 0

    def test_full_workflow_with_regression(self, tmp_path: Path) -> None:
        """Test full workflow with regression detection."""
        baseline_file = tmp_path / "baseline.jsonl"
        current_file = tmp_path / "current.jsonl"

        # Create baseline
        baseline_spans = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        baseline_file.write_text(json.dumps(baseline_spans[0]))

        # Create current with 50% latency increase
        current_spans = [
            {
                "name": "voice.llm",
                "duration_ms": 300.0,  # 50% increase
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        current_file.write_text(json.dumps(current_spans[0]))

        # Analyze and compare
        baseline_result = analyze_file(baseline_file)
        current_result = analyze_file(current_file)

        comparison = compare_runs(baseline_result, current_result)

        # Regression expected (50% > 25% critical threshold)
        assert comparison.has_regressions
        assert any("LLM" in r.description for r in comparison.regressions)

    def test_workflow_with_eval_records(self, tmp_path: Path) -> None:
        """Test workflow including evaluation records."""
        jsonl_file = tmp_path / "spans.jsonl"

        # Create spans with eval records
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.actor": "agent",
                },
            },
            {
                "name": "voiceobs.eval",
                "duration_ms": 100.0,
                "attributes": {
                    "eval.conversation_id": "conv-1",
                    "eval.turn_id": "turn-1",
                    "eval.intent_correct": True,
                    "eval.relevance_score": 0.85,
                },
            },
            {
                "name": "voiceobs.eval",
                "duration_ms": 100.0,
                "attributes": {
                    "eval.conversation_id": "conv-1",
                    "eval.turn_id": "turn-2",
                    "eval.intent_correct": False,
                    "eval.relevance_score": 0.45,
                },
            },
        ]
        jsonl_file.write_text("\n".join(json.dumps(s) for s in spans))

        # Analyze
        result = analyze_file(jsonl_file)

        # Verify eval metrics
        assert result.eval_metrics.total_evals == 2
        assert result.eval_metrics.intent_correct_count == 1
        assert result.eval_metrics.intent_incorrect_count == 1
        assert len(result.eval_metrics.relevance_scores) == 2
        assert result.eval_metrics.avg_relevance_score == 0.65

    def test_workflow_with_failures(self, tmp_path: Path) -> None:
        """Test workflow with failure classification."""
        from voiceobs.classifier import classify_file

        jsonl_file = tmp_path / "spans.jsonl"

        # Create spans with issues that trigger failures
        spans = [
            {
                "name": "voice.turn",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.actor": "agent",
                    "voice.silence.after_user_ms": 5000.0,  # Excessive silence
                    "voice.interruption.detected": True,
                    "voice.turn.overlap_ms": 300.0,
                },
            },
            {
                "name": "voice.llm",
                "duration_ms": 6000.0,  # Slow response
                "attributes": {
                    "voice.stage.type": "llm",
                },
            },
        ]
        jsonl_file.write_text("\n".join(json.dumps(s) for s in spans))

        # Classify failures
        result = classify_file(jsonl_file)

        # Verify failures detected
        assert result.failure_count > 0
        failure_types = [f.type.value for f in result.failures]
        assert "excessive_silence" in failure_types
        assert "interruption" in failure_types
        assert "slow_response" in failure_types


class TestEndToEndWithMockedEval:
    """End-to-end tests with mocked LLM evaluation."""

    def test_eval_integration(self, tmp_path: Path) -> None:
        """Test semantic evaluator integration."""
        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator
        from voiceobs.eval.evaluator import EvalOutput

        # Create mock LLM response
        mock_output = EvalOutput(
            intent_correct=True,
            relevance_score=0.92,
            explanation="The agent correctly answered the weather question.",
        )

        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            evaluator = SemanticEvaluator(config)

            # Evaluate a turn
            result = evaluator.evaluate(
                EvalInput(
                    user_transcript="What's the weather like today?",
                    agent_response="It's sunny and 72 degrees.",
                    conversation_id="conv-1",
                    turn_id="turn-1",
                )
            )

            assert result.intent_correct is True
            assert result.relevance_score == 0.92
            assert result.passed is True


class TestReportGeneration:
    """Tests for report generation in the pipeline."""

    def test_analysis_report_format(self, tmp_path: Path) -> None:
        """Test that analysis report is properly formatted."""
        jsonl_file = tmp_path / "spans.jsonl"

        spans = [
            {
                "name": "voice.llm",
                "duration_ms": 250.0,
                "attributes": {"voice.stage.type": "llm"},
            },
            {
                "name": "voice.turn",
                "duration_ms": 500.0,
                "attributes": {
                    "voice.conversation.id": "conv-1",
                    "voice.actor": "agent",
                },
            },
        ]
        jsonl_file.write_text("\n".join(json.dumps(s) for s in spans))

        result = analyze_file(jsonl_file)
        report = result.format_report()

        # Verify report structure
        assert "voiceobs Analysis Report" in report
        assert "Summary" in report
        assert "Stage Latencies" in report
        assert "LLM" in report
        assert "Response Latency" in report
        assert "Semantic Evaluation" in report

    def test_comparison_report_format(self, tmp_path: Path) -> None:
        """Test that comparison report is properly formatted."""
        baseline_file = tmp_path / "baseline.jsonl"
        current_file = tmp_path / "current.jsonl"

        spans = [
            {
                "name": "voice.llm",
                "duration_ms": 200.0,
                "attributes": {"voice.stage.type": "llm"},
            },
        ]
        baseline_file.write_text(json.dumps(spans[0]))
        current_file.write_text(json.dumps(spans[0]))

        baseline_result = analyze_file(baseline_file)
        current_result = analyze_file(current_file)

        comparison = compare_runs(
            baseline_result,
            current_result,
            baseline_file=str(baseline_file),
            current_file=str(current_file),
        )
        report = comparison.format_report()

        # Verify report structure
        assert "voiceobs Comparison Report" in report
        assert "Files" in report
        assert "Stage Latency Deltas" in report
        assert "Response Latency Deltas" in report
        assert "Regressions" in report
