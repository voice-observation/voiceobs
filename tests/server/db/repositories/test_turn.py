"""Tests for the TurnRepository class."""

from uuid import UUID, uuid4

import pytest

from voiceobs.server.db.models import TurnRow
from voiceobs.server.db.repositories import TurnRepository

from .conftest import MockRecord


class TestTurnRepository:
    """Tests for the TurnRepository class."""

    @pytest.mark.asyncio
    async def test_add_turn(self, mock_db):
        """Test adding a turn."""
        repo = TurnRepository(mock_db)
        conv_id = uuid4()
        span_id = uuid4()

        turn_id = await repo.add(
            conversation_id=conv_id,
            span_id=span_id,
            actor="user",
            turn_index=1,
        )

        assert isinstance(turn_id, UUID)
        mock_db.execute.assert_called_once()
        assert "INSERT INTO turns" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_add_turn_with_all_fields(self, mock_db):
        """Test adding a turn with all fields."""
        repo = TurnRepository(mock_db)
        conv_id = uuid4()
        span_id = uuid4()

        turn_id = await repo.add(
            conversation_id=conv_id,
            span_id=span_id,
            actor="agent",
            turn_id="ext-turn-123",
            turn_index=2,
            duration_ms=500.0,
            transcript="Hello, how can I help?",
            attributes={"custom": "attr"},
        )

        assert isinstance(turn_id, UUID)
        call_args = mock_db.execute.call_args[0]
        assert call_args[2] == "ext-turn-123"
        assert call_args[5] == "agent"
        assert call_args[6] == 2
        assert call_args[7] == 500.0
        assert call_args[8] == "Hello, how can I help?"

    @pytest.mark.asyncio
    async def test_get_turn(self, mock_db):
        """Test getting a turn by UUID."""
        repo = TurnRepository(mock_db)
        turn_id = uuid4()
        conv_id = uuid4()
        span_id = uuid4()
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": turn_id,
                "turn_id": "ext-turn-123",
                "conversation_id": conv_id,
                "span_id": span_id,
                "actor": "user",
                "turn_index": 1,
                "duration_ms": 100.0,
                "transcript": "Hello",
                "attributes": {},
                "created_at": None,
            }
        )

        result = await repo.get(turn_id)

        assert result is not None
        assert isinstance(result, TurnRow)
        assert result.id == turn_id
        assert result.actor == "user"

    @pytest.mark.asyncio
    async def test_get_turn_not_found(self, mock_db):
        """Test getting a non-existent turn."""
        repo = TurnRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_conversation(self, mock_db):
        """Test getting turns by conversation."""
        repo = TurnRepository(mock_db)
        conv_id = uuid4()
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "turn_id": "turn-1",
                    "conversation_id": conv_id,
                    "span_id": uuid4(),
                    "actor": "user",
                    "turn_index": 1,
                    "duration_ms": 100.0,
                    "transcript": "Hi",
                    "attributes": {},
                    "created_at": None,
                }
            ),
            MockRecord(
                {
                    "id": uuid4(),
                    "turn_id": "turn-2",
                    "conversation_id": conv_id,
                    "span_id": uuid4(),
                    "actor": "agent",
                    "turn_index": 2,
                    "duration_ms": 200.0,
                    "transcript": "Hello!",
                    "attributes": {},
                    "created_at": None,
                }
            ),
        ]

        result = await repo.get_by_conversation(conv_id)

        assert len(result) == 2
        assert all(isinstance(t, TurnRow) for t in result)

    @pytest.mark.asyncio
    async def test_clear_turns(self, mock_db):
        """Test clearing all turns."""
        repo = TurnRepository(mock_db)
        mock_db.fetchval.return_value = 8

        count = await repo.clear()

        assert count == 8
        mock_db.execute.assert_called_once_with("DELETE FROM turns")

    @pytest.mark.asyncio
    async def test_count_turns(self, mock_db):
        """Test counting turns."""
        repo = TurnRepository(mock_db)
        mock_db.fetchval.return_value = 15

        count = await repo.count()

        assert count == 15
