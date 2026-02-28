"""Tests for EvaluationResult model."""

from voiceobs.server.models import CriterionResult, EvaluationResult


class TestEvaluationResult:
    """Tests for EvaluationResult model."""

    def test_evaluation_result_creation(self):
        """Test EvaluationResult creation."""
        result = EvaluationResult(
            passed=True,
            score=0.88,
            goal_achieved=True,
            intent_handled=True,
            criteria=[
                CriterionResult(name="greeting", passed=True, score=0.9, evidence="Good greeting"),
            ],
            reasoning="The agent handled the request well.",
        )
        assert result.passed is True
        assert result.score == 0.88
        assert len(result.criteria) == 1

    def test_evaluation_result_to_dict(self):
        """Test serialization to dict for storing in JSONB."""
        result = EvaluationResult(
            passed=False,
            score=0.3,
            goal_achieved=False,
            intent_handled=True,
            criteria=[],
            reasoning="Agent failed to fulfill the order.",
        )
        d = result.model_dump()
        assert d["passed"] is False
        assert d["score"] == 0.3
