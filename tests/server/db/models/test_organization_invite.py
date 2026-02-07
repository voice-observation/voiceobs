"""Tests for OrganizationInvite model."""

from datetime import datetime
from uuid import uuid4

from voiceobs.server.db.models import OrganizationInviteRow


class TestOrganizationInviteRow:
    """Tests for OrganizationInviteRow dataclass."""

    def test_invite_row_creation(self):
        """Test creating an OrganizationInviteRow with all fields."""
        invite_id = uuid4()
        org_id = uuid4()
        invited_by = uuid4()
        now = datetime.now()
        expires = datetime.now()

        invite = OrganizationInviteRow(
            id=invite_id,
            org_id=org_id,
            email="test@example.com",
            token="abc123token",
            status="pending",
            invited_by=invited_by,
            created_at=now,
            expires_at=expires,
        )

        assert invite.id == invite_id
        assert invite.org_id == org_id
        assert invite.email == "test@example.com"
        assert invite.token == "abc123token"
        assert invite.status == "pending"
        assert invite.invited_by == invited_by
        assert invite.created_at == now
        assert invite.expires_at == expires

    def test_invite_row_defaults(self):
        """Test OrganizationInviteRow with default values."""
        invite = OrganizationInviteRow(
            id=uuid4(),
            org_id=uuid4(),
            email="test@example.com",
            token="token123",
            invited_by=uuid4(),
        )

        assert invite.status == "pending"
        assert invite.created_at is None
        assert invite.expires_at is None

    def test_invite_row_statuses(self):
        """Test OrganizationInviteRow with different statuses."""
        for status in ["pending", "accepted", "expired", "revoked"]:
            invite = OrganizationInviteRow(
                id=uuid4(),
                org_id=uuid4(),
                email="test@example.com",
                token=f"token-{status}",
                status=status,
                invited_by=uuid4(),
            )
            assert invite.status == status
