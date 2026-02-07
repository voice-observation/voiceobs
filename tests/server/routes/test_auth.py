"""Tests for auth routes."""

import time
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from jose import jwt

from voiceobs.server.db.models import UserRow

TEST_JWT_SECRET = "test-secret-for-unit-tests-only"


def create_test_token(user_id: str, email: str) -> str:
    """Create a test JWT token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": now + 3600,
        "iat": now,
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"provider": "google"},
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def create_test_payload(user_id: str, email: str) -> dict:
    """Create a test JWT payload (for mocking decode_supabase_jwt)."""
    now = int(time.time())
    return {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "exp": now + 3600,
        "iat": now,
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"provider": "google"},
    }


def test_get_me_authenticated(client):
    """Test GET /api/v1/auth/me with valid token."""
    user_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    mock_org_repo = AsyncMock()
    mock_org_repo.list_for_user.return_value = []

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    org_repo_patch = "voiceobs.server.routes.auth.get_organization_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_patch, return_value=mock_repo):
            with patch(org_repo_patch, return_value=mock_org_repo):
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"
    assert data["orgs"] == []
    assert data["active_org"] is None


def test_get_me_unauthenticated(client):
    """Test GET /api/v1/auth/me without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_update_me(client):
    """Test PATCH /api/v1/auth/me."""
    user_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Updated Name",
        auth_provider="google",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user
    mock_repo.update.return_value = mock_user

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    user_repo_routes_patch = "voiceobs.server.routes.auth.get_user_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_repo):
            with patch(user_repo_routes_patch, return_value=mock_repo):
                response = client.patch(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"name": "Updated Name"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_update_me_unauthenticated(client):
    """Test PATCH /api/v1/auth/me without token."""
    response = client.patch("/api/v1/auth/me", json={"name": "New Name"})
    assert response.status_code == 401


def test_get_me_invalid_token(client):
    """Test GET /api/v1/auth/me with invalid token."""
    from voiceobs.server.auth.jwt import JWTValidationError

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"

    with patch(decode_jwt_patch, side_effect=JWTValidationError("Invalid token")):
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
    assert response.status_code == 401


def test_update_me_repo_unavailable(client):
    """Test PATCH /api/v1/auth/me when user repository is unavailable."""
    import pytest

    user_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    user_repo_routes_patch = "voiceobs.server.routes.auth.get_user_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_repo):
            with patch(user_repo_routes_patch, return_value=None):  # Repo unavailable
                with pytest.raises(RuntimeError, match="User repository not available"):
                    client.patch(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"name": "New Name"},
                    )


def test_update_me_user_not_found_after_auth(client):
    """Test PATCH /api/v1/auth/me when user not found after authentication."""
    import pytest

    user_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
    )

    mock_repo = AsyncMock()
    mock_repo.upsert.return_value = mock_user
    mock_repo.update.return_value = None  # User not found during update

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    user_repo_routes_patch = "voiceobs.server.routes.auth.get_user_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_repo):
            with patch(user_repo_routes_patch, return_value=mock_repo):
                with pytest.raises(RuntimeError, match="User not found after auth"):
                    client.patch(
                        "/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {token}"},
                        json={"name": "New Name"},
                    )


def test_get_me_returns_orgs(client):
    """Test that /me returns user's organizations."""
    from voiceobs.server.db.models import OrganizationRow

    user_id = uuid4()
    org1_id = uuid4()
    org2_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
        last_active_org_id=org1_id,
    )

    orgs = [
        {
            "org": OrganizationRow(id=org1_id, name="Org 1", created_by=user_id),
            "role": "owner",
        },
        {
            "org": OrganizationRow(id=org2_id, name="Org 2", created_by=uuid4()),
            "role": "member",
        },
    ]

    active_org = OrganizationRow(id=org1_id, name="Org 1", created_by=user_id)

    mock_user_repo = AsyncMock()
    mock_user_repo.upsert.return_value = mock_user

    mock_org_repo = AsyncMock()
    mock_org_repo.list_for_user.return_value = orgs
    mock_org_repo.get.return_value = active_org

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    org_repo_patch = "voiceobs.server.routes.auth.get_organization_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_user_repo):
            with patch(org_repo_patch, return_value=mock_org_repo):
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user_id)
    assert data["user"]["email"] == "test@example.com"
    assert len(data["orgs"]) == 2
    assert data["orgs"][0]["id"] == str(org1_id)
    assert data["orgs"][0]["name"] == "Org 1"
    assert data["orgs"][0]["role"] == "owner"
    assert data["orgs"][1]["id"] == str(org2_id)
    assert data["orgs"][1]["role"] == "member"
    assert data["active_org"]["id"] == str(org1_id)
    assert data["active_org"]["name"] == "Org 1"


