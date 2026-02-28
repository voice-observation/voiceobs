"""Client for test execution queue."""

from __future__ import annotations

import logging
import os
from typing import Any
from uuid import UUID

from voiceobs.server.clients.sqs.queue_client import SQSQueueClient
from voiceobs.server.models.sqs import ExecutionMessage

logger = logging.getLogger(__name__)


class ExecutionQueueClient:
    """Client for enqueueing test execution messages."""

    def __init__(
        self,
        queue_url: str,
        sqs_client: Any | None = None,
    ) -> None:
        """Initialize execution queue client.

        Args:
            queue_url: Full SQS execution queue URL.
            sqs_client: Optional boto3 SQS client (for testing).
        """
        self._client = SQSQueueClient(queue_url=queue_url, sqs_client=sqs_client)

    @property
    def queue_url(self) -> str:
        """Get the queue URL."""
        return self._client.queue_url

    def enqueue(self, execution_id: UUID) -> str:
        """Enqueue a single execution message. Returns message ID."""
        msg = ExecutionMessage.create(execution_id)
        msg_id = self._client.send_message(msg.model_dump())
        logger.info("Enqueued execution %s", execution_id)
        return msg_id

    def enqueue_batch(self, execution_ids: list[UUID]) -> list[UUID]:
        """Enqueue batch of execution messages. Returns list of failed IDs."""
        bodies = [ExecutionMessage.create(eid).model_dump() for eid in execution_ids]
        failed_indices = self._client.send_message_batch(bodies)
        return [execution_ids[i] for i in failed_indices]

    def receive_messages(
        self,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int | None = None,
    ):
        """Receive messages from the execution queue (long-polling)."""
        return self._client.receive_messages(
            max_messages=max_messages,
            wait_time_seconds=wait_time_seconds,
            visibility_timeout=visibility_timeout,
        )

    def delete_message(self, receipt_handle: str) -> None:
        """Delete a message after successful processing."""
        self._client.delete_message(receipt_handle)

    @classmethod
    def from_env(cls, sqs_client: Any | None = None) -> ExecutionQueueClient:
        """Create from environment variables.

        Uses boto3.Session with AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY.
        Region is derived from the queue URL (required for SQS - client must match
        queue region) with fallback to AWS_REGION.
        """
        queue_url = os.environ["VOICEOBS_SQS_EXECUTION_QUEUE_URL"]
        if sqs_client is None:
            from voiceobs.server.clients.sqs.session import create_sqs_client
            from voiceobs.server.utils.queue_utils import region_from_queue_url

            region = region_from_queue_url(queue_url) or os.environ.get("AWS_REGION", "us-east-1")
            sqs_client = create_sqs_client(region_name=region)
        return cls(queue_url=queue_url, sqs_client=sqs_client)
