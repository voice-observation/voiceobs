"""Tests for suite run API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.auth.context import AuthContext, require_org_membership
from voiceobs.server.db.models import (
    OrganizationRow,
    TestExecutionRow,
    TestScenarioRow,
    TestSuiteRow,
    TestSuiteRunRow,
    UserRow,
)


def make_user(**kwargs):
    """Create a test UserRow with sensible defaults."""
    defaults = dict(id=uuid4(), email="test@example.com", name="Test User", is_active=True)
    defaults.update(kwargs)
    return UserRow(**defaults)


def make_org(**kwargs):
    """Create a test OrganizationRow with sensible defaults."""
    defaults = dict(id=uuid4(), name="Test Org", created_by=uuid4())
    defaults.update(kwargs)
    return OrganizationRow(**defaults)


class TestSuiteRuns:
    """Tests for suite run endpoints."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, client):
        """Set up auth context override for all tests."""
        self.user = make_user()
        self.org = make_org()
        self.auth_context = AuthContext(user=self.user, org=self.org)
        app = client.app

        async def override_require_org_membership():
            return self.auth_context

        app.dependency_overrides[require_org_membership] = override_require_org_membership
        yield
        app.dependency_overrides.pop(require_org_membership, None)

    @patch("voiceobs.server.routes.test_dependencies.get_execution_orchestration_service")
    def test_run_suite_returns_503_when_sqs_not_configured(
        self,
        mock_get_orchestration,
        client,
    ):
        """Test run_suite returns 503 when SQS is not configured."""
        mock_get_orchestration.return_value = None

        suite_id = uuid4()
        response = client.post(
            f"/api/v1/orgs/{self.org.id}/test-suites/{suite_id}/run",
        )

        assert response.status_code == 503
        assert "SQS" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_dependencies.get_execution_orchestration_service")
    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    def test_run_suite_success(
        self,
        mock_is_postgres,
        mock_get_scenario_repo,
        mock_get_suite_repo,
        mock_get_orchestration,
        client,
    ):
        """Test run_suite returns 202 with suite run."""
        from voiceobs.server.models import TriggerResult

        suite_id = uuid4()
        suite_run_id = uuid4()

        mock_orchestration = AsyncMock()
        mock_orchestration.trigger_suite_run.return_value = TriggerResult(
            suite_run_id=suite_run_id,
            total_scenarios=1,
        )
        mock_get_orchestration.return_value = mock_orchestration

        mock_suite_repo = AsyncMock()
        mock_suite_repo.get.return_value = TestSuiteRow(
            id=suite_id,
            org_id=self.org.id,
            name="Suite",
            status="ready",
            created_at=datetime.utcnow(),
        )
        mock_get_suite_repo.return_value = mock_suite_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.list_all.return_value = [
            TestScenarioRow(
                id=uuid4(),
                suite_id=suite_id,
                org_id=self.org.id,
                name="Scenario",
                goal="Goal",
                persona_id=uuid4(),
            )
        ]
        mock_get_scenario_repo.return_value = mock_scenario_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/test-suites/{suite_id}/run",
        )

        assert response.status_code == 202
        data = response.json()
        assert data["suite_run_id"] == str(suite_run_id)
        assert data["status"] == "running"
        assert data["total_scenarios"] == 1
        mock_orchestration.trigger_suite_run.assert_called_once_with(
            org_id=self.org.id,
            suite_id=suite_id,
            triggered_by=str(self.user.id),
        )

    @patch("voiceobs.server.routes.test_dependencies.get_execution_orchestration_service")
    def test_run_scenario_returns_503_when_sqs_not_configured(
        self,
        mock_get_orchestration,
        client,
    ):
        """Test run_scenario returns 503 when SQS is not configured."""
        mock_get_orchestration.return_value = None

        scenario_id = uuid4()
        response = client.post(
            f"/api/v1/orgs/{self.org.id}/test-scenarios/{scenario_id}/run",
        )

        assert response.status_code == 503
        assert "SQS" in response.json()["detail"]

    @patch("voiceobs.server.routes.test_dependencies.get_execution_orchestration_service")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    def test_run_scenario_success(
        self,
        mock_is_postgres,
        mock_get_scenario_repo,
        mock_get_orchestration,
        client,
    ):
        """Test run_scenario returns 202 with suite run."""
        from voiceobs.server.models import TriggerResult

        scenario_id = uuid4()
        suite_run_id = uuid4()

        mock_orchestration = AsyncMock()
        mock_orchestration.trigger_scenario_run.return_value = TriggerResult(
            suite_run_id=suite_run_id,
            total_scenarios=1,
        )
        mock_get_orchestration.return_value = mock_orchestration

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.get.return_value = TestScenarioRow(
            id=scenario_id,
            suite_id=uuid4(),
            org_id=self.org.id,
            name="Scenario",
            goal="Goal",
            persona_id=uuid4(),
        )
        mock_get_scenario_repo.return_value = mock_scenario_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/test-scenarios/{scenario_id}/run",
        )

        assert response.status_code == 202
        data = response.json()
        assert data["suite_run_id"] == str(suite_run_id)
        assert data["status"] == "running"
        assert data["total_scenarios"] == 1
        mock_orchestration.trigger_scenario_run.assert_called_once_with(
            org_id=self.org.id,
            scenario_id=scenario_id,
            triggered_by=str(self.user.id),
        )

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_run_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_scenario_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    def test_get_suite_run_success(
        self,
        mock_is_postgres,
        mock_get_scenario_repo,
        mock_get_execution_repo,
        mock_get_suite_run_repo,
        client,
    ):
        """Test get_suite_run returns suite run with executions."""
        suite_id = uuid4()
        suite_run_id = uuid4()
        execution_id = uuid4()
        scenario_id = uuid4()

        mock_suite_run_repo = AsyncMock()
        mock_suite_run_repo.get.return_value = TestSuiteRunRow(
            id=suite_run_id,
            org_id=self.org.id,
            suite_id=suite_id,
            total_scenarios=1,
            status="running",
            completed_scenarios=0,
            failed_scenarios=0,
            created_at=datetime.utcnow(),
        )
        mock_get_suite_run_repo.return_value = mock_suite_run_repo

        mock_execution_repo = AsyncMock()
        mock_execution_repo.list_by_suite_run.return_value = [
            TestExecutionRow(
                id=execution_id,
                org_id=self.org.id,
                suite_run_id=suite_run_id,
                scenario_id=scenario_id,
                status="queued",
            )
        ]
        mock_get_execution_repo.return_value = mock_execution_repo

        mock_scenario_repo = AsyncMock()
        mock_scenario_repo.get_by_id.return_value = TestScenarioRow(
            id=scenario_id,
            suite_id=suite_id,
            org_id=self.org.id,
            name="Test Scenario",
            goal="Goal",
            persona_id=uuid4(),
        )
        mock_get_scenario_repo.return_value = mock_scenario_repo

        response = client.get(
            f"/api/v1/orgs/{self.org.id}/suite-runs/{suite_run_id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(suite_run_id)
        assert data["status"] == "running"
        assert len(data["executions"]) == 1

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_run_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    def test_get_suite_run_not_found(
        self,
        mock_is_postgres,
        mock_get_execution_repo,
        mock_get_suite_run_repo,
        client,
    ):
        """Test get_suite_run returns 404 when not found."""
        mock_suite_run_repo = AsyncMock()
        mock_suite_run_repo.get.return_value = None
        mock_get_suite_run_repo.return_value = mock_suite_run_repo

        response = client.get(
            f"/api/v1/orgs/{self.org.id}/suite-runs/{uuid4()}",
        )

        assert response.status_code == 404

    @patch("voiceobs.server.routes.test_dependencies.get_test_suite_run_repository")
    @patch("voiceobs.server.routes.test_dependencies.get_test_execution_repository")
    @patch("voiceobs.server.routes.test_dependencies.is_using_postgres", return_value=True)
    def test_get_execution_success(
        self,
        mock_is_postgres,
        mock_get_execution_repo,
        mock_get_suite_run_repo,
        client,
    ):
        """Test get_execution returns execution detail."""
        execution_id = uuid4()
        scenario_id = uuid4()
        suite_run_id = uuid4()

        mock_execution_repo = AsyncMock()
        mock_execution_repo.get.return_value = TestExecutionRow(
            id=execution_id,
            org_id=self.org.id,
            suite_run_id=suite_run_id,
            scenario_id=scenario_id,
            status="completed",
            audio_url="s3://bucket/audio.wav",
            transcript=[{"role": "agent", "text": "Hello"}],
            evaluation_result={"passed": True},
            duration_seconds=30.5,
            attempt=1,
        )
        mock_get_execution_repo.return_value = mock_execution_repo

        response = client.get(
            f"/api/v1/orgs/{self.org.id}/executions/{execution_id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(execution_id)
        assert data["status"] == "completed"
        assert data["audio_url"] == "s3://bucket/audio.wav"
        assert data["duration_seconds"] == 30.5
