"""Tests for organization members routes."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import OrganizationMemberRow, UserRow


class TestListMembers:
    """Tests for listing organization members."""

    def test_list_members_success(self, client):
        """Test listing members of an organization as a member."""
        user_id = uuid4()
        other_user_id = uuid4()
        org_id = uuid4()
        joined_at = datetime.now(timezone.utc)

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

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = True
        mock_member_repo.list_members.return_value = [
            {
                "member": OrganizationMemberRow(
                    id=uuid4(),
                    org_id=org_id,
                    user_id=user_id,
                    role="owner",
                    joined_at=joined_at,
                ),
                "user_email": "test@example.com",
                "user_name": "Test User",
            },
            {
                "member": OrganizationMemberRow(
                    id=uuid4(),
                    org_id=org_id,
                    user_id=other_user_id,
                    role="member",
                    joined_at=joined_at,
                ),
                "user_email": "other@example.com",
                "user_name": "Other User",
            },
        ]

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.get(
                        f"/api/v1/orgs/{org_id}/members",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["user_id"] == str(user_id)
        assert data[0]["email"] == "test@example.com"
        assert data[0]["name"] == "Test User"
        assert data[0]["role"] == "owner"
        assert data[1]["user_id"] == str(other_user_id)
        assert data[1]["email"] == "other@example.com"
        assert data[1]["role"] == "member"

    def test_list_members_not_member(self, client):
        """Test listing members when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()

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

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = False

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.get(
                        f"/api/v1/orgs/{org_id}/members",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"]

    def test_list_members_unauthenticated(self, client):
        """Test listing members without token returns 401."""
        org_id = uuid4()
        response = client.get(f"/api/v1/orgs/{org_id}/members")
        assert response.status_code == 401


class TestRemoveMember:
    """Tests for removing organization members."""

    def test_remove_member_as_owner(self, client):
        """Test removing a member as owner succeeds."""
        user_id = uuid4()
        target_user_id = uuid4()
        org_id = uuid4()

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

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership
        mock_member_repo.remove.return_value = True

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.delete(
                        f"/api/v1/orgs/{org_id}/members/{target_user_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 204
        mock_member_repo.remove.assert_called_once_with(org_id=org_id, user_id=target_user_id)

    def test_remove_member_not_owner(self, client):
        """Test removing a member as non-owner returns 403."""
        user_id = uuid4()
        target_user_id = uuid4()
        org_id = uuid4()

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

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="member",  # Not owner
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.delete(
                        f"/api/v1/orgs/{org_id}/members/{target_user_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 403
        assert "owner" in response.json()["detail"].lower()

    def test_remove_member_not_member(self, client):
        """Test removing a member when not a member returns 403."""
        user_id = uuid4()
        target_user_id = uuid4()
        org_id = uuid4()

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

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = None

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.delete(
                        f"/api/v1/orgs/{org_id}/members/{target_user_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"]

    def test_remove_self_as_sole_owner(self, client):
        """Test removing self as sole owner returns 400."""
        user_id = uuid4()
        org_id = uuid4()
        joined_at = datetime.now(timezone.utc)

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

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership
        # Only one owner in the org
        mock_member_repo.list_members.return_value = [
            {
                "member": OrganizationMemberRow(
                    id=uuid4(),
                    org_id=org_id,
                    user_id=user_id,
                    role="owner",
                    joined_at=joined_at,
                ),
                "user_email": "test@example.com",
                "user_name": "Test User",
            },
        ]

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.delete(
                        f"/api/v1/orgs/{org_id}/members/{user_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 400
        assert "sole owner" in response.json()["detail"].lower()

    def test_remove_self_with_multiple_owners(self, client):
        """Test removing self when there are multiple owners succeeds."""
        user_id = uuid4()
        other_owner_id = uuid4()
        org_id = uuid4()
        joined_at = datetime.now(timezone.utc)

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

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership
        # Two owners in the org
        mock_member_repo.list_members.return_value = [
            {
                "member": OrganizationMemberRow(
                    id=uuid4(),
                    org_id=org_id,
                    user_id=user_id,
                    role="owner",
                    joined_at=joined_at,
                ),
                "user_email": "test@example.com",
                "user_name": "Test User",
            },
            {
                "member": OrganizationMemberRow(
                    id=uuid4(),
                    org_id=org_id,
                    user_id=other_owner_id,
                    role="owner",
                    joined_at=joined_at,
                ),
                "user_email": "other@example.com",
                "user_name": "Other User",
            },
        ]
        mock_member_repo.remove.return_value = True

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.delete(
                        f"/api/v1/orgs/{org_id}/members/{user_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 204
        mock_member_repo.remove.assert_called_once_with(org_id=org_id, user_id=user_id)

    def test_remove_member_not_found(self, client):
        """Test removing a member that doesn't exist returns 404."""
        user_id = uuid4()
        target_user_id = uuid4()
        org_id = uuid4()

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

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership
        mock_member_repo.remove.return_value = False  # Member not found

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=mock_payload,
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_members.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    response = client.delete(
                        f"/api/v1/orgs/{org_id}/members/{target_user_id}",
                        headers={"Authorization": "Bearer test-token"},
                    )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_remove_member_unauthenticated(self, client):
        """Test removing a member without token returns 401."""
        org_id = uuid4()
        user_id = uuid4()
        response = client.delete(f"/api/v1/orgs/{org_id}/members/{user_id}")
        assert response.status_code == 401
