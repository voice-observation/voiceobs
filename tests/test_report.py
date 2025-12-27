"""Tests for voiceobs report generation."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from voiceobs.analyzer import AnalysisResult
from voiceobs.classifier import ClassificationResult
from voiceobs.failures import Failure, FailureType, Severity
from voiceobs.report import (
    ReportData,
    _format_ms,
    generate_html_report,
    generate_markdown_report,
    generate_report,
    generate_report_from_file,
)


@pytest.fixture
def sample_analysis() -> AnalysisResult:
    """Create a sample AnalysisResult for testing."""
    result = AnalysisResult(
        total_spans=100,
        total_conversations=5,
        total_turns=20,
    )
    # Add ASR metrics
    result.asr_metrics.durations_ms = [150.0, 200.0, 180.0, 220.0, 170.0]
    # Add LLM metrics
    result.llm_metrics.durations_ms = [500.0, 600.0, 550.0, 700.0, 450.0]
    # Add TTS metrics
    result.tts_metrics.durations_ms = [100.0, 120.0, 110.0, 130.0, 90.0]
    # Add turn metrics
    result.turn_metrics.silence_after_user_ms = [200.0, 300.0, 250.0, 400.0, 350.0]
    result.turn_metrics.total_agent_turns = 10
    result.turn_metrics.interruptions = 2
    # Add eval metrics
    result.eval_metrics.total_evals = 10
    result.eval_metrics.intent_correct_count = 8
    result.eval_metrics.intent_incorrect_count = 2
    result.eval_metrics.relevance_scores = [0.9, 0.8, 0.85, 0.7, 0.95]
    return result


@pytest.fixture
def sample_failures() -> ClassificationResult:
    """Create a sample ClassificationResult for testing."""
    result = ClassificationResult(
        total_spans=100,
        total_turns=20,
        total_agent_turns=10,
    )
    result.failures = [
        Failure(
            type=FailureType.SLOW_RESPONSE,
            severity=Severity.MEDIUM,
            message="LLM took 2500ms (threshold: 2000ms)",
            conversation_id="conv-1",
            turn_id="turn-1",
            turn_index=1,
            signal_name="voice.llm.duration_ms",
            signal_value=2500.0,
            threshold=2000.0,
        ),
        Failure(
            type=FailureType.EXCESSIVE_SILENCE,
            severity=Severity.LOW,
            message="Silence of 4000ms (threshold: 3000ms)",
            conversation_id="conv-2",
            turn_id="turn-3",
            turn_index=3,
            signal_name="voice.silence.after_user_ms",
            signal_value=4000.0,
            threshold=3000.0,
        ),
        Failure(
            type=FailureType.INTERRUPTION,
            severity=Severity.HIGH,
            message="Agent interrupted user by 600ms",
            conversation_id="conv-1",
            turn_id="turn-5",
            turn_index=5,
            signal_name="voice.turn.overlap_ms",
            signal_value=600.0,
            threshold=0.0,
        ),
    ]
    return result


@pytest.fixture
def empty_analysis() -> AnalysisResult:
    """Create an empty AnalysisResult for testing."""
    return AnalysisResult()


@pytest.fixture
def empty_failures() -> ClassificationResult:
    """Create an empty ClassificationResult for testing."""
    return ClassificationResult()


class TestFormatMs:
    """Tests for _format_ms helper function."""

    def test_format_ms_with_value(self) -> None:
        """Test formatting a valid milliseconds value."""
        assert _format_ms(123.456) == "123.5"

    def test_format_ms_with_none(self) -> None:
        """Test formatting None value returns dash."""
        assert _format_ms(None) == "-"


class TestReportData:
    """Tests for ReportData dataclass."""

    def test_create_report_data(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test creating ReportData from analysis and failures."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        assert data.analysis.total_spans == 100
        assert data.failures.failure_count == 3

    def test_report_data_with_title(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test ReportData with custom title."""
        data = ReportData(
            analysis=sample_analysis,
            failures=sample_failures,
            title="Custom Report Title",
        )
        assert data.title == "Custom Report Title"


