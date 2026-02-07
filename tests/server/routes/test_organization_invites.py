"""Tests for organization invites routes."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from voiceobs.server.db.models import (
    OrganizationInviteRow,
    OrganizationMemberRow,
    OrganizationRow,
    UserRow,
)


def create_jwt_payload(user_id: str, email: str) -> dict:
    """Create a test JWT payload."""
    return {
        "sub": user_id,
        "email": email,
        "aud": "authenticated",
        "user_metadata": {"name": "Test User"},
        "app_metadata": {"provider": "google"},
    }


class TestListInvites:
    """Tests for listing organization invites."""

    def test_list_invites_success(self, client):
        """Test listing invites as an organization member."""
        user_id = uuid4()
        org_id = uuid4()
        created_at = datetime.now(timezone.utc)
        expires_at = datetime.now(timezone.utc)

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

        mock_invite_repo = AsyncMock()
        mock_invite_repo.list_pending_for_org.return_value = [
            OrganizationInviteRow(
                id=uuid4(),
                org_id=org_id,
                email="invitee@example.com",
                token="secret-token",
                invited_by=user_id,
                status="pending",
                created_at=created_at,
                expires_at=expires_at,
            ),
        ]

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "test@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.get(
                            f"/api/v1/orgs/{org_id}/invites",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["email"] == "invitee@example.com"
        assert data[0]["status"] == "pending"

    def test_list_invites_not_member(self, client):
        """Test listing invites when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()

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

        mock_invite_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "test@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.get(
                            f"/api/v1/orgs/{org_id}/invites",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"].lower()


