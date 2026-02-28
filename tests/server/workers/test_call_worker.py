"""Tests for CallWorker."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.models.sqs import ReceivedMessage
from voiceobs.server.workers.call_worker import CallWorker


class TestCallWorker:
    """Tests for CallWorker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_execution_client = MagicMock()
        self.mock_evaluation_client = MagicMock()
        self.mock_scenario_call_service = AsyncMock()

        self.worker = CallWorker(
            execution_client=self.mock_execution_client,
            evaluation_client=self.mock_evaluation_client,
            scenario_call_service=self.mock_scenario_call_service,
            concurrency=2,
        )

    @pytest.mark.asyncio
    async def test_execute_scenario_enqueues_eval_on_success(self):
        """Test execute_scenario enqueues for evaluation when service returns True."""
        execution_id = uuid4()

        self.mock_scenario_call_service.run_scenario.return_value = True

        await self.worker.execute_scenario(execution_id)

        self.mock_scenario_call_service.run_scenario.assert_called_once_with(execution_id)
        self.mock_evaluation_client.enqueue.assert_called_once_with(execution_id)

    @pytest.mark.asyncio
    async def test_execute_scenario_does_not_enqueue_on_failure(self):
        """Test execute_scenario does not enqueue when service returns False."""
        execution_id = uuid4()

        self.mock_scenario_call_service.run_scenario.return_value = False

        await self.worker.execute_scenario(execution_id)

        self.mock_scenario_call_service.run_scenario.assert_called_once_with(execution_id)
        self.mock_evaluation_client.enqueue.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_message_parses_and_executes(self):
        """Test process_message parses execution_id and calls execute_scenario."""
        execution_id = uuid4()
        msg = ReceivedMessage(
            Body=json.dumps({"execution_id": str(execution_id)}),
            ReceiptHandle="handle-123",
            MessageId="msg-1",
        )

        self.mock_scenario_call_service.run_scenario.return_value = True

        await self.worker.process_message(msg)

        self.mock_scenario_call_service.run_scenario.assert_called_once_with(execution_id)
        self.mock_execution_client.delete_message.assert_called_once_with("handle-123")

    @pytest.mark.asyncio
    async def test_poll_loop_receives_and_processes_messages(self):
        """Test poll_loop receives messages and processes them."""
        execution_id = uuid4()
        msg = ReceivedMessage(
            Body=json.dumps({"execution_id": str(execution_id)}),
            ReceiptHandle="handle-1",
            MessageId="msg-1",
        )

        self.mock_execution_client.receive_messages.return_value = [msg]
        self.mock_scenario_call_service.run_scenario.return_value = True

        async def stop_after_one():
            await asyncio.sleep(0.1)
            self.worker._stop = True

        with patch.object(self.worker, "_stop", False):
            poll_task = asyncio.create_task(self.worker.poll_loop())
            stop_task = asyncio.create_task(stop_after_one())
            await asyncio.gather(poll_task, stop_task)

        self.mock_execution_client.receive_messages.assert_called()
        self.mock_execution_client.delete_message.assert_called_with("handle-1")
