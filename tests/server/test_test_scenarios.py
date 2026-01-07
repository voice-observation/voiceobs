"""Tests for the test scenario API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import TestScenarioRow, TestSuiteRow


class TestTestScenarios:
    """Tests for test scenario CRUD endpoints."""

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    def test_create_scenario_success(
        self,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
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

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_scenarios.get_test_suite_repo")
    def test_create_scenario_suite_not_found(
        self,
        mock_get_suite_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_scenario_repository,
        mock_get_suite_repository,
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
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/scenarios")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["scenarios"]) == 2

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
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_repo

        response = client.get(f"/api/v1/tests/scenarios?suite_id={suite_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        mock_repo.list_all.assert_called_once_with(suite_id=suite_id)

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

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_scenarios.get_test_scenario_repo")
    def test_update_scenario_success(
        self, mock_get_repo, mock_is_postgres, mock_get_scenario_repository, client
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