class TestGenerateMarkdownReport:
    """Tests for markdown report generation."""

    def test_generates_valid_markdown(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that generated output is valid markdown."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert isinstance(markdown, str)
        assert len(markdown) > 0

    def test_contains_title(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains title."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert "# voiceobs Analysis Report" in markdown

    def test_contains_custom_title(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains custom title."""
        data = ReportData(
            analysis=sample_analysis,
            failures=sample_failures,
            title="My Custom Report",
        )
        markdown = generate_markdown_report(data)
        assert "# My Custom Report" in markdown

    def test_contains_summary_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains summary section."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert "## Summary" in markdown
        assert "Conversations" in markdown
        assert "5" in markdown  # total conversations
        assert "Turns" in markdown
        assert "20" in markdown  # total turns

    def test_contains_latency_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains latency breakdown."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert "## Latency Breakdown" in markdown
        assert "ASR" in markdown
        assert "LLM" in markdown
        assert "TTS" in markdown
        assert "p50" in markdown
        assert "p95" in markdown
        assert "p99" in markdown

    def test_contains_failure_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains failure summary."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert "## Failures" in markdown
        assert "slow_response" in markdown
        assert "excessive_silence" in markdown
        assert "interruption" in markdown

    def test_contains_eval_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains eval summary when data available."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert "## Semantic Evaluation" in markdown
        assert "Intent correct" in markdown
        assert "Relevance" in markdown

    def test_contains_recommendations_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that report contains recommendations."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        markdown = generate_markdown_report(data)
        assert "## Recommendations" in markdown

    def test_empty_data_report(
        self, empty_analysis: AnalysisResult, empty_failures: ClassificationResult
    ) -> None:
        """Test report generation with empty data."""
        data = ReportData(analysis=empty_analysis, failures=empty_failures)
        markdown = generate_markdown_report(data)
        assert "# voiceobs Analysis Report" in markdown
        assert "No data" in markdown or "0" in markdown

    def test_no_eval_section_when_no_eval_data(
        self, empty_analysis: AnalysisResult, empty_failures: ClassificationResult
    ) -> None:
        """Test that eval section is handled when no eval data."""
        data = ReportData(analysis=empty_analysis, failures=empty_failures)
        markdown = generate_markdown_report(data)
        # Should still have section but indicate no data
        assert "## Semantic Evaluation" in markdown


class TestGenerateHtmlReport:
    """Tests for HTML report generation."""

    def test_generates_valid_html(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that generated output is valid HTML."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert isinstance(html, str)
        assert "<html" in html
        assert "</html>" in html

    def test_self_contained_with_inline_css(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that HTML is self-contained with inline CSS."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert "<style>" in html
        assert "</style>" in html

    def test_contains_title(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that HTML contains title."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert "<title>" in html
        assert "voiceobs" in html

    def test_contains_summary_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that HTML contains summary section."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert "Summary" in html
        assert "5" in html  # conversations
        assert "20" in html  # turns

    def test_contains_latency_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that HTML contains latency breakdown."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert "Latency" in html
        assert "ASR" in html
        assert "LLM" in html
        assert "TTS" in html

    def test_contains_failure_section(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that HTML contains failure summary."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert "Failure" in html

    def test_contains_recommendations(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that HTML contains recommendations."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        html = generate_html_report(data)
        assert "Recommendation" in html

    def test_empty_data_html_report(
        self, empty_analysis: AnalysisResult, empty_failures: ClassificationResult
    ) -> None:
        """Test HTML report generation with empty data."""
        data = ReportData(analysis=empty_analysis, failures=empty_failures)
        html = generate_html_report(data)
        assert "<html" in html
        assert "</html>" in html


class TestGenerateReport:
    """Tests for the unified generate_report function."""

    def test_generate_markdown_format(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test generate_report with markdown format."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        report = generate_report(data, format="markdown")
        assert "# voiceobs" in report

    def test_generate_html_format(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test generate_report with HTML format."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        report = generate_report(data, format="html")
        assert "<html" in report

    def test_invalid_format_raises_error(
        self, sample_analysis: AnalysisResult, sample_failures: ClassificationResult
    ) -> None:
        """Test that invalid format raises ValueError."""
        data = ReportData(analysis=sample_analysis, failures=sample_failures)
        with pytest.raises(ValueError) as exc_info:
            generate_report(data, format="pdf")  # type: ignore
        assert "format" in str(exc_info.value).lower()


class TestGenerateReportFromFile:
    """Tests for generate_report_from_file function."""

    def test_generate_from_jsonl_file(self) -> None:
        """Test generating report from a JSONL file."""
        import json

        # Create sample data as dictionaries and convert to JSONL
        spans = [
            {
                "name": "voice.conversation",
                "attributes": {"voice.conversation.id": "conv-1"},
                "duration_ms": 5000,
            },
            {
                "name": "voice.turn",
                "attributes": {
                    "voice.actor": "user",
                    "voice.conversation.id": "conv-1",
                    "voice.turn.id": "turn-1",
                    "voice.turn.index": 0,
                },
                "duration_ms": 1000,
            },
            {
                "name": "voice.turn",
                "attributes": {
                    "voice.actor": "agent",
                    "voice.conversation.id": "conv-1",
                    "voice.turn.id": "turn-2",
                    "voice.turn.index": 1,
                    "voice.silence.after_user_ms": 500,
                },
                "duration_ms": 2000,
            },
            {
                "name": "voice.asr",
                "attributes": {"voice.stage.type": "asr"},
                "duration_ms": 150,
            },
            {
                "name": "voice.llm",
                "attributes": {"voice.stage.type": "llm"},
                "duration_ms": 800,
            },
            {
                "name": "voice.tts",
                "attributes": {"voice.stage.type": "tts"},
                "duration_ms": 100,
            },
        ]
        jsonl_content = "\n".join(json.dumps(span) for span in spans) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(jsonl_content)
            temp_path = Path(f.name)

        try:
            report = generate_report_from_file(temp_path, format="markdown")
            assert "# voiceobs Analysis Report" in report
            assert "Summary" in report
        finally:
            temp_path.unlink()

    def test_generate_html_from_file(self) -> None:
        """Test generating HTML report from a JSONL file."""
        import json

        span = {
            "name": "voice.turn",
            "attributes": {"voice.actor": "agent"},
            "duration_ms": 1000,
        }
        jsonl_content = json.dumps(span) + "\n"
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False
        ) as f:
            f.write(jsonl_content)
            temp_path = Path(f.name)

        try:
            report = generate_report_from_file(temp_path, format="html")
            assert "<html" in report
        finally:
            temp_path.unlink()

    def test_file_not_found_raises_error(self) -> None:
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            generate_report_from_file(Path("/nonexistent/file.jsonl"))


class TestRecommendations:
    """Tests for recommendation generation based on failures."""

    def test_slow_response_recommendation(
        self, sample_analysis: AnalysisResult
    ) -> None:
        """Test that slow response failures generate relevant recommendations."""
        failures = ClassificationResult()
        failures.failures = [
            Failure(
                type=FailureType.SLOW_RESPONSE,
                severity=Severity.HIGH,
                message="LLM took 5000ms",
            ),
        ]
        data = ReportData(analysis=sample_analysis, failures=failures)
        markdown = generate_markdown_report(data)
        # Should recommend optimizing slow component
        assert "Recommendation" in markdown

    def test_excessive_silence_recommendation(
        self, sample_analysis: AnalysisResult
    ) -> None:
        """Test that silence failures generate relevant recommendations."""
        failures = ClassificationResult()
        failures.failures = [
            Failure(
                type=FailureType.EXCESSIVE_SILENCE,
                severity=Severity.MEDIUM,
                message="Silence of 5000ms",
            ),
        ]
        data = ReportData(analysis=sample_analysis, failures=failures)
        markdown = generate_markdown_report(data)
        assert "Recommendation" in markdown

    def test_interruption_recommendation(
        self, sample_analysis: AnalysisResult
    ) -> None:
        """Test that interruption failures generate relevant recommendations."""
        failures = ClassificationResult()
        failures.failures = [
            Failure(
                type=FailureType.INTERRUPTION,
                severity=Severity.HIGH,
                message="Agent interrupted user",
            ),
        ]
        data = ReportData(analysis=sample_analysis, failures=failures)
        markdown = generate_markdown_report(data)
        assert "Recommendation" in markdown

    def test_no_failures_positive_message(
        self, sample_analysis: AnalysisResult, empty_failures: ClassificationResult
    ) -> None:
        """Test that no failures generates positive message."""
        data = ReportData(analysis=sample_analysis, failures=empty_failures)
        markdown = generate_markdown_report(data)
        assert "Recommendation" in markdown

    def test_low_severity_interruption_recommendation(
        self, sample_analysis: AnalysisResult
    ) -> None:
        """Test that low severity interruption generates fine-tune recommendation."""
        failures = ClassificationResult()
        failures.failures = [
            Failure(
                type=FailureType.INTERRUPTION,
                severity=Severity.LOW,
                message="Minor interruption detected",
            ),
        ]
        data = ReportData(analysis=sample_analysis, failures=failures)
        markdown = generate_markdown_report(data)
        assert "Fine-tune voice activity" in markdown

    def test_asr_low_confidence_recommendation(
        self, sample_analysis: AnalysisResult
    ) -> None:
        """Test that ASR low confidence generates relevant recommendation."""
        failures = ClassificationResult()
        failures.failures = [
            Failure(
                type=FailureType.ASR_LOW_CONFIDENCE,
                severity=Severity.MEDIUM,
                message="ASR confidence 60%",
            ),
        ]
        data = ReportData(analysis=sample_analysis, failures=failures)
        markdown = generate_markdown_report(data)
        assert "ASR confidence below threshold" in markdown

    def test_llm_incorrect_intent_recommendation(
        self, sample_analysis: AnalysisResult
    ) -> None:
        """Test that LLM incorrect intent generates relevant recommendation."""
        failures = ClassificationResult()
        failures.failures = [
            Failure(
                type=FailureType.LLM_INCORRECT_INTENT,
                severity=Severity.MEDIUM,
                message="Intent incorrect",
            ),
        ]
        data = ReportData(analysis=sample_analysis, failures=failures)
        markdown = generate_markdown_report(data)
        assert "LLM intent classification issues" in markdown
