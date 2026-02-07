"""Tests for OrganizationMember model."""

from datetime import datetime
from uuid import uuid4

from voiceobs.server.db.models import OrganizationMemberRow


class TestOrganizationMemberRow:
    """Tests for OrganizationMemberRow dataclass."""

    def test_member_row_creation(self):
        """Test creating an OrganizationMemberRow with all fields."""
        member_id = uuid4()
        org_id = uuid4()
        user_id = uuid4()
        invited_by = uuid4()
        now = datetime.now()

        member = OrganizationMemberRow(
            id=member_id,
            org_id=org_id,
            user_id=user_id,
            role="member",
            invited_by=invited_by,
            joined_at=now,
        )

        assert member.id == member_id
        assert member.org_id == org_id
        assert member.user_id == user_id
        assert member.role == "member"
        assert member.invited_by == invited_by
        assert member.joined_at == now

    def test_member_row_defaults(self):
        """Test OrganizationMemberRow with default values."""
        member_id = uuid4()
        org_id = uuid4()
        user_id = uuid4()

        member = OrganizationMemberRow(
            id=member_id,
            org_id=org_id,
            user_id=user_id,
        )

        assert member.role == "member"
        assert member.invited_by is None
        assert member.joined_at is None

    def test_member_row_owner_role(self):
        """Test OrganizationMemberRow with owner role."""
        member = OrganizationMemberRow(
            id=uuid4(),
            org_id=uuid4(),
            user_id=uuid4(),
            role="owner",
        )

        assert member.role == "owner"
