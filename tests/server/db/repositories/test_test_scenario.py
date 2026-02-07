"""Tests for the TestScenarioRepository class."""

from uuid import uuid4

import pytest

from voiceobs.server.db.models import TestScenarioRow
from voiceobs.server.db.repositories.persona import PersonaRepository
from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

from .conftest import MockRecord


class TestTestScenarioRowModel:
    """Tests for TestScenarioRow model."""

    def test_row_has_new_crud_fields(self):
        """Test that TestScenarioRow has all new CRUD fields."""
        row = TestScenarioRow(
            id=uuid4(),
            suite_id=uuid4(),
            name="Test",
            goal="Goal",
            persona_id=uuid4(),
            caller_behaviors=["step1", "step2"],
            tags=["happy-path", "booking"],
            status="ready",
        )

        assert row.caller_behaviors == ["step1", "step2"]
        assert row.tags == ["happy-path", "booking"]
        assert row.status == "ready"

    def test_row_new_fields_have_defaults(self):
        """Test that new CRUD fields have correct defaults."""
        row = TestScenarioRow(
            id=uuid4(),
            suite_id=uuid4(),
            name="Test",
            goal="Goal",
            persona_id=uuid4(),
        )

        assert row.caller_behaviors == []
        assert row.tags == []
        assert row.status == "draft"


