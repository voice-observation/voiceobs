"""Tests for SQS client factory."""

from unittest.mock import MagicMock

import pytest

from voiceobs.server.clients.sqs import SQSClientFactory


class TestSQSClientFactory:
    """Tests for SQS client factory."""

    def test_register_and_get_queue_client(self):
        """Test registering and retrieving queue clients."""
        mock_sqs = MagicMock()
        factory = SQSClientFactory(sqs_client=mock_sqs)

        factory.register_queue("execution", "https://sqs/exec")
        factory.register_queue("evaluation", "https://sqs/eval")

        client1 = factory.get_queue_client("execution")
        client2 = factory.get_queue_client("evaluation")
        client1_again = factory.get_queue_client("execution")

        assert client1.queue_url == "https://sqs/exec"
        assert client2.queue_url == "https://sqs/eval"
        assert client1 is client1_again

    def test_get_unknown_queue_raises(self):
        """Test getting unregistered queue raises KeyError."""
        factory = SQSClientFactory(sqs_client=MagicMock())

        with pytest.raises(KeyError, match="Queue 'foo' not registered"):
            factory.get_queue_client("foo")

    def test_list_queues(self):
        """Test listing registered queues."""
        factory = SQSClientFactory(sqs_client=MagicMock())
        factory.register_queue("a", "https://sqs/a")
        factory.register_queue("b", "https://sqs/b")

        assert set(factory.list_queues()) == {"a", "b"}
