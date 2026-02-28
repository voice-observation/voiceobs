"""Tests for CriterionResult model."""

from voiceobs.server.models import CriterionResult


class TestCriterionResult:
    """Tests for CriterionResult model."""

    def test_criterion_result_creation(self):
        """Test CriterionResult creation."""
        criterion = CriterionResult(
            name="greeting",
            passed=True,
            score=0.95,
            evidence="Agent said 'Hello, welcome to our service'",
        )
        assert criterion.name == "greeting"
        assert criterion.passed is True
        assert criterion.score == 0.95
