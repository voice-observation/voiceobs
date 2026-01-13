"""Tests for the TestScenarioRepository class."""

from uuid import uuid4

import pytest

from voiceobs.server.db.models import TestScenarioRow
from voiceobs.server.db.repositories.persona import PersonaRepository
from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

from .conftest import MockRecord


class TestTestScenarioRepository:
    """Tests for the TestScenarioRepository class."""

    @pytest.mark.asyncio
    async def test_create_scenario_with_valid_persona(self, mock_db):
        """Test creating a scenario with a valid active persona."""
        # Create mock persona repository
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        scenario_id = uuid4()
        persona_id = uuid4()

        # Mock persona exists and is active
        mock_db.fetchrow.side_effect = [
            # First call: persona validation
            MockRecord(
                {
                    "id": persona_id,
                    "name": "Test Persona",
                    "description": None,
                    "aggression": 0.5,
                    "patience": 0.7,
                    "verbosity": 0.3,
                    "traits": [],
                    "tts_provider": "openai",
                    "tts_config": {},
                    "preview_audio_url": None,
                    "preview_audio_text": None,
                    "metadata": {},
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                    "is_active": True,
                }
            ),
            # Second call: fetchrow for created scenario
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Test Scenario",
                    "goal": "Test goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                }
            ),
        ]

        result = await repo.create(
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )

        assert result.id == scenario_id
        assert result.persona_id == persona_id
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_create_scenario_with_nonexistent_persona(self, mock_db):
        """Test creating a scenario with a non-existent persona."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        # Mock persona doesn't exist
        mock_db.fetchrow.return_value = None

        with pytest.raises(ValueError, match="Persona .* not found"):
            await repo.create(
                suite_id=suite_id,
                name="Test Scenario",
                goal="Test goal",
                persona_id=persona_id,
            )

        # Should not call execute since validation failed
        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_scenario_with_inactive_persona(self, mock_db):
        """Test creating a scenario with an inactive persona."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        # Mock persona exists but is inactive
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Inactive Persona",
                "description": None,
                "aggression": 0.5,
                "patience": 0.7,
                "verbosity": 0.3,
                "traits": [],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": False,
            }
        )

        with pytest.raises(ValueError, match="Persona .* is not active"):
            await repo.create(
                suite_id=suite_id,
                name="Test Scenario",
                goal="Test goal",
                persona_id=persona_id,
            )

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_scenario_with_valid_persona(self, mock_db):
        """Test updating a scenario with a valid active persona."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        new_persona_id = uuid4()

        # Mock persona validation and final get
        mock_db.fetchrow.side_effect = [
            # First call: persona validation
            MockRecord(
                {
                    "id": new_persona_id,
                    "name": "New Persona",
                    "description": None,
                    "aggression": 0.5,
                    "patience": 0.7,
                    "verbosity": 0.3,
                    "traits": [],
                    "tts_provider": "openai",
                    "tts_config": {},
                    "preview_audio_url": None,
                    "preview_audio_text": None,
                    "metadata": {},
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                    "is_active": True,
                }
            ),
            # Second call: get updated scenario
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": uuid4(),
                    "name": "Updated Scenario",
                    "goal": "Updated goal",
                    "persona_id": new_persona_id,
                    "max_turns": 15,
                    "timeout": 600,
                }
            ),
        ]

        result = await repo.update(
            scenario_id=scenario_id,
            name="Updated Scenario",
            persona_id=new_persona_id,
        )

        assert result is not None
        assert result.persona_id == new_persona_id
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_scenario_with_nonexistent_persona(self, mock_db):
        """Test updating a scenario with a non-existent persona."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        persona_id = uuid4()

        # Mock persona doesn't exist
        mock_db.fetchrow.return_value = None

        with pytest.raises(ValueError, match="Persona .* not found"):
            await repo.update(
                scenario_id=scenario_id,
                persona_id=persona_id,
            )

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_scenario_with_inactive_persona(self, mock_db):
        """Test updating a scenario with an inactive persona."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        persona_id = uuid4()

        # Mock persona exists but is inactive
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Inactive Persona",
                "description": None,
                "aggression": 0.5,
                "patience": 0.7,
                "verbosity": 0.3,
                "traits": [],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": False,
            }
        )

        with pytest.raises(ValueError, match="Persona .* is not active"):
            await repo.update(
                scenario_id=scenario_id,
                persona_id=persona_id,
            )

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_scenario_without_persona_change(self, mock_db):
        """Test updating a scenario without changing persona (should not validate)."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        persona_id = uuid4()

        # Mock get to return existing scenario
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": scenario_id,
                "suite_id": uuid4(),
                "name": "Updated Name",
                "goal": "Test goal",
                "persona_id": persona_id,
                "max_turns": 10,
                "timeout": 300,
            }
        )

        result = await repo.update(
            scenario_id=scenario_id,
            name="Updated Name",
        )

        assert result is not None
        assert result.name == "Updated Name"
        # Should call execute for update and fetchrow for get
        assert mock_db.execute.called
        assert mock_db.fetchrow.called

    @pytest.mark.asyncio
    async def test_update_scenario_no_changes(self, mock_db):
        """Test updating scenario with no changes returns existing."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()

        # Mock get to return existing scenario
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": scenario_id,
                "suite_id": uuid4(),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": uuid4(),
                "max_turns": 10,
                "timeout": 300,
            }
        )

        result = await repo.update(scenario_id=scenario_id)

        assert result is not None
        # Should call fetchrow for get but not execute for update
        assert mock_db.fetchrow.called
        assert not mock_db.execute.called

    @pytest.mark.asyncio
    async def test_get_scenario(self, mock_db):
        """Test getting a scenario by UUID."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": scenario_id,
                "suite_id": uuid4(),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": persona_id,
                "max_turns": 10,
                "timeout": 300,
            }
        )

        result = await repo.get(scenario_id)

        assert result is not None
        assert result.id == scenario_id
        assert result.persona_id == persona_id

    @pytest.mark.asyncio
    async def test_get_scenario_not_found(self, mock_db):
        """Test getting a non-existent scenario."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_scenarios(self, mock_db):
        """Test listing all scenarios."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Scenario 1",
                    "goal": "Goal 1",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                }
            ),
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Scenario 2",
                    "goal": "Goal 2",
                    "persona_id": persona_id,
                    "max_turns": 15,
                    "timeout": 600,
                }
            ),
        ]

        result = await repo.list_all()

        assert len(result) == 2
        assert all(isinstance(s, TestScenarioRow) for s in result)

    @pytest.mark.asyncio
    async def test_list_scenarios_by_suite(self, mock_db):
        """Test listing scenarios filtered by suite."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Scenario 1",
                    "goal": "Goal 1",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                }
            ),
        ]

        result = await repo.list_all(suite_id=suite_id)

        assert len(result) == 1
        assert result[0].suite_id == suite_id

    @pytest.mark.asyncio
    async def test_delete_scenario(self, mock_db):
        """Test deleting a scenario."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(scenario_id)

        assert result is True
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_delete_scenario_not_found(self, mock_db):
        """Test deleting a non-existent scenario."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_create_scenario_database_failure(self, mock_db):
        """Test creating a scenario when database fails to return the created row."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        # Mock persona exists and is active
        mock_db.fetchrow.side_effect = [
            # First call: persona validation
            MockRecord(
                {
                    "id": persona_id,
                    "name": "Test Persona",
                    "description": None,
                    "aggression": 0.5,
                    "patience": 0.7,
                    "verbosity": 0.3,
                    "traits": [],
                    "tts_provider": "openai",
                    "tts_config": {},
                    "preview_audio_url": None,
                    "preview_audio_text": None,
                    "metadata": {},
                    "created_at": None,
                    "updated_at": None,
                    "created_by": None,
                    "is_active": True,
                }
            ),
            # Second call: fetchrow returns None (database failure)
            None,
        ]

        with pytest.raises(RuntimeError, match="Failed to create test scenario"):
            await repo.create(
                suite_id=suite_id,
                name="Test Scenario",
                goal="Test goal",
                persona_id=persona_id,
            )

        assert mock_db.execute.called
