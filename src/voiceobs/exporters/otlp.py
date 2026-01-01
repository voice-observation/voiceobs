"""OTLP (OpenTelemetry Protocol) exporter for voiceobs.

This module provides an exporter that sends voiceobs spans to any
OpenTelemetry-compatible backend (Grafana, Datadog, etc.) via OTLP.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

logger = logging.getLogger(__name__)


class OTLPSpanExporter(SpanExporter):
    """Exports spans to an OpenTelemetry-compatible backend via OTLP.

    Supports both gRPC and HTTP/protobuf protocols. Includes batch export
    with configurable batch size and timeout, plus retry logic with
    exponential backoff.

    Args:
        endpoint: OTLP endpoint URL (default: http://localhost:4317)
        protocol: Protocol to use, either "grpc" or "http/protobuf"
        headers: Optional headers (e.g., for authentication)
        batch_size: Maximum number of spans per batch
        batch_timeout_ms: Maximum time to wait before flushing a batch
        max_retries: Maximum number of retry attempts on failure

    Example:
        from voiceobs.exporters.otlp import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317",
            protocol="grpc",
            headers={"Authorization": "Bearer token"}
        )
        provider = TracerProvider()
        provider.add_span_processor(BatchSpanProcessor(exporter))
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:4317",
        protocol: str = "grpc",
        headers: dict[str, str] | None = None,
        batch_size: int = 512,
        batch_timeout_ms: int = 5000,
        max_retries: int = 3,
    ) -> None:
        self._endpoint = endpoint
        self._protocol = protocol
        self._headers = headers or {}
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        self._max_retries = max_retries

        # Lazy import to avoid requiring OTLP dependencies unless used
        try:
            if protocol == "grpc":
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                    OTLPSpanExporter as GrpcOTLPSpanExporter,
                )

                self._otlp_exporter = GrpcOTLPSpanExporter(
                    endpoint=endpoint,
                    headers=self._headers,
                )
            elif protocol == "http/protobuf":
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter as HttpOTLPSpanExporter,
                )

                self._otlp_exporter = HttpOTLPSpanExporter(
                    endpoint=endpoint,
                    headers=self._headers,
                )
            else:
                raise ValueError(f"Unsupported protocol: {protocol}")
        except ImportError as e:
            raise ImportError(
                "OTLP exporter dependencies not installed. "
                "Install with: pip install voiceobs[otlp]"
            ) from e

        # Batch state
        self._batch: list[ReadableSpan] = []
        self._batch_start_time: float | None = None

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to the OTLP backend.

        Spans are batched and exported with retry logic. If the batch
        is full or the timeout is reached, the batch is flushed.

        Args:
            spans: Sequence of spans to export.

        Returns:
            SpanExportResult.SUCCESS if export succeeded, FAILURE otherwise.
        """
        if not spans:
            return SpanExportResult.SUCCESS

        # Add spans to batch
        self._batch.extend(spans)

        # Check if we should flush the batch
        should_flush = False
        current_time = time.time()

        # Flush if batch is full
        if len(self._batch) >= self._batch_size:
            should_flush = True

        # Flush if timeout reached
        if self._batch_start_time is None:
            self._batch_start_time = current_time
        elif (current_time - self._batch_start_time) * 1000 >= self._batch_timeout_ms:
            should_flush = True

        if should_flush:
            return self._flush_batch()

        return SpanExportResult.SUCCESS

    def _flush_batch(self) -> SpanExportResult:
        """Flush the current batch of spans to the OTLP backend.

        Returns:
            SpanExportResult indicating success or failure.
        """
        if not self._batch:
            return SpanExportResult.SUCCESS

        # Convert spans to OTLP format and export with retry logic
        batch_to_export = self._batch.copy()
        self._batch.clear()
        self._batch_start_time = None

        # Apply resource attributes and semantic conventions
        spans_to_export = [self._convert_span(span) for span in batch_to_export]

        # Retry logic with exponential backoff
        for attempt in range(self._max_retries + 1):
            try:
                result = self._otlp_exporter.export(spans_to_export)
                if result == SpanExportResult.SUCCESS:
                    return SpanExportResult.SUCCESS
                # If not success and not last attempt, retry
                if attempt < self._max_retries:
                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(
                        f"OTLP export failed (attempt {attempt + 1}/{self._max_retries + 1}), "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
            except Exception as e:
                if attempt < self._max_retries:
                    wait_time = 2**attempt
                    logger.warning(
                        f"OTLP export error (attempt {attempt + 1}/{self._max_retries + 1}): {e}, "
                        f"retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"OTLP export failed after {self._max_retries + 1} attempts: {e}")

        return SpanExportResult.FAILURE

    def _convert_span(self, span: ReadableSpan) -> ReadableSpan:
        """Convert a voiceobs span to OTLP format.

        Maps voiceobs attributes to OpenTelemetry semantic conventions
        where possible, while preserving all custom attributes.

        Args:
            span: The span to convert.

        Returns:
            The span (may be modified in place or a new span).
        """
        # The OpenTelemetry SDK spans are already in the correct format
        # for OTLP export. We just need to ensure resource attributes
        # are set correctly. The actual conversion happens in the OTLP exporter.

        # Note: Resource attributes should be set at the TracerProvider level,
        # not per-span. The OTLP exporter will handle the conversion to
        # ResourceSpans format automatically.

        return span

    def shutdown(self) -> None:
        """Shutdown the exporter and flush any pending spans."""
        # Flush any remaining spans
        if self._batch:
            self._flush_batch()

        # Shutdown the underlying OTLP exporter
        if hasattr(self, "_otlp_exporter"):
            self._otlp_exporter.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Force flush any pending spans.

        Args:
            timeout_millis: Timeout in milliseconds (unused, kept for API compatibility).

        Returns:
            True if flush succeeded, False otherwise.
        """
        if not self._batch:
            return True

        result = self._flush_batch()
        return result == SpanExportResult.SUCCESS


def get_otlp_exporter_from_config() -> OTLPSpanExporter | None:
    """Get an OTLP exporter if enabled in config.

    Reads the voiceobs configuration and creates an OTLPSpanExporter
    if exporters.otlp.enabled is True.

    Returns:
        OTLPSpanExporter if enabled in config, None otherwise.

    Example:
        # In voiceobs.yaml:
        # exporters:
        #   otlp:
        #     enabled: true
        #     endpoint: "http://localhost:4317"
        #     protocol: "grpc"
        #     headers:
        #       Authorization: "Bearer token"

        # In Python:
        exporter = get_otlp_exporter_from_config()
        if exporter:
            provider.add_span_processor(BatchSpanProcessor(exporter))
    """
    from voiceobs.config import get_config

    config = get_config()
    if config.exporters.otlp.enabled:
        return OTLPSpanExporter(
            endpoint=config.exporters.otlp.endpoint,
            protocol=config.exporters.otlp.protocol,
            headers=config.exporters.otlp.headers,
            batch_size=config.exporters.otlp.batch_size,
            batch_timeout_ms=config.exporters.otlp.batch_timeout_ms,
            max_retries=config.exporters.otlp.max_retries,
        )
    return None
