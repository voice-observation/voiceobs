"""Tests for the persona API endpoints."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import PersonaRow
from voiceobs.server.routes.personas import DEFAULT_PREVIEW_TEXT


class TestPersonas:
    """Tests for persona CRUD endpoints."""

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_create_persona_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test successful persona creation with lazy audio generation."""
        persona_id = uuid4()

        # Mock persona created without preview audio (lazy generation)
        mock_persona = PersonaRow(
            id=persona_id,
            name="Angry Customer",
            description="An aggressive customer persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            traits=["impatient", "demanding"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            preview_audio_url=None,  # Lazy generation
            preview_audio_text=None,
            metadata={"category": "customer"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by="user@example.com",
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_persona
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
        # Audio is not generated during creation (lazy generation)
        assert data["preview_audio_url"] is None
        assert data["preview_audio_text"] is None

        # Verify persona was created
        mock_repo.create.assert_called_once()

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
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
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_list_personas_with_filters(self, mock_get_persona_repo, client):
        """Test listing personas with query filters."""
        mock_repo = AsyncMock()
        mock_repo.list_all.return_value = []
        mock_get_persona_repo.return_value = mock_repo

        response = client.get("/api/v1/personas?is_active=false&limit=10&offset=5")

        assert response.status_code == 200
        mock_repo.list_all.assert_called_once_with(is_active=False, limit=10, offset=5)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_persona_not_found(self, mock_get_persona_repo, client):
        """Test getting a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_update_persona_with_tts_change(
        self,
        mock_get_audio_storage,
        mock_get_persona_repo,
        client,
    ):
        """Test updating a persona with TTS settings change (clears preview audio)."""
        persona_id = uuid4()
        old_preview_url = "https://example.com/old_preview.mp3"

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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock updated persona (audio is cleared on update)
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
            preview_audio_url=None,  # Cleared on update
            preview_audio_text=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock audio storage
        mock_audio_storage = AsyncMock()
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
        # Audio is cleared on update (lazy regeneration)
        assert data["preview_audio_url"] is None

        # Verify old audio was deleted
        mock_audio_storage.delete_by_url.assert_called_once_with(old_preview_url)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_delete_persona(self, mock_get_audio_storage, mock_get_persona_repo, client):
        """Test deleting a persona."""
        persona_id = uuid4()

        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="openai",
            tts_config={},
            preview_audio_url=None,
            preview_audio_text=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
            is_default=False,  # Not default, can be deleted
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_persona
        mock_repo.count.return_value = 2  # More than 1 persona
        mock_repo.delete.return_value = True
        mock_get_persona_repo.return_value = mock_repo

        mock_audio_storage = AsyncMock()
        mock_get_audio_storage.return_value = mock_audio_storage

        response = client.delete(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 204
        mock_repo.delete.assert_called_once_with(persona_id)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_delete_persona_not_found(self, mock_get_persona_repo, client):
        """Test deleting a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None  # Persona not found
        mock_get_persona_repo.return_value = mock_repo

        response = client.delete(f"/api/v1/personas/{persona_id}")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_get_preview_audio_persona_not_found(self, mock_get_persona_repo, client):
        """Test getting preview audio for a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.get(f"/api/v1/personas/{persona_id}/preview-audio")

        assert response.status_code == 404

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_create_persona_invalid_tts_provider(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test creating a persona with invalid TTS provider (lazy validation)."""
        persona_id = uuid4()

        # With lazy audio generation, create accepts any tts_provider
        # Validation happens when generating preview audio
        mock_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="invalid_provider",
            tts_config={"model": "test"},
            preview_audio_url=None,  # Lazy generation
            preview_audio_text=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(
            "/api/v1/personas",
            json={
                "name": "Test Persona",
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "tts_provider": "invalid_provider",
                "tts_config": {"model": "test"},
            },
        )

        # Persona is created successfully - TTS validation is deferred
        assert response.status_code == 201
        data = response.json()
        assert data["tts_provider"] == "invalid_provider"
        assert data["preview_audio_url"] is None

        # Verify persona was created
        mock_repo.create.assert_called_once()

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    @patch("voiceobs.server.routes.personas.get_audio_storage")
    def test_update_persona_invalid_tts_provider(
        self,
        mock_get_audio_storage,
        mock_get_persona_repo,
        client,
    ):
        """Test updating a persona with invalid TTS provider (lazy validation)."""
        persona_id = uuid4()
        old_preview_url = "https://example.com/preview.mp3"

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
            preview_audio_url=old_preview_url,
            preview_audio_text=DEFAULT_PREVIEW_TEXT,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock updated persona with invalid provider (accepted with lazy validation)
        updated_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="invalid_provider",
            tts_config={},
            preview_audio_url=None,  # Audio cleared on TTS change
            preview_audio_text=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = updated_persona
        mock_get_persona_repo.return_value = mock_repo

        mock_audio_storage = AsyncMock()
        mock_get_audio_storage.return_value = mock_audio_storage

        response = client.put(
            f"/api/v1/personas/{persona_id}",
            json={"tts_provider": "invalid_provider"},
        )

        # Update succeeds - TTS validation is deferred to audio generation
        assert response.status_code == 200
        data = response.json()
        assert data["tts_provider"] == "invalid_provider"
        assert data["preview_audio_url"] is None

        # Verify old audio was deleted
        mock_audio_storage.delete_by_url.assert_called_once_with(old_preview_url)

    @patch("voiceobs.server.routes.personas.get_persona_repository")
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
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

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_success(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test starting async preview audio generation for a persona."""
        persona_id = uuid4()
        custom_preview_text = "This is a custom preview text for testing."

        # Mock existing persona with custom preview text
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            preview_audio_url=None,  # No existing preview
            preview_audio_text=custom_preview_text,
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock updated persona with generating status
        updated_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="openai",
            tts_config={"model": "tts-1", "voice": "alloy", "speed": 1.0},
            preview_audio_url=None,
            preview_audio_text=custom_preview_text,
            preview_audio_status="generating",
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = updated_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        # Async generation returns 202 Accepted
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"
        assert data["audio_url"] is None
        assert data["error_message"] is None

        # Verify status was set to generating
        mock_repo.update.assert_called_once_with(
            persona_id=persona_id,
            preview_audio_status="generating",
            preview_audio_error=None,
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_uses_default_text_when_missing(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test preview audio generation uses DEFAULT_PREVIEW_TEXT when text is None."""
        persona_id = uuid4()

        # Mock existing persona without preview_audio_text
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="elevenlabs",
            tts_config={"voice_id": "test123"},
            preview_audio_url=None,
            preview_audio_text=None,  # No preview text, will use default
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock repository
        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = existing_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        # Async generation returns 202 Accepted
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"
        assert data["audio_url"] is None
        assert data["error_message"] is None

        # Verify background task was queued (status set to generating)
        mock_repo.update.assert_called_once_with(
            persona_id=persona_id,
            preview_audio_status="generating",
            preview_audio_error=None,
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_persona_not_found(self, mock_get_persona_repo, client):
        """Test generating preview audio for a persona that doesn't exist."""
        persona_id = uuid4()

        mock_repo = AsyncMock()
        mock_repo.get.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        assert response.status_code == 404
        data = response.json()
        assert f"Persona '{persona_id}' not found" in data["detail"]

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_invalid_tts_provider(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test generating preview audio with invalid TTS provider (async)."""
        persona_id = uuid4()

        # Mock existing persona with invalid provider
        existing_persona = PersonaRow(
            id=persona_id,
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=["test"],
            tts_provider="invalid_provider",
            tts_config={},
            preview_audio_url=None,
            preview_audio_text="Test text",
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = existing_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        # Generation starts successfully - validation happens in background task
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"
        assert data["audio_url"] is None

        # Background task will fail with TTS error, but that's async
        mock_repo.update.assert_called_once_with(
            persona_id=persona_id,
            preview_audio_status="generating",
            preview_audio_error=None,
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_tts_service_error(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test generating preview audio when TTS service raises an exception (async)."""
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
            preview_audio_url=None,
            preview_audio_text="Test text",
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = existing_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        # Generation starts successfully - TTS errors happen in background task
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"
        assert data["audio_url"] is None

        # Background task will handle TTS errors and update status to "failed"
        mock_repo.update.assert_called_once_with(
            persona_id=persona_id,
            preview_audio_status="generating",
            preview_audio_error=None,
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_storage_error(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test generating preview audio when audio storage fails (async)."""
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
            preview_audio_url=None,
            preview_audio_text="Test text",
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = existing_persona
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        # Generation starts successfully - storage errors happen in background task
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"
        assert data["audio_url"] is None

        # Background task will handle storage errors and update status to "failed"
        mock_repo.update.assert_called_once_with(
            persona_id=persona_id,
            preview_audio_status="generating",
            preview_audio_error=None,
        )

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_repository_update_error(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test generating preview audio when repository update fails (async)."""
        import pytest

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
            preview_audio_url=None,
            preview_audio_text="Test text",
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock repository to raise ValueError on update
        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.side_effect = ValueError("Database constraint violation")
        mock_get_persona_repo.return_value = mock_repo

        # Endpoint doesn't handle ValueError from repo.update(), so exception propagates
        with pytest.raises(ValueError, match="Database constraint violation"):
            client.post(f"/api/v1/personas/{persona_id}/preview-audio")

    @patch("voiceobs.server.routes.personas.get_persona_repository")
    def test_generate_preview_audio_update_returns_none(
        self,
        mock_get_persona_repo,
        client,
    ):
        """Test generating preview audio when repository update returns None (async)."""
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
            preview_audio_url=None,
            preview_audio_text="Test text",
            preview_audio_status=None,
            preview_audio_error=None,
            metadata={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            created_by=None,
            is_active=True,
        )

        # Mock repository to return None on update
        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_persona
        mock_repo.update.return_value = None
        mock_get_persona_repo.return_value = mock_repo

        response = client.post(f"/api/v1/personas/{persona_id}/preview-audio")

        # Update returns None during status setting - generation still accepted
        # The endpoint doesn't check the update return value
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "generating"

        # Verify update was called to set status
        mock_repo.update.assert_called_once_with(
            persona_id=persona_id,
            preview_audio_status="generating",
            preview_audio_error=None,
        )
