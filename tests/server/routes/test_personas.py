"""Tests for the persona API endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import PersonaRow
from voiceobs.server.routes.personas import DEFAULT_PREVIEW_TEXT


class TestPersonas:
    """Tests for persona CRUD endpoints."""

    @patch("voiceobs.server.routes.personas.is_using_postgres", return_value=False)
    def test_create_persona_postgres_required(self, mock_is_postgres, client):
        """Test creating a persona without PostgreSQL configured."""
        response = client.post(
            "/api/v1/personas",
            json={
                "name": "Test Persona",
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "tts_provider": "openai",
            },
        )

        assert response.status_code == 501
        data = response.json()
        assert "PostgreSQL database" in data["detail"]

    @patch("voiceobs.server.routes.personas.is_using_postgres", return_value=True)
    @patch("voiceobs.server.routes.personas.get_persona_repository", return_value=None)
    def test_create_persona_repository_unavailable(self, mock_get_repo, mock_is_postgres, client):
        """Test creating a persona when repository is unavailable."""
        response = client.post(
            "/api/v1/personas",
            json={
                "name": "Test Persona",
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "tts_provider": "openai",
            },
        )

        assert response.status_code == 500
        data = response.json()
        assert "not available" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    @patch("voiceobs.server.routes.personas.TTSServiceFactory")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_create_persona_success(
        self,
        mock_get_audio_storage,
        mock_tts_factory,
        mock_get_persona_repo,
        client,
    ):
        """Test successful persona creation with preview audio generation."""
        persona_id = uuid4()
        preview_audio_url = "https://storage.example.com/audio/personas/preview/test.mp3"

        # Mock TTS service
        mock_tts_service = AsyncMock()
        mock_tts_service.synthesize.return_value = (
            b"fake_audio_bytes",
            "audio/mpeg",
            1500.0,
        )
        mock_tts_factory.create.return_value = mock_tts_service

        # Mock audio storage
        mock_audio_storage = AsyncMock()
        mock_audio_storage.store_audio.return_value = preview_audio_url
        mock_get_audio_storage.return_value = mock_audio_storage

        # Mock persona repository - first created without preview_audio_url
        mock_persona_initial = PersonaRow(
            id=persona_id,
            name="Angry Customer",
            description="An aggressive customer persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            traits=["impatient", "demanding"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            preview_audio_url=None,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={"category": "customer"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="user@example.com",
            is_active=True,
        )

        # Mock persona after update with preview_audio_url
        mock_persona_updated = PersonaRow(
            id=persona_id,
            name="Angry Customer",
            description="An aggressive customer persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            traits=["impatient", "demanding"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            preview_audio_url=preview_audio_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={"category": "customer"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="user@example.com",
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_persona_initial
        mock_repo.update.return_value = mock_persona_updated
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(
            "/api/v1/personas",
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
        assert data["aggression"] == 0.8
        assert data["preview_audio_url"] == preview_audio_url
        assert data["preview_audio_text"] == DEFAULT_PREVIEW_TEXT

        # Verify TTS service was called
        mock_tts_service.synthesize.assert_called_once_with(
            DEFAULT_PREVIEW_TEXT,
            {"model": "tts-1", "voice": "alloy", "speed": 1.0},
        )

        # Verify audio storage was called with store_audio
        mock_audio_storage.store_audio.assert_called_once()

        # Verify persona was updated with preview audio URL
        mock_repo.update.assert_called_once()

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_list_personas_success(self, mock_get_persona_repo, client):
        """Test listing personas."""
        persona1_id = uuid4()
        persona2_id = uuid4()

        mock_personas = [
            PersonaRow(
                id=persona1_id,
                name="Polite Customer",
                description="A patient customer",
                aggression=0.2,
                patience=0.9,
                verbosity=0.5,
                traits=["polite", "patient"],
                tts_provider="openai",
                tts_config={"model": "tts-1", "voice": "nova"},
                preview_audio_url="https://example.com/preview1.mp3",
                preview_audio_text=DEFAULT_PREVIEW_TEXT,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=None,
                is_active=True,
            ),
            PersonaRow(
                id=persona2_id,
                name="Angry Customer",
                description="An aggressive customer",
                aggression=0.8,
                patience=0.2,
                verbosity=0.6,
                traits=["impatient"],
                tts_provider="elevenlabs",
                tts_config={"voice_id": "test123"},
                preview_audio_url="https://example.com/preview2.mp3",
                preview_audio_text=DEFAULT_PREVIEW_TEXT,
                metadata={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by=None,
                is_active=True,
            ),
        ]

        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = mock_personas
        mock_get_persona_repo.return_value = mock_repo

        response = client.get("/api/v1/personas")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["personas"]) == 2
        assert data["personas"][0]["name"] == "Polite Customer"
        assert data["personas"][1]["name"] == "Angry Customer"

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_list_personas_with_filters(self, mock_get_persona_repo, client):
        """Test listing personas with query filters."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_get_persona_repo.return_value = mock_repo

        response = client.get("/api/v1/personas?is_active=false&limit=10&offset=5")

        assert response.status_code == 200
        mock_repo.list_all.assert_called_once_with(is_active=False, limit=10, offset=5)

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_get_persona_success(self, mock_get_persona_repo, client):
        """Test getting a single persona by ID."""
        persona_id = uuid4()

        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url="https://example.com/preview.mp3",
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(persona_id)
        assert data["name"] == "Test Persona"

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_get_persona_not_found(self, mock_get_persona_repo, client):
        """Test getting a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    @patch("voiceobs.server.routes.personas.TTSServiceFactory")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_update_persona_with_tts_change(
        self,
        mock_get_audio_storage,
        mock_tts_factory,
        mock_get_persona_repo,
        client,
    ):
        """Test updating a persona with TTS settings change (regenerates preview audio)."""
        persona_id = uuid4()
        old_preview_url = "https://example.com/old_preview.mp3"
        new_preview_url = "https://example.com/new_preview.mp3"

        # Mock existing persona
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy"},
            preview_audio_url=old_preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        # Mock updated persona
        updated_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="elevenlabs",
            tts_config={"voice_id": "new_voice"},
            preview_audio_url=new_preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        # Mock TTS service
        mock_tts_service = AsyncMock()
        mock_tts_service.synthesize.return_value = (
            b"new_audio_bytes",
            "audio/mpeg",
            1500.0,
        )
        mock_tts_factory.create.return_value = mock_tts_service

        # Mock audio storage
        mock_audio_storage = AsyncMock()
        mock_audio_storage.store_audio.return_value = new_preview_url
        mock_get_audio_storage.return_value = mock_audio_storage

        # Mock repo
        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = updated_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/personas/{persona_id}",
            json={
                "tts_provider": "elevenlabs",
                "tts_config": {"voice_id": "new_voice"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tts_provider"] == "elevenlabs"
        assert data["preview_audio_url"] == new_preview_url

        # Verify preview audio was regenerated
        mock_tts_service.synthesize.assert_called_once()

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_update_persona_without_tts_change(self, mock_get_persona_repo, client):
        """Test updating a persona without TTS settings change (no preview regeneration)."""
        persona_id = uuid4()
        preview_url = "https://example.com/preview.mp3"

        # Mock existing persona
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Old description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url=preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        # Mock updated persona
        updated_persona = PersonaRow(
            id=persona_id,
            name="Updated Persona",
            description="New description",
            aggression=0.7,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url=preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = updated_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/personas/{persona_id}",
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

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_update_persona_not_found(self, mock_get_persona_repo, client):
        """Test updating a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/personas/{persona_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_delete_persona_soft_delete(self, mock_get_persona_repo, client):
        """Test soft deleting a persona (default)."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 204
        mock_repo.delete.assert_called_once_with(persona_id, soft=True)

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_delete_persona_hard_delete(self, mock_get_persona_repo, client):
        """Test hard deleting a persona."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.delete.return_value = True
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/personas/{persona_id}?soft=false")

        assert response.status_code == 204
        mock_repo.delete.assert_called_once_with(persona_id, soft=False)

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_delete_persona_not_found(self, mock_get_persona_repo, client):
        """Test deleting a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.delete.return_value = False
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_get_preview_audio_success(self, mock_get_persona_repo, client):
        """Test getting preview audio for a persona."""
        persona_id = uuid4()
        preview_url = "https://example.com/preview.mp3"

        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url=preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}/preview-audio")

        assert response.status_code == 200
        data = response.json()
        assert data["audio_url"] == preview_url
        assert data["text"] == DEFAULT_PREVIEW_TEXT
        assert data["format"] == "audio/mpeg"

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_get_preview_audio_persona_not_found(self, mock_get_persona_repo, client):
        """Test getting preview audio for a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}/preview-audio")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_get_preview_audio_not_available(self, mock_get_persona_repo, client):
        """Test getting preview audio when not available."""
        persona_id = uuid4()

        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url=None,  # No preview audio
            preview_audio_text=None,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}/preview-audio")

        assert response.status_code == 404
        data = response.json()
        assert "Preview audio not available" in data["detail"]

    def test_create_persona_validation_error(self, client):
        """Test creating a persona with invalid data."""
        response = client.post(
            "/api/v1/personas",
            json={
                "name": "",  # Empty name
                "aggression": 1.5,  # Out of range
                "patience": -0.1,  # Out of range
                "verbosity": 0.5,
                "tts_provider": "openai",
            },
        )

        assert response.status_code == 422

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    @patch("voiceobs.server.routes.personas.TTSServiceFactory")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_create_persona_invalid_tts_provider(
        self,
        mock_get_audio_storage,
        mock_tts_factory,
        mock_get_persona_repo,
        client,
    ):
        """Test creating a persona with invalid TTS provider."""
        # Mock TTS factory to raise ValueError for unsupported provider
        mock_tts_factory.create.side_effect = ValueError(
            "Unsupported TTS provider: invalid_provider"
        )

        mock_repo = AsyncMock()
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(
            "/api/v1/personas",
            json={
                "name": "Test Persona",
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "tts_provider": "invalid_provider",
                "tts_config": {},
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported TTS provider" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    @patch("voiceobs.server.routes.personas.TTSServiceFactory")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_create_persona_repository_error(
        self,
        mock_get_audio_storage,
        mock_tts_factory,
        mock_get_persona_repo,
        client,
    ):
        """Test creating a persona with repository validation error."""
        # Mock TTS service
        mock_tts_service = AsyncMock()
        mock_tts_service.synthesize.return_value = (
            b"fake_audio_bytes",
            "audio/mpeg",
            1500.0,
        )
        mock_tts_factory.create.return_value = mock_tts_service

        # Mock audio storage
        mock_audio_storage = AsyncMock()
        mock_audio_storage.store_audio.return_value = "https://example.com/audio.mp3"
        mock_get_audio_storage.return_value = mock_audio_storage

        # Mock repository to raise ValueError
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = ValueError("Invalid aggression value")
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(
            "/api/v1/personas",
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

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    @patch("voiceobs.server.routes.personas.TTSServiceFactory")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_update_persona_invalid_tts_provider(
        self,
        mock_get_audio_storage,
        mock_tts_factory,
        mock_get_persona_repo,
        client,
    ):
        """Test updating a persona with invalid TTS provider."""
        persona_id = uuid4()

        # Mock existing persona
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url="https://example.com/preview.mp3",
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        # Mock TTS factory to raise ValueError
        mock_tts_factory.create.side_effect = ValueError(
            "Unsupported TTS provider: invalid_provider"
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/personas/{persona_id}",
            json={"tts_provider": "invalid_provider"},
        )

        assert response.status_code == 400

    @patch("voiceobs.server.routes.personas.get_persona_repo")
    def test_update_persona_repository_error(self, mock_get_persona_repo, client):
        """Test updating a persona with repository validation error."""
        persona_id = uuid4()

        # Mock existing persona
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1"},
            preview_audio_url="https://example.com/preview.mp3",
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.side_effect = ValueError("Database error")
        mock_get_persona_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/personas/{persona_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 400
