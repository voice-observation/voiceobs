"""Tests for EvaluationMessage."""

from uuid import uuid4

from voiceobs.server.models.sqs import EvaluationMessage


class TestEvaluationMessage:
    """Tests for EvaluationMessage."""

    def test_create(self):
        """Test creating evaluation message from UUID."""
        execution_id = uuid4()
        msg = EvaluationMessage.create(execution_id)
        assert msg.execution_id == str(execution_id)

    def test_model_dump(self):
        """Test serialization for SQS."""
        execution_id = uuid4()
        msg = EvaluationMessage.create(execution_id)
        d = msg.model_dump()
        assert d == {"execution_id": str(execution_id)}
