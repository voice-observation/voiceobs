"""Tests for ExecutionOrchestrationService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import (
    TestExecutionRow,
    TestScenarioRow,
    TestSuiteRunRow,
)
from voiceobs.server.services.execution.service import ExecutionOrchestrationService


class TestExecutionOrchestrationService:
    """Tests for ExecutionOrchestrationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_suite_run_repo = AsyncMock()
        self.mock_execution_repo = AsyncMock()
        self.mock_scenario_repo = AsyncMock()
        self.mock_execution_client = MagicMock()

        self.service = ExecutionOrchestrationService(
            suite_run_repo=self.mock_suite_run_repo,
            execution_repo=self.mock_execution_repo,
            scenario_repo=self.mock_scenario_repo,
            execution_client=self.mock_execution_client,
        )

    @pytest.mark.asyncio
    async def test_trigger_suite_run_success(self):
        """Test triggering a suite run creates records and enqueues."""
        org_id = uuid4()
        suite_id = uuid4()
        triggered_by = "user-123"

        scenario1 = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            org_id=org_id,
            name="Scenario 1",
            goal="Goal 1",
            persona_id=uuid4(),
        )
        scenario2 = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            org_id=org_id,
            name="Scenario 2",
            goal="Goal 2",
            persona_id=uuid4(),
        )

        suite_run = TestSuiteRunRow(
            id=uuid4(),
            org_id=org_id,
            suite_id=suite_id,
            status="pending",
            total_scenarios=2,
            created_at=datetime.utcnow(),
        )

        exec1 = TestExecutionRow(
            id=uuid4(),
            org_id=org_id,
            suite_run_id=suite_run.id,
            scenario_id=scenario1.id,
        )
        exec2 = TestExecutionRow(
            id=uuid4(),
            org_id=org_id,
            suite_run_id=suite_run.id,
            scenario_id=scenario2.id,
        )

        self.mock_scenario_repo.list_all.return_value = [scenario1, scenario2]
        self.mock_suite_run_repo.create.return_value = suite_run
        self.mock_execution_repo.create.side_effect = [exec1, exec2]
        self.mock_execution_client.enqueue_batch.return_value = []

        result = await self.service.trigger_suite_run(
            org_id=org_id,
            suite_id=suite_id,
            triggered_by=triggered_by,
        )

        assert result.suite_run_id == suite_run.id
        assert result.total_scenarios == 2
        self.mock_suite_run_repo.create.assert_called_once_with(
            org_id=org_id,
            suite_id=suite_id,
            total_scenarios=2,
            triggered_by=triggered_by,
        )
        assert self.mock_execution_repo.create.call_count == 2
        self.mock_execution_client.enqueue_batch.assert_called_once_with([exec1.id, exec2.id])
        self.mock_suite_run_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_scenario_run_success(self):
        """Test triggering a single scenario run."""
        org_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()
        triggered_by = "user-123"

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            org_id=org_id,
            name="Single scenario",
            goal="Test goal",
            persona_id=uuid4(),
        )

        suite_run = TestSuiteRunRow(
            id=uuid4(),
            org_id=org_id,
            suite_id=suite_id,
            status="pending",
            total_scenarios=1,
            created_at=datetime.utcnow(),
        )

        execution = TestExecutionRow(
            id=uuid4(),
            org_id=org_id,
            suite_run_id=suite_run.id,
            scenario_id=scenario_id,
        )

        self.mock_scenario_repo.get.return_value = scenario
        self.mock_suite_run_repo.create.return_value = suite_run
        self.mock_execution_repo.create.return_value = execution
        self.mock_execution_client.enqueue_batch.return_value = []

        result = await self.service.trigger_scenario_run(
            org_id=org_id,
            scenario_id=scenario_id,
            triggered_by=triggered_by,
        )

        assert result.suite_run_id == suite_run.id
        assert result.total_scenarios == 1
        self.mock_execution_client.enqueue_batch.assert_called_once_with([execution.id])
        self.mock_suite_run_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_scenario_run_scenario_not_found(self):
        """Test trigger_scenario_run raises when scenario not found."""
        self.mock_scenario_repo.get.return_value = None

        with pytest.raises(ValueError, match="Scenario .* not found"):
            await self.service.trigger_scenario_run(
                org_id=uuid4(),
                scenario_id=uuid4(),
                triggered_by="user",
            )
