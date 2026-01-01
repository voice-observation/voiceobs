"""Span exporters for voiceobs.

This module provides custom span exporters for voiceobs, including
JSONL export for local analysis.
"""

from __future__ import annotations

import json
import threading
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


class JSONLSpanExporter(SpanExporter):
    """Exports spans to a JSONL file (one JSON object per line).

    This exporter writes spans to a file in JSONL format, which is easy
    to parse and analyze. Each line contains a complete JSON object with
    span information.

    Args:
        file_path: Path to the output JSONL file. Will be created if it
            doesn't exist, or appended to if it does.

    Example:
        from voiceobs.exporters import JSONLSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        exporter = JSONLSpanExporter("spans.jsonl")
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
    """

    def __init__(self, file_path: str) -> None:
        self._file_path = file_path
        self._lock = threading.Lock()
        # Create/truncate the file on initialization
        with open(self._file_path, "w"):
            pass  # Just create/truncate the file

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to the JSONL file.

        Args:
            spans: Sequence of spans to export.

        Returns:
            SpanExportResult.SUCCESS if export succeeded.
        """
        try:
            with self._lock:
                with open(self._file_path, "a") as f:
                    for span in spans:
                        span_data = self._span_to_dict(span)
                        f.write(json.dumps(span_data) + "\n")
            return SpanExportResult.SUCCESS
        except Exception:
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        pass  # Nothing to clean up

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending spans.

        Args:
            timeout_millis: Timeout in milliseconds (unused).

        Returns:
            True always, as we flush after each export.
        """
        return True

    def _span_to_dict(self, span: ReadableSpan) -> dict:
        """Convert a span to a dictionary for JSON serialization.

        Args:
            span: The span to convert.

        Returns:
            Dictionary representation of the span.
        """
        # Get context info
        context = span.get_span_context()

        # Build the span dictionary
        span_dict = {
            "name": span.name,
            "trace_id": format(context.trace_id, "032x"),
            "span_id": format(context.span_id, "016x"),
            "parent_span_id": (format(span.parent.span_id, "016x") if span.parent else None),
            "start_time_ns": span.start_time,
            "end_time_ns": span.end_time,
            "duration_ms": (
                (span.end_time - span.start_time) / 1_000_000
                if span.end_time and span.start_time
                else None
            ),
            "status": {
                "status_code": span.status.status_code.name,
                "description": span.status.description,
            },
            "attributes": dict(span.attributes) if span.attributes else {},
            "events": [
                {
                    "name": event.name,
                    "timestamp_ns": event.timestamp,
                    "attributes": dict(event.attributes) if event.attributes else {},
                }
                for event in span.events
            ],
            "kind": span.kind.name if span.kind else None,
        }

        return span_dict


def get_jsonl_exporter_from_config() -> JSONLSpanExporter | None:
    """Get a JSONL exporter if enabled in config.

    Reads the voiceobs configuration and creates a JSONLSpanExporter
    if exporters.jsonl.enabled is True.

    Returns:
        JSONLSpanExporter if enabled in config, None otherwise.

    Example:
        # In voiceobs.yaml:
        # exporters:
        #   jsonl:
        #     enabled: true
        #     path: "./traces.jsonl"

        # In Python:
        exporter = get_jsonl_exporter_from_config()
        if exporter:
            provider.add_span_processor(BatchSpanProcessor(exporter))
    """
    from voiceobs.config import get_config

    config = get_config()
    if config.exporters.jsonl.enabled:
        return JSONLSpanExporter(config.exporters.jsonl.path)
    return None
