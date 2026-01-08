"""Tests for the PersonaRepository class."""

from uuid import uuid4

import pytest

from voiceobs.server.db.models import PersonaRow
from voiceobs.server.db.repositories.persona import PersonaRepository

from .conftest import MockRecord


class TestPersonaRepository:
    """Tests for the PersonaRepository class."""

    @pytest.mark.asyncio
    async def test_create_persona_minimal(self, mock_db):
        """Test creating a persona with minimal required fields."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        # Mock the insert and select operations
        mock_db.fetchrow.return_value = MockRecord(
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
        )

        result = await repo.create(
            name="Test Persona",
            aggression=0.5,
            patience=0.7,
            verbosity=0.3,
            tts_provider="openai",
        )

        assert result.id == persona_id
        assert result.name == "Test Persona"
        assert result.aggression == 0.5
        assert result.patience == 0.7
        assert result.verbosity == 0.3
        assert result.tts_provider == "openai"
        assert result.is_active is True
        mock_db.execute.assert_called_once()
        assert "INSERT INTO personas" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_persona_full(self, mock_db):
        """Test creating a persona with all fields."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Full Persona",
                "description": "A test persona",
                "aggression": 0.8,
                "patience": 0.2,
                "verbosity": 0.9,
                "traits": ["friendly", "patient"],
                "tts_provider": "elevenlabs",
                "tts_config": {"voice_id": "test-voice", "model_id": "test-model"},
                "preview_audio_url": "https://example.com/audio.mp3",
                "preview_audio_text": "Hello, this is a test.",
                "metadata": {"custom": "data"},
                "created_at": None,
                "updated_at": None,
                "created_by": "test-user",
                "is_active": True,
            }
        )

        result = await repo.create(
            name="Full Persona",
            aggression=0.8,
            patience=0.2,
            verbosity=0.9,
            tts_provider="elevenlabs",
            tts_config={"voice_id": "test-voice", "model_id": "test-model"},
            description="A test persona",
            traits=["friendly", "patient"],
            metadata={"custom": "data"},
            created_by="test-user",
            preview_audio_url="https://example.com/audio.mp3",
            preview_audio_text="Hello, this is a test.",
        )

        assert result.name == "Full Persona"
        assert result.description == "A test persona"
        assert result.traits == ["friendly", "patient"]
        assert result.tts_config == {"voice_id": "test-voice", "model_id": "test-model"}
        assert result.created_by == "test-user"

    @pytest.mark.asyncio
    async def test_create_persona_unsupported_provider(self, mock_db):
        """Test creating a persona with unsupported TTS provider."""
        repo = PersonaRepository(mock_db)

        with pytest.raises(ValueError, match="Unsupported TTS provider"):
            await repo.create(
                name="Test",
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="unsupported_provider",
            )

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_persona_database_failure(self, mock_db):
        """Test creating a persona when database fails to return the created row."""
        repo = PersonaRepository(mock_db)

        # Mock the fetchrow to return None (simulating database failure)
        mock_db.fetchrow.return_value = None

        with pytest.raises(RuntimeError, match="Failed to create persona"):
            await repo.create(
                name="Test",
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
            )

        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_persona(self, mock_db):
        """Test getting a persona by UUID."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
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
        )

        result = await repo.get(persona_id)

        assert result is not None
        assert result.id == persona_id
        assert result.name == "Test Persona"

    @pytest.mark.asyncio
    async def test_get_persona_not_found(self, mock_db):
        """Test getting a non-existent persona."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_name(self, mock_db):
        """Test getting a persona by name."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Named Persona",
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
        )

        result = await repo.get_by_name("Named Persona")

        assert result is not None
        assert result.name == "Named Persona"
        assert "WHERE name = $1 AND is_active = true" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_by_name_not_found(self, mock_db):
        """Test getting a persona by name that doesn't exist."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get_by_name("Nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_default(self, mock_db):
        """Test listing all active personas (default)."""
        repo = PersonaRepository(mock_db)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": uuid4(),
                    "name": "Persona 1",
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
            MockRecord(
                {
                    "id": uuid4(),
                    "name": "Persona 2",
                    "description": None,
                    "aggression": 0.8,
                    "patience": 0.2,
                    "verbosity": 0.9,
                    "traits": [],
                    "tts_provider": "elevenlabs",
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
        ]

        result = await repo.list_all()

        assert len(result) == 2
        assert all(isinstance(p, PersonaRow) for p in result)
        assert "WHERE is_active = $1" in mock_db.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_all_include_inactive(self, mock_db):
        """Test listing all personas including inactive ones."""
        repo = PersonaRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.list_all(is_active=None)

        assert result == []
        # Should not filter by is_active when None
        assert "WHERE is_active" not in mock_db.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_list_all_with_pagination(self, mock_db):
        """Test listing personas with limit and offset."""
        repo = PersonaRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.list_all(limit=10, offset=5)

        assert result == []
        sql = mock_db.fetch.call_args[0][0]
        assert "LIMIT" in sql
        assert "OFFSET" in sql

    @pytest.mark.asyncio
    async def test_update_persona_single_field(self, mock_db):
        """Test updating a single field."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        # Mock get to return existing persona
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Updated Name",
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
        )

        result = await repo.update(persona_id, name="Updated Name")

        assert result is not None
        assert result.name == "Updated Name"
        mock_db.execute.assert_called_once()
        assert "UPDATE personas" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_persona_multiple_fields(self, mock_db):
        """Test updating multiple fields."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Updated",
                "description": "New description",
                "aggression": 0.9,
                "patience": 0.1,
                "verbosity": 0.8,
                "traits": ["new"],
                "tts_provider": "deepgram",
                "tts_config": {"new": "config"},
                "preview_audio_url": "new-url",
                "preview_audio_text": "new-text",
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.update(
            persona_id,
            name="Updated",
            description="New description",
            aggression=0.9,
            patience=0.1,
            verbosity=0.8,
            traits=["new"],
            tts_provider="deepgram",
            tts_config={"new": "config"},
            preview_audio_url="new-url",
            preview_audio_text="new-text",
        )

        assert result is not None
        assert result.name == "Updated"
        assert result.aggression == 0.9
        assert result.tts_provider == "deepgram"

    @pytest.mark.asyncio
    async def test_update_persona_not_found(self, mock_db):
        """Test updating a non-existent persona."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.update(uuid4(), name="Updated")

        assert result is None

    @pytest.mark.asyncio
    async def test_update_persona_no_changes(self, mock_db):
        """Test update with no fields to update."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Original",
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
        )

        result = await repo.update(persona_id)

        assert result is not None
        assert result.name == "Original"
        # Should call fetchrow for get but not execute for update
        assert mock_db.fetchrow.called
        assert not mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_persona_metadata(self, mock_db):
        """Test updating metadata field."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.7,
                "verbosity": 0.3,
                "traits": [],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "metadata": {"key": "value"},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
            }
        )

        result = await repo.update(persona_id, metadata={"key": "value"})

        assert result is not None
        assert result.metadata == {"key": "value"}
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_persona_unsupported_provider(self, mock_db):
        """Test updating with unsupported TTS provider."""
        repo = PersonaRepository(mock_db)

        with pytest.raises(ValueError, match="Unsupported TTS provider"):
            await repo.update(uuid4(), tts_provider="invalid")

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_soft(self, mock_db):
        """Test soft deleting a persona (default)."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()
        mock_db.execute.return_value = "UPDATE 1"

        result = await repo.delete(persona_id, soft=True)

        assert result is True
        mock_db.execute.assert_called_once()
        sql = mock_db.execute.call_args[0][0]
        assert "UPDATE personas" in sql
        assert "is_active = false" in sql

    @pytest.mark.asyncio
    async def test_delete_hard(self, mock_db):
        """Test hard deleting a persona."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()
        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(persona_id, soft=False)

        assert result is True
        mock_db.execute.assert_called_once()
        sql = mock_db.execute.call_args[0][0]
        assert "DELETE FROM personas" in sql

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db):
        """Test deleting a non-existent persona."""
        repo = PersonaRepository(mock_db)
        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(uuid4(), soft=False)

        assert result is False

    @pytest.mark.asyncio
    async def test_count_active(self, mock_db):
        """Test counting active personas (default)."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchval.return_value = 5

        count = await repo.count()

        assert count == 5
        sql = mock_db.fetchval.call_args[0][0]
        assert "COUNT(*)" in sql
        assert "WHERE is_active = $1" in sql

    @pytest.mark.asyncio
    async def test_count_all(self, mock_db):
        """Test counting all personas."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchval.return_value = 10

        count = await repo.count(is_active=None)

        assert count == 10
        sql = mock_db.fetchval.call_args[0][0]
        assert "COUNT(*)" in sql
        assert "WHERE is_active" not in sql

    @pytest.mark.asyncio
    async def test_count_inactive(self, mock_db):
        """Test counting inactive personas."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchval.return_value = 3

        count = await repo.count(is_active=False)

        assert count == 3
        sql = mock_db.fetchval.call_args[0][0]
        assert "WHERE is_active = $1" in sql
