"""Tests for the TestSuiteRepository class."""

from datetime import datetime
from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.test_suite import TestSuiteRepository

from .conftest import MockRecord


class TestTestSuiteRepository:
    """Tests for the TestSuiteRepository class."""

    @pytest.mark.asyncio
    async def test_create_suite_minimal(self, mock_db):
        """Test creating a test suite with minimal fields."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Test Suite",
                "description": None,
                "status": "pending",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.create(org_id=org_id, name="Test Suite", agent_id=agent_id)

        assert result.id == suite_id
        assert result.name == "Test Suite"
        assert result.description is None
        assert result.status == "pending"
        assert result.agent_id == agent_id
        assert result.test_scopes == ["core_flows", "common_mistakes"]
        assert result.thoroughness == 1
        assert result.edge_cases == []
        assert result.evaluation_strictness == "balanced"
        mock_db.execute.assert_called_once()
        assert "INSERT INTO test_suites" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_suite_with_description(self, mock_db):
        """Test creating a test suite with description."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Test Suite",
                "description": "Test description",
                "status": "pending",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.create(
            org_id=org_id,
            name="Test Suite",
            description="Test description",
            agent_id=agent_id,
        )

        assert result.id == suite_id
        assert result.name == "Test Suite"
        assert result.description == "Test description"
        assert result.status == "pending"
        assert result.agent_id == agent_id

    @pytest.mark.asyncio
    async def test_create_suite_failure(self, mock_db):
        """Test creating a test suite when fetchrow returns None."""
        repo = TestSuiteRepository(mock_db)
        mock_db.fetchrow.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create test suite"):
            await repo.create(org_id=uuid4(), name="Test Suite")

    @pytest.mark.asyncio
    async def test_get_suite_found(self, mock_db):
        """Test getting a test suite that exists."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Test Suite",
                "description": "Test description",
                "status": "pending",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows"],
                "thoroughness": 2,
                "edge_cases": ["hesitations"],
                "evaluation_strictness": "strict",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.get(suite_id, org_id)

        assert result is not None
        assert result.id == suite_id
        assert result.name == "Test Suite"
        assert result.description == "Test description"
        assert result.status == "pending"
        assert result.agent_id == agent_id
        assert result.test_scopes == ["core_flows"]
        assert result.thoroughness == 2
        assert result.edge_cases == ["hesitations"]
        assert result.evaluation_strictness == "strict"
        mock_db.fetchrow.assert_called_once()
        assert suite_id in mock_db.fetchrow.call_args[0]
        assert org_id in mock_db.fetchrow.call_args[0]

    @pytest.mark.asyncio
    async def test_get_suite_not_found(self, mock_db):
        """Test getting a test suite that doesn't exist."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        mock_db.fetchrow.return_value = None

        result = await repo.get(suite_id, uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_empty(self, mock_db):
        """Test listing all test suites when none exist."""
        repo = TestSuiteRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.list_all(org_id=uuid4())

        assert result == []
        mock_db.fetch.assert_called_once()
        assert "SELECT" in mock_db.fetch.call_args[0][0]
        assert "ORDER BY created_at DESC" in mock_db.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_all_multiple(self, mock_db):
        """Test listing all test suites with multiple results."""
        repo = TestSuiteRepository(mock_db)
        suite1_id = uuid4()
        suite2_id = uuid4()
        agent1_id = uuid4()
        agent2_id = uuid4()
        org_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": suite1_id,
                    "org_id": org_id,
                    "name": "Suite 1",
                    "description": "Description 1",
                    "status": "pending",
                    "generation_error": None,
                    "agent_id": agent1_id,
                    "test_scopes": ["core_flows", "common_mistakes"],
                    "thoroughness": 1,
                    "edge_cases": [],
                    "evaluation_strictness": "balanced",
                    "created_at": datetime.utcnow(),
                }
            ),
            MockRecord(
                {
                    "id": suite2_id,
                    "org_id": org_id,
                    "name": "Suite 2",
                    "description": "Description 2",
                    "status": "completed",
                    "generation_error": None,
                    "agent_id": agent2_id,
                    "test_scopes": ["safety_adversarial"],
                    "thoroughness": 2,
                    "edge_cases": ["adversarial"],
                    "evaluation_strictness": "strict",
                    "created_at": datetime.utcnow(),
                }
            ),
        ]

        result = await repo.list_all(org_id=org_id)

        assert len(result) == 2
        assert result[0].id == suite1_id
        assert result[0].name == "Suite 1"
        assert result[0].status == "pending"
        assert result[0].agent_id == agent1_id
        assert result[1].id == suite2_id
        assert result[1].name == "Suite 2"
        assert result[1].status == "completed"
        assert result[1].agent_id == agent2_id

    @pytest.mark.asyncio
    async def test_update_suite_name(self, mock_db):
        """Test updating a test suite's name."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        # Mock get() call after update
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Updated Suite",
                "description": "Original description",
                "status": "pending",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.update(suite_id, org_id, {"name": "Updated Suite"})

        assert result is not None
        assert result.name == "Updated Suite"
        mock_db.execute.assert_called_once()
        assert "UPDATE test_suites" in mock_db.execute.call_args[0][0]
        assert "name = $1" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_suite_description(self, mock_db):
        """Test updating a test suite's description."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Test Suite",
                "description": "Updated description",
                "status": "pending",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.update(suite_id, org_id, {"description": "Updated description"})

        assert result is not None
        assert result.description == "Updated description"
        assert "description = $1" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_suite_status(self, mock_db):
        """Test updating a test suite's status."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Test Suite",
                "description": "Description",
                "status": "running",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.update(suite_id, org_id, {"status": "running"})

        assert result is not None
        assert result.status == "running"
        assert "status = $1" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_suite_multiple_fields(self, mock_db):
        """Test updating multiple fields of a test suite."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Updated Suite",
                "description": "Updated description",
                "status": "completed",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.update(
            suite_id,
            org_id,
            {
                "name": "Updated Suite",
                "description": "Updated description",
                "status": "completed",
            },
        )

        assert result is not None
        assert result.name == "Updated Suite"
        assert result.description == "Updated description"
        assert result.status == "completed"
        # Should have multiple SET clauses
        update_query = mock_db.execute.call_args[0][0]
        assert "name = $" in update_query
        assert "description = $" in update_query
        assert "status = $" in update_query

    @pytest.mark.asyncio
    async def test_update_suite_no_changes(self, mock_db):
        """Test updating a test suite with no changes."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        agent_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": suite_id,
                "org_id": org_id,
                "name": "Test Suite",
                "description": "Description",
                "status": "pending",
                "generation_error": None,
                "agent_id": agent_id,
                "test_scopes": ["core_flows", "common_mistakes"],
                "thoroughness": 1,
                "edge_cases": [],
                "evaluation_strictness": "balanced",
                "created_at": datetime.utcnow(),
            }
        )

        result = await repo.update(suite_id, org_id, {})

        assert result is not None
        # Should call get() but not execute()
        mock_db.fetchrow.assert_called()
        # execute should not be called when no updates
        assert not hasattr(mock_db.execute, "call_count") or mock_db.execute.call_count == 0

    @pytest.mark.asyncio
    async def test_update_suite_not_found(self, mock_db):
        """Test updating a test suite that doesn't exist."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        org_id = uuid4()

        # First call for update, second call for get()
        mock_db.fetchrow.side_effect = [None]

        result = await repo.update(suite_id, org_id, {"name": "Updated"})

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_suite_success(self, mock_db):
        """Test successfully deleting a test suite."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        org_id = uuid4()
        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(suite_id, org_id)

        assert result is True
        mock_db.execute.assert_called_once()
        assert "DELETE FROM test_suites" in mock_db.execute.call_args[0][0]
        assert suite_id in mock_db.execute.call_args[0]

    @pytest.mark.asyncio
    async def test_delete_suite_not_found(self, mock_db):
        """Test deleting a test suite that doesn't exist."""
        repo = TestSuiteRepository(mock_db)
        suite_id = uuid4()
        org_id = uuid4()
        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(suite_id, org_id)

        assert result is False