class TestSendInvite:
    """Tests for sending organization invites."""

    def test_send_invite_as_owner(self, client):
        """Test sending an invite as organization owner."""
        user_id = uuid4()
        org_id = uuid4()
        invite_id = uuid4()
        created_at = datetime.now(timezone.utc)
        expires_at = datetime.now(timezone.utc)

        mock_user = UserRow(
            id=user_id,
            email="owner@example.com",
            name="Owner User",
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

        mock_invite_repo = AsyncMock()
        mock_invite_repo.create.return_value = OrganizationInviteRow(
            id=invite_id,
            org_id=org_id,
            email="invitee@example.com",
            token="generated-token",
            invited_by=user_id,
            status="pending",
            created_at=created_at,
            expires_at=expires_at,
        )

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "owner@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.post(
                            f"/api/v1/orgs/{org_id}/invites",
                            json={"email": "invitee@example.com"},
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "invitee@example.com"
        assert data["status"] == "pending"

    def test_send_invite_not_owner(self, client):
        """Test sending an invite as non-owner returns 403."""
        user_id = uuid4()
        org_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="member@example.com",
            name="Member User",
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

        mock_invite_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "member@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.post(
                            f"/api/v1/orgs/{org_id}/invites",
                            json={"email": "invitee@example.com"},
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 403
        assert "owner" in response.json()["detail"].lower()


class TestRevokeInvite:
    """Tests for revoking organization invites."""

    def test_revoke_invite_as_owner(self, client):
        """Test revoking an invite as organization owner."""
        user_id = uuid4()
        org_id = uuid4()
        invite_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="owner@example.com",
            name="Owner User",
            auth_provider="google",
        )

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
        )

        mock_invite = OrganizationInviteRow(
            id=invite_id,
            org_id=org_id,
            email="invitee@example.com",
            token="some-token",
            invited_by=user_id,
            status="pending",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_id.return_value = mock_invite
        mock_invite_repo.update_status.return_value = mock_invite

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "owner@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}/invites/{invite_id}",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 204
        mock_invite_repo.update_status.assert_called_once_with(invite_id, "revoked")

    def test_revoke_invite_not_owner(self, client):
        """Test revoking an invite as non-owner returns 403."""
        user_id = uuid4()
        org_id = uuid4()
        invite_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="member@example.com",
            name="Member User",
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

        mock_invite_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "member@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}/invites/{invite_id}",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 403
        assert "owner" in response.json()["detail"].lower()


class TestGetInviteByToken:
    """Tests for getting invite details by token."""

    def test_get_invite_by_token_success(self, client):
        """Test getting invite details by token (public endpoint)."""
        org_id = uuid4()
        invite_token = "valid-invite-token"

        mock_invite = OrganizationInviteRow(
            id=uuid4(),
            org_id=org_id,
            email="invitee@example.com",
            token=invite_token,
            invited_by=uuid4(),
            status="pending",
        )

        mock_org = OrganizationRow(
            id=org_id,
            name="Test Organization",
            created_by=uuid4(),
        )

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = mock_invite

        mock_org_repo = AsyncMock()
        mock_org_repo.get.return_value = mock_org

        with patch(
            "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
            return_value=mock_invite_repo,
        ):
            with patch(
                "voiceobs.server.routes.organization_invites.get_organization_repository",
                return_value=mock_org_repo,
            ):
                response = client.get(f"/api/v1/invites/{invite_token}")

        assert response.status_code == 200
        data = response.json()
        assert data["org_name"] == "Test Organization"
        assert data["email"] == "invitee@example.com"
        assert data["status"] == "pending"

    def test_get_invite_by_token_not_found(self, client):
        """Test getting invite with invalid token returns 404."""
        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = None

        mock_org_repo = AsyncMock()

        with patch(
            "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
            return_value=mock_invite_repo,
        ):
            with patch(
                "voiceobs.server.routes.organization_invites.get_organization_repository",
                return_value=mock_org_repo,
            ):
                response = client.get("/api/v1/invites/invalid-token")

        assert response.status_code == 404


class TestAcceptInvite:
    """Tests for accepting organization invites."""

    def test_accept_invite_success(self, client):
        """Test accepting an invite and joining the organization."""
        user_id = uuid4()
        org_id = uuid4()
        invite_id = uuid4()
        invite_token = "valid-invite-token"

        mock_user = UserRow(
            id=user_id,
            email="invitee@example.com",
            name="Invitee User",
            auth_provider="google",
        )

        mock_invite = OrganizationInviteRow(
            id=invite_id,
            org_id=org_id,
            email="invitee@example.com",
            token=invite_token,
            invited_by=uuid4(),
            status="pending",
        )

        mock_org = OrganizationRow(
            id=org_id,
            name="Test Organization",
            created_by=uuid4(),
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = mock_invite

        mock_org_repo = AsyncMock()
        mock_org_repo.get.return_value = mock_org

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = False

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "invitee@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                    return_value=mock_invite_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_repository",
                        return_value=mock_org_repo,
                    ):
                        with patch(
                            "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                            return_value=mock_member_repo,
                        ):
                            response = client.post(
                                f"/api/v1/invites/{invite_token}/accept",
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 200
        data = response.json()
        assert data["org_id"] == str(org_id)
        assert data["org_name"] == "Test Organization"
        assert data["role"] == "member"

        # Verify member was added and invite status updated
        mock_member_repo.add.assert_called_once_with(org_id=org_id, user_id=user_id, role="member")
        mock_invite_repo.update_status.assert_called_once_with(invite_id, "accepted")

    def test_accept_invite_email_mismatch(self, client):
        """Test accepting invite with different email returns 403."""
        user_id = uuid4()
        org_id = uuid4()
        invite_token = "valid-invite-token"

        mock_user = UserRow(
            id=user_id,
            email="different@example.com",
            name="Different User",
            auth_provider="google",
        )

        mock_invite = OrganizationInviteRow(
            id=uuid4(),
            org_id=org_id,
            email="invitee@example.com",  # Different email
            token=invite_token,
            invited_by=uuid4(),
            status="pending",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = mock_invite

        mock_org_repo = AsyncMock()
        mock_member_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "different@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                    return_value=mock_invite_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_repository",
                        return_value=mock_org_repo,
                    ):
                        with patch(
                            "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                            return_value=mock_member_repo,
                        ):
                            response = client.post(
                                f"/api/v1/invites/{invite_token}/accept",
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 403
        assert "different email" in response.json()["detail"].lower()

    def test_accept_invite_already_member(self, client):
        """Test accepting invite when already a member returns 400."""
        user_id = uuid4()
        org_id = uuid4()
        invite_token = "valid-invite-token"

        mock_user = UserRow(
            id=user_id,
            email="invitee@example.com",
            name="Invitee User",
            auth_provider="google",
        )

        mock_invite = OrganizationInviteRow(
            id=uuid4(),
            org_id=org_id,
            email="invitee@example.com",
            token=invite_token,
            invited_by=uuid4(),
            status="pending",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = mock_invite

        mock_org_repo = AsyncMock()

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member.return_value = True  # Already a member

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "invitee@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                    return_value=mock_invite_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_repository",
                        return_value=mock_org_repo,
                    ):
                        with patch(
                            "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                            return_value=mock_member_repo,
                        ):
                            response = client.post(
                                f"/api/v1/invites/{invite_token}/accept",
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 400
        assert "already a member" in response.json()["detail"].lower()

    def test_accept_invite_unauthenticated(self, client):
        """Test accepting invite without token returns 401."""
        response = client.post("/api/v1/invites/some-token/accept")
        assert response.status_code == 401

    def test_accept_invite_not_found(self, client):
        """Test accepting invite with invalid token returns 404."""
        user_id = uuid4()
        invite_token = "invalid-token"

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = None  # Not found

        mock_org_repo = AsyncMock()
        mock_member_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "test@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                    return_value=mock_invite_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_repository",
                        return_value=mock_org_repo,
                    ):
                        with patch(
                            "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                            return_value=mock_member_repo,
                        ):
                            response = client.post(
                                f"/api/v1/invites/{invite_token}/accept",
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_accept_invite_not_pending(self, client):
        """Test accepting invite that is already accepted/revoked returns 400."""
        user_id = uuid4()
        org_id = uuid4()
        invite_token = "valid-token"

        mock_user = UserRow(
            id=user_id,
            email="invitee@example.com",
            name="Invitee User",
            auth_provider="google",
        )

        mock_invite = OrganizationInviteRow(
            id=uuid4(),
            org_id=org_id,
            email="invitee@example.com",
            token=invite_token,
            invited_by=uuid4(),
            status="accepted",  # Already accepted
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = mock_invite

        mock_org_repo = AsyncMock()
        mock_member_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "invitee@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                    return_value=mock_invite_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_repository",
                        return_value=mock_org_repo,
                    ):
                        with patch(
                            "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                            return_value=mock_member_repo,
                        ):
                            response = client.post(
                                f"/api/v1/invites/{invite_token}/accept",
                                headers={"Authorization": "Bearer test-token"},
                            )

        assert response.status_code == 400
        assert "accepted" in response.json()["detail"].lower()


class TestSendInviteNotMember:
    """Tests for sending invite when user is not a member."""

    def test_send_invite_not_member(self, client):
        """Test sending invite when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = None  # Not a member

        mock_invite_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "test@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.post(
                            f"/api/v1/orgs/{org_id}/invites",
                            json={"email": "invitee@example.com"},
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"].lower()


class TestRevokeInviteNotMember:
    """Tests for revoking invite when user is not a member."""

    def test_revoke_invite_not_member(self, client):
        """Test revoking invite when not a member returns 403."""
        user_id = uuid4()
        org_id = uuid4()
        invite_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="test@example.com",
            name="Test User",
            auth_provider="google",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = None  # Not a member

        mock_invite_repo = AsyncMock()

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "test@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}/invites/{invite_id}",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 403
        assert "not a member" in response.json()["detail"].lower()

    def test_revoke_invite_not_found(self, client):
        """Test revoking invite that doesn't exist returns 404."""
        user_id = uuid4()
        org_id = uuid4()
        invite_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="owner@example.com",
            name="Owner User",
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

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_id.return_value = None  # Invite not found

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "owner@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}/invites/{invite_id}",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_revoke_invite_wrong_org(self, client):
        """Test revoking invite from different org returns 404."""
        user_id = uuid4()
        org_id = uuid4()
        other_org_id = uuid4()
        invite_id = uuid4()

        mock_user = UserRow(
            id=user_id,
            email="owner@example.com",
            name="Owner User",
            auth_provider="google",
        )

        mock_membership = OrganizationMemberRow(
            id=uuid4(),
            org_id=org_id,
            user_id=user_id,
            role="owner",
        )

        mock_invite = OrganizationInviteRow(
            id=invite_id,
            org_id=other_org_id,  # Different org
            email="invitee@example.com",
            token="some-token",
            invited_by=uuid4(),
            status="pending",
        )

        mock_user_repo = AsyncMock()
        mock_user_repo.upsert.return_value = mock_user

        mock_member_repo = AsyncMock()
        mock_member_repo.get.return_value = mock_membership

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_id.return_value = mock_invite

        with patch(
            "voiceobs.server.auth.dependencies.decode_supabase_jwt",
            return_value=create_jwt_payload(str(user_id), "owner@example.com"),
        ):
            with patch(
                "voiceobs.server.auth.dependencies.get_user_repository",
                return_value=mock_user_repo,
            ):
                with patch(
                    "voiceobs.server.routes.organization_invites.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
                        return_value=mock_invite_repo,
                    ):
                        response = client.delete(
                            f"/api/v1/orgs/{org_id}/invites/{invite_id}",
                            headers={"Authorization": "Bearer test-token"},
                        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetInviteByTokenNotPending:
    """Tests for getting invite by token when not pending."""

    def test_get_invite_by_token_not_pending(self, client):
        """Test getting invite that is not pending returns 400."""
        org_id = uuid4()
        invite_token = "valid-token"

        mock_invite = OrganizationInviteRow(
            id=uuid4(),
            org_id=org_id,
            email="invitee@example.com",
            token=invite_token,
            invited_by=uuid4(),
            status="revoked",  # Not pending
        )

        mock_invite_repo = AsyncMock()
        mock_invite_repo.get_by_token.return_value = mock_invite

        mock_org_repo = AsyncMock()

        with patch(
            "voiceobs.server.routes.organization_invites.get_organization_invite_repository",
            return_value=mock_invite_repo,
        ):
            with patch(
                "voiceobs.server.routes.organization_invites.get_organization_repository",
                return_value=mock_org_repo,
            ):
                response = client.get(f"/api/v1/invites/{invite_token}")

        assert response.status_code == 400
        assert "revoked" in response.json()["detail"].lower()
