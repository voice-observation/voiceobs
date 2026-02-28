"""Message received from SQS queue."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReceivedMessage:
    """A message received from SQS."""

    Body: str
    ReceiptHandle: str
    MessageId: str
