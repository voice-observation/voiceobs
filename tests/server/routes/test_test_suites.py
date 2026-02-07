"""Tests for the test suite API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from voiceobs.server.db.models import AgentRow, TestSuiteRow


class TestTestSuites:
    """Tests for test suite CRUD endpoints."""

    def test_create_suite_requires_postgres(self, client):
        """Test that creating a suite requires PostgreSQL."""
        agent_id = uuid4()
        response = client.post(
            "/api/v1/tests/suites",
            json={
                "name": "Test Suite",
                "description": "Test description",
                "agent_id": str(agent_id),
            },
        )

        assert response.status_code == 501
        assert "PostgreSQL" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_suites.require_postgres")
    @patch("voiceobs.server.routes.test_suites.get_agent_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_create_suite_requires_agent_id(
        self,
        mock_get_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_agent_repository,
        mock_require_postgres,
        client,
    ):
        """Test that creating a suite requires agent_id."""
        mock_repo = AsyncMock()
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        # Mock agent repository getter
        mock_agent_repo = AsyncMock()
        mock_get_agent_repository.return_value = mock_agent_repo

        response = client.post(
            "/api/v1/tests/suites",
            json={"name": "Test Suite", "description": "Test description"},
        )

        # Should get a 422 validation error for missing agent_id
        assert response.status_code == 422
        errors = response.json()["detail"]
        assert any("agent_id" in str(e) for e in errors)

    @patch("voiceobs.server.routes.test_suites.require_postgres")
    @patch("voiceobs.server.routes.test_suites.get_agent_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_create_suite_success(
        self,
        mock_get_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_agent_repository,
        mock_require_postgres,
        client,
    ):
        """Test successful suite creation."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        agent_id = uuid4()
        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            agent_id=agent_id,
            created_at=datetime.utcnow(),
        )
        mock_repo.create.return_value = mock_suite
        # Mock the dependency function to return the mock repo when called
        mock_get_repo.return_value = mock_repo
        # Also mock the underlying repository getter that the dependency function calls
        mock_get_repository.return_value = mock_repo

        # Mock agent repository - return a mock agent
        mock_agent_repo = AsyncMock()
        mock_agent = MagicMock(spec=AgentRow)
        mock_agent.id = agent_id
        mock_agent_repo.get.return_value = mock_agent
        mock_get_agent_repository.return_value = mock_agent_repo

        response = client.post(
            "/api/v1/tests/suites",
            json={
                "name": "Test Suite",
                "description": "Test description",
                "agent_id": str(agent_id),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Suite"
        assert data["description"] == "Test description"
        assert data["status"] == "pending"
        assert data["agent_id"] == str(agent_id)
        assert "id" in data

    @patch("voiceobs.server.routes.test_suites.require_postgres")
    @patch("voiceobs.server.routes.test_suites.get_agent_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_create_suite_agent_not_found(
        self,
        mock_get_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_agent_repository,
        mock_require_postgres,
        client,
    ):
        """Test suite creation fails when agent not found."""
        mock_repo = AsyncMock()
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        # Mock agent repository - return None for agent not found
        mock_agent_repo = AsyncMock()
        mock_agent_repo.get.return_value = None
        mock_get_agent_repository.return_value = mock_agent_repo

        agent_id = uuid4()
        response = client.post(
            "/api/v1/tests/suites",
            json={
                "name": "Test Suite",
                "description": "Test description",
                "agent_id": str(agent_id),
            },
        )

        assert response.status_code == 404
        assert "Agent" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_suites.require_postgres")
    @patch("voiceobs.server.routes.test_suites.get_agent_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_create_suite_invalid_agent_id_format(
        self,
        mock_get_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_agent_repository,
        mock_require_postgres,
        client,
    ):
        """Test that creating a suite with invalid agent_id format returns 400."""
        mock_repo = AsyncMock()
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        # Mock agent repository
        mock_agent_repo = AsyncMock()
        mock_get_agent_repository.return_value = mock_agent_repo

        response = client.post(
            "/api/v1/tests/suites",
            json={
                "name": "Test Suite",
                "description": "A test suite",
                "agent_id": "not-a-valid-uuid",
            },
        )

        assert response.status_code == 400
        assert "Invalid agent ID format" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_list_suites_success(
        self,
        mock_get_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_scenario_repository,
        client,
    ):
        """Test successful suite listing."""
        mock_repo = AsyncMock()
        mock_scenario_repo = AsyncMock()
        agent_id1 = uuid4()
        agent_id2 = uuid4()
        suite1_id = uuid4()
        suite2_id = uuid4()
        suite1 = TestSuiteRow(
            id=suite1_id,
            name="Suite 1",
            description="Description 1",
            status="pending",
            agent_id=agent_id1,
            created_at=datetime.utcnow(),
        )
        suite2 = TestSuiteRow(
            id=suite2_id,
            name="Suite 2",
            description="Description 2",
            status="completed",
            agent_id=agent_id2,
            created_at=datetime.utcnow(),
        )
        mock_repo.list_all.return_value = [suite1, suite2]
        mock_scenario_repo.list_all.return_value = []  # No scenarios
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_repository.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        response = client.get("/api/v1/tests/suites")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["suites"]) == 2
        assert data["suites"][0]["name"] == "Suite 1"
        assert data["suites"][0]["agent_id"] == str(agent_id1)
        assert data["suites"][0]["scenario_count"] == 0
        assert data["suites"][1]["name"] == "Suite 2"
        assert data["suites"][1]["agent_id"] == str(agent_id2)
        assert data["suites"][1]["scenario_count"] == 0

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_get_suite_success(
        self,
        mock_get_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_scenario_repository,
        client,
    ):
        """Test successful suite retrieval."""
        mock_repo = AsyncMock()
        mock_scenario_repo = AsyncMock()
        suite_id = uuid4()
        agent_id = uuid4()
        mock_suite = TestSuiteRow(
            id=suite_id,
            name="Test Suite",
            description="Test description",
            status="pending",
            agent_id=agent_id,
            created_at=datetime.utcnow(),
        )
        mock_repo.get.return_value = mock_suite
        mock_scenario_repo.list_all.return_value = []  # No scenarios
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_repository.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        response = client.get(f"/api/v1/tests/suites/{suite_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Suite"
        assert data["id"] == str(suite_id)
        assert data["agent_id"] == str(agent_id)
        assert data["scenario_count"] == 0

    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_scenario_repo")
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_get_suite_not_found(
        self,
        mock_get_repo,
        mock_get_scenario_repo,
        mock_is_postgres,
        mock_get_repository,
        mock_get_scenario_repository,
        client,
    ):
        """Test suite not found."""
        mock_repo = AsyncMock()
        mock_scenario_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_repo.return_value = mock_repo
        mock_get_scenario_repo.return_value = mock_scenario_repo
        mock_get_repository.return_value = mock_repo
        mock_get_scenario_repository.return_value = mock_scenario_repo

        suite_id = uuid4()
        response = client.get(f"/api/v1/tests/suites/{suite_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_update_suite_success(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test successful suite update."""
        mock_repo = AsyncMock()
        suite_id = uuid4()
        agent_id = uuid4()
        updated_suite = TestSuiteRow(
            id=suite_id,
            name="Updated Suite",
            description="Updated description",
            status="running",
            agent_id=agent_id,
            created_at=datetime.utcnow(),
        )
        mock_repo.update.return_value = updated_suite
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        response = client.put(
            f"/api/v1/tests/suites/{suite_id}",
            json={"name": "Updated Suite", "status": "running"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Suite"
        assert data["status"] == "running"
        assert data["agent_id"] == str(agent_id)

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_delete_suite_success(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test successful suite deletion."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        suite_id = uuid4()
        response = client.delete(f"/api/v1/tests/suites/{suite_id}")

        assert response.status_code == 204

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.test_suites.get_test_suite_repo")
    def test_delete_suite_not_found(
        self, mock_get_repo, mock_is_postgres, mock_get_repository, client
    ):
        """Test suite deletion when not found."""
        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        mock_get_repo.return_value = mock_repo
        mock_get_repository.return_value = mock_repo

        suite_id = uuid4()
        response = client.delete(f"/api/v1/tests/suites/{suite_id}")

        assert response.status_code == 404
