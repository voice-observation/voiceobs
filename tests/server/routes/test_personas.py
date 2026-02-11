"""Tests for the org-scoped persona API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.auth.context import AuthContext, require_org_membership
from voiceobs.server.db.models import OrganizationRow, PersonaRow, UserRow
from voiceobs.server.routes.personas import DEFAULT_PREVIEW_TEXT


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


def make_persona(org_id, **kwargs):
    """Create a test PersonaRow with sensible defaults."""
    defaults = dict(
        id=uuid4(),
        name="Test Persona",
        aggression=0.5,
        patience=0.5,
        verbosity=0.5,
        tts_provider="openai",
        tts_config={},
        traits=[],
        description=None,
        preview_audio_url=None,
        preview_audio_text=None,
        preview_audio_status=None,
        preview_audio_error=None,
        metadata={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by=None,
        is_active=True,
        is_default=False,
        org_id=org_id,
        persona_type="custom",
    )
    defaults.update(kwargs)
    return PersonaRow(**defaults)


class TestPersonas:
    """Tests for org-scoped persona CRUD endpoints."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, client):
        """Set up auth context override for all tests.

        Creates user and org objects and overrides the require_org_membership dependency
        so that FastAPI injects our mock AuthContext.
        """
        self.user = make_user()
        self.org = make_org()
        self.auth_context = AuthContext(user=self.user, org=self.org)

        # Get the underlying FastAPI app from the TestClient
        app = client.app

        async def override_require_org_membership():
            return self.auth_context

        app.dependency_overrides[require_org_membership] = override_require_org_membership
        yield
        app.dependency_overrides.pop(require_org_membership, None)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_list_personas_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test GET /api/v1/orgs/{org_id}/personas returns 200 with personas."""
        persona1 = make_persona(self.org.id, name="Polite Customer")
        persona2 = make_persona(self.org.id, name="Angry Customer")

        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = [persona1, persona2]
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/personas")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["personas"]) == 2
        assert data["personas"][0]["name"] == "Polite Customer"
        assert data["personas"][1]["name"] == "Angry Customer"
        assert data["personas"][0]["persona_type"] == "custom"

        mock_repo.list_all.assert_called_once_with(
            is_active=None, limit=None, offset=None, org_id=self.org.id
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_list_personas_with_filters(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test listing personas with query filters passes them through."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(
            f"/api/v1/orgs/{self.org.id}/personas?is_active=false&limit=10&offset=5"
        )

        assert response.status_code == 200
        mock_repo.list_all.assert_called_once_with(
            is_active=False, limit=10, offset=5, org_id=self.org.id
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_create_persona_sets_custom_type(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test POST creates persona with persona_type='custom' and org_id."""
        persona = make_persona(
            self.org.id,
            name="Angry Customer",
            description="An aggressive customer persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            traits=["impatient", "demanding"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            metadata={"category": "customer"},
            created_by="user@example.com",
            persona_type="custom",
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/personas",
            json={
                "name": "Angry Customer",
                "description": "An aggressive customer persona",
                "aggression": 0.8,
                "patience": 0.2,
                "verbosity": 0.6,
                "traits": ["impatient", "demanding"],
                "tts_provider": "openai",
                "tts_config": {"model": "tts-1", "voice": "alloy", "speed": 1.0},
                "metadata": {"category": "customer"},
                "created_by": "user@example.com",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Angry Customer"
        assert data["persona_type"] == "custom"
        assert data["preview_audio_url"] is None

        # Verify create was called with org_id and persona_type
        mock_repo.create.assert_called_once()
        call_kwargs = mock_repo.create.call_args.kwargs
        assert call_kwargs["org_id"] == self.org.id
        assert call_kwargs["persona_type"] == "custom"

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_persona_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test GET /api/v1/orgs/{org_id}/personas/{id} returns 200."""
        persona = make_persona(self.org.id, name="Test Persona")

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(persona.id)
        assert data["name"] == "Test Persona"
        assert data["persona_type"] == "custom"

        mock_repo.get.assert_called_once_with(persona.id, org_id=self.org.id)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test GET on non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/personas/{persona_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_update_persona_with_tts_change(
        self,
        mock_get_audio_storage,
        mock_get_persona_repo,
        client,
    ):
        """Test PUT clears preview audio when TTS settings change."""
        old_preview_url = "https://example.com/old_preview.mp3"
        existing_persona = make_persona(
            self.org.id,
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy"},
            preview_audio_url=old_preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
        )

        updated_persona = make_persona(
            self.org.id,
            id=existing_persona.id,
            tts_provider="elevenlabs",
            tts_config={"voice_id": "new_voice"},
            preview_audio_url=None,
            preview_audio_text=None,
        )

        mock_audio_storage = AsyncMock()
        mock_get_audio_storage.return_value = mock_audio_storage

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = updated_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/personas/{existing_persona.id}",
            json={
                "tts_provider": "elevenlabs",
                "tts_config": {"voice_id": "new_voice"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tts_provider"] == "elevenlabs"
        assert data["preview_audio_url"] is None
        assert data["persona_type"] == "custom"

        mock_audio_storage.delete_by_url.assert_called_once_with(old_preview_url)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_update_persona_without_tts_change(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test PUT preserves audio when no TTS change."""
        preview_url = "https://example.com/preview.mp3"
        existing_persona = make_persona(
            self.org.id,
            name="Test Persona",
            description="Old description",
            preview_audio_url=preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
        )

        updated_persona = make_persona(
            self.org.id,
            id=existing_persona.id,
            name="Updated Persona",
            description="New description",
            aggression=0.7,
            preview_audio_url=preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = updated_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/personas/{existing_persona.id}",
            json={
                "name": "Updated Persona",
                "description": "New description",
                "aggression": 0.7,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Persona"
        assert data["description"] == "New description"
        assert data["preview_audio_url"] == preview_url

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_delete_system_persona_forbidden(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test DELETE on system persona returns 403."""
        system_persona = make_persona(self.org.id, persona_type="system")

        mock_repo = AsyncMock()
        mock_repo.get.return_value = system_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/orgs/{self.org.id}/personas/{system_persona.id}")

        assert response.status_code == 403
        data = response.json()
        assert "System personas cannot be deleted" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_delete_custom_persona_success(
        self,
        mock_get_audio_storage,
        mock_get_persona_repo,
        client,
    ):
        """Test DELETE on custom persona returns 204."""
        persona = make_persona(self.org.id, persona_type="custom", is_default=False)

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_repo.count.return_value = 2
        mock_repo.delete.return_value = True
        mock_get_persona_repo.return_value = mock_repo

        mock_audio_storage = AsyncMock()
        mock_get_audio_storage.return_value = mock_audio_storage

        response = client.delete(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}")

        assert response.status_code == 204
        mock_repo.delete.assert_called_once_with(persona.id, org_id=self.org.id)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_delete_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test DELETE on non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/orgs/{self.org.id}/personas/{persona_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test POST preview-audio returns 202 Accepted."""
        persona = make_persona(
            self.org.id,
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            preview_audio_text="Custom text",
            preview_audio_status=None,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_repo.update.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}/preview-audio")

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"
        assert data["audio_url"] is None
        assert data["error_message"] is None

        mock_repo.update.assert_called_once_with(
            persona_id=persona.id,
            preview_audio_status="generating",
            preview_audio_error=None,
            org_id=self.org.id,
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_preview_audio_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test GET preview-audio returns 200 with audio URL."""
        preview_url = "https://example.com/preview.mp3"
        persona = make_persona(
            self.org.id,
            preview_audio_url=preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}/preview-audio")

        assert response.status_code == 200
        data = response.json()
        assert data["audio_url"] == preview_url
        assert data["text"] == DEFAULT_PREVIEW_TEXT
        assert data["format"] == "audio/mpeg"

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_preview_audio_not_available(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test GET preview-audio returns 404 when audio not available."""
        persona = make_persona(self.org.id, preview_audio_url=None)

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}/preview-audio")

        assert response.status_code == 404
        data = response.json()
        assert "Preview audio not available" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_set_default_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test POST set-default returns 200."""
        persona = make_persona(self.org.id, is_default=True)

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_repo.set_default.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}/set-default")

        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] is True
        assert data["persona_type"] == "custom"

        mock_repo.set_default.assert_called_once_with(persona.id, org_id=self.org.id)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_toggle_active_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test PATCH active returns 200."""
        persona = make_persona(self.org.id, is_active=False)

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_repo.update.return_value = make_persona(self.org.id, id=persona.id, is_active=False)
        mock_get_persona_repo.return_value = mock_repo

        response = client.patch(
            f"/api/v1/orgs/{self.org.id}/personas/{persona.id}/active",
            json={"is_active": False},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["persona_type"] == "custom"

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_update_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test updating a non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/personas/{persona_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_create_persona_repo_error(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test creating a persona when repo raises ValueError returns 400."""
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = ValueError("Invalid aggression value")
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/personas",
            json={
                "name": "Test Persona",
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "tts_provider": "openai",
                "tts_config": {},
            },
        )

        assert response.status_code == 400

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_delete_default_persona_rejected(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test DELETE on default persona returns 400."""
        default_persona = make_persona(self.org.id, is_default=True, persona_type="custom")

        mock_repo = AsyncMock()
        mock_repo.get.return_value = default_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/orgs/{self.org.id}/personas/{default_persona.id}")

        assert response.status_code == 400
        data = response.json()
        assert "Cannot delete the default persona" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test POST preview-audio for non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/orgs/{self.org.id}/personas/{persona_id}/preview-audio")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_preview_audio_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test GET preview-audio for non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/orgs/{self.org.id}/personas/{persona_id}/preview-audio")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_set_default_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test POST set-default for non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/orgs/{self.org.id}/personas/{persona_id}/set-default")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_toggle_active_persona_not_found(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test PATCH active for non-existent persona returns 404."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.patch(
            f"/api/v1/orgs/{self.org.id}/personas/{persona_id}/active",
            json={"is_active": True},
        )

        assert response.status_code == 404

    def test_create_persona_validation_error(self, client):
        """Test creating a persona with invalid data returns 422."""
        response = client.post(
            f"/api/v1/orgs/{self.org.id}/personas",
            json={
                "name": "",  # Empty name
                "aggression": 1.5,  # Out of range
                "patience": -0.1,  # Out of range
                "verbosity": 0.5,
                "tts_provider": "openai",
            },
        )

        assert response.status_code == 422

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_already_generating(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test POST preview-audio when already generating returns 202 immediately."""
        persona = make_persona(
            self.org.id,
            preview_audio_status="generating",
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}/preview-audio")

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"

        # Should not call update since already generating
        mock_repo.update.assert_not_called()

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_delete_last_persona_rejected(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test DELETE on last remaining persona returns 400."""
        persona = make_persona(self.org.id, persona_type="custom", is_default=False)

        mock_repo = AsyncMock()
        mock_repo.get.return_value = persona
        mock_repo.count.return_value = 1  # Last persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/orgs/{self.org.id}/personas/{persona.id}")

        assert response.status_code == 400
        data = response.json()
        assert "Cannot delete the last remaining persona" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_update_persona_repo_error(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test updating a persona with repo error returns 400."""
        existing = make_persona(self.org.id)

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing
        mock_repo.update.side_effect = ValueError("Database error")
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/personas/{existing.id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 400
