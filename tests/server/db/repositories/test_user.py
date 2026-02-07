"""Tests for UserRepository."""

from uuid import uuid4

import pytest

from voiceobs.server.db.models import UserRow
from voiceobs.server.db.repositories.user import UserRepository

from .conftest import MockRecord


class TestUserRepository:
    """Tests for the UserRepository class."""

    @pytest.mark.asyncio
    async def test_upsert_creates_user(self, mock_db):
        """Test creating a user via upsert."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Test User",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.upsert(
            user_id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.auth_provider == "google"
        assert user.is_active is True
        mock_db.execute.assert_called_once()
        assert "INSERT INTO users" in mock_db.execute.call_args[0][0]
        assert "ON CONFLICT" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_upsert_updates_existing_user(self, mock_db):
        """Test that upsert updates existing user."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        # First call returns None (during execute), second call returns the user
        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Updated Name",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        # Upsert with updated name
        user = await repo.upsert(
            user_id=user_id,
            email="test@example.com",
            name="Updated Name",
            auth_provider="google",
        )

        assert user.name == "Updated Name"

    @pytest.mark.asyncio
    async def test_upsert_database_failure(self, mock_db):
        """Test upsert when database fails to return user."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        # Mock the fetchrow to return None (simulating database failure)
        mock_db.fetchrow.return_value = None

        with pytest.raises(RuntimeError, match="Failed to upsert user"):
            await repo.upsert(
                user_id=user_id,
                email="test@example.com",
            )

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, mock_db):
        """Test getting a user by ID."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Test User",
                "avatar_url": None,
                "auth_provider": "email",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.get(user_id)

        assert user is not None
        assert user.id == user_id
        assert user.email == "test@example.com"
        mock_db.fetchrow.assert_called_once()
        assert "FROM users WHERE id = $1" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, mock_db):
        """Test getting a user that doesn't exist."""
        repo = UserRepository(mock_db)
        mock_db.fetchrow.return_value = None

        user = await repo.get(uuid4())

        assert user is None

    @pytest.mark.asyncio
    async def test_update_user_single_field(self, mock_db):
        """Test updating a single field."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Updated Name",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.update(
            user_id=user_id,
            name="Updated Name",
        )

        assert user is not None
        assert user.name == "Updated Name"
        mock_db.execute.assert_called_once()
        assert "UPDATE users" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_user_multiple_fields(self, mock_db):
        """Test updating multiple fields."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Updated",
                "avatar_url": "https://example.com/new-avatar.jpg",
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.update(
            user_id=user_id,
            name="Updated",
            avatar_url="https://example.com/new-avatar.jpg",
        )

        assert user is not None
        assert user.name == "Updated"
        assert user.avatar_url == "https://example.com/new-avatar.jpg"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, mock_db):
        """Test updating a non-existent user."""
        repo = UserRepository(mock_db)
        mock_db.fetchrow.return_value = None

        user = await repo.update(uuid4(), name="Updated")

        assert user is None

    @pytest.mark.asyncio
    async def test_update_user_no_changes(self, mock_db):
        """Test update with no fields to update."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Original",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.update(user_id)

        assert user is not None
        assert user.name == "Original"
        # Should call fetchrow for get but not execute for update
        assert mock_db.fetchrow.called
        assert not mock_db.execute.called

    @pytest.mark.asyncio
    async def test_update_user_is_active(self, mock_db):
        """Test updating user is_active status."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Test",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": False,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.update(user_id, is_active=False)

        assert user is not None
        assert user.is_active is False
        mock_db.execute.assert_called_once()
        update_query = mock_db.execute.call_args[0][0]
        assert "is_active" in update_query

    @pytest.mark.asyncio
    async def test_row_to_user(self, mock_db):
        """Test _row_to_user correctly converts database row."""
        repo = UserRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Test User",
                "avatar_url": "https://example.com/avatar.jpg",
                "auth_provider": "github",
                "is_active": True,
                "last_active_org_id": None,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.get(user_id)

        assert user is not None
        assert isinstance(user, UserRow)
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.jpg"
        assert user.auth_provider == "github"

    @pytest.mark.asyncio
    async def test_upsert_returns_last_active_org_id(self, mock_db):
        """Test that upsert returns last_active_org_id."""
        repo = UserRepository(mock_db)
        user_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Test",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": org_id,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.upsert(user_id=user_id, email="test@example.com")

        assert user.last_active_org_id == org_id

    @pytest.mark.asyncio
    async def test_update_last_active_org_id(self, mock_db):
        """Test updating last_active_org_id."""
        repo = UserRepository(mock_db)
        user_id = uuid4()
        org_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": user_id,
                "email": "test@example.com",
                "name": "Test",
                "avatar_url": None,
                "auth_provider": "google",
                "is_active": True,
                "last_active_org_id": org_id,
                "created_at": None,
                "updated_at": None,
            }
        )

        user = await repo.update(user_id, last_active_org_id=org_id)

        assert user is not None
        assert user.last_active_org_id == org_id
        mock_db.execute.assert_called_once()
        assert "last_active_org_id" in mock_db.execute.call_args[0][0]
