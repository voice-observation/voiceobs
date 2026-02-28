"""Call worker that polls SQS execution queue and runs test calls via LiveKit SIP."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING
from uuid import UUID

from voiceobs.server.models.sqs import ExecutionMessage, ReceivedMessage

if TYPE_CHECKING:
    from voiceobs.server.clients.sqs import (
        EvaluationQueueClient,
        ExecutionQueueClient,
    )
    from voiceobs.server.services.execution import ScenarioCallService

logger = logging.getLogger(__name__)


class CallWorker:
    """Worker that polls the execution queue and runs test scenario calls."""

    def __init__(
        self,
        execution_client: ExecutionQueueClient,
        evaluation_client: EvaluationQueueClient,
        scenario_call_service: ScenarioCallService,
        concurrency: int = 10,
    ) -> None:
        """Initialize the call worker."""
        self._execution_client = execution_client
        self._evaluation_client = evaluation_client
        self._scenario_call_service = scenario_call_service
        self._semaphore = asyncio.Semaphore(concurrency)
        self._stop = False

    async def execute_scenario(self, execution_id: UUID) -> None:
        """Execute a test scenario via LiveKit SIP; on success enqueue for evaluation."""
        success = await self._scenario_call_service.run_scenario(execution_id)
        if success:
            self._evaluation_client.enqueue(execution_id)

    async def process_message(self, message: ReceivedMessage) -> None:
        """Process a single SQS message."""
        try:
            body = json.loads(message.Body)
            logger.info("Processing message: %s", body)
            msg = ExecutionMessage.model_validate(body)
            execution_id = UUID(msg.execution_id)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error("Invalid message body: %s", e)
            return

        async with self._semaphore:
            await self.execute_scenario(execution_id)

        self._execution_client.delete_message(message.ReceiptHandle)

    async def poll_loop(self) -> None:
        """Long-poll SQS and process messages until stopped."""
        self._stop = False
        while not self._stop:
            try:
                messages = await asyncio.to_thread(
                    self._execution_client.receive_messages,
                    max_messages=10,
                    wait_time_seconds=20,
                    visibility_timeout=300,
                )
                for msg in messages:
                    await self.process_message(msg)
            except Exception as e:
                logger.exception("Error in poll loop: %s", e)
                await asyncio.sleep(5)
