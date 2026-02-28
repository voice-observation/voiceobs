"""Per-queue SQS client."""

from __future__ import annotations

import json
import logging
from typing import Any

from voiceobs.server.clients.retry import retryable
from voiceobs.server.clients.sqs.base import BaseSQSQueueClient
from voiceobs.server.models.sqs import ReceivedMessage

log = logging.getLogger(__name__)


class SQSQueueClient(BaseSQSQueueClient):
    """Per-queue SQS client with single and batch send operations."""

    def __init__(
        self,
        queue_url: str,
        sqs_client: Any | None = None,
        max_retries: int = 2,
        retry_base_delay: float = 1.0,
    ) -> None:
        """Initialize SQS queue client.

        Args:
            queue_url: Full SQS queue URL.
            sqs_client: Optional boto3 SQS client (for testing).
            max_retries: Number of retries on transient failures (default 2 = 3 total attempts).
            retry_base_delay: Base delay in seconds for exponential backoff (default 1.0).
        """
        super().__init__(queue_url)
        if sqs_client is not None:
            self._sqs = sqs_client
        else:
            from voiceobs.server.clients.sqs.session import create_sqs_client

            self._sqs = create_sqs_client()
        self._max_retries = max_retries
        self._retry_base_delay = retry_base_delay

    @retryable("send_message")
    def send_message(self, body: dict) -> str:
        """Send a single message to the queue."""
        response = self._sqs.send_message(
            QueueUrl=self._queue_url,
            MessageBody=json.dumps(body),
        )
        return response["MessageId"]

    @retryable("send_message_batch")
    def _send_chunk(self, chunk: list[dict]) -> dict:
        """Send a single chunk (up to 10 messages) to the queue."""
        return self._sqs.send_message_batch(
            QueueUrl=self._queue_url,
            Entries=chunk,
        )

    def send_message_batch(self, bodies: list[dict]) -> list[int]:
        """Send a batch of messages. Returns indices of failed messages."""
        entries = [{"Id": str(i), "MessageBody": json.dumps(body)} for i, body in enumerate(bodies)]

        failed_indices: list[int] = []
        for chunk_start in range(0, len(entries), 10):
            chunk = entries[chunk_start : chunk_start + 10]
            response = self._send_chunk(chunk)
            for fail in response.get("Failed", []):
                idx = int(fail["Id"])
                failed_indices.append(chunk_start + idx)

        return failed_indices

    @retryable("receive_messages")
    def receive_messages(
        self,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int | None = None,
    ) -> list[ReceivedMessage]:
        """Receive messages from the queue (long-polling)."""
        params: dict[str, Any] = {
            "QueueUrl": self._queue_url,
            "MaxNumberOfMessages": min(max_messages, 10),
            "WaitTimeSeconds": wait_time_seconds,
        }
        if visibility_timeout is not None:
            params["VisibilityTimeout"] = visibility_timeout
        log.info("Receiving messages from queue %s", self._queue_url)
        response = self._sqs.receive_message(**params)
        messages = response.get("Messages", [])
        return [
            ReceivedMessage(
                Body=msg["Body"],
                ReceiptHandle=msg["ReceiptHandle"],
                MessageId=msg["MessageId"],
            )
            for msg in messages
        ]

    @retryable("delete_message")
    def delete_message(self, receipt_handle: str) -> None:
        """Delete a message after successful processing."""
        self._sqs.delete_message(
            QueueUrl=self._queue_url,
            ReceiptHandle=receipt_handle,
        )
