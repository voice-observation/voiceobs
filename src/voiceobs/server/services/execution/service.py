"""Execution orchestration service for triggering suite and scenario runs."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from voiceobs.server.models import TriggerResult

if TYPE_CHECKING:
    from voiceobs.server.clients.sqs import ExecutionQueueClient
    from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
    from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
    from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository

logger = logging.getLogger(__name__)


class ExecutionOrchestrationService:
    """Orchestrates creation of suite runs and execution records with SQS enqueue."""

    def __init__(
        self,
        suite_run_repo: TestSuiteRunRepository,
        execution_repo: TestExecutionRepository,
        scenario_repo: TestScenarioRepository,
        execution_client: ExecutionQueueClient,
    ) -> None:
        """Initialize the execution orchestration service."""
        self._suite_run_repo = suite_run_repo
        self._execution_repo = execution_repo
        self._scenario_repo = scenario_repo
        self._execution_client = execution_client

    async def trigger_suite_run(
        self,
        org_id: UUID,
        suite_id: UUID,
        triggered_by: str | None = None,
    ) -> TriggerResult:
        """Trigger execution of all ready scenarios in a suite."""
        scenarios = await self._scenario_repo.list_all(
            org_id=org_id, suite_id=suite_id, status="ready"
        )

        suite_run = await self._suite_run_repo.create(
            org_id=org_id,
            suite_id=suite_id,
            total_scenarios=len(scenarios),
            triggered_by=triggered_by,
        )

        execution_ids: list[UUID] = []
        for scenario in scenarios:
            execution = await self._execution_repo.create(
                org_id=org_id,
                suite_run_id=suite_run.id,
                scenario_id=scenario.id,
                status="pending",
            )
            execution_ids.append(execution.id)

        if execution_ids:
            failed = self._execution_client.enqueue_batch(execution_ids)
            for exec_id in execution_ids:
                if exec_id not in failed:
                    await self._execution_repo.update(exec_id, org_id, {"status": "queued"})
                else:
                    await self._execution_repo.update(exec_id, org_id, {"status": "failed"})

        await self._suite_run_repo.update(
            suite_run.id,
            org_id,
            {"status": "running", "started_at": datetime.utcnow()},
        )

        return TriggerResult(suite_run_id=suite_run.id, total_scenarios=len(scenarios))

    async def trigger_scenario_run(
        self,
        org_id: UUID,
        scenario_id: UUID,
        triggered_by: str | None = None,
    ) -> TriggerResult:
        """Trigger execution of a single scenario."""
        scenario = await self._scenario_repo.get(scenario_id, org_id)
        if scenario is None:
            raise ValueError(f"Scenario {scenario_id} not found")

        suite_run = await self._suite_run_repo.create(
            org_id=org_id,
            suite_id=scenario.suite_id,
            total_scenarios=1,
            triggered_by=triggered_by,
        )

        execution = await self._execution_repo.create(
            org_id=org_id,
            suite_run_id=suite_run.id,
            scenario_id=scenario.id,
            status="pending",
        )

        failed = self._execution_client.enqueue_batch([execution.id])
        if execution.id not in failed:
            await self._execution_repo.update(execution.id, org_id, {"status": "queued"})
        else:
            await self._execution_repo.update(execution.id, org_id, {"status": "failed"})

        await self._suite_run_repo.update(
            suite_run.id,
            org_id,
            {"status": "running", "started_at": datetime.utcnow()},
        )

        return TriggerResult(suite_run_id=suite_run.id, total_scenarios=1)