class TestTestScenarioRepository:
    """Tests for the TestScenarioRepository class."""

    def test_row_to_model_handles_new_fields(self, mock_db):
        """Test that _row_to_model correctly parses new CRUD fields."""
        from unittest.mock import MagicMock

        mock_persona_repo = MagicMock()
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        row = {
            "id": scenario_id,
            "suite_id": suite_id,
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": persona_id,
            "max_turns": 10,
            "timeout": 300,
            "intent": "book_flight",
            "persona_traits": '["impatient", "demanding"]',
            "persona_match_score": 0.75,
            "caller_behaviors": '["Provide destination", "Confirm booking"]',
            "tags": '["happy-path"]',
            "status": "ready",
        }

        result = repo._row_to_model(row)

        assert result.caller_behaviors == ["Provide destination", "Confirm booking"]
        assert result.tags == ["happy-path"]
        assert result.status == "ready"

    def test_row_to_model_handles_null_new_fields(self, mock_db):
        """Test that _row_to_model correctly handles None/missing new CRUD fields."""
        from unittest.mock import MagicMock

        mock_persona_repo = MagicMock()
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        row = {
            "id": scenario_id,
            "suite_id": suite_id,
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": persona_id,
            "max_turns": 10,
            "timeout": 300,
            "intent": None,
            "persona_traits": None,
            "persona_match_score": None,
            "caller_behaviors": None,
            "tags": None,
            "status": None,
        }

        result = repo._row_to_model(row)

        assert result.caller_behaviors == []
        assert result.tags == []
        assert result.status == "draft"

    def test_row_to_model_handles_list_new_fields(self, mock_db):
        """Test that _row_to_model handles already-parsed list fields."""
        from unittest.mock import MagicMock

        mock_persona_repo = MagicMock()
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        row = {
            "id": scenario_id,
            "suite_id": suite_id,
            "name": "Test Scenario",
            "goal": "Test goal",
            "persona_id": persona_id,
            "max_turns": 10,
            "timeout": 300,
            "intent": "book_flight",
            "persona_traits": ["impatient"],
            "persona_match_score": 0.75,
            "caller_behaviors": ["Provide destination"],
            "tags": ["happy-path"],
            "status": "ready",
        }

        result = repo._row_to_model(row)

        assert result.caller_behaviors == ["Provide destination"]
        assert result.tags == ["happy-path"]

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
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
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
        suite_id = uuid4()
        new_persona_id = uuid4()

        # Mock persona validation, get current scenario (for status compute), and final get
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
            # Second call: get current scenario (for status computation)
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Old Name",
                    "goal": "Updated goal",
                    "persona_id": uuid4(),
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
            # Third call: get updated scenario
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Updated Scenario",
                    "goal": "Updated goal",
                    "persona_id": new_persona_id,
                    "max_turns": 15,
                    "timeout": 600,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
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
                "intent": None,
                "persona_traits": None,
                "persona_match_score": None,
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
                "intent": None,
                "persona_traits": None,
                "persona_match_score": None,
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
                "intent": "check_order_status",
                "persona_traits": ["impatient", "direct"],
                "persona_match_score": 0.85,
            }
        )

        result = await repo.get(scenario_id)

        assert result is not None
        assert result.id == scenario_id
        assert result.persona_id == persona_id
        # Verify generation fields are returned
        assert result.intent == "check_order_status"
        assert result.persona_traits == ["impatient", "direct"]
        assert result.persona_match_score == 0.85

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
                    "intent": "check_order",
                    "persona_traits": ["patient"],
                    "persona_match_score": 0.9,
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
                    "intent": "cancel_order",
                    "persona_traits": ["impatient", "aggressive"],
                    "persona_match_score": 0.75,
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
                    "intent": "check_order",
                    "persona_traits": ["friendly"],
                    "persona_match_score": 0.88,
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

    @pytest.mark.asyncio
    async def test_update_scenario_with_generation_fields(self, mock_db):
        """Test updating a scenario with generation fields."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        persona_id = uuid4()

        # Mock get to return updated scenario with generation fields
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": scenario_id,
                "suite_id": uuid4(),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": persona_id,
                "max_turns": 10,
                "timeout": 300,
                "intent": "new_intent",
                "persona_traits": '["confident", "assertive"]',  # JSON string
                "persona_match_score": 0.92,
            }
        )

        result = await repo.update(
            scenario_id=scenario_id,
            intent="new_intent",
            persona_traits=["confident", "assertive"],
            persona_match_score=0.92,
        )

        assert result is not None
        assert result.intent == "new_intent"
        assert result.persona_traits == ["confident", "assertive"]
        assert result.persona_match_score == 0.92
        assert mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_scenario_all_fields(self, mock_db):
        """Test updating a scenario with all possible fields."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        new_persona_id = uuid4()
        suite_id = uuid4()

        # Mock persona validation, get current scenario, and final get
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
            # Second call: get current scenario (for status computation)
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Old Name",
                    "goal": "Old goal",
                    "persona_id": uuid4(),
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
            # Third call: get updated scenario
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Updated Name",
                    "goal": "Updated goal",
                    "persona_id": new_persona_id,
                    "max_turns": 20,
                    "timeout": 600,
                    "intent": "updated_intent",
                    "persona_traits": '["updated_trait"]',
                    "persona_match_score": 0.95,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
        ]

        result = await repo.update(
            scenario_id=scenario_id,
            name="Updated Name",
            goal="Updated goal",
            persona_id=new_persona_id,
            max_turns=20,
            timeout=600,
            intent="updated_intent",
            persona_traits=["updated_trait"],
            persona_match_score=0.95,
        )

        assert result is not None
        assert result.name == "Updated Name"
        assert result.goal == "Updated goal"
        assert result.persona_id == new_persona_id
        assert result.max_turns == 20
        assert result.timeout == 600
        assert result.intent == "updated_intent"
        assert result.persona_traits == ["updated_trait"]
        assert result.persona_match_score == 0.95
        assert mock_db.execute.called


