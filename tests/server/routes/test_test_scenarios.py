"""Tests for the test scenario API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import PersonaRow, TestScenarioRow, TestSuiteRow


class TestTestScenarios:
    """Tests for test scenario CRUD endpoints."""

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_create_scenario_success(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test successful scenario creation."""
        suite_id = uuid4()
        scenario_id = uuid4()

        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            created_at=datetime.utcnow(),
        )
        persona_id = uuid4()
        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
        )
        mock_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = mock_suite
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.create.return_value = mock_scenario
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        response = client.post(
            "/api/v1/tests/scenarios",
            json={
                "suite_id": str(suite_id),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": str(persona_id),
                "max_turns": 10,
                "timeout": 300,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Scenario"
        assert data["goal"] == "Test goal"
        assert data["suite_id"] == str(suite_id)

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_create_scenario_suite_not_found(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test scenario creation when suite not found."""
        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = None
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_persona_repo = AsyncMock()
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        suite_id = uuid4()
        persona_id = uuid4()
        response = client.post(
            "/api/v1/tests/scenarios",
            json={
                "suite_id": str(suite_id),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": str(persona_id),
            },
        )

        assert response.status_code == 404

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_success(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test successful scenario listing."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        persona_id = uuid4()
        scenario1 = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Scenario 1",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )
        scenario2 = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Scenario 2",
            goal="Goal 2",
            persona_id=persona_id,
            max_turns=15,
            timeout=600,
        )
        mock_repo.list_all.return_value = [scenario1, scenario2]
        mock_repo.count.return_value = 2
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["scenarios"]) == 2
        assert data["limit"] == 20
        assert data["offset"] == 0

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_with_filter(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test scenario listing with suite filter."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        persona_id = uuid4()
        scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Scenario 1",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )
        mock_repo.list_all.return_value = [scenario]
        mock_repo.count.return_value = 1
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get(f"/api/v1/tests/scenarios?suite_id={suite_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        mock_repo.list_all.assert_called_once_with(
            suite_id=suite_id, status=None, tags=None, limit=20, offset=0
        )

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_get_scenario_success(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test successful scenario retrieval."""
        mock_repo = AsyncMock()
        scenario_id = uuid4()
        persona_id = uuid4()
        mock_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=uuid4(),
            name="Test Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )
        mock_repo.get.return_value = mock_scenario
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get(f"/api/v1/tests/scenarios/{scenario_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Scenario"

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_update_scenario_success(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test successful scenario update."""
        mock_repo = AsyncMock()
        scenario_id = uuid4()
        persona_id = uuid4()
        updated_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=uuid4(),
            name="Updated Scenario",
            goal="Updated goal",
            persona_id=persona_id,
            max_turns=15,
            timeout=600,
        )
        mock_repo.update.return_value = updated_scenario
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        mock_persona_repo = AsyncMock()
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        mock_suite_repo = AsyncMock()
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        response = client.put(
            f"/api/v1/tests/scenarios/{scenario_id}",
            json={"name": "Updated Scenario", "max_turns": 15},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Scenario"
        assert data["max_turns"] == 15

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_delete_scenario_success(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test successful scenario deletion."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        scenario_id = uuid4()
        response = client.delete(f"/api/v1/tests/scenarios/{scenario_id}")

        assert response.status_code == 204

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_create_scenario_persona_not_found(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test scenario creation when persona not found."""
        suite_id = uuid4()
        persona_id = uuid4()

        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            created_at=datetime.utcnow(),
        )

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = mock_suite
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        # Persona not found
        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        response = client.post(
            "/api/v1/tests/scenarios",
            json={
                "suite_id": str(suite_id),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": str(persona_id),
            },
        )

        assert response.status_code == 404
        assert "Persona" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_create_scenario_persona_inactive(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test scenario creation when persona is inactive."""
        suite_id = uuid4()
        persona_id = uuid4()

        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            created_at=datetime.utcnow(),
        )

        # Inactive persona
        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=False,
        )

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = mock_suite
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        response = client.post(
            "/api/v1/tests/scenarios",
            json={
                "suite_id": str(suite_id),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": str(persona_id),
            },
        )

        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_update_scenario_persona_not_found(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test scenario update when persona not found."""
        scenario_id = uuid4()
        persona_id = uuid4()

        mock_scenario_repo = AsyncMock()
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_suite_repo = AsyncMock()
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        # Persona not found
        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        response = client.put(
            f"/api/v1/tests/scenarios/{scenario_id}",
            json={"persona_id": str(persona_id)},
        )

        assert response.status_code == 404
        assert "Persona" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_update_scenario_persona_inactive(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test scenario update when persona is inactive."""
        scenario_id = uuid4()
        persona_id = uuid4()

        # Inactive persona
        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=False,
        )

        mock_scenario_repo = AsyncMock()
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_suite_repo = AsyncMock()
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        response = client.put(
            f"/api/v1/tests/scenarios/{scenario_id}",
            json={"persona_id": str(persona_id)},
        )

        assert response.status_code == 400
        assert "inactive" in response.json()["detail"].lower()

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_with_status_filter(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test listing scenarios filtered by status."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        persona_id = uuid4()
        scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Ready Scenario",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            status="ready",
        )
        mock_repo.list_all.return_value = [scenario]
        mock_repo.count.return_value = 1
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/scenarios?status=ready")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        # Verify the repository was called with status filter
        mock_repo.list_all.assert_called_once()
        call_kwargs = mock_repo.list_all.call_args[1]
        assert call_kwargs.get("status") == "ready"

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_with_tags_filter(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test listing scenarios filtered by tags (returns scenarios with ANY tag)."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        persona_id = uuid4()
        scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Tagged Scenario",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            tags=["happy-path", "booking"],
        )
        mock_repo.list_all.return_value = [scenario]
        mock_repo.count.return_value = 1
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/scenarios?tags=happy-path&tags=urgent")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        # Verify the repository was called with tags filter
        mock_repo.list_all.assert_called_once()
        call_kwargs = mock_repo.list_all.call_args[1]
        assert call_kwargs.get("tags") == ["happy-path", "urgent"]

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_with_multiple_filters(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test listing scenarios with multiple filters combined."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        persona_id = uuid4()
        scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Filtered Scenario",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            status="ready",
            tags=["happy-path"],
        )
        mock_repo.list_all.return_value = [scenario]
        mock_repo.count.return_value = 1
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get(
            f"/api/v1/tests/scenarios?suite_id={suite_id}&status=ready&tags=happy-path"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        # Verify the repository was called with all filters
        mock_repo.list_all.assert_called_once()
        call_kwargs = mock_repo.list_all.call_args[1]
        assert call_kwargs.get("suite_id") == suite_id
        assert call_kwargs.get("status") == "ready"
        assert call_kwargs.get("tags") == ["happy-path"]

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_with_pagination(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test listing scenarios with custom pagination parameters."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        persona_id = uuid4()
        scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Scenario 1",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )
        mock_repo.list_all.return_value = [scenario]
        mock_repo.count.return_value = 50  # Total count is higher than returned
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/scenarios?limit=10&offset=20")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 50  # Total count
        assert len(data["scenarios"]) == 1  # Returned count
        assert data["limit"] == 10
        assert data["offset"] == 20
        # Verify repository was called with pagination params
        mock_repo.list_all.assert_called_once_with(
            suite_id=None, status=None, tags=None, limit=10, offset=20
        )

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_pagination_limit_max(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test that pagination limit is capped at 100."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_repo.count.return_value = 0
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        # Request limit > 100 should fail validation
        response = client.get("/api/v1/tests/scenarios?limit=200")

        assert response.status_code == 422  # Validation error

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_pagination_limit_min(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test that pagination limit must be at least 1."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_repo.count.return_value = 0
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        # Request limit < 1 should fail validation
        response = client.get("/api/v1/tests/scenarios?limit=0")

        assert response.status_code == 422  # Validation error

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_pagination_negative_offset(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test that pagination offset cannot be negative."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_repo.count.return_value = 0
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        # Negative offset should fail validation
        response = client.get("/api/v1/tests/scenarios?offset=-1")

        assert response.status_code == 422  # Validation error


class TestTestScenariosNewCrudFields:
    """Tests for new CRUD fields in test scenario endpoints."""

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_create_scenario_with_new_crud_fields(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test creating scenario with caller_behaviors and tags."""
        suite_id = uuid4()
        scenario_id = uuid4()
        persona_id = uuid4()

        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            created_at=datetime.utcnow(),
        )
        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
        )
        mock_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            caller_behaviors=["Ask about order", "Provide order number"],
            tags=["happy-path", "order"],
            status="ready",
        )

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = mock_suite
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.create.return_value = mock_scenario
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        response = client.post(
            "/api/v1/tests/scenarios",
            json={
                "suite_id": str(suite_id),
                "name": "Test Scenario",
                "goal": "Test goal",
                "persona_id": str(persona_id),
                "max_turns": 10,
                "timeout": 300,
                "caller_behaviors": ["Ask about order", "Provide order number"],
                "tags": ["happy-path", "order"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        # Verify the response includes new fields
        assert data["caller_behaviors"] == ["Ask about order", "Provide order number"]
        assert data["tags"] == ["happy-path", "order"]
        assert data["status"] == "ready"

        # Verify repository was called with new fields
        mock_scenario_repo.create.assert_called_once()
        call_kwargs = mock_scenario_repo.create.call_args[1]
        assert call_kwargs["caller_behaviors"] == ["Ask about order", "Provide order number"]
        assert call_kwargs["tags"] == ["happy-path", "order"]

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_update_scenario_with_new_crud_fields(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test updating scenario with caller_behaviors and tags."""
        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        updated_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Updated Scenario",
            goal="Updated goal",
            persona_id=persona_id,
            max_turns=15,
            timeout=600,
            caller_behaviors=["Updated step 1", "Updated step 2"],
            tags=["updated-tag"],
            status="ready",
        )

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.update.return_value = updated_scenario
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_suite_repo = AsyncMock()
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_persona_repo = AsyncMock()
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        response = client.put(
            f"/api/v1/tests/scenarios/{scenario_id}",
            json={
                "name": "Updated Scenario",
                "caller_behaviors": ["Updated step 1", "Updated step 2"],
                "tags": ["updated-tag"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Verify the response includes new fields
        assert data["caller_behaviors"] == ["Updated step 1", "Updated step 2"]
        assert data["tags"] == ["updated-tag"]
        assert data["status"] == "ready"

        # Verify repository was called with new fields
        mock_scenario_repo.update.assert_called_once()
        call_kwargs = mock_scenario_repo.update.call_args[1]
        assert call_kwargs["caller_behaviors"] == ["Updated step 1", "Updated step 2"]
        assert call_kwargs["tags"] == ["updated-tag"]

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_get_scenario_includes_new_crud_fields(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test getting scenario returns all new CRUD fields."""
        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        mock_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Test Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            intent="check_order",
            persona_traits=["patient"],
            persona_match_score=0.85,
            caller_behaviors=["Ask about order"],
            tags=["order", "happy-path"],
            status="ready",
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_scenario
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get(f"/api/v1/tests/scenarios/{scenario_id}")

        assert response.status_code == 200
        data = response.json()
        # Verify all new fields are in the response
        assert data["caller_behaviors"] == ["Ask about order"]
        assert data["tags"] == ["order", "happy-path"]
        assert data["status"] == "ready"
        # Also verify existing fields that were previously in the response
        assert data["intent"] == "check_order"
        assert data["persona_traits"] == ["patient"]
        assert data["persona_match_score"] == 0.85


class TestIsManualField:
    """Tests for is_manual field in test scenarios."""

    @patch("voiceobs.server.routes.test_dependencies.get_persona_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_persona_repo")
    def test_manual_scenario_has_is_manual_true(
        self,
        mock_get_persona_repo,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
        mock_get_persona_repository,
        client,
    ):
        """Test that manually created scenarios (no persona_traits) have is_manual=True."""
        suite_id = uuid4()
        scenario_id = uuid4()
        persona_id = uuid4()

        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            created_at=datetime.utcnow(),
        )
        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
        )
        # Manual scenario: no persona_traits, so is_manual should be True
        mock_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="Manual Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            persona_traits=[],  # Empty = manual
            is_manual=True,
        )

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = mock_suite
        mock_get_suite_repo.return_value = mock_suite_repo
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_persona_repo = AsyncMock()
        mock_persona_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_persona_repo
        mock_get_persona_repository.return_value = mock_persona_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.create.return_value = mock_scenario
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        response = client.post(
            "/api/v1/tests/scenarios",
            json={
                "suite_id": str(suite_id),
                "name": "Manual Scenario",
                "goal": "Test goal",
                "persona_id": str(persona_id),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_manual"] is True
        assert data["persona_match_score"] is None

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_ai_generated_scenario_has_is_manual_false(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test that AI-generated scenarios (with persona_traits) have is_manual=False."""
        scenario_id = uuid4()
        suite_id = uuid4()
        persona_id = uuid4()

        # AI-generated scenario: has persona_traits, so is_manual should be False
        mock_scenario = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            name="AI Generated Scenario",
            goal="Test goal",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
            persona_traits=["impatient", "direct"],  # Has traits = AI generated
            persona_match_score=0.85,
            is_manual=False,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_scenario
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get(f"/api/v1/tests/scenarios/{scenario_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["is_manual"] is False
        assert data["persona_match_score"] == 0.85
        assert data["persona_traits"] == ["impatient", "direct"]

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_list_scenarios_includes_is_manual(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
    ):
        """Test that listing scenarios includes is_manual field."""
        suite_id = uuid4()
        persona_id = uuid4()

        # One manual, one AI-generated
        manual_scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="Manual Scenario",
            goal="Goal 1",
            persona_id=persona_id,
            persona_traits=[],
            is_manual=True,
        )
        ai_scenario = TestScenarioRow(
            id=uuid4(),
            suite_id=suite_id,
            name="AI Scenario",
            goal="Goal 2",
            persona_id=persona_id,
            persona_traits=["patient"],
            persona_match_score=0.9,
            is_manual=False,
        )

        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = [manual_scenario, ai_scenario]
        mock_repo.count.return_value = 2
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

        # Find each scenario by name and verify is_manual
        scenarios_by_name = {s["name"]: s for s in data["scenarios"]}
        assert scenarios_by_name["Manual Scenario"]["is_manual"] is True
        assert scenarios_by_name["AI Scenario"]["is_manual"] is False
