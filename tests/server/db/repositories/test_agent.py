"""Tests for the AgentRepository class."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from voiceobs.server.db.models import AgentRow
from voiceobs.server.db.repositories.agent import AgentRepository

from .conftest import MockRecord


class TestAgentRepository:
    """Tests for the AgentRepository class."""

    @pytest.mark.asyncio
    async def test_create_agent_minimal(self, mock_db):
        """Test creating an agent with minimal required fields."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": {"phone_number": "+1234567890"},
                "supported_intents": [],
                "connection_status": "saved",
                "verification_attempts": 0,
                "last_verification_at": None,
                "verification_error": None,
                "verification_transcript": None,
                "verification_reasoning": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.create(
            name="Test Agent",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            goal="Test goal",
            supported_intents=[],
        )

        assert result.id == agent_id
        assert result.name == "Test Agent"
        assert result.agent_type == "phone"
        assert result.connection_status == "saved"
        assert result.verification_transcript is None
        assert result.verification_reasoning is None
        mock_db.execute.assert_called_once()
        assert "INSERT INTO agents" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_phone_agent_missing_phone_number(self, mock_db):
        """Test creating a phone agent without phone_number raises error."""
        repo = AgentRepository(mock_db)

        with pytest.raises(ValueError, match="phone_number"):
            await repo.create(
                name="Test Agent",
                agent_type="phone",
                contact_info={},  # Missing phone_number
                goal="Test goal",
                supported_intents=[],
            )

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_agent_database_failure(self, mock_db):
        """Test creating an agent when database fails to return the created row."""
        repo = AgentRepository(mock_db)

        mock_db.fetchrow.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create agent"):
            await repo.create(
                name="Test Agent",
                agent_type="phone",
                contact_info={"phone_number": "+1234567890"},
                goal="Test goal",
                supported_intents=[],
            )

        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_agent(self, mock_db):
        """Test getting an agent by UUID."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": {"phone_number": "+1234567890"},
                "supported_intents": ["intent1"],
                "connection_status": "verified",
                "verification_attempts": 1,
                "last_verification_at": datetime.now(timezone.utc),
                "verification_error": None,
                "verification_transcript": [
                    {"role": "assistant", "content": "Hello"},
                    {"role": "user", "content": "Hi there"},
                ],
                "verification_reasoning": "Agent responded correctly to test prompts",
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.get(agent_id)

        assert result is not None
        assert result.id == agent_id
        assert result.name == "Test Agent"
        assert result.verification_transcript == [
            {"role": "assistant", "content": "Hello"},
            {"role": "user", "content": "Hi there"},
        ]
        assert result.verification_reasoning == "Agent responded correctly to test prompts"

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, mock_db):
        """Test getting a non-existent agent."""
        repo = AgentRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_agents(self, mock_db):
        """Test listing all agents."""
        repo = AgentRepository(mock_db)
        agent1_id = uuid4()
        agent2_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": agent1_id,
                    "name": "Agent 1",
                    "goal": "Goal 1",
                    "agent_type": "phone",
                    "contact_info": {"phone_number": "+1111111111"},
                    "supported_intents": [],
                    "connection_status": "saved",
                    "verification_attempts": 0,
                    "last_verification_at": None,
                    "verification_error": None,
                    "verification_transcript": None,
                    "verification_reasoning": None,
                    "metadata": {},
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                    "is_active": True,
                }
            ),
            MockRecord(
                {
                    "id": agent2_id,
                    "name": "Agent 2",
                    "goal": "Goal 2",
                    "agent_type": "web",
                    "contact_info": {"web_url": "https://example.com"},
                    "supported_intents": ["intent1"],
                    "connection_status": "verified",
                    "verification_attempts": 1,
                    "last_verification_at": None,
                    "verification_error": None,
                    "verification_transcript": [{"role": "assistant", "content": "Test"}],
                    "verification_reasoning": "Verified successfully",
                    "metadata": {},
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                    "is_active": True,
                }
            ),
        ]

        result = await repo.list_all()

        assert len(result) == 2
        assert all(isinstance(a, AgentRow) for a in result)
        assert result[0].verification_transcript is None
        assert result[1].verification_transcript == [{"role": "assistant", "content": "Test"}]
        assert result[1].verification_reasoning == "Verified successfully"

    @pytest.mark.asyncio
    async def test_list_all_with_filters(self, mock_db):
        """Test listing agents with filters."""
        repo = AgentRepository(mock_db)
        mock_db.fetch.return_value = []

        await repo.list_all(connection_status="verified", is_active=True, limit=10, offset=5)

        sql = mock_db.fetch.call_args[0][0]
        assert "connection_status = $1" in sql
        assert "is_active = $2" in sql
        assert "LIMIT $3" in sql
        assert "OFFSET $4" in sql

    @pytest.mark.asyncio
    async def test_update_agent_verification_fields(self, mock_db):
        """Test updating verification transcript and reasoning fields."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()
        transcript = [
            {"role": "assistant", "content": "Hello, how can I help?"},
            {"role": "user", "content": "I need support"},
        ]
        reasoning = "Agent correctly identified as support agent"

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": {"phone_number": "+1234567890"},
                "supported_intents": [],
                "connection_status": "verified",
                "verification_attempts": 1,
                "last_verification_at": datetime.now(timezone.utc),
                "verification_error": None,
                "verification_transcript": transcript,
                "verification_reasoning": reasoning,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.update(
            agent_id,
            verification_transcript=transcript,
            verification_reasoning=reasoning,
        )

        assert result is not None
        assert result.verification_transcript == transcript
        assert result.verification_reasoning == reasoning
        mock_db.execute.assert_called_once()
        sql = mock_db.execute.call_args[0][0]
        assert "verification_transcript" in sql
        assert "verification_reasoning" in sql

    @pytest.mark.asyncio
    async def test_update_agent_no_changes(self, mock_db):
        """Test update with no fields to update."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": {"phone_number": "+1234567890"},
                "supported_intents": [],
                "connection_status": "saved",
                "verification_attempts": 0,
                "last_verification_at": None,
                "verification_error": None,
                "verification_transcript": None,
                "verification_reasoning": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.update(agent_id)

        assert result is not None
        assert mock_db.fetchrow.called
        assert not mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_with_status_and_verification_fields(self, mock_db):
        """Test update with status and verification transcript and reasoning."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()
        now = datetime.now(timezone.utc)
        transcript = [{"role": "assistant", "content": "Test message"}]
        reasoning = "Verification successful"

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": {"phone_number": "+1234567890"},
                "supported_intents": [],
                "connection_status": "verified",
                "verification_attempts": 1,
                "last_verification_at": now,
                "verification_error": None,
                "verification_transcript": transcript,
                "verification_reasoning": reasoning,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.update(
            agent_id,
            connection_status="verified",
            verification_attempts=1,
            last_verification_at=now,
            verification_transcript=transcript,
            verification_reasoning=reasoning,
        )

        assert result is not None
        assert result.connection_status == "verified"
        assert result.verification_transcript == transcript
        assert result.verification_reasoning == reasoning
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_row_to_agent_with_string_transcript(self, mock_db):
        """Test _row_to_agent handles string verification_transcript (JSONB from asyncpg)."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": '{"phone_number": "+1234567890"}',  # JSON string
                "supported_intents": "[]",  # JSON string
                "connection_status": "verified",
                "verification_attempts": 1,
                "last_verification_at": None,
                "verification_error": None,
                # JSON string (as asyncpg might return it)
                "verification_transcript": '[{"role": "assistant", "content": "Hello"}]',
                "verification_reasoning": "Test reasoning",
                "metadata": "{}",  # JSON string
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.get(agent_id)

        assert result is not None
        assert result.contact_info == {"phone_number": "+1234567890"}
        assert result.supported_intents == []
        assert result.verification_transcript == [{"role": "assistant", "content": "Hello"}]
        assert result.verification_reasoning == "Test reasoning"
        assert result.metadata == {}

    @pytest.mark.asyncio
    async def test_row_to_agent_with_none_fields(self, mock_db):
        """Test _row_to_agent handles None fields correctly."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": None,
                "supported_intents": None,
                "connection_status": "saved",
                "verification_attempts": 0,
                "last_verification_at": None,
                "verification_error": None,
                "verification_transcript": None,
                "verification_reasoning": None,
                "metadata": None,
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.get(agent_id)

        assert result is not None
        assert result.contact_info == {}
        assert result.supported_intents == []
        assert result.verification_transcript is None
        assert result.verification_reasoning is None
        assert result.metadata == {}

    @pytest.mark.asyncio
    async def test_delete(self, mock_db):
        """Test deleting an agent."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()
        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(agent_id)

        assert result is True
        mock_db.execute.assert_called_once()
        sql = mock_db.execute.call_args[0][0]
        assert "DELETE FROM agents" in sql

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db):
        """Test deleting a non-existent agent."""
        repo = AgentRepository(mock_db)
        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_count_active(self, mock_db):
        """Test counting active agents (default)."""
        repo = AgentRepository(mock_db)
        mock_db.fetchval.return_value = 5

        count = await repo.count()

        assert count == 5
        sql = mock_db.fetchval.call_args[0][0]
        assert "COUNT(*)" in sql
        assert "WHERE is_active = $1" in sql

    @pytest.mark.asyncio
    async def test_count_all(self, mock_db):
        """Test counting all agents."""
        repo = AgentRepository(mock_db)
        mock_db.fetchval.return_value = 10

        count = await repo.count(is_active=None)

        assert count == 10
        sql = mock_db.fetchval.call_args[0][0]
        assert "COUNT(*)" in sql
        assert "WHERE is_active" not in sql

    @pytest.mark.asyncio
    async def test_update_to_pending_retry_status(self, mock_db):
        """Test update can set pending_retry status with verification fields."""
        repo = AgentRepository(mock_db)
        agent_id = uuid4()
        now = datetime.now(timezone.utc)
        transcript = [
            {"role": "assistant", "content": "Hello, this is support."},
            {"role": "user", "content": "I need help with my order."},
        ]
        reasoning = "Call dropped unexpectedly, will retry verification"

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": agent_id,
                "name": "Test Agent",
                "goal": "Test goal",
                "agent_type": "phone",
                "contact_info": {"phone_number": "+1234567890"},
                "supported_intents": [],
                "connection_status": "pending_retry",
                "verification_attempts": 1,
                "last_verification_at": now,
                "verification_error": None,
                "verification_transcript": transcript,
                "verification_reasoning": reasoning,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.update(
            agent_id,
            connection_status="pending_retry",
            verification_attempts=1,
            last_verification_at=now,
            verification_transcript=transcript,
            verification_reasoning=reasoning,
        )

        assert result is not None
        assert result.connection_status == "pending_retry"
        assert result.verification_attempts == 1
        assert result.verification_transcript == transcript
        assert result.verification_reasoning == reasoning
        mock_db.execute.assert_called_once()
        sql = mock_db.execute.call_args[0][0]
        assert "connection_status" in sql
        assert "verification_transcript" in sql
        assert "verification_reasoning" in sql
