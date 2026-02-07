"""Tests for is_default field on personas."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from voiceobs.server.db.models import PersonaRow
from voiceobs.server.models import PersonaListItem, PersonaResponse


class TestPersonaResponseIsDefault:
    """Tests for is_default field in PersonaResponse."""

    def test_persona_response_includes_is_default_field(self):
        """Test that PersonaResponse includes is_default field."""
        persona = PersonaResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="openai",
            tts_config={},
            preview_audio_url=None,
            preview_audio_text=None,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test@example.com",
            is_active=True,
            is_default=True,
        )

        assert hasattr(persona, "is_default")
        assert persona.is_default is True

    def test_persona_response_is_default_defaults_to_false(self):
        """Test that is_default defaults to False."""
        persona = PersonaResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Persona",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="openai",
            tts_config={},
            preview_audio_url=None,
            preview_audio_text=None,
            metadata={},
            created_at=None,
            updated_at=None,
            created_by=None,
            is_active=True,
        )

        assert persona.is_default is False


class TestPersonaListItemIsDefault:
    """Tests for is_default field in PersonaListItem."""

    def test_persona_list_item_includes_is_default_field(self):
        """Test that PersonaListItem includes is_default field."""
        item = PersonaListItem(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            preview_audio_url=None,
            preview_audio_text=None,
            is_active=True,
            is_default=True,
        )

        assert hasattr(item, "is_default")
        assert item.is_default is True

    def test_persona_list_item_is_default_defaults_to_false(self):
        """Test that is_default defaults to False in PersonaListItem."""
        item = PersonaListItem(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Persona",
            description=None,
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            preview_audio_url=None,
            preview_audio_text=None,
            is_active=True,
        )

        assert item.is_default is False


class TestPersonaRowIsDefault:
    """Tests for is_default field in PersonaRow."""

    def test_persona_row_includes_is_default_field(self):
        """Test that PersonaRow includes is_default field."""
        from uuid import uuid4

        row = PersonaRow(
            id=uuid4(),
            name="Test Persona",
            description="Test description",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            traits=[],
            tts_provider="openai",
            tts_config={},
            preview_audio_url=None,
            preview_audio_text=None,
            metadata={},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by="test@example.com",
            is_active=True,
            is_default=True,
        )

        assert hasattr(row, "is_default")
        assert row.is_default is True

    def test_persona_row_is_default_defaults_to_false(self):
        """Test that is_default defaults to False in PersonaRow."""
        from uuid import uuid4

        row = PersonaRow(
            id=uuid4(),
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
        )

        assert row.is_default is False


class TestDeletePersonaValidation:
    """Tests for delete validation rules on personas."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock persona repository."""
        repo = MagicMock()
        repo.get = AsyncMock()
        repo.delete = AsyncMock()
        repo.count = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_cannot_delete_default_persona(self, mock_repo):
        """Test that deleting the default persona returns 400 error."""
        from uuid import uuid4

        from voiceobs.server.routes.personas import delete_persona

        persona_id = uuid4()
        mock_repo.get.return_value = PersonaRow(
            id=persona_id,
            name="Default Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
            is_default=True,
        )
        mock_repo.count.return_value = 5

        with (
            patch("voiceobs.server.routes.personas.get_persona_repository", return_value=mock_repo),
            patch("voiceobs.server.routes.personas.parse_uuid", return_value=persona_id),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await delete_persona(str(persona_id))

            assert exc_info.value.status_code == 400
            assert "default" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_cannot_delete_last_persona(self, mock_repo):
        """Test that deleting the last persona returns 400 error."""
        from uuid import uuid4

        from voiceobs.server.routes.personas import delete_persona

        persona_id = uuid4()
        mock_repo.get.return_value = PersonaRow(
            id=persona_id,
            name="Last Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
            is_default=False,
        )
        mock_repo.count.return_value = 1  # Only one persona left

        with (
            patch("voiceobs.server.routes.personas.get_persona_repository", return_value=mock_repo),
            patch("voiceobs.server.routes.personas.parse_uuid", return_value=persona_id),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await delete_persona(str(persona_id))

            assert exc_info.value.status_code == 400
            assert "last" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_can_delete_non_default_persona_when_others_exist(self, mock_repo):
        """Test that non-default persona can be deleted when others exist."""
        from uuid import uuid4

        from voiceobs.server.routes.personas import delete_persona

        persona_id = uuid4()
        mock_repo.get.return_value = PersonaRow(
            id=persona_id,
            name="Regular Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
            is_default=False,
        )
        mock_repo.count.return_value = 3  # Multiple personas exist
        mock_repo.delete.return_value = True

        with (
            patch("voiceobs.server.routes.personas.get_persona_repository", return_value=mock_repo),
            patch("voiceobs.server.routes.personas.parse_uuid", return_value=persona_id),
        ):
            result = await delete_persona(str(persona_id))

            assert result is None  # 204 No Content
            mock_repo.delete.assert_called_once_with(persona_id)


class TestSetDefaultPersonaEndpoint:
    """Tests for set-default persona endpoint."""

    @pytest.fixture
    def mock_repo(self):
        """Create a mock persona repository."""
        repo = MagicMock()
        repo.get = AsyncMock()
        repo.set_default = AsyncMock()
        return repo

    @pytest.mark.asyncio
    async def test_set_default_persona_success(self, mock_repo):
        """Test successfully setting a persona as default."""
        from uuid import uuid4

        from voiceobs.server.routes.personas import set_persona_default

        persona_id = uuid4()
        mock_repo.get.return_value = PersonaRow(
            id=persona_id,
            name="New Default",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
            is_default=False,
        )
        mock_repo.set_default.return_value = PersonaRow(
            id=persona_id,
            name="New Default",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
            is_default=True,
        )

        with (
            patch("voiceobs.server.routes.personas.get_persona_repository", return_value=mock_repo),
            patch("voiceobs.server.routes.personas.parse_uuid", return_value=persona_id),
        ):
            result = await set_persona_default(str(persona_id))

            assert result.is_default is True
            mock_repo.set_default.assert_called_once_with(persona_id)

    @pytest.mark.asyncio
    async def test_set_default_persona_not_found(self, mock_repo):
        """Test setting default on non-existent persona returns 404."""
        from uuid import uuid4

        from voiceobs.server.routes.personas import set_persona_default

        persona_id = uuid4()
        mock_repo.get.return_value = None

        with (
            patch("voiceobs.server.routes.personas.get_persona_repository", return_value=mock_repo),
            patch("voiceobs.server.routes.personas.parse_uuid", return_value=persona_id),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await set_persona_default(str(persona_id))

            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_set_default_returns_500_when_repo_returns_none(self, mock_repo):
        """Test that 500 error is returned when set_default unexpectedly returns None."""
        from uuid import uuid4

        from voiceobs.server.routes.personas import set_persona_default

        persona_id = uuid4()
        # Persona exists when we check
        mock_repo.get.return_value = PersonaRow(
            id=persona_id,
            name="Test Persona",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            is_active=True,
            is_default=False,
        )
        # But set_default returns None (unexpected failure)
        mock_repo.set_default.return_value = None

        with (
            patch("voiceobs.server.routes.personas.get_persona_repository", return_value=mock_repo),
            patch("voiceobs.server.routes.personas.parse_uuid", return_value=persona_id),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await set_persona_default(str(persona_id))

            assert exc_info.value.status_code == 500
            assert "Failed to set persona as default" in exc_info.value.detail


class TestPersonaRepositoryIsDefaultMethods:
    """Tests for is_default related methods in PersonaRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database connection."""
        db = MagicMock()
        db.fetchrow = AsyncMock()
        db.fetch = AsyncMock()
        db.execute = AsyncMock()
        db.fetchval = AsyncMock()
        return db

    @pytest.mark.asyncio
    async def test_get_default_returns_default_persona(self, mock_db):
        """Test get_default returns the persona with is_default=True."""
        from uuid import uuid4

        from voiceobs.server.db.repositories.persona import PersonaRepository

        persona_id = uuid4()
        mock_db.fetchrow.return_value = {
            "id": persona_id,
            "name": "Default Persona",
            "description": "The default one",
            "aggression": 0.5,
            "patience": 0.5,
            "verbosity": 0.5,
            "traits": [],
            "tts_provider": "openai",
            "tts_config": {},
            "preview_audio_url": None,
            "preview_audio_text": None,
            "metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": None,
            "is_active": True,
            "is_default": True,
        }

        repo = PersonaRepository(mock_db)
        result = await repo.get_default()

        assert result is not None
        assert result.is_default is True
        assert result.name == "Default Persona"

    @pytest.mark.asyncio
    async def test_get_default_returns_none_when_no_default(self, mock_db):
        """Test get_default returns None when no default persona exists."""
        from voiceobs.server.db.repositories.persona import PersonaRepository

        mock_db.fetchrow.return_value = None

        repo = PersonaRepository(mock_db)
        result = await repo.get_default()

        assert result is None

    @pytest.mark.asyncio
    async def test_set_default_unsets_old_and_sets_new(self, mock_db):
        """Test set_default atomically unsets old default and sets new."""
        from contextlib import asynccontextmanager
        from uuid import uuid4

        from voiceobs.server.db.repositories.persona import PersonaRepository

        persona_id = uuid4()
        mock_db.fetchrow.return_value = {
            "id": persona_id,
            "name": "New Default",
            "description": None,
            "aggression": 0.5,
            "patience": 0.5,
            "verbosity": 0.5,
            "traits": [],
            "tts_provider": "openai",
            "tts_config": {},
            "preview_audio_url": None,
            "preview_audio_text": None,
            "metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "created_by": None,
            "is_active": True,
            "is_default": True,
        }

        # Mock the transaction context manager
        mock_conn = AsyncMock()

        @asynccontextmanager
        async def mock_transaction():
            yield mock_conn

        mock_db.transaction = mock_transaction

        repo = PersonaRepository(mock_db)
        result = await repo.set_default(persona_id)

        assert result is not None
        assert result.is_default is True
        # Verify that execute was called on the connection (for unsetting old and setting new)
        assert mock_conn.execute.call_count == 2
