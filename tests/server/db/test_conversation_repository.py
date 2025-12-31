"""Tests for the ConversationRepository class."""

from uuid import UUID, uuid4

import pytest

from voiceobs.server.db.models import ConversationRow
from voiceobs.server.db.repositories import ConversationRepository

from .conftest import MockRecord


class TestConversationRepository:
    """Tests for the ConversationRepository class."""

    @pytest.mark.asyncio
    async def test_get_or_create_existing(self, mock_db):
        """Test get_or_create returns existing conversation."""
        repo = ConversationRepository(mock_db)
        existing_id = uuid4()
        mock_db.fetchrow.return_value = MockRecord({
            "id": existing_id,
            "conversation_id": "conv-123",
            "created_at": None,
            "updated_at": None,
        })

        result = await repo.get_or_create("conv-123")

        assert result.id == existing_id
        assert result.conversation_id == "conv-123"
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_new(self, mock_db):
        """Test get_or_create creates new conversation."""
        repo = ConversationRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get_or_create("new-conv-123")

        assert isinstance(result.id, UUID)
        assert result.conversation_id == "new-conv-123"
        mock_db.execute.assert_called_once()
        assert "INSERT INTO conversations" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_conversation(self, mock_db):
        """Test getting a conversation by UUID."""
        repo = ConversationRepository(mock_db)
        conv_id = uuid4()
        mock_db.fetchrow.return_value = MockRecord({
            "id": conv_id,
            "conversation_id": "conv-123",
            "created_at": None,
            "updated_at": None,
        })

        result = await repo.get(conv_id)

        assert result is not None
        assert result.id == conv_id

    @pytest.mark.asyncio
    async def test_get_conversation_not_found(self, mock_db):
        """Test getting a non-existent conversation."""
        repo = ConversationRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_external_id(self, mock_db):
        """Test getting a conversation by external ID."""
        repo = ConversationRepository(mock_db)
        conv_id = uuid4()
        mock_db.fetchrow.return_value = MockRecord({
            "id": conv_id,
            "conversation_id": "ext-conv-123",
            "created_at": None,
            "updated_at": None,
        })

        result = await repo.get_by_external_id("ext-conv-123")

        assert result is not None
        assert result.conversation_id == "ext-conv-123"

    @pytest.mark.asyncio
    async def test_get_all_conversations(self, mock_db):
        """Test getting all conversations."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({
                "id": uuid4(),
                "conversation_id": "conv-1",
                "created_at": None,
                "updated_at": None,
            }),
            MockRecord({
                "id": uuid4(),
                "conversation_id": "conv-2",
                "created_at": None,
                "updated_at": None,
            }),
        ]

        result = await repo.get_all()

        assert len(result) == 2
        assert all(isinstance(c, ConversationRow) for c in result)

    @pytest.mark.asyncio
    async def test_get_summary(self, mock_db):
        """Test getting conversation summaries."""
        repo = ConversationRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord({
                "id": uuid4(),
                "conversation_id": "conv-1",
                "span_count": 10,
                "turn_count": 5,
                "has_failures": False,
            }),
        ]

        result = await repo.get_summary()

        assert len(result) == 1
        assert result[0]["id"] == "conv-1"
        assert result[0]["span_count"] == 10
        assert result[0]["turn_count"] == 5
        assert result[0]["has_failures"] is False

    @pytest.mark.asyncio
    async def test_clear_conversations(self, mock_db):
        """Test clearing all conversations."""
        repo = ConversationRepository(mock_db)
        mock_db.fetchval.return_value = 3

        count = await repo.clear()

        assert count == 3
        mock_db.execute.assert_called_once_with("DELETE FROM conversations")

    @pytest.mark.asyncio
    async def test_count_conversations(self, mock_db):
        """Test counting conversations."""
        repo = ConversationRepository(mock_db)
        mock_db.fetchval.return_value = 7

        count = await repo.count()

        assert count == 7
