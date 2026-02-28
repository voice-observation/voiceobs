"""Tests for execution queue client."""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from voiceobs.server.clients.sqs import ExecutionQueueClient


class TestExecutionQueueClient:
    """Tests for execution queue client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sqs = MagicMock()
        self.client = ExecutionQueueClient(
            queue_url="https://sqs/exec",
            sqs_client=self.mock_sqs,
        )

    def test_enqueue_single(self):
        """Test enqueueing a single execution."""
        execution_id = uuid4()
        self.mock_sqs.send_message.return_value = {"MessageId": "msg-1"}

        result = self.client.enqueue(execution_id)

        assert result == "msg-1"
        body = json.loads(self.mock_sqs.send_message.call_args[1]["MessageBody"])
        assert body["execution_id"] == str(execution_id)

    def test_enqueue_batch(self):
        """Test batch enqueue."""
        ids = [uuid4() for _ in range(3)]
        self.mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": str(i)} for i in range(3)],
            "Failed": [],
        }

        failed = self.client.enqueue_batch(ids)
        assert failed == []

    def test_from_env(self):
        """Test creating client from environment."""
        with patch.dict(
            "os.environ",
            {"VOICEOBS_SQS_EXECUTION_QUEUE_URL": "https://sqs/exec"},
        ):
            client = ExecutionQueueClient.from_env(sqs_client=MagicMock())
            assert client.queue_url == "https://sqs/exec"
