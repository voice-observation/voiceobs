"""Tests for EvalWorker."""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from voiceobs.server.models.sqs import ReceivedMessage
from voiceobs.server.workers.eval_worker import EvalWorker


class TestEvalWorker:
    """Tests for EvalWorker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_evaluation_client = MagicMock()
        self.mock_execution_repo = AsyncMock()
        self.mock_suite_run_repo = AsyncMock()
        self.mock_evaluation_service = AsyncMock()

        self.worker = EvalWorker(
            evaluation_client=self.mock_evaluation_client,
            execution_repo=self.mock_execution_repo,
            suite_run_repo=self.mock_suite_run_repo,
            evaluation_service=self.mock_evaluation_service,
            concurrency=5,
        )

    @pytest.mark.asyncio
    async def test_evaluate_execution_saves_result_and_increments(self):
        """Test evaluate_execution saves result and increments suite run."""
        execution_id = uuid4()
        org_id = uuid4()
        suite_run_id = uuid4()

        execution = MagicMock(
            id=execution_id,
            org_id=org_id,
            suite_run_id=suite_run_id,
            transcript=[{"role": "agent", "text": "Hello", "timestamp_ms": 0}],
        )
        eval_result = MagicMock(
            passed=True,
            score=0.9,
            model_dump=lambda: {"passed": True, "score": 0.9},
        )

        self.mock_execution_repo.get_by_id.return_value = execution
        self.mock_evaluation_service.evaluate.return_value = eval_result
        self.mock_suite_run_repo.get.return_value = MagicMock(
            completed_scenarios=4, failed_scenarios=0, total_scenarios=5
        )

        await self.worker.evaluate_execution(execution_id)

        self.mock_execution_repo.update.assert_called_once()
        # update(execution_id, org_id, updates_dict) - third arg is updates
        updates = self.mock_execution_repo.update.call_args[0][2]
        assert "evaluation_result" in updates
        assert updates["status"] == "completed"

        self.mock_suite_run_repo.increment_completed.assert_called_once_with(suite_run_id, org_id)

    @pytest.mark.asyncio
    async def test_process_message_parses_and_evaluates(self):
        """Test process_message parses execution_id and calls evaluate_execution."""
        execution_id = uuid4()
        msg = ReceivedMessage(
            Body=json.dumps({"execution_id": str(execution_id)}),
            ReceiptHandle="handle-1",
            MessageId="msg-1",
        )

        execution = MagicMock(
            id=execution_id,
            org_id=uuid4(),
            suite_run_id=uuid4(),
            transcript=[{"role": "agent", "text": "Hi", "timestamp_ms": 0}],
        )
        self.mock_execution_repo.get_by_id.return_value = execution
        self.mock_evaluation_service.evaluate.return_value = MagicMock(model_dump=lambda: {})
        self.mock_suite_run_repo.get.return_value = MagicMock(
            completed_scenarios=0, failed_scenarios=0, total_scenarios=1
        )

        await self.worker.process_message(msg)

        self.mock_evaluation_client.delete_message.assert_called_once_with("handle-1")
