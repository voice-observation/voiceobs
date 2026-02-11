"""Tests for scenario persona update recalculating match score."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import PersonaRow, TestScenarioRow
from voiceobs.server.services.scenario_generation import PersonaMatcher


def make_persona(
    name: str,
    traits: list[str],
    is_default: bool = False,
    persona_id: str | None = None,
) -> PersonaRow:
    """Create a PersonaRow for testing."""
    return PersonaRow(
        id=uuid4() if persona_id is None else persona_id,
        name=name,
        aggression=0.5,
        patience=0.5,
        verbosity=0.5,
        tts_provider="deepgram",
        org_id=uuid4(),
        traits=traits,
        is_default=is_default,
    )


def make_scenario(
    scenario_id: str | None = None,
    persona_id: str | None = None,
    persona_traits: list[str] | None = None,
    persona_match_score: float | None = None,
) -> TestScenarioRow:
    """Create a TestScenarioRow for testing."""
    return TestScenarioRow(
        id=scenario_id if scenario_id else uuid4(),
        suite_id=uuid4(),
        name="Test Scenario",
        goal="Test Goal",
        persona_id=persona_id if persona_id else uuid4(),
        max_turns=10,
        timeout=300,
        intent="test_intent",
        persona_traits=persona_traits or [],
        persona_match_score=persona_match_score,
    )


class TestPersonaMatcherIntegration:
    """Tests for PersonaMatcher calculating match scores."""

    def test_calculate_match_score_for_single_persona(self):
        """Test calculating match score when updating to a specific persona."""
        persona = make_persona("Patient Customer", ["patient", "friendly"])
        scenario_traits = ["patient", "calm"]

        # Create matcher with just the new persona
        matcher = PersonaMatcher([persona])
        match = matcher.find_best_match(scenario_traits)

        # Jaccard: intersection=1 (patient), union=3 (patient, friendly, calm)
        # Score = 1/3 = 0.333...
        assert 0.0 <= match.score <= 1.0
        assert match.persona == persona

    def test_match_score_with_exact_trait_match(self):
        """Test match score when persona traits exactly match scenario traits."""
        persona = make_persona("Exact Match", ["impatient", "direct"])
        scenario_traits = ["impatient", "direct"]

        matcher = PersonaMatcher([persona])
        match = matcher.find_best_match(scenario_traits)

        assert match.score == 1.0

    def test_match_score_with_empty_scenario_traits(self):
        """Test match score is 0.0 when scenario has no traits."""
        persona = make_persona("Some Persona", ["trait1", "trait2"])
        scenario_traits = []

        matcher = PersonaMatcher([persona])
        match = matcher.find_best_match(scenario_traits)

        assert match.score == 0.0


class TestScenarioPersonaUpdateRoute:
    """Tests for the scenario update route recalculating persona match score."""

    @pytest.mark.asyncio
    async def test_update_persona_recalculates_match_score(self):
        """Test that updating persona_id recalculates persona_match_score."""
        from voiceobs.server.models import TestScenarioUpdateRequest
        from voiceobs.server.routes.test_scenarios import update_test_scenario

        original_persona_id = uuid4()
        new_persona_id = uuid4()
        scenario_id = uuid4()

        # Create personas - new persona has traits matching scenario
        new_persona = make_persona(
            "New Persona",
            ["impatient", "direct"],
            persona_id=new_persona_id,
        )

        # Scenario has traits from LLM generation
        scenario_with_traits = make_scenario(
            scenario_id=scenario_id,
            persona_id=original_persona_id,
            persona_traits=["impatient", "direct"],
            persona_match_score=0.5,  # Old score with previous persona
        )

        # Updated scenario after the update operation
        updated_scenario = make_scenario(
            scenario_id=scenario_id,
            persona_id=new_persona_id,
            persona_traits=["impatient", "direct"],
            persona_match_score=1.0,  # New score should be 1.0 (exact match)
        )

        # Mock dependencies
        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.get.return_value = scenario_with_traits
        mock_scenario_repo.update.return_value = updated_scenario

        mock_persona_repo = AsyncMock()
        mock_persona_repo._get_by_id_unchecked.return_value = new_persona

        request = TestScenarioUpdateRequest(persona_id=str(new_persona_id))

        # Call the route handler
        await update_test_scenario(
            scenario_id=str(scenario_id),
            request=request,
            repo=mock_scenario_repo,
            persona_repo=mock_persona_repo,
        )

        # Verify persona_match_score was passed to update
        mock_scenario_repo.update.assert_called_once()
        call_kwargs = mock_scenario_repo.update.call_args[1]
        assert "persona_match_score" in call_kwargs
        # Score should be 1.0 since traits match exactly
        assert call_kwargs["persona_match_score"] == pytest.approx(1.0)

    @pytest.mark.asyncio
    async def test_update_persona_no_recalculation_if_no_traits(self):
        """Test that updating persona_id does not recalculate if scenario has no traits."""
        from voiceobs.server.models import TestScenarioUpdateRequest
        from voiceobs.server.routes.test_scenarios import update_test_scenario

        original_persona_id = uuid4()
        new_persona_id = uuid4()
        scenario_id = uuid4()

        new_persona = make_persona(
            "New Persona",
            ["friendly", "patient"],
            persona_id=new_persona_id,
        )

        # Scenario without persona_traits (old scenario before generation feature)
        scenario_without_traits = make_scenario(
            scenario_id=scenario_id,
            persona_id=original_persona_id,
            persona_traits=[],  # Empty traits
            persona_match_score=None,
        )

        updated_scenario = make_scenario(
            scenario_id=scenario_id,
            persona_id=new_persona_id,
            persona_traits=[],
            persona_match_score=None,
        )

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.get.return_value = scenario_without_traits
        mock_scenario_repo.update.return_value = updated_scenario

        mock_persona_repo = AsyncMock()
        mock_persona_repo._get_by_id_unchecked.return_value = new_persona

        request = TestScenarioUpdateRequest(persona_id=str(new_persona_id))

        await update_test_scenario(
            scenario_id=str(scenario_id),
            request=request,
            repo=mock_scenario_repo,
            persona_repo=mock_persona_repo,
        )

        # Verify persona_match_score was NOT passed (or is None)
        mock_scenario_repo.update.assert_called_once()
        call_kwargs = mock_scenario_repo.update.call_args[1]
        # Should not have persona_match_score or should be None
        assert call_kwargs.get("persona_match_score") is None

    @pytest.mark.asyncio
    async def test_update_without_persona_change_no_recalculation(self):
        """Test that updates without persona_id change don't recalculate score."""
        from voiceobs.server.models import TestScenarioUpdateRequest
        from voiceobs.server.routes.test_scenarios import update_test_scenario

        persona_id = uuid4()
        scenario_id = uuid4()

        scenario = make_scenario(
            scenario_id=scenario_id,
            persona_id=persona_id,
            persona_traits=["impatient", "direct"],
            persona_match_score=0.75,
        )

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.update.return_value = scenario

        mock_persona_repo = AsyncMock()

        # Update only name, not persona_id
        request = TestScenarioUpdateRequest(name="Updated Name")

        await update_test_scenario(
            scenario_id=str(scenario_id),
            request=request,
            repo=mock_scenario_repo,
            persona_repo=mock_persona_repo,
        )

        # Verify persona_match_score was NOT recalculated
        mock_scenario_repo.update.assert_called_once()
        call_kwargs = mock_scenario_repo.update.call_args[1]
        assert (
            "persona_match_score" not in call_kwargs
            or call_kwargs.get("persona_match_score") is None
        )

    @pytest.mark.asyncio
    async def test_update_persona_partial_match_score(self):
        """Test recalculation with partial trait match."""
        from voiceobs.server.models import TestScenarioUpdateRequest
        from voiceobs.server.routes.test_scenarios import update_test_scenario

        original_persona_id = uuid4()
        new_persona_id = uuid4()
        scenario_id = uuid4()

        # New persona has partial trait overlap
        new_persona = make_persona(
            "Partial Match",
            ["impatient", "friendly", "verbose"],  # Only 'impatient' matches
            persona_id=new_persona_id,
        )

        scenario = make_scenario(
            scenario_id=scenario_id,
            persona_id=original_persona_id,
            persona_traits=["impatient", "direct"],  # 'impatient' and 'direct'
            persona_match_score=0.8,
        )

        updated_scenario = make_scenario(
            scenario_id=scenario_id,
            persona_id=new_persona_id,
            persona_traits=["impatient", "direct"],
            persona_match_score=0.25,
        )

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.get.return_value = scenario
        mock_scenario_repo.update.return_value = updated_scenario

        mock_persona_repo = AsyncMock()
        mock_persona_repo._get_by_id_unchecked.return_value = new_persona

        request = TestScenarioUpdateRequest(persona_id=str(new_persona_id))

        await update_test_scenario(
            scenario_id=str(scenario_id),
            request=request,
            repo=mock_scenario_repo,
            persona_repo=mock_persona_repo,
        )

        # Verify the partial match score was calculated
        # Jaccard: intersection=1 (impatient), union=4 (impatient, friendly, verbose, direct)
        # Score = 1/4 = 0.25
        mock_scenario_repo.update.assert_called_once()
        call_kwargs = mock_scenario_repo.update.call_args[1]
        assert call_kwargs["persona_match_score"] == pytest.approx(0.25)
