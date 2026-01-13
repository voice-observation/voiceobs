"""Tests for the TestExecutionRepository class."""

from datetime import datetime
from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.test_execution import TestExecutionRepository

from .conftest import MockRecord


class TestTestExecutionRepository:
    """Tests for the TestExecutionRepository class."""

    @pytest.mark.asyncio
    async def test_create_execution_minimal(self, mock_db):
        """Test creating a test execution with minimal fields."""
        repo = TestExecutionRepository(mock_db)
        execution_id = uuid4()
        scenario_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": execution_id,
                "scenario_id": scenario_id,
                "conversation_id": None,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "result_json": {},
            }
        )

        result = await repo.create(scenario_id=scenario_id)

        assert result.id == execution_id
        assert result.scenario_id == scenario_id
        assert result.conversation_id is None
        assert result.status == "pending"
        assert result.started_at is None
        assert result.completed_at is None
        assert result.result_json == {}
        mock_db.execute.assert_called_once()
        assert "INSERT INTO test_executions" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_execution_with_conversation(self, mock_db):
        """Test creating a test execution with conversation ID."""
        repo = TestExecutionRepository(mock_db)
        execution_id = uuid4()
        scenario_id = uuid4()
        conversation_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": execution_id,
                "scenario_id": scenario_id,
                "conversation_id": conversation_id,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "result_json": {},
            }
        )

        result = await repo.create(scenario_id=scenario_id, conversation_id=conversation_id)

        assert result.id == execution_id
        assert result.scenario_id == scenario_id
        assert result.conversation_id == conversation_id
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_create_execution_with_status_running(self, mock_db):
        """Test creating a test execution with running status sets started_at."""
        repo = TestExecutionRepository(mock_db)
        execution_id = uuid4()
        scenario_id = uuid4()
        started_at = datetime.utcnow()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": execution_id,
                "scenario_id": scenario_id,
                "conversation_id": None,
                "status": "running",
                "started_at": started_at,
                "completed_at": None,
                "result_json": {},
            }
        )

        result = await repo.create(scenario_id=scenario_id, status="running")

        assert result.id == execution_id
        assert result.status == "running"
        # started_at should be set when status is running
        assert "running" in mock_db.execute.call_args[0]

    @pytest.mark.asyncio
    async def test_create_execution_failure(self, mock_db):
        """Test creating a test execution when fetchrow returns None."""
        repo = TestExecutionRepository(mock_db)
        scenario_id = uuid4()
        mock_db.fetchrow.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create test execution"):
            await repo.create(scenario_id=scenario_id)

    @pytest.mark.asyncio
    async def test_get_execution_found(self, mock_db):
        """Test getting a test execution that exists."""
        repo = TestExecutionRepository(mock_db)
        execution_id = uuid4()
        scenario_id = uuid4()
        conversation_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": execution_id,
                "scenario_id": scenario_id,
                "conversation_id": conversation_id,
                "status": "completed",
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "result_json": {"passed": True, "avg_latency_ms": 150.5},
            }
        )

        result = await repo.get(execution_id)

        assert result is not None
        assert result.id == execution_id
        assert result.scenario_id == scenario_id
        assert result.conversation_id == conversation_id
        assert result.status == "completed"
        assert result.result_json == {"passed": True, "avg_latency_ms": 150.5}

    @pytest.mark.asyncio
    async def test_get_execution_not_found(self, mock_db):
        """Test getting a test execution that doesn't exist."""
        repo = TestExecutionRepository(mock_db)
        execution_id = uuid4()
        mock_db.fetchrow.return_value = None

        result = await repo.get(execution_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_execution_with_null_result_json(self, mock_db):
        """Test getting a test execution with null result_json defaults to empty dict."""
        repo = TestExecutionRepository(mock_db)
        execution_id = uuid4()
        scenario_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": execution_id,
                "scenario_id": scenario_id,
                "conversation_id": None,
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "result_json": None,
            }
        )

        result = await repo.get(execution_id)

        assert result is not None
        assert result.result_json == {}

    @pytest.mark.asyncio
    async def test_get_summary_no_suite_id(self, mock_db):
        """Test getting summary statistics without suite filter."""
        repo = TestExecutionRepository(mock_db)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": 10,
                    "passed": 7,
                    "failed": 3,
                    "avg_duration_ms": 5000.5,
                    "avg_latency_ms": 150.2,
                }
            )
        ]

        result = await repo.get_summary()

        assert result["total"] == 10
        assert result["passed"] == 7
        assert result["failed"] == 3
        assert result["pass_rate"] == 0.7
        assert result["avg_duration_ms"] == 5000.5
        assert result["avg_latency_ms"] == 150.2
        mock_db.fetch.assert_called_once()
        # Should not have JOIN clause when no suite_id
        query = mock_db.fetch.call_args[0][0]
        assert "JOIN test_scenarios" not in query

    @pytest.mark.asyncio
    async def test_get_summary_with_suite_id(self, mock_db):
        """Test getting summary statistics with suite filter."""
        repo = TestExecutionRepository(mock_db)
        suite_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": 5,
                    "passed": 4,
                    "failed": 1,
                    "avg_duration_ms": 3000.0,
                    "avg_latency_ms": 120.5,
                }
            )
        ]

        result = await repo.get_summary(suite_id=suite_id)

        assert result["total"] == 5
        assert result["passed"] == 4
        assert result["failed"] == 1
        assert result["pass_rate"] == 0.8
        assert result["avg_duration_ms"] == 3000.0
        assert result["avg_latency_ms"] == 120.5
        # Should have JOIN clause when suite_id is provided
        query = mock_db.fetch.call_args[0][0]
        assert "JOIN test_scenarios" in query
        assert suite_id in mock_db.fetch.call_args[0]

    @pytest.mark.asyncio
    async def test_get_summary_empty_results(self, mock_db):
        """Test getting summary when no executions exist."""
        repo = TestExecutionRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.get_summary()

        assert result["total"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["pass_rate"] is None
        assert result["avg_duration_ms"] is None
        assert result["avg_latency_ms"] is None

    @pytest.mark.asyncio
    async def test_get_summary_null_total(self, mock_db):
        """Test getting summary when total is None."""
        repo = TestExecutionRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": None,
                    "passed": None,
                    "failed": None,
                    "avg_duration_ms": None,
                    "avg_latency_ms": None,
                }
            )
        ]

        result = await repo.get_summary()

        assert result["total"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["pass_rate"] is None
        assert result["avg_duration_ms"] is None
        assert result["avg_latency_ms"] is None

    @pytest.mark.asyncio
    async def test_get_summary_zero_total(self, mock_db):
        """Test getting summary when total is 0."""
        repo = TestExecutionRepository(mock_db)
        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "avg_duration_ms": None,
                    "avg_latency_ms": None,
                }
            )
        ]

        result = await repo.get_summary()

        assert result["total"] == 0
        assert result["passed"] == 0
        assert result["failed"] == 0
        assert result["pass_rate"] is None

    @pytest.mark.asyncio
    async def test_get_summary_with_null_avg_values(self, mock_db):
        """Test getting summary with null average values."""
        repo = TestExecutionRepository(mock_db)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": 5,
                    "passed": 3,
                    "failed": 2,
                    "avg_duration_ms": None,
                    "avg_latency_ms": None,
                }
            )
        ]

        result = await repo.get_summary()

        assert result["total"] == 5
        assert result["passed"] == 3
        assert result["failed"] == 2
        assert result["pass_rate"] == 0.6
        assert result["avg_duration_ms"] is None
        assert result["avg_latency_ms"] is None

    @pytest.mark.asyncio
    async def test_get_summary_all_passed(self, mock_db):
        """Test getting summary when all tests passed."""
        repo = TestExecutionRepository(mock_db)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": 10,
                    "passed": 10,
                    "failed": 0,
                    "avg_duration_ms": 2000.0,
                    "avg_latency_ms": 100.0,
                }
            )
        ]

        result = await repo.get_summary()

        assert result["total"] == 10
        assert result["passed"] == 10
        assert result["failed"] == 0
        assert result["pass_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_summary_all_failed(self, mock_db):
        """Test getting summary when all tests failed."""
        repo = TestExecutionRepository(mock_db)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "total": 5,
                    "passed": 0,
                    "failed": 5,
                    "avg_duration_ms": 1000.0,
                    "avg_latency_ms": 200.0,
                }
            )
        ]

        result = await repo.get_summary()

        assert result["total"] == 5
        assert result["passed"] == 0
        assert result["failed"] == 5
        assert result["pass_rate"] == 0.0