class TestCrudFieldsSqlQueries:
    """Tests for SQL queries with new CRUD fields.

    Tests for caller_behaviors, tags, status.
    """

    @pytest.mark.asyncio
    async def test_create_with_new_crud_fields(self, mock_db):
        """Test that create includes new CRUD fields in INSERT query."""
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
            # Second call: fetchrow for created scenario with new fields
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Test Scenario",
                    "goal": "Test goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": '["Step 1", "Step 2"]',
                    "tags": '["happy-path"]',
                    "status": "ready",
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
            caller_behaviors=["Step 1", "Step 2"],
            tags=["happy-path"],
        )

        # Verify result includes new fields
        assert result.caller_behaviors == ["Step 1", "Step 2"]
        assert result.tags == ["happy-path"]
        assert result.status == "ready"

        # Verify INSERT query was called with new fields
        assert mock_db.execute.called
        insert_call = mock_db.execute.call_args
        insert_query = insert_call[0][0]
        # Verify the INSERT includes new columns
        assert "caller_behaviors" in insert_query
        assert "tags" in insert_query
        assert "status" in insert_query

    @pytest.mark.asyncio
    async def test_get_returns_new_crud_fields(self, mock_db):
        """Test that get includes new CRUD fields in SELECT query."""
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
                "intent": "check_status",
                "persona_traits": ["patient"],
                "persona_match_score": 0.85,
                "caller_behaviors": ["Provide order number", "Ask about ETA"],
                "tags": ["order-status", "high-priority"],
                "status": "ready",
            }
        )

        result = await repo.get(scenario_id)

        assert result is not None
        assert result.caller_behaviors == ["Provide order number", "Ask about ETA"]
        assert result.tags == ["order-status", "high-priority"]
        assert result.status == "ready"

        # Verify the SELECT query includes new fields
        fetchrow_call = mock_db.fetchrow.call_args
        select_query = fetchrow_call[0][0]
        assert "caller_behaviors" in select_query
        assert "tags" in select_query
        assert "status" in select_query

    @pytest.mark.asyncio
    async def test_list_all_returns_new_crud_fields(self, mock_db):
        """Test that list_all includes new CRUD fields in SELECT query."""
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
                    "intent": "check_order",
                    "persona_traits": ["patient"],
                    "persona_match_score": 0.9,
                    "caller_behaviors": ["Step 1"],
                    "tags": ["tag1"],
                    "status": "ready",
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
                    "intent": "cancel_order",
                    "persona_traits": ["impatient"],
                    "persona_match_score": 0.75,
                    "caller_behaviors": ["Step A", "Step B"],
                    "tags": ["tag2", "tag3"],
                    "status": "draft",
                }
            ),
        ]

        result = await repo.list_all()

        assert len(result) == 2
        # Verify first scenario has new fields
        assert result[0].caller_behaviors == ["Step 1"]
        assert result[0].tags == ["tag1"]
        assert result[0].status == "ready"
        # Verify second scenario has new fields
        assert result[1].caller_behaviors == ["Step A", "Step B"]
        assert result[1].tags == ["tag2", "tag3"]
        assert result[1].status == "draft"

        # Verify the SELECT query includes new fields
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        assert "caller_behaviors" in select_query
        assert "tags" in select_query
        assert "status" in select_query

    @pytest.mark.asyncio
    async def test_list_all_by_suite_returns_new_crud_fields(self, mock_db):
        """Test that list_all with suite_id filter includes new CRUD fields."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Scenario",
                    "goal": "Goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": "test",
                    "persona_traits": [],
                    "persona_match_score": None,
                    "caller_behaviors": ["Behavior"],
                    "tags": ["tag"],
                    "status": "ready",
                }
            ),
        ]

        result = await repo.list_all(suite_id=suite_id)

        assert len(result) == 1
        assert result[0].caller_behaviors == ["Behavior"]
        assert result[0].status == "ready"

        # Verify the SELECT query includes new fields
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        assert "caller_behaviors" in select_query
        assert "tags" in select_query
        assert "status" in select_query

    @pytest.mark.asyncio
    async def test_update_with_new_crud_fields(self, mock_db):
        """Test that update can modify new CRUD fields."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        # Mock get to return updated scenario
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": scenario_id,
                "suite_id": suite_id,
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": persona_id,
                "max_turns": 10,
                "timeout": 300,
                "intent": None,
                "persona_traits": None,
                "persona_match_score": None,
                "caller_behaviors": '["Updated Step 1", "Updated Step 2"]',
                "tags": '["updated-tag"]',
                "status": "ready",
            }
        )

        result = await repo.update(
            scenario_id=scenario_id,
            caller_behaviors=["Updated Step 1", "Updated Step 2"],
            tags=["updated-tag"],
        )

        assert result is not None
        assert result.caller_behaviors == ["Updated Step 1", "Updated Step 2"]
        assert result.tags == ["updated-tag"]
        assert result.status == "ready"

        # Verify the UPDATE query was called and includes new fields
        assert mock_db.execute.called
        update_call = mock_db.execute.call_args
        update_query = update_call[0][0]
        assert "caller_behaviors" in update_query
        assert "tags" in update_query

    @pytest.mark.asyncio
    async def test_update_single_crud_field(self, mock_db):
        """Test updating a single new CRUD field."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": scenario_id,
                "suite_id": suite_id,
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": persona_id,
                "max_turns": 10,
                "timeout": 300,
                "intent": None,
                "persona_traits": None,
                "persona_match_score": None,
                "caller_behaviors": '["New behavior"]',
                "tags": None,
                "status": "draft",
            }
        )

        result = await repo.update(
            scenario_id=scenario_id,
            caller_behaviors=["New behavior"],
        )

        assert result is not None
        assert result.caller_behaviors == ["New behavior"]
        assert mock_db.execute.called


class TestStatusAutoComputation:
    """Tests for status auto-computation logic."""

    def test_compute_status_ready_when_complete(self):
        """Status is 'ready' when name and goal are present and non-empty."""
        from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

        status = TestScenarioRepository._compute_status(name="Test Scenario", goal="Test Goal")
        assert status == "ready"

    def test_compute_status_draft_when_missing_name(self):
        """Status is 'draft' when name is empty."""
        from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

        status = TestScenarioRepository._compute_status(name="", goal="Goal")
        assert status == "draft"

    def test_compute_status_draft_when_name_is_whitespace(self):
        """Status is 'draft' when name is only whitespace."""
        from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

        status = TestScenarioRepository._compute_status(name="   ", goal="Goal")
        assert status == "draft"

    def test_compute_status_draft_when_missing_goal(self):
        """Status is 'draft' when goal is empty."""
        from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

        status = TestScenarioRepository._compute_status(name="Test", goal="")
        assert status == "draft"

    def test_compute_status_draft_when_goal_is_whitespace(self):
        """Status is 'draft' when goal is only whitespace."""
        from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

        status = TestScenarioRepository._compute_status(name="Test", goal="   ")
        assert status == "draft"

    def test_compute_status_draft_when_both_empty(self):
        """Status is 'draft' when both name and goal are empty."""
        from voiceobs.server.db.repositories.test_scenario import TestScenarioRepository

        status = TestScenarioRepository._compute_status(name="", goal="")
        assert status == "draft"


class TestStatusAutoComputationInRepository:
    """Tests for status auto-computation in create and update methods."""

    @pytest.mark.asyncio
    async def test_create_sets_status_ready_when_complete(self, mock_db):
        """Status is auto-set to 'ready' on create when name and goal are present."""
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
                    "goal": "Test Goal",
                    "persona_id": persona_id,
                    "max_turns": None,
                    "timeout": None,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
        ]

        result = await repo.create(
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test Goal",
            persona_id=persona_id,
        )

        assert result.status == "ready"
        # Verify status was set to 'ready' in the INSERT
        insert_call = mock_db.execute.call_args
        insert_args = insert_call[0]
        # status is the 13th parameter (index 13 after the query)
        assert insert_args[13] == "ready"

    @pytest.mark.asyncio
    async def test_create_sets_status_draft_when_name_empty(self, mock_db):
        """Status is auto-set to 'draft' on create when name is empty."""
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
                    "name": "",
                    "goal": "Test Goal",
                    "persona_id": persona_id,
                    "max_turns": None,
                    "timeout": None,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "draft",
                }
            ),
        ]

        result = await repo.create(
            suite_id=suite_id,
            name="",
            goal="Test Goal",
            persona_id=persona_id,
        )

        assert result.status == "draft"
        # Verify status was set to 'draft' in the INSERT
        insert_call = mock_db.execute.call_args
        insert_args = insert_call[0]
        assert insert_args[13] == "draft"

    @pytest.mark.asyncio
    async def test_update_recomputes_status_to_ready(self, mock_db):
        """Status is auto-recomputed to 'ready' on update when name and goal become present."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        # Need to return the current scenario first for status computation
        # Then return the updated scenario
        mock_db.fetchrow.side_effect = [
            # First call: get current scenario (for computing new status)
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "",
                    "goal": "Existing Goal",
                    "persona_id": persona_id,
                    "max_turns": None,
                    "timeout": None,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "draft",
                }
            ),
            # Second call: get updated scenario
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "New Name",
                    "goal": "Existing Goal",
                    "persona_id": persona_id,
                    "max_turns": None,
                    "timeout": None,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
        ]

        result = await repo.update(
            scenario_id=scenario_id,
            name="New Name",
        )

        assert result is not None
        assert result.status == "ready"
        # Verify status was updated in the UPDATE query
        update_call = mock_db.execute.call_args
        update_query = update_call[0][0]
        assert "status" in update_query

    @pytest.mark.asyncio
    async def test_update_recomputes_status_to_draft(self, mock_db):
        """Status is auto-recomputed to 'draft' on update when name becomes empty."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetchrow.side_effect = [
            # First call: get current scenario (for computing new status)
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "Existing Name",
                    "goal": "Existing Goal",
                    "persona_id": persona_id,
                    "max_turns": None,
                    "timeout": None,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
            # Second call: get updated scenario
            MockRecord(
                {
                    "id": scenario_id,
                    "suite_id": suite_id,
                    "name": "",
                    "goal": "Existing Goal",
                    "persona_id": persona_id,
                    "max_turns": None,
                    "timeout": None,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "draft",
                }
            ),
        ]

        result = await repo.update(
            scenario_id=scenario_id,
            name="",
        )

        assert result is not None
        assert result.status == "draft"
        # Verify status was updated in the UPDATE query
        update_call = mock_db.execute.call_args
        update_query = update_call[0][0]
        assert "status" in update_query


class TestListAllFiltering:
    """Tests for list_all method with status and tags filters."""

    @pytest.mark.asyncio
    async def test_list_all_with_status_filter(self, mock_db):
        """Test listing scenarios filtered by status."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Ready Scenario",
                    "goal": "Goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "ready",
                }
            ),
        ]

        result = await repo.list_all(status="ready")

        assert len(result) == 1
        assert result[0].status == "ready"
        # Verify the query includes status filter
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        assert "status = $" in select_query

    @pytest.mark.asyncio
    async def test_list_all_with_tags_filter(self, mock_db):
        """Test listing scenarios filtered by tags (returns scenarios with ANY tag)."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Tagged Scenario",
                    "goal": "Goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": '["happy-path", "booking"]',
                    "status": "ready",
                }
            ),
        ]

        result = await repo.list_all(tags=["happy-path", "urgent"])

        assert len(result) == 1
        assert result[0].tags == ["happy-path", "booking"]
        # Verify the query includes tags filter using JSONB overlap operator
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        assert "tags" in select_query

    @pytest.mark.asyncio
    async def test_list_all_with_status_and_suite_filters(self, mock_db):
        """Test listing scenarios with both status and suite filters."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Scenario",
                    "goal": "Goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": None,
                    "status": "draft",
                }
            ),
        ]

        result = await repo.list_all(suite_id=suite_id, status="draft")

        assert len(result) == 1
        # Verify both filters are in the query
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        assert "suite_id = $" in select_query
        assert "status = $" in select_query

    @pytest.mark.asyncio
    async def test_list_all_with_all_filters(self, mock_db):
        """Test listing scenarios with suite, status, and tags filters combined."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        suite_id = uuid4()
        persona_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "suite_id": suite_id,
                    "name": "Fully Filtered",
                    "goal": "Goal",
                    "persona_id": persona_id,
                    "max_turns": 10,
                    "timeout": 300,
                    "intent": None,
                    "persona_traits": None,
                    "persona_match_score": None,
                    "caller_behaviors": None,
                    "tags": '["happy-path"]',
                    "status": "ready",
                }
            ),
        ]

        result = await repo.list_all(suite_id=suite_id, status="ready", tags=["happy-path"])

        assert len(result) == 1
        # Verify all filters are in the query
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        assert "suite_id = $" in select_query
        assert "status = $" in select_query
        assert "tags" in select_query

    @pytest.mark.asyncio
    async def test_list_all_empty_tags_not_applied(self, mock_db):
        """Test that empty tags list is not applied as a filter."""
        mock_persona_repo = PersonaRepository(mock_db)
        repo = TestScenarioRepository(mock_db, mock_persona_repo)

        mock_db.fetch.return_value = []

        await repo.list_all(tags=[])

        # Verify the query does not include tags filter for empty list
        fetch_call = mock_db.fetch.call_args
        select_query = fetch_call[0][0]
        # The tags filter should not be present for empty list
        assert "?|" not in select_query or "tags @>" not in select_query