def test_get_me_no_active_org(client):
    """Test that /me works when user has no active org."""
    from voiceobs.server.db.models import OrganizationRow

    user_id = uuid4()
    org_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
        last_active_org_id=None,  # No active org
    )

    orgs = [
        {
            "org": OrganizationRow(id=org_id, name="Org 1", created_by=user_id),
            "role": "owner",
        },
    ]

    mock_user_repo = AsyncMock()
    mock_user_repo.upsert.return_value = mock_user

    mock_org_repo = AsyncMock()
    mock_org_repo.list_for_user.return_value = orgs

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    org_repo_patch = "voiceobs.server.routes.auth.get_organization_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_user_repo):
            with patch(org_repo_patch, return_value=mock_org_repo):
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user_id)
    assert len(data["orgs"]) == 1
    assert data["active_org"] is None


def test_get_me_no_orgs(client):
    """Test that /me works when user has no organizations."""
    user_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
        last_active_org_id=None,
    )

    mock_user_repo = AsyncMock()
    mock_user_repo.upsert.return_value = mock_user

    mock_org_repo = AsyncMock()
    mock_org_repo.list_for_user.return_value = []

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    org_repo_patch = "voiceobs.server.routes.auth.get_organization_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_user_repo):
            with patch(org_repo_patch, return_value=mock_org_repo):
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user_id)
    assert len(data["orgs"]) == 0
    assert data["active_org"] is None


def test_get_me_org_repo_none(client):
    """Test that /me works when org repository is not available."""
    user_id = uuid4()
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
    )

    mock_user_repo = AsyncMock()
    mock_user_repo.upsert.return_value = mock_user

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    org_repo_patch = "voiceobs.server.routes.auth.get_organization_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_user_repo):
            with patch(org_repo_patch, return_value=None):  # No org repo
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user_id)
    assert len(data["orgs"]) == 0
    assert data["active_org"] is None


def test_get_me_active_org_not_found(client):
    """Test that /me works when active org is not found (deleted or invalid)."""
    user_id = uuid4()
    org_id = uuid4()
    deleted_org_id = uuid4()  # This org was deleted or doesn't exist
    token = create_test_token(str(user_id), "test@example.com")
    payload = create_test_payload(str(user_id), "test@example.com")

    mock_user = UserRow(
        id=user_id,
        email="test@example.com",
        name="Test User",
        auth_provider="google",
        last_active_org_id=deleted_org_id,  # Points to a deleted/non-existent org
    )

    from voiceobs.server.db.models import OrganizationRow

    orgs = [
        {
            "org": OrganizationRow(id=org_id, name="Org 1", created_by=user_id),
            "role": "owner",
        },
    ]

    mock_user_repo = AsyncMock()
    mock_user_repo.upsert.return_value = mock_user

    mock_org_repo = AsyncMock()
    mock_org_repo.list_for_user.return_value = orgs
    mock_org_repo.get.return_value = None  # Active org not found (deleted)

    decode_jwt_patch = "voiceobs.server.auth.dependencies.decode_supabase_jwt"
    user_repo_dep_patch = "voiceobs.server.auth.dependencies.get_user_repository"
    org_repo_patch = "voiceobs.server.routes.auth.get_organization_repository"

    with patch(decode_jwt_patch, return_value=payload):
        with patch(user_repo_dep_patch, return_value=mock_user_repo):
            with patch(org_repo_patch, return_value=mock_org_repo):
                response = client.get(
                    "/api/v1/auth/me",
                    headers={"Authorization": f"Bearer {token}"},
                )

    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == str(user_id)
    assert len(data["orgs"]) == 1
    # Active org should be None since the referenced org doesn't exist
    assert data["active_org"] is None
