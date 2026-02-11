"""Tests for the PersonaRepository class."""

from uuid import uuid4

import pytest

from voiceobs.server.db.models import PersonaRow
from voiceobs.server.db.repositories.persona import PersonaRepository

from .conftest import MockRecord

# Test organization ID for org-scoped operations
TEST_ORG_ID = uuid4()


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
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(persona_id, org_id=TEST_ORG_ID)

        assert result is not None
        assert result.id == persona_id
        assert result.name == "Test Persona"

    @pytest.mark.asyncio
    async def test_get_persona_not_found(self, mock_db):
        """Test getting a non-existent persona."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchrow.return_value = None

        result = await repo.get(uuid4(), org_id=TEST_ORG_ID)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_all_default(self, mock_db):
        """Test listing all personas (default is None = all personas)."""
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
                    "is_default": False,
                    "org_id": TEST_ORG_ID,
                    "persona_type": "custom",
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
                    "is_active": False,
                    "is_default": False,
                    "org_id": TEST_ORG_ID,
                    "persona_type": "custom",
                }
            ),
        ]

        result = await repo.list_all(org_id=TEST_ORG_ID)

        assert len(result) == 2
        assert all(isinstance(p, PersonaRow) for p in result)
        # Should have WHERE clause for org_id
        query = mock_db.fetch.call_args[0][0]
        assert "WHERE" in query
        assert "org_id" in query

    @pytest.mark.asyncio
    async def test_list_all_include_inactive(self, mock_db):
        """Test listing all personas including inactive ones."""
        repo = PersonaRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.list_all(org_id=TEST_ORG_ID, is_active=None)

        assert result == []
        # Should filter by org_id but not by is_active when None
        query = mock_db.fetch.call_args[0][0]
        assert "org_id" in query
        assert "WHERE is_active" not in query

    @pytest.mark.asyncio
    async def test_list_all_with_pagination(self, mock_db):
        """Test listing personas with limit and offset."""
        repo = PersonaRepository(mock_db)
        mock_db.fetch.return_value = []

        result = await repo.list_all(org_id=TEST_ORG_ID, limit=10, offset=5)

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
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.update(persona_id, org_id=TEST_ORG_ID, name="Updated Name")

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
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.update(
            persona_id,
            org_id=TEST_ORG_ID,
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

        result = await repo.update(uuid4(), org_id=TEST_ORG_ID, name="Updated")

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
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.update(persona_id, org_id=TEST_ORG_ID)

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
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.update(persona_id, org_id=TEST_ORG_ID, metadata={"key": "value"})

        assert result is not None
        assert result.metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_row_to_persona_with_string_traits(self, mock_db):
        """Test _row_to_persona handles string traits (JSONB from asyncpg)."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        # Mock traits as JSON string (how asyncpg might return it)
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Test Persona",
                "description": None,
                "aggression": 0.5,
                "patience": 0.7,
                "verbosity": 0.3,
                "traits": '["friendly", "calm"]',  # JSON string
                "tts_provider": "openai",
                "tts_config": '{"model": "tts-1"}',  # JSON string
                "preview_audio_url": None,
                "preview_audio_text": None,
                "metadata": '{"key": "value"}',  # JSON string
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(persona_id, org_id=TEST_ORG_ID)

        assert result is not None
        assert result.traits == ["friendly", "calm"]
        assert result.tts_config == {"model": "tts-1"}
        assert result.metadata == {"key": "value"}

    @pytest.mark.asyncio
    async def test_row_to_persona_with_object_traits(self, mock_db):
        """Test _row_to_persona handles object traits (from seed data)."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        # Mock traits as list of objects (seed data format)
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Test Persona",
                "description": None,
                "aggression": 0.5,
                "patience": 0.7,
                "verbosity": 0.3,
                "traits": [{"key": "friendly"}, {"key": "calm"}],  # Object format
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(persona_id, org_id=TEST_ORG_ID)

        assert result is not None
        assert result.traits == ["friendly", "calm"]  # Should extract "key" values

    @pytest.mark.asyncio
    async def test_row_to_persona_with_none_fields(self, mock_db):
        """Test _row_to_persona handles None fields correctly."""
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
                "traits": None,  # None traits
                "tts_provider": "openai",
                "tts_config": None,  # None tts_config
                "preview_audio_url": None,
                "preview_audio_text": None,
                "metadata": None,  # None metadata
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(persona_id, org_id=TEST_ORG_ID)

        assert result is not None
        assert result.traits == []
        assert result.tts_config == {}
        assert result.metadata == {}

    @pytest.mark.asyncio
    async def test_update_persona_is_active(self, mock_db):
        """Test updating persona is_active status."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        # Mock return value for get() call at the end of update
        # Note: update() calls get() which needs fetchrow
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
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": False,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.update(persona_id, org_id=TEST_ORG_ID, is_active=False)

        assert result is not None
        assert result.is_active is False
        # Verify is_active was included in update (False is not None, so it should be included)
        # The update method filters out None values, and False is not None
        assert mock_db.execute.called
        # Check that execute was called with is_active in the query
        call_args = mock_db.execute.call_args
        if call_args:
            update_query = call_args[0][0] if call_args[0] else ""
            # is_active=False should be included since False is not None
            assert "is_active" in update_query
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_persona_unsupported_provider(self, mock_db):
        """Test updating with unsupported TTS provider."""
        repo = PersonaRepository(mock_db)

        with pytest.raises(ValueError, match="Unsupported TTS provider"):
            await repo.update(uuid4(), org_id=TEST_ORG_ID, tts_provider="invalid")

        mock_db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete(self, mock_db):
        """Test deleting a persona."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()
        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(persona_id, org_id=TEST_ORG_ID)

        assert result is True
        mock_db.execute.assert_called_once()
        sql = mock_db.execute.call_args[0][0]
        assert "DELETE FROM personas" in sql

    @pytest.mark.asyncio
    async def test_delete_not_found(self, mock_db):
        """Test deleting a non-existent persona."""
        repo = PersonaRepository(mock_db)
        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(uuid4(), org_id=TEST_ORG_ID)

        assert result is False

    @pytest.mark.asyncio
    async def test_count_active(self, mock_db):
        """Test counting active personas (default)."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchval.return_value = 5

        count = await repo.count(org_id=TEST_ORG_ID)

        assert count == 5
        sql = mock_db.fetchval.call_args[0][0]
        assert "COUNT(*)" in sql
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_count_all(self, mock_db):
        """Test counting all personas."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchval.return_value = 10

        count = await repo.count(org_id=TEST_ORG_ID, is_active=None)

        assert count == 10
        sql = mock_db.fetchval.call_args[0][0]
        assert "COUNT(*)" in sql
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_count_inactive(self, mock_db):
        """Test counting inactive personas."""
        repo = PersonaRepository(mock_db)
        mock_db.fetchval.return_value = 3

        count = await repo.count(org_id=TEST_ORG_ID, is_active=False)

        assert count == 3
        sql = mock_db.fetchval.call_args[0][0]
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_create_persona_with_preview_audio_status(self, mock_db):
        """Test creating a persona with preview_audio_status."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Test Persona",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": [],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": "generating",
                "preview_audio_error": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
            }
        )

        persona = await repo.create(
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            preview_audio_status="generating",
        )

        assert persona.preview_audio_status == "generating"
        assert persona.preview_audio_error is None

    @pytest.mark.asyncio
    async def test_update_persona_with_preview_audio_status(self, mock_db):
        """Test updating a persona's preview_audio_status and preview_audio_error."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Test Persona",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": [],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": "failed",
                "preview_audio_error": "TTS service unavailable",
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.update(
            persona_id,
            org_id=TEST_ORG_ID,
            preview_audio_status="failed",
            preview_audio_error="TTS service unavailable",
        )

        assert result is not None
        assert result.preview_audio_status == "failed"
        assert result.preview_audio_error == "TTS service unavailable"
        mock_db.execute.assert_called_once()
        update_query = mock_db.execute.call_args[0][0]
        assert "preview_audio_status" in update_query
        assert "preview_audio_error" in update_query


class TestPersonaRepositoryOrgScoped:
    """Tests for org-scoped persona repository methods."""

    @pytest.mark.asyncio
    async def test_create_with_org_id_and_persona_type(self, mock_db):
        """create() accepts org_id and persona_type params."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": uuid4(),
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": "[]",
                "tts_provider": "openai",
                "tts_config": "{}",
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": "{}",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": org_id,
                "persona_type": "system",
            }
        )

        result = await repo.create(
            name="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            org_id=org_id,
            persona_type="system",
        )

        assert result.org_id == org_id
        assert result.persona_type == "system"
        # Verify SQL includes org_id and persona_type
        insert_sql = mock_db.execute.call_args[0][0]
        assert "org_id" in insert_sql
        assert "persona_type" in insert_sql

    @pytest.mark.asyncio
    async def test_create_with_is_default_true(self, mock_db):
        """create() respects is_default parameter."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": uuid4(),
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": "[]",
                "tts_provider": "openai",
                "tts_config": "{}",
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": "{}",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": True,
                "org_id": org_id,
                "persona_type": "system",
            }
        )

        result = await repo.create(
            name="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            org_id=org_id,
            persona_type="system",
            is_default=True,
        )

        assert result.is_default is True

    @pytest.mark.asyncio
    async def test_list_all_filters_by_org_id(self, mock_db):
        """list_all() includes org_id in WHERE clause."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()
        mock_db.fetch.return_value = []

        await repo.list_all(org_id=org_id)

        sql = mock_db.fetch.call_args[0][0]
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_get_checks_org_id(self, mock_db):
        """get() includes org_id filter when provided."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()
        mock_db.fetchrow.return_value = None

        await repo.get(uuid4(), org_id=org_id)

        sql = mock_db.fetchrow.call_args[0][0]
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_delete_checks_org_id(self, mock_db):
        """delete() includes org_id filter when provided."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()
        mock_db.execute.return_value = "DELETE 1"

        await repo.delete(uuid4(), org_id=org_id)

        sql = mock_db.execute.call_args[0][0]
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_count_filters_by_org_id(self, mock_db):
        """count() includes org_id filter when provided."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()
        mock_db.fetchval.return_value = 3

        result = await repo.count(org_id=org_id)

        sql = mock_db.fetchval.call_args[0][0]
        assert "org_id" in sql
        assert result == 3

    @pytest.mark.asyncio
    async def test_get_default_with_org_id(self, mock_db):
        """get_default() scopes to org when org_id is provided."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()
        mock_db.fetchrow.return_value = None

        await repo.get_default(org_id=org_id)

        sql = mock_db.fetchrow.call_args[0][0]
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_update_with_org_id(self, mock_db):
        """update() includes org_id in WHERE clause when provided."""
        repo = PersonaRepository(mock_db)
        persona_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Updated",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": "[]",
                "tts_provider": "openai",
                "tts_config": "{}",
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": "{}",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": org_id,
                "persona_type": "custom",
            }
        )

        await repo.update(persona_id, name="Updated", org_id=org_id)

        update_sql = mock_db.execute.call_args[0][0]
        assert "org_id" in update_sql

    @pytest.mark.asyncio
    async def test_list_all_with_is_active_and_org_id(self, mock_db):
        """list_all() includes both is_active and org_id in WHERE clause."""
        repo = PersonaRepository(mock_db)
        org_id = uuid4()
        mock_db.fetch.return_value = []

        await repo.list_all(is_active=True, org_id=org_id)

        sql = mock_db.fetch.call_args[0][0]
        assert "is_active" in sql
        assert "org_id" in sql

    @pytest.mark.asyncio
    async def test_set_default_with_org_id(self, mock_db):
        """set_default() scopes unset query to org when org_id provided."""
        from contextlib import asynccontextmanager
        from unittest.mock import AsyncMock

        repo = PersonaRepository(mock_db)
        persona_id = uuid4()
        org_id = uuid4()

        # Mock transaction context manager
        mock_conn = AsyncMock()

        @asynccontextmanager
        async def mock_transaction():
            yield mock_conn

        mock_db.transaction = mock_transaction

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": persona_id,
                "name": "Default",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": "[]",
                "tts_provider": "openai",
                "tts_config": "{}",
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": "{}",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": True,
                "org_id": org_id,
                "persona_type": "custom",
            }
        )

        result = await repo.set_default(persona_id, org_id=org_id)

        assert result is not None
        # Verify the unset query includes org_id
        unset_call = mock_conn.execute.call_args_list[0]
        assert "org_id" in unset_call[0][0]

    @pytest.mark.asyncio
    async def test_create_with_none_tts_provider(self, mock_db):
        """create() skips TTS validation when provider is None."""
        repo = PersonaRepository(mock_db)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": uuid4(),
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": "[]",
                "tts_provider": None,
                "tts_config": "{}",
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": "{}",
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": None,
                "persona_type": "custom",
            }
        )

        result = await repo.create(
            name="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider=None,
        )

        assert result is not None
        assert result.tts_provider is None

    @pytest.mark.asyncio
    async def test_row_to_persona_with_value_dict_traits(self, mock_db):
        """_row_to_persona handles dict traits with 'value' key."""
        repo = PersonaRepository(mock_db)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": uuid4(),
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": [{"value": "friendly"}, {"value": "calm"}],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(uuid4(), org_id=TEST_ORG_ID)

        assert result is not None
        assert result.traits == ["friendly", "calm"]

    @pytest.mark.asyncio
    async def test_row_to_persona_with_unknown_dict_traits(self, mock_db):
        """_row_to_persona handles dict traits without 'key' or 'value'."""
        repo = PersonaRepository(mock_db)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": uuid4(),
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": [{"other": "data"}],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(uuid4(), org_id=TEST_ORG_ID)

        assert result is not None
        assert result.traits == ["{'other': 'data'}"]

    @pytest.mark.asyncio
    async def test_row_to_persona_with_numeric_traits(self, mock_db):
        """_row_to_persona handles non-string, non-dict traits."""
        repo = PersonaRepository(mock_db)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": uuid4(),
                "name": "Test",
                "description": None,
                "aggression": 0.5,
                "patience": 0.5,
                "verbosity": 0.5,
                "traits": [42, True],
                "tts_provider": "openai",
                "tts_config": {},
                "preview_audio_url": None,
                "preview_audio_text": None,
                "preview_audio_status": None,
                "preview_audio_error": None,
                "metadata": {},
                "created_at": None,
                "updated_at": None,
                "created_by": None,
                "is_active": True,
                "is_default": False,
                "org_id": TEST_ORG_ID,
                "persona_type": "custom",
            }
        )

        result = await repo.get(uuid4(), org_id=TEST_ORG_ID)

        assert result is not None
        assert result.traits == ["42", "True"]
