"""Tests for voiceobs exporters."""

import json
import os
from unittest.mock import patch

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from voiceobs import JSONLSpanExporter
from voiceobs.exporters import get_jsonl_exporter_from_env


class TestJSONLSpanExporter:
    """Tests for JSONLSpanExporter class."""

    def test_creates_empty_file_on_init(self, tmp_path):
        """Test that exporter creates an empty file on initialization."""
        file_path = tmp_path / "spans.jsonl"
        JSONLSpanExporter(str(file_path))  # Side effect: creates file

        assert file_path.exists()
        assert file_path.read_text() == ""

    def test_truncates_existing_file_on_init(self, tmp_path):
        """Test that exporter truncates existing files."""
        file_path = tmp_path / "spans.jsonl"
        file_path.write_text("old content\n")

        JSONLSpanExporter(str(file_path))  # Side effect: truncates file

        assert file_path.read_text() == ""

    def test_force_flush_returns_true(self, tmp_path):
        """Test that force_flush returns True."""
        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        assert exporter.force_flush() is True

    def test_shutdown_does_not_raise(self, tmp_path):
        """Test that shutdown completes without error."""
        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        # Should not raise
        exporter.shutdown()

    def test_export_returns_failure_on_write_error(self, tmp_path):
        """Test that export returns FAILURE when write fails."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        # Create a span to export
        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            pass

        # Patch open to simulate write failure
        with patch("builtins.open", side_effect=OSError("Disk full")):
            # Create a mock span to export
            mock_span = span
            result = exporter.export([mock_span])

            assert result == SpanExportResult.FAILURE


class TestGetJSONLExporterFromEnv:
    """Tests for get_jsonl_exporter_from_env function."""

    def test_returns_none_when_env_not_set(self):
        """Test that None is returned when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Make sure env var is not set
            os.environ.pop("VOICEOBS_JSONL_OUT", None)
            exporter = get_jsonl_exporter_from_env()
            assert exporter is None

    def test_returns_exporter_when_env_set(self, tmp_path):
        """Test that exporter is returned when env var is set."""
        file_path = tmp_path / "test.jsonl"
        with patch.dict(os.environ, {"VOICEOBS_JSONL_OUT": str(file_path)}):
            exporter = get_jsonl_exporter_from_env()
            assert exporter is not None
            assert isinstance(exporter, JSONLSpanExporter)


class TestJSONLExportIntegration:
    """Integration tests for JSONL export with voice spans."""

    def test_exports_spans_to_jsonl_file(self, tmp_path):
        """Test that spans are exported to JSONL file."""

        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        # Create a fresh provider with our exporter
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer("test")

        # Create some spans
        with tracer.start_as_current_span("voice.conversation") as conv_span:
            conv_span.set_attribute("voice.conversation.id", "test-123")
            with tracer.start_as_current_span("voice.turn") as turn_span:
                turn_span.set_attribute("voice.actor", "user")

        # Read and parse the JSONL file
        content = file_path.read_text().strip()
        assert content, "File should not be empty"

        lines = content.split("\n")
        assert len(lines) == 2  # conversation + turn

        # Verify each line is valid JSON
        for line in lines:
            span_data = json.loads(line)
            assert "name" in span_data
            assert "trace_id" in span_data
            assert "span_id" in span_data
            assert "attributes" in span_data

    def test_jsonl_span_has_required_fields(self, tmp_path):
        """Test that exported spans have all required fields."""

        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("voice.turn") as span:
            span.set_attribute("voice.actor", "user")
            span.set_attribute("voice.turn.id", "turn-456")

        content = file_path.read_text().strip()
        lines = content.split("\n")
        turn_span = json.loads(lines[0])

        # Check required fields
        assert "name" in turn_span
        assert turn_span["name"] == "voice.turn"
        assert "trace_id" in turn_span
        assert "span_id" in turn_span
        assert "start_time_ns" in turn_span
        assert "end_time_ns" in turn_span
        assert "duration_ms" in turn_span
        assert "attributes" in turn_span
        assert "status" in turn_span
        assert "events" in turn_span

        # Check voice-specific attributes
        assert "voice.actor" in turn_span["attributes"]
        assert turn_span["attributes"]["voice.actor"] == "user"

    def test_jsonl_includes_parent_span_id(self, tmp_path):
        """Test that child spans have parent_span_id."""

        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("voice.conversation") as conv_span:
            with tracer.start_as_current_span("voice.turn") as turn_span:
                pass

        content = file_path.read_text().strip()
        lines = content.split("\n")
        spans = [json.loads(line) for line in lines]

        # Find conversation and turn spans
        conv_span = next(s for s in spans if s["name"] == "voice.conversation")
        turn_span = next(s for s in spans if s["name"] == "voice.turn")

        # Turn should have conversation as parent
        assert turn_span["parent_span_id"] == conv_span["span_id"]

    def test_multiple_traces_in_same_file(self, tmp_path):
        """Test that multiple traces are written to the same file."""

        file_path = tmp_path / "spans.jsonl"
        exporter = JSONLSpanExporter(str(file_path))

        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer("test")

        # First trace
        with tracer.start_as_current_span("voice.conversation"):
            with tracer.start_as_current_span("voice.turn"):
                pass

        # Second trace
        with tracer.start_as_current_span("voice.conversation"):
            with tracer.start_as_current_span("voice.turn"):
                pass

        content = file_path.read_text().strip()
        lines = content.split("\n")

        # Should have 4 spans (2 conversations + 2 turns)
        assert len(lines) == 4

        # Verify we have multiple trace_ids
        trace_ids = set()
        for line in lines:
            span_data = json.loads(line)
            trace_ids.add(span_data["trace_id"])

        assert len(trace_ids) == 2
