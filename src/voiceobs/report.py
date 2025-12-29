"""Report generation for voiceobs analysis results.

This module provides functions to generate markdown and HTML reports
from JSONL trace analysis results.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from voiceobs.analyzer import AnalysisResult, analyze_file
from voiceobs.classifier import ClassificationResult, classify_file
from voiceobs.failures import FailureType, Severity


@dataclass
class ReportData:
    """Data container for report generation."""

    analysis: AnalysisResult
    failures: ClassificationResult
    title: str = "voiceobs Analysis Report"


def _format_ms(value: float | None) -> str:
    """Format milliseconds value for display."""
    if value is None:
        return "-"
    return f"{value:.1f}"


def _generate_recommendations(data: ReportData) -> list[str]:
    """Generate recommendations based on analysis and failures."""
    recommendations: list[str] = []

    # Check for slow response failures
    slow_failures = [f for f in data.failures.failures if f.type == FailureType.SLOW_RESPONSE]
    if slow_failures:
        high_severity = any(f.severity == Severity.HIGH for f in slow_failures)
        if high_severity:
            recommendations.append(
                "**Critical latency issues detected.** Consider optimizing "
                "the slowest stages (check p99 values) or using faster models."
            )
        else:
            recommendations.append(
                "Some stages are exceeding latency thresholds. Review the "
                "latency breakdown to identify bottlenecks."
            )

    # Check for excessive silence
    silence_failures = [
        f for f in data.failures.failures if f.type == FailureType.EXCESSIVE_SILENCE
    ]
    if silence_failures:
        recommendations.append(
            "Response delays detected. Consider implementing streaming "
            "responses or optimizing the processing pipeline."
        )

    # Check for interruptions
    interruption_failures = [
        f for f in data.failures.failures if f.type == FailureType.INTERRUPTION
    ]
    if interruption_failures:
        high_severity = any(f.severity == Severity.HIGH for f in interruption_failures)
        if high_severity:
            recommendations.append(
                "**Significant interruption issues.** Review turn-taking "
                "logic and consider adding end-of-speech detection improvements."
            )
        else:
            recommendations.append(
                "Some interruptions detected. Fine-tune voice activity detection thresholds."
            )

    # Check for ASR confidence issues
    asr_failures = [f for f in data.failures.failures if f.type == FailureType.ASR_LOW_CONFIDENCE]
    if asr_failures:
        recommendations.append(
            "ASR confidence below threshold. Consider improving audio quality, "
            "using noise suppression, or trying a different ASR provider."
        )

    # Check for LLM intent issues
    intent_failures = [
        f for f in data.failures.failures if f.type == FailureType.LLM_INCORRECT_INTENT
    ]
    if intent_failures:
        recommendations.append(
            "LLM intent classification issues. Review and improve system prompts "
            "or consider fine-tuning the model for your domain."
        )

    # No failures - positive message
    if data.failures.failure_count == 0:
        recommendations.append(
            "No failures detected. Your voice pipeline is performing well within "
            "the configured thresholds."
        )

    return recommendations


def generate_markdown_report(data: ReportData) -> str:
    """Generate a markdown report from analysis data.

    Args:
        data: ReportData containing analysis and failure results.

    Returns:
        Markdown formatted report string.
    """
    lines: list[str] = []

    # Title
    lines.append(f"# {data.title}")
    lines.append("")

    # Summary section
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Total Spans | {data.analysis.total_spans} |")
    lines.append(f"| Conversations | {data.analysis.total_conversations} |")
    lines.append(f"| Turns | {data.analysis.total_turns} |")
    lines.append(f"| Failures | {data.failures.failure_count} |")
    lines.append("")

    # Latency breakdown
    lines.append("## Latency Breakdown")
    lines.append("")

    # Stage latencies table
    lines.append("| Stage | Count | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) |")
    lines.append("|-------|-------|-----------|----------|----------|----------|")

    for name, metrics in [
        ("ASR", data.analysis.asr_metrics),
        ("LLM", data.analysis.llm_metrics),
        ("TTS", data.analysis.tts_metrics),
    ]:
        if metrics.count > 0:
            lines.append(
                f"| {name} | {metrics.count} | "
                f"{_format_ms(metrics.mean_ms)} | "
                f"{_format_ms(metrics.p50_ms)} | "
                f"{_format_ms(metrics.p95_ms)} | "
                f"{_format_ms(metrics.p99_ms)} |"
            )
        else:
            lines.append(f"| {name} | 0 | - | - | - | - |")
    lines.append("")

    # Response latency (silence)
    if data.analysis.turn_metrics.silence_after_user_ms:
        lines.append("### Response Latency")
        lines.append("")
        lines.append(f"- Samples: {len(data.analysis.turn_metrics.silence_after_user_ms)}")
        lines.append(f"- Mean: {_format_ms(data.analysis.turn_metrics.silence_mean_ms)} ms")
        lines.append(f"- p95: {_format_ms(data.analysis.turn_metrics.silence_p95_ms)} ms")
        lines.append("")

    # Failures section
    lines.append("## Failures")
    lines.append("")

    if data.failures.failure_count > 0:
        # Summary by type
        lines.append("### By Type")
        lines.append("")
        lines.append("| Type | Count |")
        lines.append("|------|-------|")
        for failure_type, failures in data.failures.failures_by_type.items():
            lines.append(f"| {failure_type.value} | {len(failures)} |")
        lines.append("")

        # Summary by severity
        lines.append("### By Severity")
        lines.append("")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for severity in [Severity.HIGH, Severity.MEDIUM, Severity.LOW]:
            count = len(data.failures.failures_by_severity.get(severity, []))
            lines.append(f"| {severity.value} | {count} |")
        lines.append("")

        # Detailed failures
        lines.append("### Details")
        lines.append("")
        for failure in data.failures.failures:
            severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                failure.severity.value, "⚪"
            )
            lines.append(
                f"- {severity_icon} **{failure.type.value}** ({failure.severity.value}): "
                f"{failure.message}"
            )
        lines.append("")
    else:
        lines.append("No failures detected.")
        lines.append("")

    # Semantic evaluation section
    lines.append("## Semantic Evaluation")
    lines.append("")

    if data.analysis.eval_metrics.total_evals > 0:
        lines.append(f"- Evaluated turns: {data.analysis.eval_metrics.total_evals}")
        if data.analysis.eval_metrics.intent_correct_rate is not None:
            lines.append(f"- Intent correct: {data.analysis.eval_metrics.intent_correct_rate:.1f}%")
        if data.analysis.eval_metrics.avg_relevance_score is not None:
            lines.append(f"- Relevance (avg): {data.analysis.eval_metrics.avg_relevance_score:.2f}")
        if data.analysis.eval_metrics.min_relevance_score is not None:
            lines.append(
                f"- Relevance range: "
                f"{data.analysis.eval_metrics.min_relevance_score:.2f} - "
                f"{data.analysis.eval_metrics.max_relevance_score:.2f}"
            )
    else:
        lines.append("No evaluation data available.")
        lines.append("")
        lines.append("Run semantic evaluation to generate eval records:")
        lines.append("```bash")
        lines.append("voiceobs eval --input run.jsonl")
        lines.append("```")
    lines.append("")

    # Recommendations section
    lines.append("## Recommendations")
    lines.append("")
    recommendations = _generate_recommendations(data)
    for rec in recommendations:
        lines.append(f"- {rec}")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append("*Generated by [voiceobs](https://github.com/voice-observation/voiceobs)*")
    lines.append("")

    return "\n".join(lines)


def generate_html_report(data: ReportData) -> str:
    """Generate an HTML report from analysis data.

    Args:
        data: ReportData containing analysis and failure results.

    Returns:
        Self-contained HTML report string with inline CSS.
    """
    # CSS styles
    css = """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background-color: #f9fafb;
        }
        h1 { color: #1a1a2e; border-bottom: 2px solid #4361ee; padding-bottom: 10px; }
        h2 { color: #2d2d44; margin-top: 30px; }
        h3 { color: #4a4a6a; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; background: white; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #4361ee; color: white; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        .summary-grid {
            display: grid; grid-template-columns: repeat(4, 1fr);
            gap: 15px; margin: 20px 0;
        }
        .summary-card {
            background: white; padding: 20px; border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;
        }
        .summary-card .value { font-size: 2em; font-weight: bold; color: #4361ee; }
        .summary-card .label { color: #666; font-size: 0.9em; }
        .failure-item {
            padding: 10px 15px; margin: 10px 0; border-radius: 6px;
            background: white; border-left: 4px solid;
        }
        .failure-high { border-color: #dc2626; }
        .failure-medium { border-color: #f59e0b; }
        .failure-low { border-color: #10b981; }
        .recommendation {
            background: #e0f2fe; padding: 15px; border-radius: 6px; margin: 10px 0;
        }
        .no-data { color: #666; font-style: italic; }
        .footer {
            margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;
            color: #666; font-size: 0.9em;
        }
        .severity-badge {
            display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 0.8em; font-weight: bold;
        }
        .severity-high { background: #fee2e2; color: #dc2626; }
        .severity-medium { background: #fef3c7; color: #d97706; }
        .severity-low { background: #d1fae5; color: #059669; }
    """

    # Build HTML content
    html_parts: list[str] = []

    html_parts.append("<!DOCTYPE html>")
    html_parts.append('<html lang="en">')
    html_parts.append("<head>")
    html_parts.append('<meta charset="UTF-8">')
    html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_parts.append(f"<title>{data.title}</title>")
    html_parts.append(f"<style>{css}</style>")
    html_parts.append("</head>")
    html_parts.append("<body>")

    # Title
    html_parts.append(f"<h1>{data.title}</h1>")

    # Summary cards
    html_parts.append("<h2>Summary</h2>")
    html_parts.append('<div class="summary-grid">')
    for label, value in [
        ("Spans", data.analysis.total_spans),
        ("Conversations", data.analysis.total_conversations),
        ("Turns", data.analysis.total_turns),
        ("Failures", data.failures.failure_count),
    ]:
        html_parts.append('<div class="summary-card">')
        html_parts.append(f'<div class="value">{value}</div>')
        html_parts.append(f'<div class="label">{label}</div>')
        html_parts.append("</div>")
    html_parts.append("</div>")

    # Latency breakdown
    html_parts.append("<h2>Latency Breakdown</h2>")
    html_parts.append("<table>")
    html_parts.append(
        "<tr><th>Stage</th><th>Count</th><th>Mean (ms)</th>"
        "<th>p50 (ms)</th><th>p95 (ms)</th><th>p99 (ms)</th></tr>"
    )
    for name, metrics in [
        ("ASR", data.analysis.asr_metrics),
        ("LLM", data.analysis.llm_metrics),
        ("TTS", data.analysis.tts_metrics),
    ]:
        if metrics.count > 0:
            html_parts.append(
                f"<tr><td>{name}</td><td>{metrics.count}</td>"
                f"<td>{_format_ms(metrics.mean_ms)}</td>"
                f"<td>{_format_ms(metrics.p50_ms)}</td>"
                f"<td>{_format_ms(metrics.p95_ms)}</td>"
                f"<td>{_format_ms(metrics.p99_ms)}</td></tr>"
            )
        else:
            html_parts.append(
                f"<tr><td>{name}</td><td>0</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>"
            )
    html_parts.append("</table>")

    # Failures section
    html_parts.append("<h2>Failures</h2>")

    if data.failures.failure_count > 0:
        # By type table
        html_parts.append("<h3>By Type</h3>")
        html_parts.append("<table>")
        html_parts.append("<tr><th>Type</th><th>Count</th></tr>")
        for failure_type, failures in data.failures.failures_by_type.items():
            html_parts.append(f"<tr><td>{failure_type.value}</td><td>{len(failures)}</td></tr>")
        html_parts.append("</table>")

        # Detailed failures
        html_parts.append("<h3>Details</h3>")
        for failure in data.failures.failures:
            severity_class = f"failure-{failure.severity.value}"
            badge_class = f"severity-{failure.severity.value}"
            html_parts.append(f'<div class="failure-item {severity_class}">')
            severity_upper = failure.severity.value.upper()
            html_parts.append(
                f'<span class="severity-badge {badge_class}">{severity_upper}</span> '
                f"<strong>{failure.type.value}</strong>: {failure.message}"
            )
            html_parts.append("</div>")
    else:
        html_parts.append('<p class="no-data">No failures detected.</p>')

    # Semantic evaluation
    html_parts.append("<h2>Semantic Evaluation</h2>")
    eval_metrics = data.analysis.eval_metrics
    if eval_metrics.total_evals > 0:
        html_parts.append("<table>")
        html_parts.append("<tr><th>Metric</th><th>Value</th></tr>")
        html_parts.append(f"<tr><td>Evaluated turns</td><td>{eval_metrics.total_evals}</td></tr>")
        if eval_metrics.intent_correct_rate is not None:
            rate = eval_metrics.intent_correct_rate
            html_parts.append(f"<tr><td>Intent correct</td><td>{rate:.1f}%</td></tr>")
        if eval_metrics.avg_relevance_score is not None:
            score = eval_metrics.avg_relevance_score
            html_parts.append(f"<tr><td>Relevance (avg)</td><td>{score:.2f}</td></tr>")
        html_parts.append("</table>")
    else:
        html_parts.append(
            '<p class="no-data">No evaluation data available. '
            "Run semantic evaluation to generate eval records.</p>"
        )

    # Recommendations
    html_parts.append("<h2>Recommendations</h2>")
    recommendations = _generate_recommendations(data)
    for rec in recommendations:
        html_parts.append(f'<div class="recommendation">{rec}</div>')

    # Footer
    html_parts.append('<div class="footer">')
    html_parts.append(
        'Generated by <a href="https://github.com/voice-observation/voiceobs">voiceobs</a>'
    )
    html_parts.append("</div>")

    html_parts.append("</body>")
    html_parts.append("</html>")

    return "\n".join(html_parts)


def generate_report(
    data: ReportData,
    format: Literal["markdown", "html"] = "markdown",
) -> str:
    """Generate a report in the specified format.

    Args:
        data: ReportData containing analysis and failure results.
        format: Output format - "markdown" or "html".

    Returns:
        Formatted report string.

    Raises:
        ValueError: If format is not supported.
    """
    if format == "markdown":
        return generate_markdown_report(data)
    elif format == "html":
        return generate_html_report(data)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'markdown' or 'html'.")


def generate_report_from_file(
    file_path: str | Path,
    format: Literal["markdown", "html"] = "markdown",
    title: str | None = None,
) -> str:
    """Generate a report from a JSONL file.

    Args:
        file_path: Path to the JSONL file.
        format: Output format - "markdown" or "html".
        title: Optional custom title for the report.

    Returns:
        Formatted report string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    analysis = analyze_file(path)
    failures = classify_file(path)

    data = ReportData(
        analysis=analysis,
        failures=failures,
        title=title or "voiceobs Analysis Report",
    )

    return generate_report(data, format=format)
