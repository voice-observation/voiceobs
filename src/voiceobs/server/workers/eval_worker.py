"""Eval worker that polls SQS evaluation queue and runs LLM evaluation."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from voiceobs.server.models.sqs import EvaluationMessage, ReceivedMessage

if TYPE_CHECKING:
    from voiceobs.server.clients.sqs import EvaluationQueueClient
    from voiceobs.server.db.repositories.test_execution import TestExecutionRepository
    from voiceobs.server.db.repositories.test_suite_run import TestSuiteRunRepository
    from voiceobs.server.services.evaluation import EvaluationService

logger = logging.getLogger(__name__)


class EvalWorker:
    """Worker that polls the evaluation queue and runs LLM-based evaluation."""

    def __init__(
        self,
        evaluation_client: EvaluationQueueClient,
        execution_repo: TestExecutionRepository,
        suite_run_repo: TestSuiteRunRepository,
        evaluation_service: EvaluationService,
        concurrency: int = 20,
    ) -> None:
        """Initialize the eval worker."""
        self._evaluation_client = evaluation_client
        self._execution_repo = execution_repo
        self._suite_run_repo = suite_run_repo
        self._evaluation_service = evaluation_service
        self._semaphore = asyncio.Semaphore(concurrency)
        self._stop = False

    async def evaluate_execution(self, execution_id: UUID) -> None:
        """Evaluate an execution and save result to DB."""
        execution = await self._execution_repo.get_by_id(execution_id)
        if execution is None:
            logger.warning("Execution %s not found, skipping", execution_id)
            return

        try:
            result = await self._evaluation_service.evaluate(execution_id)
            await self._execution_repo.update(
                execution_id,
                execution.org_id,
                {
                    "status": "completed",
                    "evaluation_result": result.model_dump(),
                },
            )
            await self._suite_run_repo.increment_completed(execution.suite_run_id, execution.org_id)
        except Exception as e:
            logger.exception("Evaluation failed for %s: %s", execution_id, e)
            await self._execution_repo.update(
                execution_id,
                execution.org_id,
                {"status": "failed", "error_message": str(e)},
            )
            await self._suite_run_repo.increment_failed(execution.suite_run_id, execution.org_id)
            return

        suite_run = await self._suite_run_repo.get(execution.suite_run_id, execution.org_id)
        if suite_run and self._is_suite_run_complete(suite_run):
            await self._suite_run_repo.update(
                execution.suite_run_id,
                execution.org_id,
                {"status": "completed", "completed_at": datetime.utcnow()},
            )

    def _is_suite_run_complete(self, suite_run) -> bool:
        """Check if all executions in suite run have finished."""
        total = suite_run.completed_scenarios + suite_run.failed_scenarios
        return total >= suite_run.total_scenarios

    async def process_message(self, message: ReceivedMessage) -> None:
        """Process a single SQS message."""
        try:
            body = json.loads(message.Body)
            msg = EvaluationMessage.model_validate(body)
            execution_id = UUID(msg.execution_id)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Invalid message body: %s", e)
            return

        async with self._semaphore:
            await self.evaluate_execution(execution_id)

        self._evaluation_client.delete_message(message.ReceiptHandle)

    async def poll_loop(self) -> None:
        """Long-poll SQS and process messages until stopped."""
        self._stop = False
        while not self._stop:
            try:
                messages = await asyncio.to_thread(
                    self._evaluation_client.receive_messages,
                    max_messages=10,
                    wait_time_seconds=20,
                    visibility_timeout=60,
                )
                for msg in messages:
                    await self.process_message(msg)
            except Exception as e:
                logger.exception("Error in poll loop: %s", e)
                await asyncio.sleep(5)
