"""Tests for evaluation queue client."""

import json
from unittest.mock import MagicMock, patch
from uuid import uuid4

from voiceobs.server.clients.sqs import EvaluationQueueClient


class TestEvaluationQueueClient:
    """Tests for evaluation queue client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sqs = MagicMock()
        self.client = EvaluationQueueClient(
            queue_url="https://sqs/eval",
            sqs_client=self.mock_sqs,
        )

    def test_enqueue(self):
        """Test enqueueing an evaluation message."""
        execution_id = uuid4()
        self.mock_sqs.send_message.return_value = {"MessageId": "msg-eval"}

        result = self.client.enqueue(execution_id)

        assert result == "msg-eval"
        body = json.loads(self.mock_sqs.send_message.call_args[1]["MessageBody"])
        assert body["execution_id"] == str(execution_id)

    def test_from_env(self):
        """Test creating client from environment."""
        with patch.dict(
            "os.environ",
            {"VOICEOBS_SQS_EVALUATION_QUEUE_URL": "https://sqs/eval"},
        ):
            client = EvaluationQueueClient.from_env(sqs_client=MagicMock())
            assert client.queue_url == "https://sqs/eval"
