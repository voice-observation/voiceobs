"""Tests for persona utility functions."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import PersonaRow, TestScenarioRow
from voiceobs.server.db.repositories.persona import PersonaRepository
from voiceobs.server.utils.persona import resolve_persona_for_scenario
from voiceobs.sim.persona import PersonaDNA


class TestResolvePersonaForScenario:
    """Tests for resolve_persona_for_scenario function."""

    @pytest.mark.asyncio
    async def test_resolve_persona_success(self):
        """Test successful persona resolution."""
        # Arrange
        persona_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=60,
        )

        persona_row = PersonaRow(
            id=persona_id,
            name="Friendly Tester",
            description="A friendly test persona",
            aggression=0.3,
            patience=0.8,
            verbosity=0.5,
            traits=["friendly", "helpful"],
            tts_provider="openai",
            tts_config={"voice": "alloy"},
            preview_audio_url="https://example.com/audio.mp3",
            preview_audio_text="Hello, this is how I sound.",
            metadata={},
            is_active=True,
        )

        mock_repo = AsyncMock(spec=PersonaRepository)
        mock_repo.get.return_value = persona_row

        # Act
        result = await resolve_persona_for_scenario(scenario, mock_repo)

        # Assert
        mock_repo.get.assert_called_once_with(persona_id)
        assert isinstance(result, PersonaDNA)
        assert result.aggression == 0.3
        assert result.patience == 0.8
        assert result.verbosity == 0.5
        assert result.traits == ["friendly", "helpful"]

    @pytest.mark.asyncio
    async def test_resolve_persona_not_found(self):
        """Test persona resolution when persona is not found."""
        # Arrange
        persona_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
        )

        mock_repo = AsyncMock(spec=PersonaRepository)
        mock_repo.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await resolve_persona_for_scenario(scenario, mock_repo)

        assert f"Persona {persona_id} not found" in str(exc_info.value)
        mock_repo.get.assert_called_once_with(persona_id)

    @pytest.mark.asyncio
    async def test_resolve_persona_inactive(self):
        """Test persona resolution when persona is inactive."""
        # Arrange
        persona_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
        )

        persona_row = PersonaRow(
            id=persona_id,
            name="Inactive Persona",
            description="An inactive persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="openai",
            tts_config={},
            is_active=False,  # Inactive persona
        )

        mock_repo = AsyncMock(spec=PersonaRepository)
        mock_repo.get.return_value = persona_row

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            await resolve_persona_for_scenario(scenario, mock_repo)

        assert f"Persona {persona_id} is not active" in str(exc_info.value)
        mock_repo.get.assert_called_once_with(persona_id)

    @pytest.mark.asyncio
    async def test_resolve_persona_with_empty_traits(self):
        """Test persona resolution with empty traits list."""
        # Arrange
        persona_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
        )

        persona_row = PersonaRow(
            id=persona_id,
            name="Simple Persona",
            description="A simple persona",
            aggression=0.2,
            patience=0.9,
            verbosity=0.4,
            traits=[],  # Empty traits
            tts_provider="elevenlabs",
            tts_config={"voice_id": "abc123"},
            is_active=True,
        )

        mock_repo = AsyncMock(spec=PersonaRepository)
        mock_repo.get.return_value = persona_row

        # Act
        result = await resolve_persona_for_scenario(scenario, mock_repo)

        # Assert
        assert isinstance(result, PersonaDNA)
        assert result.aggression == 0.2
        assert result.patience == 0.9
        assert result.verbosity == 0.4
        assert result.traits == []

    @pytest.mark.asyncio
    async def test_resolve_persona_preserves_trait_values(self):
        """Test that persona trait values are preserved correctly."""
        # Arrange
        persona_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
        )

        # Test boundary values
        persona_row = PersonaRow(
            id=persona_id,
            name="Boundary Persona",
            description="Persona with boundary trait values",
            aggression=0.0,  # Minimum
            patience=1.0,  # Maximum
            verbosity=0.5,  # Middle
            traits=["calm", "patient", "balanced"],
            tts_provider="deepgram",
            tts_config={"model": "aura-asteria-en"},
            is_active=True,
        )

        mock_repo = AsyncMock(spec=PersonaRepository)
        mock_repo.get.return_value = persona_row

        # Act
        result = await resolve_persona_for_scenario(scenario, mock_repo)

        # Assert
        assert result.aggression == 0.0
        assert result.patience == 1.0
        assert result.verbosity == 0.5
        assert result.traits == ["calm", "patient", "balanced"]

    @pytest.mark.asyncio
    async def test_resolve_persona_multiple_traits(self):
        """Test persona resolution with multiple traits."""
        # Arrange
        persona_id = uuid4()
        scenario_id = uuid4()
        suite_id = uuid4()

        scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
        )

        traits = ["professional", "patient", "detail-oriented", "helpful", "empathetic"]
        persona_row = PersonaRow(
            id=persona_id,
            name="Multi-trait Persona",
            description="Persona with multiple traits",
            aggression=0.1,
            patience=0.95,
            verbosity=0.7,
            traits=traits,
            tts_provider="openai",
            tts_config={"voice": "nova"},
            is_active=True,
        )

        mock_repo = AsyncMock(spec=PersonaRepository)
        mock_repo.get.return_value = persona_row

        # Act
        result = await resolve_persona_for_scenario(scenario, mock_repo)

        # Assert
        assert result.traits == traits
        assert len(result.traits) == 5
