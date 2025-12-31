"""In-memory span store for the voiceobs server.

This provides temporary storage for spans before database persistence is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any
from uuid import UUID, uuid4


@dataclass
class StoredSpan:
    """A span stored in memory."""

    id: UUID
    name: str
    start_time: str | None
    end_time: str | None
    duration_ms: float | None
    attributes: dict[str, Any]
    trace_id: str | None
    span_id: str | None
    parent_span_id: str | None


class SpanStore:
    """Thread-safe in-memory span storage.

    This is a temporary implementation until PostgreSQL persistence is added.
    """

    def __init__(self) -> None:
        """Initialize the span store."""
        self._spans: dict[UUID, StoredSpan] = {}
        self._lock = Lock()

    def add_span(
        self,
        name: str,
        start_time: str | None = None,
        end_time: str | None = None,
        duration_ms: float | None = None,
        attributes: dict[str, Any] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> UUID:
        """Add a span to the store.

        Args:
            name: Span name.
            start_time: Start time as ISO 8601 string.
            end_time: End time as ISO 8601 string.
            duration_ms: Duration in milliseconds.
            attributes: Span attributes.
            trace_id: OpenTelemetry trace ID.
            span_id: OpenTelemetry span ID.
            parent_span_id: Parent span ID.

        Returns:
            The UUID of the stored span.
        """
        span_uuid = uuid4()
        stored_span = StoredSpan(
            id=span_uuid,
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            attributes=attributes or {},
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
        )

        with self._lock:
            self._spans[span_uuid] = stored_span

        return span_uuid

    def get_span(self, span_id: UUID) -> StoredSpan | None:
        """Get a span by ID.

        Args:
            span_id: The span UUID.

        Returns:
            The stored span, or None if not found.
        """
        with self._lock:
            return self._spans.get(span_id)

    def get_all_spans(self) -> list[StoredSpan]:
        """Get all stored spans.

        Returns:
            List of all stored spans.
        """
        with self._lock:
            return list(self._spans.values())

    def get_spans_as_dicts(self) -> list[dict[str, Any]]:
        """Get all stored spans as dictionaries (for analysis).

        Returns:
            List of span dictionaries compatible with analyzer.
        """
        with self._lock:
            return [
                {
                    "name": span.name,
                    "duration_ms": span.duration_ms,
                    "attributes": span.attributes,
                }
                for span in self._spans.values()
            ]

    def clear(self) -> int:
        """Clear all stored spans.

        Returns:
            Number of spans cleared.
        """
        with self._lock:
            count = len(self._spans)
            self._spans.clear()
            return count

    def count(self) -> int:
        """Get the number of stored spans.

        Returns:
            Number of spans in store.
        """
        with self._lock:
            return len(self._spans)


# Global span store instance
_span_store: SpanStore | None = None


def get_span_store() -> SpanStore:
    """Get the global span store instance.

    Returns:
        The span store singleton.
    """
    global _span_store
    if _span_store is None:
        _span_store = SpanStore()
    return _span_store


def reset_span_store() -> None:
    """Reset the global span store (for testing)."""
    global _span_store
    _span_store = None
