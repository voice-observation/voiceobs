"""Tests for OTLP exporter."""

from unittest.mock import MagicMock, patch

import pytest

from voiceobs.config import (
    ExporterOtlpConfig,
    ExportersConfig,
    VoiceobsConfig,
)


@pytest.fixture
def mock_otlp_grpc():
    """Mock the gRPC OTLP exporter."""
    with patch(
        "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter"
    ) as mock_exporter_class:
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = None
        mock_exporter.shutdown.return_value = None
        mock_exporter_class.return_value = mock_exporter
        yield mock_exporter


@pytest.fixture
def mock_otlp_http():
    """Mock the HTTP OTLP exporter."""
    with patch(
        "opentelemetry.exporter.otlp.proto.http.trace_exporter.OTLPSpanExporter"
    ) as mock_exporter_class:
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = None
        mock_exporter.shutdown.return_value = None
        mock_exporter_class.return_value = mock_exporter
        yield mock_exporter


class TestOTLPSpanExporter:
    """Tests for OTLPSpanExporter class."""

    def test_creates_grpc_exporter_by_default(self, mock_otlp_grpc):
        """Test that gRPC exporter is created by default."""
        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint="http://localhost:4317", protocol="grpc")

        assert exporter._protocol == "grpc"
        assert exporter._endpoint == "http://localhost:4317"

    def test_creates_http_exporter_when_specified(self, mock_otlp_http):
        """Test that HTTP exporter is created when protocol is http/protobuf."""
        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(endpoint="http://localhost:4318", protocol="http/protobuf")

        assert exporter._protocol == "http/protobuf"
        assert exporter._endpoint == "http://localhost:4318"

    def test_raises_error_on_unsupported_protocol(self):
        """Test that unsupported protocol raises ValueError."""
        from voiceobs.exporters.otlp import OTLPSpanExporter

        with pytest.raises(ValueError, match="Unsupported protocol"):
            OTLPSpanExporter(protocol="unsupported")

    def test_raises_error_when_dependencies_missing(self):
        """Test that missing dependencies raise ImportError."""
        with patch(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter",
            side_effect=ImportError("Module not found"),
        ):
            from voiceobs.exporters.otlp import OTLPSpanExporter

            with pytest.raises(ImportError, match="OTLP exporter dependencies not installed"):
                OTLPSpanExporter()

    def test_sets_headers(self, mock_otlp_grpc):
        """Test that headers are passed to the underlying exporter."""
        from voiceobs.exporters.otlp import OTLPSpanExporter

        headers = {"Authorization": "Bearer token", "X-Custom": "value"}
        exporter = OTLPSpanExporter(headers=headers)

        # Check that headers were stored
        assert exporter._headers == headers

    def test_batches_spans(self, mock_otlp_grpc):
        """Test that spans are batched before export."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=3, batch_timeout_ms=10000)
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        # Create spans
        spans = []
        for i in range(2):
            with tracer.start_as_current_span(f"span.{i}") as span:
                spans.append(span)

        # Export - should not flush yet (batch size is 3, we have 2)
        result = exporter.export(spans)
        assert result == SpanExportResult.SUCCESS
        mock_otlp_grpc.export.assert_not_called()

        # Add one more span - should flush now
        with tracer.start_as_current_span("span.2") as span:
            result = exporter.export([span])
        assert result == SpanExportResult.SUCCESS
        assert mock_otlp_grpc.export.call_count == 1

    def test_flushes_on_timeout(self, mock_otlp_grpc):
        """Test that batch flushes when timeout is reached."""
        import time

        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=100, batch_timeout_ms=100)
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("span.1") as span:
            exporter.export([span])

        # Wait for timeout
        time.sleep(0.15)

        # Export another span to trigger flush check
        with tracer.start_as_current_span("span.2") as span:
            exporter.export([span])

        # Should have flushed
        assert mock_otlp_grpc.export.call_count >= 1

    def test_retries_on_failure(self, mock_otlp_grpc):
        """Test that exporter retries on failure with exponential backoff."""

        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=1, max_retries=2)
        # First two calls fail, third succeeds
        mock_otlp_grpc.export.side_effect = [
            SpanExportResult.FAILURE,
            SpanExportResult.FAILURE,
            SpanExportResult.SUCCESS,
        ]

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            result = exporter.export([span])

        # Should have retried and eventually succeeded
        assert result == SpanExportResult.SUCCESS
        assert mock_otlp_grpc.export.call_count == 3

    def test_returns_failure_after_max_retries(self, mock_otlp_grpc):
        """Test that exporter returns failure after max retries."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=1, max_retries=2)
        mock_otlp_grpc.export.return_value = SpanExportResult.FAILURE

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            result = exporter.export([span])

        # Should have failed after all retries
        assert result == SpanExportResult.FAILURE
        assert mock_otlp_grpc.export.call_count == 3  # Initial + 2 retries

    def test_handles_exceptions_during_export(self, mock_otlp_grpc):
        """Test that exceptions during export are handled with retries."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=1, max_retries=1)
        # First call raises exception, second succeeds
        mock_otlp_grpc.export.side_effect = [
            ConnectionError("Connection failed"),
            SpanExportResult.SUCCESS,
        ]

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            result = exporter.export([span])

        # Should succeed after retry
        assert result == SpanExportResult.SUCCESS
        assert mock_otlp_grpc.export.call_count == 2

    def test_shutdown_flushes_pending_spans(self, mock_otlp_grpc):
        """Test that shutdown flushes any pending spans."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=100)
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            exporter.export([span])

        # Shutdown should flush
        exporter.shutdown()

        assert mock_otlp_grpc.export.call_count == 1
        mock_otlp_grpc.shutdown.assert_called_once()

    def test_force_flush_returns_true_when_successful(self, mock_otlp_grpc):
        """Test that force_flush returns True when successful."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter()
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            exporter.export([span])

        result = exporter.force_flush()
        assert result is True

    def test_force_flush_returns_false_on_failure(self, mock_otlp_grpc):
        """Test that force_flush returns False on failure."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        # Use batch_size > 1 so export doesn't flush immediately
        exporter = OTLPSpanExporter(batch_size=10, max_retries=0)
        mock_otlp_grpc.export.return_value = SpanExportResult.FAILURE

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            exporter.export([span])

        # Now force_flush should try to flush the batch and fail
        result = exporter.force_flush()
        assert result is False

    def test_export_empty_spans_returns_success(self, mock_otlp_grpc):
        """Test that exporting empty span list returns success."""
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter()
        result = exporter.export([])

        assert result == SpanExportResult.SUCCESS
        mock_otlp_grpc.export.assert_not_called()

    def test_converts_spans(self, mock_otlp_grpc):
        """Test that spans are converted before export."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=1)
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("test.span") as span:
            span.set_attribute("test.attr", "value")
            result = exporter.export([span])

        assert result == SpanExportResult.SUCCESS
        # Verify that export was called with spans
        assert mock_otlp_grpc.export.call_count == 1
        call_args = mock_otlp_grpc.export.call_args[0][0]
        assert len(call_args) == 1


class TestGetOTLPExporterFromConfig:
    """Tests for get_otlp_exporter_from_config function."""

    def test_returns_none_when_disabled(self):
        """Test that None is returned when OTLP export is disabled."""
        from unittest.mock import patch

        from voiceobs.exporters.otlp import get_otlp_exporter_from_config

        config = VoiceobsConfig(exporters=ExportersConfig(otlp=ExporterOtlpConfig(enabled=False)))
        with patch("voiceobs.config.get_config", return_value=config):
            exporter = get_otlp_exporter_from_config()
            assert exporter is None

    def test_returns_exporter_when_enabled(self, mock_otlp_grpc):
        """Test that exporter is returned when OTLP export is enabled."""
        from unittest.mock import patch

        from voiceobs.exporters.otlp import get_otlp_exporter_from_config

        config = VoiceobsConfig(
            exporters=ExportersConfig(
                otlp=ExporterOtlpConfig(
                    enabled=True,
                    endpoint="http://localhost:4317",
                    protocol="grpc",
                    headers={"Authorization": "Bearer token"},
                )
            )
        )
        with patch("voiceobs.config.get_config", return_value=config):
            exporter = get_otlp_exporter_from_config()
            assert exporter is not None
            assert exporter._endpoint == "http://localhost:4317"
            assert exporter._protocol == "grpc"
            assert exporter._headers == {"Authorization": "Bearer token"}

    def test_uses_config_values(self, mock_otlp_grpc):
        """Test that config values are used correctly."""
        from unittest.mock import patch

        from voiceobs.exporters.otlp import get_otlp_exporter_from_config

        config = VoiceobsConfig(
            exporters=ExportersConfig(
                otlp=ExporterOtlpConfig(
                    enabled=True,
                    endpoint="http://custom:4318",
                    protocol="http/protobuf",
                    batch_size=256,
                    batch_timeout_ms=3000,
                    max_retries=5,
                )
            )
        )
        with patch("voiceobs.config.get_config", return_value=config):
            exporter = get_otlp_exporter_from_config()
            assert exporter is not None
            assert exporter._endpoint == "http://custom:4318"
            assert exporter._protocol == "http/protobuf"
            assert exporter._batch_size == 256
            assert exporter._batch_timeout_ms == 3000
            assert exporter._max_retries == 5


class TestOTLPIntegration:
    """Integration tests for OTLP export."""

    def test_exports_voice_spans(self, mock_otlp_grpc):
        """Test that voice spans are exported correctly."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=1)
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        # Create a voice conversation span
        with tracer.start_as_current_span("voice.conversation") as conv_span:
            conv_span.set_attribute("voice.conversation.id", "test-123")
            with tracer.start_as_current_span("voice.turn") as turn_span:
                turn_span.set_attribute("voice.actor", "user")
                turn_span.set_attribute("voice.turn.id", "turn-456")

                # Export
                result = exporter.export([turn_span])

        assert result == SpanExportResult.SUCCESS
        assert mock_otlp_grpc.export.call_count == 1

    def test_preserves_custom_attributes(self, mock_otlp_grpc):
        """Test that custom voiceobs attributes are preserved."""
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SpanExportResult

        from voiceobs.exporters.otlp import OTLPSpanExporter

        exporter = OTLPSpanExporter(batch_size=1)
        mock_otlp_grpc.export.return_value = SpanExportResult.SUCCESS

        provider = TracerProvider()
        tracer = provider.get_tracer("test")

        with tracer.start_as_current_span("voice.turn") as span:
            span.set_attribute("voice.actor", "user")
            span.set_attribute("custom.attr", "custom.value")
            span.set_attribute("voice.custom", "value")

            result = exporter.export([span])

        assert result == SpanExportResult.SUCCESS
        # Verify attributes were passed through
        call_args = mock_otlp_grpc.export.call_args[0][0]
        exported_span = call_args[0]
        assert exported_span.attributes.get("voice.actor") == "user"
        assert exported_span.attributes.get("custom.attr") == "custom.value"
        assert exported_span.attributes.get("voice.custom") == "value"
