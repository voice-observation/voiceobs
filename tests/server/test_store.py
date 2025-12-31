"""Tests for the SpanStore class."""

from uuid import uuid4


class TestSpanStore:
    """Tests for the SpanStore class."""

    def test_add_and_get_span(self, span_store):
        """Test adding and retrieving a span."""
        span_id = span_store.add_span(
            name="test.span",
            duration_ms=100.0,
            attributes={"key": "value"},
        )

        span = span_store.get_span(span_id)

        assert span is not None
        assert span.name == "test.span"
        assert span.duration_ms == 100.0
        assert span.attributes == {"key": "value"}

    def test_get_nonexistent_span(self, span_store):
        """Test getting a span that doesn't exist."""
        result = span_store.get_span(uuid4())
        assert result is None

    def test_get_all_spans(self, span_store):
        """Test getting all spans."""
        span_store.add_span(name="span1", attributes={})
        span_store.add_span(name="span2", attributes={})
        span_store.add_span(name="span3", attributes={})

        spans = span_store.get_all_spans()

        assert len(spans) == 3

    def test_get_spans_as_dicts(self, span_store):
        """Test getting spans as dictionaries."""
        span_store.add_span(
            name="voice.turn",
            duration_ms=500.0,
            attributes={"voice.actor": "agent"},
        )

        dicts = span_store.get_spans_as_dicts()

        assert len(dicts) == 1
        assert dicts[0]["name"] == "voice.turn"
        assert dicts[0]["duration_ms"] == 500.0
        assert dicts[0]["attributes"] == {"voice.actor": "agent"}

    def test_clear_spans(self, span_store):
        """Test clearing all spans."""
        span_store.add_span(name="span1", attributes={})
        span_store.add_span(name="span2", attributes={})

        count = span_store.clear()

        assert count == 2
        assert span_store.count() == 0

    def test_count_spans(self, span_store):
        """Test counting spans."""
        assert span_store.count() == 0

        span_store.add_span(name="span1", attributes={})
        assert span_store.count() == 1

        span_store.add_span(name="span2", attributes={})
        assert span_store.count() == 2
