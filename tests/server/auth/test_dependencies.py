"""Tests for auth dependencies."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from voiceobs.server.auth.dependencies import (
    get_current_user,
    get_current_user_optional,
    get_user_repository,
)
from voiceobs.server.auth.jwt import JWTValidationError
from voiceobs.server.db.models import OrganizationRow, UserRow
from voiceobs.server.db.repositories import UserRepository


@pytest.fixture(autouse=True)
def mock_org_service():
    """Mock organization service for all tests in this file."""
    with patch(
        "voiceobs.server.auth.dependencies.get_organization_service",
        return_value=AsyncMock(),
    ):
        yield


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test get_current_user with valid token."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        "user_metadata": {"name": "Test User", "avatar_url": None},
        "app_metadata": {"provider": "google"},
    }

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=mock_repo):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            user = await get_current_user(authorization="Bearer test-token")

    assert user.id == user_id
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    """Test get_current_user without Authorization header."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_optional_missing_header():
    """Test get_current_user_optional without Authorization header."""
    user = await get_current_user_optional(authorization=None)
    assert user is None


@pytest.mark.asyncio
async def test_get_current_user_invalid_header_format():
    """Test get_current_user with invalid Authorization header format."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="InvalidFormat token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test get_current_user with expired token."""
    with patch(
        "voiceobs.server.auth.dependencies.decode_supabase_jwt",
        side_effect=JWTValidationError("Token has expired"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(authorization="Bearer expired-token")

        assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_no_database():
    """Test get_current_user when database is not available."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"provider": "google"},
    }

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=None):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(authorization="Bearer test-token")

            assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_get_current_user_inactive_user():
    """Test get_current_user with inactive user."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"provider": "google"},
    }

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
        is_active=False,  # User is disabled
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=mock_repo):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(authorization="Bearer test-token")

            assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_optional_with_valid_token():
    """Test get_current_user_optional with valid token."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"provider": "google"},
    }

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=mock_repo):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            user = await get_current_user_optional(authorization="Bearer test-token")

    assert user is not None
    assert user.id == user_id


@pytest.mark.asyncio
async def test_get_current_user_optional_with_invalid_token():
    """Test get_current_user_optional with invalid token returns None."""
    with patch(
        "voiceobs.server.auth.dependencies.decode_supabase_jwt",
        side_effect=JWTValidationError("Invalid token"),
    ):
        user = await get_current_user_optional(authorization="Bearer invalid-token")

    assert user is None


@pytest.mark.asyncio
async def test_get_current_user_extracts_metadata():
    """Test that get_current_user correctly extracts user metadata from JWT."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        "user_metadata": {
            "name": "John Doe",
            "full_name": "John Full Doe",
            "avatar_url": "https://example.com/avatar.jpg",
        },
        "app_metadata": {"provider": "github"},
    }

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="John Doe",
        avatar_url="https://example.com/avatar.jpg",
        auth_provider="github",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=mock_repo):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            user = await get_current_user(authorization="Bearer test-token")

    # Verify upsert was called with correct arguments
    mock_repo.upsert.assert_called_once_with(
        user_id=user_id,
        email="test@example.com",
        name="John Doe",  # Should use 'name' over 'full_name'
        avatar_url="https://example.com/avatar.jpg",
        auth_provider="github",
    )
    assert user.id == user_id


def test_get_user_repository_returns_none_when_database_not_configured():
    """Test get_user_repository raises RuntimeError when database is not configured."""
    with patch("voiceobs.server.dependencies._user_repo", None):
        with pytest.raises(RuntimeError, match="User repository.*not available"):
            get_user_repository()


def test_get_user_repository_returns_repository_when_database_configured():
    """Test get_user_repository returns UserRepository when database is configured."""
    mock_repo = MagicMock(spec=UserRepository)

    with patch("voiceobs.server.dependencies._user_repo", mock_repo):
        repo = get_user_repository()
        assert repo is not None
        assert repo is mock_repo


@pytest.mark.asyncio
async def test_get_current_user_uses_full_name_as_fallback():
    """Test that get_current_user uses full_name when name is not present."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        "user_metadata": {
            "full_name": "John Full Name",
            "avatar_url": "https://example.com/avatar.jpg",
        },
        "app_metadata": {"provider": "github"},
    }

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="John Full Name",
        avatar_url="https://example.com/avatar.jpg",
        auth_provider="github",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=mock_repo):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            user = await get_current_user(authorization="Bearer test-token")

    # Verify upsert was called with full_name since name is not present
    mock_repo.upsert.assert_called_once_with(
        user_id=user_id,
        email="test@example.com",
        name="John Full Name",  # Should use 'full_name' as fallback
        avatar_url="https://example.com/avatar.jpg",
        auth_provider="github",
    )
    assert user.id == user_id


@pytest.mark.asyncio
async def test_get_current_user_with_minimal_metadata():
    """Test get_current_user with JWT that has no user_metadata or app_metadata."""
    user_id = uuid4()

    mock_payload = {
        "sub": str(user_id),
        "email": "test@example.com",
        # No user_metadata or app_metadata
    }

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name=None,
        avatar_url=None,
        auth_provider="email",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    with patch("voiceobs.server.auth.dependencies.get_user_repository", return_value=mock_repo):
        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            user = await get_current_user(authorization="Bearer test-token")

    # Verify upsert was called with defaults
    mock_repo.upsert.assert_called_once_with(
        user_id=user_id,
        email="test@example.com",
        name=None,
        avatar_url=None,
        auth_provider="email",  # Default when no provider in app_metadata
    )
    assert user.id == user_id


class TestGetCurrentUserWithOrgCreation:
    """Tests for get_current_user with auto org creation."""

    @pytest.mark.asyncio
    async def test_creates_org_for_new_user(self):
        """Test that a new user gets an org created."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="new@example.com", name="New User")
        org = OrganizationRow(id=org_id, name="New User's Organization", created_by=user_id)

        mock_repo = AsyncMock()
        mock_repo.upsert = AsyncMock(return_value=user)

        mock_org_service = AsyncMock()
        mock_org_service.ensure_user_has_org = AsyncMock(return_value=org)

        mock_jwt_payload = {
            "sub": str(user_id),
            "email": "new@example.com",
            "user_metadata": {"name": "New User"},
            "app_metadata": {"provider": "email"},
        }

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_jwt_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_repo,
            ):
                with patch(
                    "voiceobs.server.auth.dependencies.get_organization_service",
                    return_value=mock_org_service,
                ):
                    result = await get_current_user(authorization="Bearer token")

        assert result == user
        mock_org_service.ensure_user_has_org.assert_called_once_with(user)

    @pytest.mark.asyncio
    async def test_skips_org_creation_when_service_is_none(self):
        """Test that org creation is skipped when organization service is None."""
        user_id = uuid4()

        user = UserRow(id=user_id, email="new@example.com", name="New User")

        mock_repo = AsyncMock()
        mock_repo.upsert = AsyncMock(return_value=user)

        mock_jwt_payload = {
            "sub": str(user_id),
            "email": "new@example.com",
            "user_metadata": {"name": "New User"},
            "app_metadata": {"provider": "email"},
        }

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_jwt_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_repo,
            ):
                with patch(
                    "voiceobs.server.auth.dependencies.get_organization_service",
                    return_value=None,
                ):
                    result = await get_current_user(authorization="Bearer token")

        assert result == user
        # No org service called since it's None
