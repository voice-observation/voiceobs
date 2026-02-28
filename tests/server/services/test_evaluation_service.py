"""Tests for EvaluationService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import (
    TestExecutionRow,
    TestScenarioRow,
    TestSuiteRow,
)
from voiceobs.server.models import CriterionResult, EvaluationResult
from voiceobs.server.services.evaluation.service import EvaluationService


class TestEvaluationService:
    """Tests for EvaluationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_execution_repo = AsyncMock()
        self.mock_scenario_repo = AsyncMock()
        self.mock_suite_repo = AsyncMock()
        self.mock_llm_service = AsyncMock()

        self.service = EvaluationService(
            execution_repo=self.mock_execution_repo,
            scenario_repo=self.mock_scenario_repo,
            suite_repo=self.mock_suite_repo,
            llm_service=self.mock_llm_service,
        )

    @pytest.mark.asyncio
    async def test_evaluate_execution_not_found(self):
        """Test evaluate raises when execution not found."""
        execution_id = uuid4()
        self.mock_execution_repo.get_by_id.return_value = None

        with pytest.raises(ValueError, match="Execution .* not found"):
            await self.service.evaluate(execution_id)

        self.mock_execution_repo.get_by_id.assert_called_once_with(execution_id)
        self.mock_llm_service.generate_structured.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_no_transcript(self):
        """Test evaluate raises when execution has no transcript."""
        execution_id = uuid4()
        org_id = uuid4()
        scenario_id = uuid4()

        execution = TestExecutionRow(
            id=execution_id,
            org_id=org_id,
            suite_run_id=uuid4(),
            scenario_id=scenario_id,
            transcript=None,
        )
        self.mock_execution_repo.get_by_id.return_value = execution

        with pytest.raises(ValueError, match="No transcript"):
            await self.service.evaluate(execution_id)

        self.mock_llm_service.generate_structured.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_success(self):
        """Test successful evaluation returns EvaluationResult."""
        execution_id = uuid4()
        org_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        transcript = [
            {"role": "persona", "text": "Hi, I need help", "timestamp_ms": 0},
            {"role": "agent", "text": "Hello! How can I assist?", "timestamp_ms": 1500},
        ]

        execution = TestExecutionRow(
            id=execution_id,
            org_id=org_id,
            suite_run_id=uuid4(),
            scenario_id=scenario_id,
            transcript=transcript,
        )

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            org_id=org_id,
            name="Order pizza",
            goal="Order a large pepperoni pizza",
            persona_id=uuid4(),
            intent="order_pizza",
            caller_behaviors=["Be polite"],
        )

        suite = TestSuiteRow(
            id=suite_id,
            org_id=org_id,
            name="Pizza Suite",
            evaluation_strictness="balanced",
        )

        expected_result = EvaluationResult(
            passed=True,
            score=0.9,
            goal_achieved=True,
            intent_handled=True,
            criteria=[
                CriterionResult(
                    name="greeting",
                    passed=True,
                    score=0.95,
                    evidence="Agent said hello",
                ),
            ],
            reasoning="The agent handled the request well.",
        )

        self.mock_execution_repo.get_by_id.return_value = execution
        self.mock_scenario_repo.get.return_value = scenario
        self.mock_suite_repo.get.return_value = suite
        self.mock_llm_service.generate_structured.return_value = expected_result

        result = await self.service.evaluate(execution_id)

        assert result == expected_result
        self.mock_execution_repo.get_by_id.assert_called_once_with(execution_id)
        self.mock_scenario_repo.get.assert_called_once_with(scenario_id, org_id)
        self.mock_suite_repo.get.assert_called_once_with(suite_id, org_id)
        self.mock_llm_service.generate_structured.assert_called_once()
        call_args = self.mock_llm_service.generate_structured.call_args
        prompt = call_args[1]["prompt"]
        assert "Order a large pepperoni pizza" in prompt
        assert "order_pizza" in prompt
        assert "Hi, I need help" in prompt
        assert "balanced" in prompt

    @pytest.mark.asyncio
    async def test_evaluate_scenario_not_found(self):
        """Test evaluate raises when scenario not found."""
        execution_id = uuid4()
        org_id = uuid4()
        scenario_id = uuid4()

        execution = TestExecutionRow(
            id=execution_id,
            org_id=org_id,
            suite_run_id=uuid4(),
            scenario_id=scenario_id,
            transcript=[{"role": "agent", "text": "Hello", "timestamp_ms": 0}],
        )

        self.mock_execution_repo.get_by_id.return_value = execution
        self.mock_scenario_repo.get.return_value = None

        with pytest.raises(ValueError, match="Scenario .* not found"):
            await self.service.evaluate(execution_id)

        self.mock_llm_service.generate_structured.assert_not_called()

    @pytest.mark.asyncio
    async def test_evaluate_suite_not_found(self):
        """Test evaluate raises when suite not found."""
        execution_id = uuid4()
        org_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        execution = TestExecutionRow(
            id=execution_id,
            org_id=org_id,
            suite_run_id=uuid4(),
            scenario_id=scenario_id,
            transcript=[{"role": "agent", "text": "Hello", "timestamp_ms": 0}],
        )

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            org_id=org_id,
            name="Test",
            goal="Test goal",
            persona_id=uuid4(),
        )

        self.mock_execution_repo.get_by_id.return_value = execution
        self.mock_scenario_repo.get.return_value = scenario
        self.mock_suite_repo.get.return_value = None

        with pytest.raises(ValueError, match="Test suite .* not found"):
            await self.service.evaluate(execution_id)

        self.mock_llm_service.generate_structured.assert_not_called()
