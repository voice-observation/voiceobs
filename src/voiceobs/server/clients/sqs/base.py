"""Base class for SQS queue operations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from voiceobs.server.models.sqs import ReceivedMessage


class BaseSQSQueueClient(ABC):
    """Abstract base class for SQS queue operations.

    Handles send, receive, and delete operations. Supports hundreds of
    queues via per-queue client instances.
    """

    def __init__(self, queue_url: str) -> None:
        """Initialize with queue URL.

        Args:
            queue_url: Full SQS queue URL.
        """
        self._queue_url = queue_url

    @property
    def queue_url(self) -> str:
        """Get the queue URL."""
        return self._queue_url

    @abstractmethod
    def send_message(self, body: dict) -> str:
        """Send a single message to the queue.

        Args:
            body: Message body as dict (will be JSON-serialized).

        Returns:
            Message ID from SQS.
        """
        ...

    @abstractmethod
    def send_message_batch(self, bodies: list[dict]) -> list[int]:
        """Send a batch of messages to the queue.

        Args:
            bodies: List of message bodies (will be JSON-serialized).

        Returns:
            List of indices of messages that failed to send.
        """
        ...

    @abstractmethod
    def receive_messages(
        self,
        max_messages: int = 10,
        wait_time_seconds: int = 20,
        visibility_timeout: int | None = None,
    ) -> list[ReceivedMessage]:
        """Receive messages from the queue (long-polling).

        Args:
            max_messages: Maximum number of messages to return (1-10).
            wait_time_seconds: Long-poll wait time (0-20 seconds).
            visibility_timeout: How long message is hidden after receive (seconds).

        Returns:
            List of received messages. Caller must delete each after processing.
        """
        ...

    @abstractmethod
    def delete_message(self, receipt_handle: str) -> None:
        """Delete a message after successful processing.

        Args:
            receipt_handle: ReceiptHandle from the received message.
        """
        ...
