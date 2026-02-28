"""Tests for TestSuiteRunRepository."""

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import TestSuiteRunRow
from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository


class TestTestSuiteRunRepository:
    """Tests for TestSuiteRunRepository."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = AsyncMock()
        self.repo = TestSuiteRunRepository(self.mock_db)

    @pytest.mark.asyncio
    async def test_create(self):
        """Test creating a suite run."""
        org_id = uuid4()
        suite_id = uuid4()
        run_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": suite_id,
            "status": "pending",
            "total_scenarios": 5,
            "completed_scenarios": 0,
            "failed_scenarios": 0,
            "triggered_by": "user-123",
            "started_at": None,
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.create(
            org_id=org_id,
            suite_id=suite_id,
            total_scenarios=5,
            triggered_by="user-123",
        )

        assert isinstance(result, TestSuiteRunRow)
        assert result.id == run_id
        assert result.status == "pending"
        assert result.total_scenarios == 5
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get(self):
        """Test fetching a suite run by ID."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 3,
            "failed_scenarios": 1,
            "triggered_by": "user-123",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.get(run_id, org_id)
        assert result is not None
        assert result.id == run_id
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        """Test fetching a non-existent suite run."""
        self.mock_db.fetchrow.return_value = None
        result = await self.repo.get(uuid4(), uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_update(self):
        """Test updating suite run fields."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 5,
            "failed_scenarios": 0,
            "triggered_by": "user-123",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.update(
            run_id, org_id, {"status": "running", "completed_scenarios": 5}
        )
        assert result is not None
        assert result.status == "running"

    @pytest.mark.asyncio
    async def test_increment_completed(self):
        """Test incrementing completed_scenarios counter."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 6,
            "failed_scenarios": 0,
            "triggered_by": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.increment_completed(run_id, org_id)
        assert result is not None
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_failed(self):
        """Test incrementing failed_scenarios counter."""
        run_id = uuid4()
        org_id = uuid4()

        self.mock_db.fetchrow.return_value = {
            "id": run_id,
            "org_id": org_id,
            "suite_id": uuid4(),
            "status": "running",
            "total_scenarios": 10,
            "completed_scenarios": 5,
            "failed_scenarios": 2,
            "triggered_by": None,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "created_at": datetime.utcnow(),
        }

        result = await self.repo.increment_failed(run_id, org_id)
        assert result is not None
        self.mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_by_suite(self):
        """Test listing suite runs for a suite."""
        org_id = uuid4()
        suite_id = uuid4()

        self.mock_db.fetch.return_value = [
            {
                "id": uuid4(),
                "org_id": org_id,
                "suite_id": suite_id,
                "status": "completed",
                "total_scenarios": 5,
                "completed_scenarios": 5,
                "failed_scenarios": 0,
                "triggered_by": "user-123",
                "started_at": datetime.utcnow(),
                "completed_at": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }
        ]

        result = await self.repo.list_by_suite(org_id, suite_id)
        assert len(result) == 1
        assert result[0].status == "completed"
