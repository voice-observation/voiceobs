"""Tests for the test execution API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import TestExecutionRow, TestScenarioRow, TestSuiteRow


class TestTestExecution:
    """Tests for test execution endpoints."""

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_repos")
    def test_run_tests_with_suite_id(
        self,
        mock_get_repos,
        mock_is_postgres,
        mock_get_suite_repository,
        mock_get_scenario_repository,
        mock_get_execution_repository,
        client,
    ):
        """Test running tests with suite ID."""
        suite_id = uuid4()
        scenario_id = uuid4()
        execution_id = uuid4()

        mock_suite = TestSuiteRow(
            id=suite_id,
            org_id=uuid4(),
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
        mock_execution = TestExecutionRow(
            id=execution_id,
            scenario_id=scenario_id,
            conversation_id=None,
            status="queued",
            started_at=None,
            completed_at=None,
            result_json={},
        )

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get_by_id.return_value = mock_suite
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.list_all.return_value = [mock_scenario]
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_execution_repo = AsyncMock()
        mock_execution_repo.create.return_value = mock_execution
        mock_get_execution_repository.return_value = mock_execution_repo

        # get_test_repos returns a tuple of (suite_repo, scenario_repo, execution_repo)
        mock_get_repos.return_value = (mock_suite_repo, mock_scenario_repo, mock_execution_repo)

        response = client.post(
            "/api/v1/tests/run",
            json={"suite_id": str(suite_id), "max_workers": 10},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "queued"
        assert data["scenarios_count"] == 1
        assert "execution_id" in data

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_repos")
    def test_run_tests_with_scenarios(
        self,
        mock_get_repos,
        mock_is_postgres,
        mock_get_suite_repository,
        mock_get_scenario_repository,
        mock_get_execution_repository,
        client,
    ):
        """Test running tests with specific scenario IDs."""
        scenario_id1 = uuid4()
        scenario_id2 = uuid4()
        execution_id = uuid4()

        persona_id = uuid4()
        mock_scenario1 = TestScenarioRow(
            id=scenario_id1,
            suite_id=uuid4(),
            name="Scenario 1",
            goal="Goal 1",
            persona_id=persona_id,
            max_turns=10,
            timeout=300,
        )
        mock_scenario2 = TestScenarioRow(
            id=scenario_id2,
            suite_id=uuid4(),
            name="Scenario 2",
            goal="Goal 2",
            persona_id=persona_id,
            max_turns=15,
            timeout=600,
        )
        mock_execution = TestExecutionRow(
            id=execution_id,
            scenario_id=scenario_id1,
            conversation_id=None,
            status="queued",
            started_at=None,
            completed_at=None,
            result_json={},
        )

        mock_suite_repo = AsyncMock()
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.get.side_effect = [mock_scenario1, mock_scenario2]
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_execution_repo = AsyncMock()
        mock_execution_repo.create.return_value = mock_execution
        mock_get_execution_repository.return_value = mock_execution_repo

        # get_test_repos returns a tuple of (suite_repo, scenario_repo, execution_repo)
        mock_get_repos.return_value = (mock_suite_repo, mock_scenario_repo, mock_execution_repo)

        response = client.post(
            "/api/v1/tests/run",
            json={
                "scenarios": [str(scenario_id1), str(scenario_id2)],
                "max_workers": 10,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "queued"
        assert data["scenarios_count"] == 2

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_repos")
    def test_run_tests_suite_not_found(
        self,
        mock_get_repos,
        mock_is_postgres,
        mock_get_suite_repository,
        mock_get_scenario_repository,
        mock_get_execution_repository,
        client,
    ):
        """Test running tests when suite not found."""
        mock_suite_repo = AsyncMock()
        mock_suite_repo.get_by_id.return_value = None
        mock_get_suite_repository.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_get_scenario_repository.return_value = mock_scenario_repo

        mock_execution_repo = AsyncMock()
        mock_get_execution_repository.return_value = mock_execution_repo

        # get_test_repos returns a tuple of (suite_repo, scenario_repo, execution_repo)
        mock_get_repos.return_value = (mock_suite_repo, mock_scenario_repo, mock_execution_repo)

        suite_id = uuid4()
        response = client.post(
            "/api/v1/tests/run",
            json={"suite_id": str(suite_id), "max_workers": 10},
        )

        assert response.status_code == 404

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_execution_repo")
    def test_get_summary_success(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test successful summary retrieval."""
        mock_repo = AsyncMock()
        mock_repo.get_summary.return_value = {
            "total": 50,
            "passed": 40,
            "failed": 10,
            "pass_rate": 0.8,
            "avg_duration_ms": 45000.0,
            "avg_latency_ms": 850.0,
        }
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        response = client.get("/api/v1/tests/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 50
        assert data["passed"] == 40
        assert data["failed"] == 10
        assert data["pass_rate"] == 0.8
        assert data["avg_duration_ms"] == 45000.0
        assert data["avg_latency_ms"] == 850.0

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_execution_repo")
    def test_get_summary_with_suite_filter(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test summary with suite filter."""
        mock_repo = AsyncMock()
        mock_repo.get_summary.return_value = {
            "total": 20,
            "passed": 18,
            "failed": 2,
            "pass_rate": 0.9,
            "avg_duration_ms": 30000.0,
            "avg_latency_ms": 750.0,
        }
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        suite_id = uuid4()
        response = client.get(f"/api/v1/tests/summary?suite_id={suite_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 20
        mock_repo.get_summary.assert_called_once_with(suite_id=suite_id)

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_execution_repo")
    def test_get_execution_success(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test successful execution retrieval."""
        mock_repo = AsyncMock()
        execution_id = uuid4()
        mock_execution = TestExecutionRow(
            id=execution_id,
            scenario_id=uuid4(),
            conversation_id=uuid4(),
            status="completed",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            result_json={"passed": True, "score": 0.95},
        )
        mock_repo.get.return_value = mock_execution
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        response = client.get(f"/api/v1/tests/executions/{execution_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["id"] == str(execution_id)
        assert "conversation_id" in data

    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_executions.get_test_execution_repo")
    def test_get_execution_not_found(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test execution not found."""
        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        execution_id = uuid4()
        response = client.get(f"/api/v1/tests/executions/{execution_id}")

        assert response.status_code == 404
