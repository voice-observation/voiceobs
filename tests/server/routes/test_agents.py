"""Tests for the org-scoped agent API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.auth.context import AuthContext, require_org_membership
from voiceobs.server.db.models import AgentRow, OrganizationRow, UserRow


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


class TestAgents:
    """Tests for agent CRUD endpoints."""

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

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_create_phone_agent_success(
        self, mock_get_agent_repo, mock_get_verification_service, client
    ):
        """Test successful phone agent creation."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Customer Support Agent",
            goal="Help customers with inquiries",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["product_inquiry", "support_request"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={"department": "support"},
            created_at=now,
            updated_at=now,
            created_by="user@example.com",
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        mock_verification_service = AsyncMock()
        mock_get_verification_service.return_value = mock_verification_service

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents",
            json={
                "name": "Customer Support Agent",
                "agent_type": "phone",
                "phone_number": "+1234567890",
                "goal": "Help customers with inquiries",
                "supported_intents": ["product_inquiry", "support_request"],
                "metadata": {"department": "support"},
                "created_by": "user@example.com",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(agent_id)
        assert data["name"] == "Customer Support Agent"
        assert data["agent_type"] == "phone"
        assert data["phone_number"] == "+1234567890"
        assert data["goal"] == "Help customers with inquiries"
        assert data["connection_status"] == "saved"
        assert data["supported_intents"] == ["product_inquiry", "support_request"]

        # Verify repository was called correctly
        mock_repo.create.assert_called_once()
        call_kwargs = mock_repo.create.call_args[1]
        assert call_kwargs["org_id"] == self.org.id
        assert call_kwargs["name"] == "Customer Support Agent"
        assert call_kwargs["agent_type"] == "phone"
        assert call_kwargs["contact_info"] == {"phone_number": "+1234567890"}
        assert call_kwargs["goal"] == "Help customers with inquiries"

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_create_web_agent_success(
        self, mock_get_agent_repo, mock_get_verification_service, client
    ):
        """Test successful web agent creation."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Web Chat Agent",
            goal="Handle web inquiries",
            agent_type="web",
            contact_info={"web_url": "https://api.example.com/agent"},
            supported_intents=["product_inquiry"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        mock_verification_service = AsyncMock()
        mock_get_verification_service.return_value = mock_verification_service

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents",
            json={
                "name": "Web Chat Agent",
                "agent_type": "web",
                "web_url": "https://api.example.com/agent",
                "goal": "Handle web inquiries",
                "supported_intents": ["product_inquiry"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(agent_id)
        assert data["name"] == "Web Chat Agent"
        assert data["agent_type"] == "web"
        assert data["web_url"] == "https://api.example.com/agent"
        assert data["goal"] == "Handle web inquiries"

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_create_agent_validation_error(
        self, mock_get_agent_repo, mock_get_verification_service, client
    ):
        """Test agent creation with repository validation error."""
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = ValueError("Invalid phone number format")
        mock_get_agent_repo.return_value = mock_repo

        # Provide a valid request that will pass pydantic validation and reach repository
        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents",
            json={
                "name": "Test Agent",
                "agent_type": "phone",
                "phone_number": "+1234567890",
                "goal": "Test goal",
                "supported_intents": ["intent1"],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid phone number format" in data["detail"]

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_list_agents_success(self, mock_get_agent_repo, client):
        """Test listing agents."""
        agent1_id = uuid4()
        agent2_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agents = [
            AgentRow(
                id=agent1_id,
                org_id=self.org.id,
                name="Phone Agent",
                goal="Phone support",
                agent_type="phone",
                contact_info={"phone_number": "+1234567890"},
                supported_intents=["support"],
                connection_status="verified",
                verification_attempts=1,
                last_verification_at=now,
                verification_error=None,
                metadata={},
                created_at=now,
                updated_at=now,
                created_by=None,
                is_active=True,
            ),
            AgentRow(
                id=agent2_id,
                org_id=self.org.id,
                name="Web Agent",
                goal="Web support",
                agent_type="web",
                contact_info={"web_url": "https://api.example.com"},
                supported_intents=["inquiry"],
                connection_status="saved",
                verification_attempts=0,
                last_verification_at=None,
                verification_error=None,
                metadata={},
                created_at=now,
                updated_at=now,
                created_by=None,
                is_active=True,
            ),
        ]

        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = mock_agents
        mock_get_agent_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["agents"]) == 2
        assert data["agents"][0]["name"] == "Phone Agent"
        assert data["agents"][0]["phone_number"] == "+1234567890"
        assert data["agents"][1]["name"] == "Web Agent"
        assert data["agents"][1]["web_url"] == "https://api.example.com"

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_list_agents_with_filters(self, mock_get_agent_repo, client):
        """Test listing agents with query filters."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_get_agent_repo.return_value = mock_repo

        base = f"/api/v1/orgs/{self.org.id}/agents"
        url = f"{base}?connection_status=verified&is_active=true&limit=10&offset=5"
        response = client.get(url)

        assert response.status_code == 200
        mock_repo.list_all.assert_called_once_with(
            org_id=self.org.id,
            connection_status="verified",
            is_active=True,
            limit=10,
            offset=5,
        )

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_get_agent_success(self, mock_get_agent_repo, client):
        """Test getting a single agent by ID."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1", "intent2"],
            connection_status="verified",
            verification_attempts=1,
            last_verification_at=now,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={"key": "value"},
            created_at=now,
            updated_at=now,
            created_by="user@example.com",
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(agent_id)
        assert data["name"] == "Test Agent"
        assert data["phone_number"] == "+1234567890"
        assert data["supported_intents"] == ["intent1", "intent2"]

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_get_agent_not_found(self, mock_get_agent_repo, client):
        """Test getting a non-existent agent."""
        agent_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_agent_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/agents/{agent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_get_agent_invalid_uuid(self, mock_get_agent_repo, client):
        """Test getting an agent with invalid UUID."""
        response = client.get(f"/api/v1/orgs/{self.org.id}/agents/invalid-uuid")

        assert response.status_code == 400
        data = response.json()
        assert "invalid" in data["detail"].lower()

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_update_agent_success(self, mock_get_agent_repo, client):
        """Test updating an agent."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        existing_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Old Name",
            goal="Old goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["old_intent"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        updated_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="New Name",
            goal="New goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["new_intent"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={"updated": True},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_agent
        mock_repo.update.return_value = updated_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}",
            json={
                "name": "New Name",
                "goal": "New goal",
                "supported_intents": ["new_intent"],
                "metadata": {"updated": True},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["goal"] == "New goal"
        assert data["supported_intents"] == ["new_intent"]
        assert data["metadata"]["updated"] is True

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_update_agent_phone_number(
        self, mock_get_agent_repo, mock_get_verification_service, client
    ):
        """Test updating agent phone number."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        existing_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        updated_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+9876543210"},
            supported_intents=["intent1"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_agent
        mock_repo.update.return_value = updated_agent
        mock_get_agent_repo.return_value = mock_repo

        mock_verification_service = AsyncMock()
        mock_get_verification_service.return_value = mock_verification_service

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}",
            json={"phone_number": "+9876543210"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "+9876543210"

        # Verify contact_info was merged correctly
        call_kwargs = mock_repo.update.call_args[1]
        assert call_kwargs["contact_info"]["phone_number"] == "+9876543210"

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_update_agent_not_found(self, mock_get_agent_repo, client):
        """Test updating a non-existent agent."""
        agent_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_agent_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_update_agent_validation_error(self, mock_get_agent_repo, client):
        """Test updating agent with validation error from repository."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        existing_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_agent
        mock_repo.update.side_effect = ValueError("phone_number is required for phone agents")
        mock_get_agent_repo.return_value = mock_repo

        # Send a valid request that will reach the repository where the error is raised
        response = client.put(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "phone_number is required" in data["detail"]

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_delete_agent(self, mock_get_agent_repo, client):
        """Test deleting an agent."""
        agent_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_get_agent_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/orgs/{self.org.id}/agents/{agent_id}")

        assert response.status_code == 204
        mock_repo.delete.assert_called_once_with(agent_id, self.org.id)

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_delete_agent_not_found(self, mock_get_agent_repo, client):
        """Test deleting a non-existent agent."""
        agent_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        mock_get_agent_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/orgs/{self.org.id}/agents/{agent_id}")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_verify_agent_success(self, mock_get_agent_repo, mock_get_verification_service, client):
        """Test verifying an agent."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"],
            connection_status="saved",
            verification_attempts=0,
            last_verification_at=None,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        mock_verification_service = AsyncMock()
        mock_get_verification_service.return_value = mock_verification_service

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verify",
            json={"force": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(agent_id)
        assert data["connection_status"] == "saved"

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_verify_agent_already_verified(self, mock_get_agent_repo, client):
        """Test verifying an already verified agent without force."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"],
            connection_status="verified",
            verification_attempts=1,
            last_verification_at=now,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verify",
            json={"force": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["connection_status"] == "verified"

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_verify_agent_force(self, mock_get_agent_repo, mock_get_verification_service, client):
        """Test force verifying an agent."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"],
            connection_status="verified",
            verification_attempts=1,
            last_verification_at=now,
            verification_error=None,
            verification_transcript=None,
            verification_reasoning=None,
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        mock_verification_service = AsyncMock()
        mock_get_verification_service.return_value = mock_verification_service

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verify",
            json={"force": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(agent_id)

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_verify_agent_not_found(self, mock_get_agent_repo, client):
        """Test verifying a non-existent agent."""
        agent_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_agent_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verify",
            json={"force": False},
        )

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_list_agents_empty(self, mock_get_agent_repo, client):
        """Test listing agents when no agents exist."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_get_agent_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/agents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["agents"] == []

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_get_verification_status_success(self, mock_get_agent_repo, client):
        """Test getting verification status for a valid agent."""
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id,
            org_id=self.org.id,
            name="Test Agent",
            goal="Test goal",
            agent_type="phone",
            contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"],
            connection_status="verified",
            verification_attempts=2,
            last_verification_at=now,
            verification_error=None,
            verification_transcript=[
                {"role": "assistant", "content": "Hello, this is verification call."},
                {"role": "user", "content": "Hi, how can I help you?"},
            ],
            verification_reasoning="Agent responded correctly to verification prompt.",
            metadata={},
            created_at=now,
            updated_at=now,
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verification-status")

        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == str(agent_id)
        assert data["status"] == "verified"
        assert data["attempts"] == 2
        assert data["reasoning"] == "Agent responded correctly to verification prompt."
        assert len(data["transcript"]) == 2
        assert data["transcript"][0]["role"] == "assistant"
        assert data["error"] is None

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_get_verification_status_not_found(self, mock_get_agent_repo, client):
        """Test getting verification status for a non-existent agent."""
        agent_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_agent_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verification-status")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
