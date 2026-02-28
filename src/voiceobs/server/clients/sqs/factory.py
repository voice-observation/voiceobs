"""Factory for creating and managing SQS queue clients."""

from __future__ import annotations

import os
from typing import Any

from voiceobs.server.clients.sqs.queue_client import SQSQueueClient


class SQSClientFactory:
    """Factory for creating and managing SQS queue clients.

    Supports hundreds of queues via a registry. Each queue gets its own
    client instance.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        sqs_client: Any | None = None,
    ) -> None:
        """Initialize factory.

        Args:
            region: AWS region for SQS.
            sqs_client: Optional boto3 SQS client (for testing).
        """
        self._region = region
        self._sqs_client = sqs_client
        self._queue_clients: dict[str, SQSQueueClient] = {}
        self._queue_urls: dict[str, str] = {}

    def register_queue(self, name: str, queue_url: str) -> None:
        """Register a queue by name and URL.

        Args:
            name: Logical queue name (e.g., "execution", "evaluation").
            queue_url: Full SQS queue URL.
        """
        self._queue_urls[name] = queue_url
        if name in self._queue_clients:
            del self._queue_clients[name]

    def get_queue_client(self, name: str) -> SQSQueueClient:
        """Get or create a client for the named queue.

        Args:
            name: Logical queue name.

        Returns:
            SQSQueueClient for the queue.

        Raises:
            KeyError: If queue is not registered.
        """
        if name not in self._queue_urls:
            raise KeyError(f"Queue '{name}' not registered")

        if name not in self._queue_clients:
            self._queue_clients[name] = SQSQueueClient(
                queue_url=self._queue_urls[name],
                sqs_client=self._sqs_client,
            )

        return self._queue_clients[name]

    def list_queues(self) -> list[str]:
        """List registered queue names."""
        return list(self._queue_urls.keys())

    @classmethod
    def from_env(
        cls,
        queue_config: dict[str, str] | None = None,
        sqs_client: Any | None = None,
    ) -> SQSClientFactory:
        """Create factory from environment variables.

        Args:
            queue_config: Optional override mapping queue names to env var names.
                Default: {"execution": "VOICEOBS_SQS_EXECUTION_QUEUE_URL",
                         "evaluation": "VOICEOBS_SQS_EVALUATION_QUEUE_URL"}
            sqs_client: Optional boto3 SQS client (for testing).

        Returns:
            Configured SQSClientFactory.
        """
        region = os.environ.get("AWS_REGION", "us-east-1")
        if sqs_client is None:
            from voiceobs.server.clients.sqs.session import create_sqs_client

            sqs_client = create_sqs_client(region_name=region)

        factory = cls(region=region, sqs_client=sqs_client)

        config = queue_config or {
            "execution": "VOICEOBS_SQS_EXECUTION_QUEUE_URL",
            "evaluation": "VOICEOBS_SQS_EVALUATION_QUEUE_URL",
        }

        for queue_name, env_var in config.items():
            url = os.environ.get(env_var)
            if url:
                factory.register_queue(queue_name, url)

        return factory
