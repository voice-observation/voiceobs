"""Tests for SQS queue client."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.clients.sqs import SQSQueueClient


class TestSQSQueueClient:
    """Tests for per-queue SQS client."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_sqs = MagicMock()
        self.client = SQSQueueClient(
            queue_url="https://sqs.us-east-1.amazonaws.com/123/test-queue",
            sqs_client=self.mock_sqs,
        )

    def test_send_message(self):
        """Test sending a single message."""
        self.mock_sqs.send_message.return_value = {"MessageId": "msg-123"}

        result = self.client.send_message({"execution_id": str(uuid4())})

        self.mock_sqs.send_message.assert_called_once()
        call_kwargs = self.mock_sqs.send_message.call_args[1]
        assert call_kwargs["QueueUrl"] == self.client.queue_url
        assert result == "msg-123"

    def test_send_message_batch(self):
        """Test batch send returns failed indices."""
        self.mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": "0"}, {"Id": "1"}, {"Id": "2"}],
            "Failed": [],
        }

        bodies = [{"execution_id": str(uuid4())} for _ in range(3)]
        failed = self.client.send_message_batch(bodies)

        self.mock_sqs.send_message_batch.assert_called_once()
        assert failed == []

    def test_send_message_batch_with_failures(self):
        """Test batch send returns correct failed indices."""
        self.mock_sqs.send_message_batch.return_value = {
            "Successful": [{"Id": "0"}, {"Id": "2"}],
            "Failed": [{"Id": "1"}],
        }

        bodies = [{"execution_id": str(uuid4())} for _ in range(3)]
        failed = self.client.send_message_batch(bodies)

        assert failed == [1]

    def test_receive_messages(self):
        """Test receiving messages from queue."""
        self.mock_sqs.receive_message.return_value = {
            "Messages": [
                {
                    "Body": '{"execution_id": "abc-123"}',
                    "ReceiptHandle": "rh-1",
                    "MessageId": "msg-1",
                },
            ],
        }

        messages = self.client.receive_messages(max_messages=5, wait_time_seconds=10)

        assert len(messages) == 1
        assert messages[0].Body == '{"execution_id": "abc-123"}'
        assert messages[0].ReceiptHandle == "rh-1"
        assert messages[0].MessageId == "msg-1"
        self.mock_sqs.receive_message.assert_called_once_with(
            QueueUrl=self.client.queue_url,
            MaxNumberOfMessages=5,
            WaitTimeSeconds=10,
        )

    def test_delete_message(self):
        """Test deleting a message after processing."""
        self.client.delete_message("rh-123")

        self.mock_sqs.delete_message.assert_called_once_with(
            QueueUrl=self.client.queue_url,
            ReceiptHandle="rh-123",
        )

    @patch("voiceobs.server.clients.retry.time.sleep")
    def test_send_message_retries_on_throttling_then_succeeds(self, mock_sleep):
        """Test send_message retries on throttling and succeeds."""
        from botocore.exceptions import ClientError

        self.mock_sqs.send_message.side_effect = [
            ClientError(
                {"Error": {"Code": "RequestThrottled", "Message": "Rate exceeded"}},
                "SendMessage",
            ),
            {"MessageId": "msg-123"},
        ]

        result = self.client.send_message({"execution_id": str(uuid4())})

        assert self.mock_sqs.send_message.call_count == 2
        assert result == "msg-123"

    @patch("voiceobs.server.clients.retry.time.sleep")
    def test_send_message_raises_after_max_retries(self, mock_sleep):
        """Test send_message raises after exhausting retries."""
        from botocore.exceptions import ClientError

        self.mock_sqs.send_message.side_effect = ClientError(
            {"Error": {"Code": "RequestThrottled", "Message": "Rate exceeded"}},
            "SendMessage",
        )

        with pytest.raises(ClientError):
            self.client.send_message({"execution_id": str(uuid4())})

        assert self.mock_sqs.send_message.call_count == 3  # 1 initial + 2 retries

    def test_send_message_no_retry_on_non_retryable_error(self):
        """Test send_message does not retry on invalid parameter errors."""
        from botocore.exceptions import ClientError

        self.mock_sqs.send_message.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterValue", "Message": "Bad value"}},
            "SendMessage",
        )

        with pytest.raises(ClientError):
            self.client.send_message({"execution_id": str(uuid4())})

        self.mock_sqs.send_message.assert_called_once()

    @patch("voiceobs.server.clients.retry.time.sleep")
    def test_receive_messages_retries_on_throttling_then_succeeds(self, mock_sleep):
        """Test receive_messages retries on throttling and succeeds."""
        from botocore.exceptions import ClientError

        self.mock_sqs.receive_message.side_effect = [
            ClientError(
                {"Error": {"Code": "OverLimit", "Message": "Too many requests"}},
                "ReceiveMessage",
            ),
            {"Messages": []},
        ]

        messages = self.client.receive_messages()

        assert self.mock_sqs.receive_message.call_count == 2
        assert messages == []
