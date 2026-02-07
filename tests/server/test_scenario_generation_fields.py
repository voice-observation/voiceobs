"""Tests for test scenario generation fields."""

from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository
from voiceobs.server.models import TestScenarioResponse


class TestScenarioGenerationFields:
    """Tests for the test scenario generation fields."""

    def test_test_scenario_response_includes_generation_fields(self) -> None:
        """Test that TestScenarioResponse includes generation fields."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Order Status Check",
            goal="User wants to check their order status",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            max_turns=10,
            timeout=300,
            intent="check_order_status",
            persona_traits=["impatient", "direct"],
            persona_match_score=0.85,
        )

        assert response.intent == "check_order_status"
        assert response.persona_traits == ["impatient", "direct"]
        assert response.persona_match_score == 0.85

    def test_test_scenario_response_generation_fields_optional(self) -> None:
        """Test that generation fields are optional for backwards compat."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Order Status Check",
            goal="User wants to check their order status",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
        )

        assert response.intent is None
        assert response.persona_traits is None
        assert response.persona_match_score is None

    def test_test_scenario_response_persona_match_score_validation(self) -> None:
        """Test that persona_match_score validates range (0-1)."""
        # Valid score at lower bound
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test",
            goal="Goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            persona_match_score=0.0,
        )
        assert response.persona_match_score == 0.0

        # Valid score at upper bound
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test",
            goal="Goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            persona_match_score=1.0,
        )
        assert response.persona_match_score == 1.0

    def test_test_scenario_response_persona_match_score_invalid_range(self) -> None:
        """Test that persona_match_score rejects values outside 0-1."""
        with pytest.raises(ValueError):
            TestScenarioResponse(
                id="550e8400-e29b-41d4-a716-446655440000",
                suite_id="550e8400-e29b-41d4-a716-446655440001",
                name="Test",
                goal="Goal",
                persona_id="550e8400-e29b-41d4-a716-446655440002",
                persona_match_score=1.5,  # Invalid: > 1.0
            )

        with pytest.raises(ValueError):
            TestScenarioResponse(
                id="550e8400-e29b-41d4-a716-446655440000",
                suite_id="550e8400-e29b-41d4-a716-446655440001",
                name="Test",
                goal="Goal",
                persona_id="550e8400-e29b-41d4-a716-446655440002",
                persona_match_score=-0.1,  # Invalid: < 0.0
            )


class TestRowToModelEdgeCases:
    """Tests for _row_to_model edge cases with persona_traits parsing."""

    def test_row_to_model_persona_traits_none(self) -> None:
        """Test _row_to_model handles None persona_traits as empty list."""
        # Create a mock row with None persona_traits
        row = {
            "id": uuid4(),
            "suite_id": uuid4(),
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": uuid4(),
            "max_turns": 10,
            "timeout": 300,
            "intent": "check_order",
            "persona_traits": None,
            "persona_match_score": 0.8,
        }

        # Call _row_to_model directly (it's a method on the repository)
        repo = TestScenarioRepository.__new__(TestScenarioRepository)
        result = repo._row_to_model(row)

        assert result.persona_traits == []

    def test_row_to_model_persona_traits_json_string(self) -> None:
        """Test _row_to_model parses JSON string persona_traits."""
        row = {
            "id": uuid4(),
            "suite_id": uuid4(),
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": uuid4(),
            "max_turns": 10,
            "timeout": 300,
            "intent": "check_order",
            "persona_traits": '["impatient", "direct", "demanding"]',
            "persona_match_score": 0.85,
        }

        repo = TestScenarioRepository.__new__(TestScenarioRepository)
        result = repo._row_to_model(row)

        assert result.persona_traits == ["impatient", "direct", "demanding"]

    def test_row_to_model_persona_traits_list(self) -> None:
        """Test _row_to_model passes through list persona_traits unchanged."""
        row = {
            "id": uuid4(),
            "suite_id": uuid4(),
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": uuid4(),
            "max_turns": 10,
            "timeout": 300,
            "intent": "check_order",
            "persona_traits": ["friendly", "patient"],
            "persona_match_score": 0.9,
        }

        repo = TestScenarioRepository.__new__(TestScenarioRepository)
        result = repo._row_to_model(row)

        assert result.persona_traits == ["friendly", "patient"]

    def test_row_to_model_empty_json_array_string(self) -> None:
        """Test _row_to_model handles empty JSON array string."""
        row = {
            "id": uuid4(),
            "suite_id": uuid4(),
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": uuid4(),
            "max_turns": 10,
            "timeout": 300,
            "intent": "check_order",
            "persona_traits": "[]",
            "persona_match_score": 0.75,
        }

        repo = TestScenarioRepository.__new__(TestScenarioRepository)
        result = repo._row_to_model(row)

        assert result.persona_traits == []
