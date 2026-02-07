"""Tests for OrganizationInviteRepository."""

from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.organization_invite import (
    OrganizationInviteRepository,
)

from .conftest import MockRecord


class TestOrganizationInviteRepository:
    """Tests for the OrganizationInviteRepository class."""

    @pytest.mark.asyncio
    async def test_create_invite(self, mock_db):
        """Test creating an organization invite with generated token."""
        repo = OrganizationInviteRepository(mock_db)
        invite_id = uuid4()
        org_id = uuid4()
        email = "invitee@example.com"
        invited_by = uuid4()
        expires_at = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)
        generated_token = "a" * 64  # 32 hex bytes = 64 chars

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": invite_id,
                "org_id": org_id,
                "email": email,
                "token": generated_token,
                "invited_by": invited_by,
                "status": "pending",
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        with patch(
            "voiceobs.server.db.repositories.organization_invite.secrets.token_hex",
            return_value=generated_token,
        ):
            invite = await repo.create(
                org_id=org_id,
                email=email,
                invited_by=invited_by,
                expires_at=expires_at,
            )

        assert invite.id == invite_id
        assert invite.org_id == org_id
        assert invite.email == email
        assert invite.token == generated_token
        assert invite.invited_by == invited_by
        assert invite.status == "pending"
        assert invite.created_at == created_at
        assert invite.expires_at == expires_at
        mock_db.fetchrow.assert_called_once()
        assert "INSERT INTO organization_invites" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_by_token(self, mock_db):
        """Test getting an invite by token."""
        repo = OrganizationInviteRepository(mock_db)
        invite_id = uuid4()
        org_id = uuid4()
        email = "invitee@example.com"
        invited_by = uuid4()
        token = "test_token_123"
        expires_at = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": invite_id,
                "org_id": org_id,
                "email": email,
                "token": token,
                "invited_by": invited_by,
                "status": "pending",
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        invite = await repo.get_by_token(token=token)

        assert invite is not None
        assert invite.id == invite_id
        assert invite.token == token
        mock_db.fetchrow.assert_called_once()
        assert "SELECT" in mock_db.fetchrow.call_args[0][0]
        assert "token = $1" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_by_token_not_found(self, mock_db):
        """Test getting an invite by token that doesn't exist."""
        repo = OrganizationInviteRepository(mock_db)
        mock_db.fetchrow.return_value = None

        invite = await repo.get_by_token(token="nonexistent_token")

        assert invite is None

    @pytest.mark.asyncio
    async def test_get_by_id(self, mock_db):
        """Test getting an invite by ID."""
        repo = OrganizationInviteRepository(mock_db)
        invite_id = uuid4()
        org_id = uuid4()
        email = "invitee@example.com"
        invited_by = uuid4()
        token = "test_token_123"
        expires_at = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": invite_id,
                "org_id": org_id,
                "email": email,
                "token": token,
                "invited_by": invited_by,
                "status": "pending",
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        invite = await repo.get_by_id(invite_id=invite_id)

        assert invite is not None
        assert invite.id == invite_id
        mock_db.fetchrow.assert_called_once()
        assert "SELECT" in mock_db.fetchrow.call_args[0][0]
        assert "id = $1" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_db):
        """Test getting an invite by ID that doesn't exist."""
        repo = OrganizationInviteRepository(mock_db)
        mock_db.fetchrow.return_value = None

        invite = await repo.get_by_id(invite_id=uuid4())

        assert invite is None

    @pytest.mark.asyncio
    async def test_get_pending_for_email(self, mock_db):
        """Test getting a pending invite for a specific email in an org."""
        repo = OrganizationInviteRepository(mock_db)
        invite_id = uuid4()
        org_id = uuid4()
        email = "invitee@example.com"
        invited_by = uuid4()
        token = "test_token_123"
        expires_at = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": invite_id,
                "org_id": org_id,
                "email": email,
                "token": token,
                "invited_by": invited_by,
                "status": "pending",
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        invite = await repo.get_pending_for_email(org_id=org_id, email=email)

        assert invite is not None
        assert invite.id == invite_id
        assert invite.email == email
        assert invite.status == "pending"
        mock_db.fetchrow.assert_called_once()
        query = mock_db.fetchrow.call_args[0][0]
        assert "org_id = $1" in query
        assert "email = $2" in query
        assert "status = 'pending'" in query

    @pytest.mark.asyncio
    async def test_get_pending_for_email_not_found(self, mock_db):
        """Test getting a pending invite for email that doesn't exist."""
        repo = OrganizationInviteRepository(mock_db)
        mock_db.fetchrow.return_value = None

        invite = await repo.get_pending_for_email(org_id=uuid4(), email="no@example.com")

        assert invite is None

    @pytest.mark.asyncio
    async def test_update_status(self, mock_db):
        """Test updating an invite's status."""
        repo = OrganizationInviteRepository(mock_db)
        invite_id = uuid4()
        org_id = uuid4()
        email = "invitee@example.com"
        invited_by = uuid4()
        token = "test_token_123"
        expires_at = datetime.now(timezone.utc)
        created_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": invite_id,
                "org_id": org_id,
                "email": email,
                "token": token,
                "invited_by": invited_by,
                "status": "accepted",
                "created_at": created_at,
                "expires_at": expires_at,
            }
        )

        invite = await repo.update_status(invite_id=invite_id, status="accepted")

        assert invite is not None
        assert invite.id == invite_id
        assert invite.status == "accepted"
        mock_db.fetchrow.assert_called_once()
        query = mock_db.fetchrow.call_args[0][0]
        assert "UPDATE organization_invites" in query
        assert "status = $1" in query
        assert "id = $2" in query

    @pytest.mark.asyncio
    async def test_update_status_not_found(self, mock_db):
        """Test updating status for nonexistent invite."""
        repo = OrganizationInviteRepository(mock_db)
        mock_db.fetchrow.return_value = None

        invite = await repo.update_status(invite_id=uuid4(), status="revoked")

        assert invite is None

    @pytest.mark.asyncio
    async def test_list_pending_for_org(self, mock_db):
        """Test listing all pending invites for an organization."""
        repo = OrganizationInviteRepository(mock_db)
        org_id = uuid4()
        invite1_id = uuid4()
        invite2_id = uuid4()
        invited_by = uuid4()
        created_at = datetime.now(timezone.utc)
        expires_at = datetime.now(timezone.utc)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": invite1_id,
                    "org_id": org_id,
                    "email": "user1@example.com",
                    "token": "token1",
                    "invited_by": invited_by,
                    "status": "pending",
                    "created_at": created_at,
                    "expires_at": expires_at,
                }
            ),
            MockRecord(
                {
                    "id": invite2_id,
                    "org_id": org_id,
                    "email": "user2@example.com",
                    "token": "token2",
                    "invited_by": invited_by,
                    "status": "pending",
                    "created_at": created_at,
                    "expires_at": expires_at,
                }
            ),
        ]

        invites = await repo.list_pending_for_org(org_id=org_id)

        assert len(invites) == 2
        assert invites[0].id == invite1_id
        assert invites[0].email == "user1@example.com"
        assert invites[1].id == invite2_id
        assert invites[1].email == "user2@example.com"
        mock_db.fetch.assert_called_once()
        query = mock_db.fetch.call_args[0][0]
        assert "org_id = $1" in query
        assert "status = 'pending'" in query

    @pytest.mark.asyncio
    async def test_list_pending_for_org_empty(self, mock_db):
        """Test listing pending invites for org with no pending invites."""
        repo = OrganizationInviteRepository(mock_db)
        mock_db.fetch.return_value = []

        invites = await repo.list_pending_for_org(org_id=uuid4())

        assert invites == []

    @pytest.mark.asyncio
    async def test_delete_invite(self, mock_db):
        """Test deleting an invite."""
        repo = OrganizationInviteRepository(mock_db)
        invite_id = uuid4()

        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(invite_id=invite_id)

        assert result is True
        mock_db.execute.assert_called_once()
        assert "DELETE FROM organization_invites" in mock_db.execute.call_args[0][0]
        assert "id = $1" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_invite_not_found(self, mock_db):
        """Test deleting an invite that doesn't exist."""
        repo = OrganizationInviteRepository(mock_db)

        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(invite_id=uuid4())

        assert result is False
