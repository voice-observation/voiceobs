"""Tests for the SpanRepository class."""

from uuid import UUID, uuid4

import pytest

from voiceobs.server.db.models import SpanRow
from voiceobs.server.db.repositories import SpanRepository

from .conftest import MockRecord


class TestSpanRepository:
    """Tests for the SpanRepository class."""

    @pytest.mark.asyncio
    async def test_add_span(self, mock_db):
        """Test adding a span."""
        repo = SpanRepository(mock_db)

        span_id = await repo.add(
            name="voice.turn",
            duration_ms=100.0,
            attributes={"voice.actor": "user"},
        )

        assert isinstance(span_id, UUID)
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO spans" in call_args[0]
        assert call_args[2] == "voice.turn"

    @pytest.mark.asyncio
    async def test_add_span_with_all_fields(self, mock_db):
        """Test adding a span with all fields."""
        repo = SpanRepository(mock_db)
        conv_id = uuid4()

        span_id = await repo.add(
            name="voice.asr",
            start_time="2024-01-01T00:00:00Z",
            end_time="2024-01-01T00:00:01Z",
            duration_ms=1000.0,
            attributes={"voice.asr.confidence": 0.95},
            trace_id="trace123",
            span_id="span456",
            parent_span_id="parent789",
            conversation_id=conv_id,
        )

        assert isinstance(span_id, UUID)
        call_args = mock_db.execute.call_args[0]
        assert call_args[3] == "2024-01-01T00:00:00Z"
        assert call_args[4] == "2024-01-01T00:00:01Z"
        assert call_args[5] == 1000.0
        assert call_args[7] == "trace123"
        assert call_args[10] == conv_id

    @pytest.mark.asyncio
    async def test_get_span_found(self, mock_db):
        """Test getting an existing span."""
        repo = SpanRepository(mock_db)
        span_id = uuid4()
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": span_id,
                "name": "voice.turn",
                "start_time": None,
                "end_time": None,
                "duration_ms": 100.0,
                "attributes": {"key": "value"},
                "trace_id": "trace123",
                "span_id": "span456",
                "parent_span_id": None,
                "conversation_id": None,
                "created_at": None,
            }
        )

        result = await repo.get(span_id)

        assert result is not None
        assert isinstance(result, SpanRow)
        assert result.id == span_id
        assert result.name == "voice.turn"
        assert result.duration_ms == 100.0
        assert result.attributes == {"key": "value"}

    @pytest.mark.asyncio
    async def test_get_span_not_found(self, mock_db):
        """Test getting a non-existent span."""
        repo = SpanRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_all_spans(self, mock_db):
        """Test getting all spans."""
        repo = SpanRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "name": "span1",
                    "start_time": None,
                    "end_time": None,
                    "duration_ms": 100.0,
                    "attributes": {},
                    "trace_id": None,
                    "span_id": None,
                    "parent_span_id": None,
                    "conversation_id": None,
                    "created_at": None,
                }
            ),
            MockRecord(
                {
                    "id": uuid4(),
                    "name": "span2",
                    "start_time": None,
                    "end_time": None,
                    "duration_ms": 200.0,
                    "attributes": {},
                    "trace_id": None,
                    "span_id": None,
                    "parent_span_id": None,
                    "conversation_id": None,
                    "created_at": None,
                }
            ),
        ]

        result = await repo.get_all()

        assert len(result) == 2
        assert all(isinstance(s, SpanRow) for s in result)

    @pytest.mark.asyncio
    async def test_get_spans_as_dicts(self, mock_db):
        """Test getting spans as dictionaries."""
        repo = SpanRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "name": "voice.turn",
                    "duration_ms": 100.0,
                    "attributes": {"voice.actor": "user"},
                }
            ),
        ]

        result = await repo.get_as_dicts()

        assert len(result) == 1
        assert result[0]["name"] == "voice.turn"
        assert result[0]["duration_ms"] == 100.0
        assert result[0]["attributes"] == {"voice.actor": "user"}

    @pytest.mark.asyncio
    async def test_get_by_conversation(self, mock_db):
        """Test getting spans by conversation."""
        repo = SpanRepository(mock_db)
        conv_id = uuid4()
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "name": "voice.turn",
                    "start_time": None,
                    "end_time": None,
                    "duration_ms": 100.0,
                    "attributes": {},
                    "trace_id": None,
                    "span_id": None,
                    "parent_span_id": None,
                    "conversation_id": conv_id,
                    "created_at": None,
                }
            ),
        ]

        result = await repo.get_by_conversation(conv_id)

        assert len(result) == 1
        mock_db.fetch.assert_called_once()
        assert conv_id in mock_db.fetch.call_args[0]

    @pytest.mark.asyncio
    async def test_clear_spans(self, mock_db):
        """Test clearing all spans."""
        repo = SpanRepository(mock_db)
        mock_db.fetchval.return_value = 5

        count = await repo.clear()

        assert count == 5
        mock_db.execute.assert_called_once_with("DELETE FROM spans")

    @pytest.mark.asyncio
    async def test_count_spans(self, mock_db):
        """Test counting spans."""
        repo = SpanRepository(mock_db)
        mock_db.fetchval.return_value = 10

        count = await repo.count()

        assert count == 10
