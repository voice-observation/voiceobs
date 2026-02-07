"""Tests for organization routes."""

import time
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from jose import jwt

from voiceobs.server.db.models import OrganizationMemberRow, OrganizationRow, UserRow

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


class TestListOrgs:
    """Tests for listing user's organizations."""

    def test_list_orgs_returns_user_organizations(self, client):
        """Test listing organizations returns user's orgs with role."""
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
        )

        mock_org1 = OrganizationRow(id=org1_id, name="Org One", created_by=user_id)
        mock_org2 = OrganizationRow(id=org2_id, name="Org Two", created_by=uuid4())

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.list_for_user.return_value = [
            {"org": mock_org1, "role": "owner"},
            {"org": mock_org2, "role": "member"},
        ]

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    response = client.get(
                        "/api/v1/orgs",
                        headers={"Authorization": f"Bearer {token}"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == str(org1_id)
        assert data[0]["name"] == "Org One"
        assert data[0]["role"] == "owner"
        assert data[1]["id"] == str(org2_id)
        assert data[1]["name"] == "Org Two"
        assert data[1]["role"] == "member"

    def test_list_orgs_empty(self, client):
        """Test listing organizations returns empty list when user has no orgs."""
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

        mock_org_repo = AsyncMock()
        mock_org_repo.list_for_user.return_value = []

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    response = client.get(
                        "/api/v1/orgs",
                        headers={"Authorization": f"Bearer {token}"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_orgs_unauthenticated(self, client):
        """Test listing organizations without token returns 401."""
        response = client.get("/api/v1/orgs")
        assert response.status_code == 401


class TestCreateOrg:
    """Tests for creating organizations."""

    def test_create_org_success(self, client):
        """Test creating an organization successfully."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_org = OrganizationRow(id=org_id, name="New Org", created_by=user_id)
        mock_member = OrganizationMemberRow(
            id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.create.return_value = mock_org

        mock_member_repo = AsyncMock()
        mock_member_repo.add.return_value = mock_member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.post(
                            "/api/v1/orgs",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"name": "New Org"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(org_id)
        assert data["name"] == "New Org"
        assert data["role"] == "owner"
        mock_org_repo.create.assert_called_once_with(name="New Org", created_by=user_id)
        mock_member_repo.add.assert_called_once_with(org_id=org_id, user_id=user_id, role="owner")

    def test_create_org_unauthenticated(self, client):
        """Test creating organization without token returns 401."""
        response = client.post("/api/v1/orgs", json={"name": "New Org"})
        assert response.status_code == 401

    def test_create_org_invalid_name(self, client):
        """Test creating organization with empty name returns 422."""
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

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                response = client.post(
                    "/api/v1/orgs",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"name": ""},
                )

        assert response.status_code == 422


class TestGetOrg:
    """Tests for getting organization details."""

    def test_get_org_as_member(self, client):
        """Test getting organization details as a member."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_org = OrganizationRow(id=org_id, name="Test Org", created_by=uuid4())
        mock_member = OrganizationMemberRow(
            id=uuid4(), org_id=org_id, user_id=user_id, role="member"
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.get.return_value = mock_org

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = True
        mock_member_repo.get.return_value = mock_member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.get(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(org_id)
        assert data["name"] == "Test Org"
        assert data["role"] == "member"

    def test_get_org_not_member(self, client):
        """Test getting organization details when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_org = OrganizationRow(id=org_id, name="Test Org", created_by=uuid4())

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.get.return_value = mock_org

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = False

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.get(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"]

    def test_get_org_not_found(self, client):
        """Test getting non-existent organization returns 404."""
        user_id = uuid4()
        org_id = uuid4()
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

        mock_org_repo = AsyncMock()
        mock_org_repo.get.return_value = None

        mock_member_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.get(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 404

    def test_get_org_unauthenticated(self, client):
        """Test getting organization without token returns 401."""
        org_id = uuid4()
        response = client.get(f"/api/v1/orgs/{org_id}")
        assert response.status_code == 401


class TestUpdateOrg:
    """Tests for updating organization."""

    def test_update_org_success(self, client):
        """Test updating organization name successfully."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_org = OrganizationRow(id=org_id, name="Updated Org", created_by=user_id)
        mock_member = OrganizationMemberRow(
            id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.update.return_value = mock_org

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = True
        mock_member_repo.get.return_value = mock_member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.patch(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"name": "Updated Org"},
                        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Org"
        mock_org_repo.update.assert_called_once_with(org_id, name="Updated Org")

    def test_update_org_not_member(self, client):
        """Test updating organization when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()
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

        mock_org_repo = AsyncMock()

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = False

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.patch(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"name": "Updated Org"},
                        )

        assert response.status_code == 403

    def test_update_org_not_found(self, client):
        """Test updating non-existent organization returns 404."""
        user_id = uuid4()
        org_id = uuid4()
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

        mock_org_repo = AsyncMock()
        mock_org_repo.update.return_value = None

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = True

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.patch(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"name": "Updated Org"},
                        )

        assert response.status_code == 404

    def test_update_org_unauthenticated(self, client):
        """Test updating organization without token returns 401."""
        org_id = uuid4()
        response = client.patch(f"/api/v1/orgs/{org_id}", json={"name": "Updated"})
        assert response.status_code == 401


class TestDeleteOrg:
    """Tests for deleting organization."""

    def test_delete_org_as_owner(self, client):
        """Test deleting organization as owner succeeds."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_member = OrganizationMemberRow(
            id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.delete.return_value = True

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 204
        mock_org_repo.delete.assert_called_once_with(org_id)

    def test_delete_org_not_owner(self, client):
        """Test deleting organization as member (not owner) returns 403."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_member = OrganizationMemberRow(
            id=uuid4(), org_id=org_id, user_id=user_id, role="member"
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 403
        assert "owner" in response.json()["detail"].lower()

    def test_delete_org_not_member(self, client):
        """Test deleting organization when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()
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

        mock_org_repo = AsyncMock()

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = None

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 403

    def test_delete_org_not_found(self, client):
        """Test deleting non-existent organization returns 404."""
        user_id = uuid4()
        org_id = uuid4()
        token = create_test_token(str(user_id), "test@example.com")
        payload = create_test_payload(str(user_id), "test@example.com")

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_member = OrganizationMemberRow(
            id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_org_repo = AsyncMock()
        mock_org_repo.delete.return_value = False

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organizations.get_organization_repository",
                    return_value=mock_org_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organizations.get_organization_member_repository",
                        return_value=mock_member_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )

        assert response.status_code == 404

    def test_delete_org_unauthenticated(self, client):
        """Test deleting organization without token returns 401."""
        org_id = uuid4()
        response = client.delete(f"/api/v1/orgs/{org_id}")
        assert response.status_code == 401
