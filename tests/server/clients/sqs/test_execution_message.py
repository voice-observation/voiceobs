"""Tests for ExecutionMessage."""

from uuid import uuid4

from voiceobs.server.models.sqs import ExecutionMessage


class TestExecutionMessage:
    """Tests for ExecutionMessage."""

    def test_create(self):
        """Test creating execution message from UUID."""
        execution_id = uuid4()
        msg = ExecutionMessage.create(execution_id)
        assert msg.execution_id == str(execution_id)

    def test_model_dump(self):
        """Test serialization for SQS."""
        execution_id = uuid4()
        msg = ExecutionMessage.create(execution_id)
        d = msg.model_dump()
        assert d == {"execution_id": str(execution_id)}
