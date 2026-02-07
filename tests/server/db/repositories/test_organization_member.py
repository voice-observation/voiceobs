"""Tests for OrganizationMemberRepository."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.organization_member import (
    OrganizationMemberRepository,
)

from .conftest import MockRecord


class TestOrganizationMemberRepository:
    """Tests for the OrganizationMemberRepository class."""

    @pytest.mark.asyncio
    async def test_add_member(self, mock_db):
        """Test adding a member to an organization."""
        repo = OrganizationMemberRepository(mock_db)
        member_id = uuid4()
        org_id = uuid4()
        user_id = uuid4()
        invited_by = uuid4()
        joined_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": member_id,
                "org_id": org_id,
                "user_id": user_id,
                "role": "member",
                "invited_by": invited_by,
                "joined_at": joined_at,
            }
        )

        member = await repo.add(
            org_id=org_id, user_id=user_id, role="member", invited_by=invited_by
        )

        assert member.id == member_id
        assert member.org_id == org_id
        assert member.user_id == user_id
        assert member.role == "member"
        assert member.invited_by == invited_by
        assert member.joined_at == joined_at
        mock_db.fetchrow.assert_called_once()
        assert "INSERT INTO organization_members" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_add_owner(self, mock_db):
        """Test adding an owner to an organization."""
        repo = OrganizationMemberRepository(mock_db)
        member_id = uuid4()
        org_id = uuid4()
        user_id = uuid4()
        joined_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": member_id,
                "org_id": org_id,
                "user_id": user_id,
                "role": "owner",
                "invited_by": None,
                "joined_at": joined_at,
            }
        )

        member = await repo.add(org_id=org_id, user_id=user_id, role="owner")

        assert member.id == member_id
        assert member.role == "owner"
        assert member.invited_by is None
        mock_db.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_membership(self, mock_db):
        """Test getting a specific membership."""
        repo = OrganizationMemberRepository(mock_db)
        member_id = uuid4()
        org_id = uuid4()
        user_id = uuid4()
        joined_at = datetime.now(timezone.utc)

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": member_id,
                "org_id": org_id,
                "user_id": user_id,
                "role": "member",
                "invited_by": None,
                "joined_at": joined_at,
            }
        )

        member = await repo.get(org_id=org_id, user_id=user_id)

        assert member is not None
        assert member.id == member_id
        assert member.org_id == org_id
        assert member.user_id == user_id
        mock_db.fetchrow.assert_called_once()
        assert "SELECT" in mock_db.fetchrow.call_args[0][0]
        assert "organization_members" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_nonexistent_membership(self, mock_db):
        """Test getting a membership that doesn't exist."""
        repo = OrganizationMemberRepository(mock_db)
        mock_db.fetchrow.return_value = None

        member = await repo.get(org_id=uuid4(), user_id=uuid4())

        assert member is None

    @pytest.mark.asyncio
    async def test_is_member(self, mock_db):
        """Test checking if a user is a member of an organization."""
        repo = OrganizationMemberRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord({"exists": True})

        result = await repo.is_member(org_id=org_id, user_id=user_id)

        assert result is True
        mock_db.fetchrow.assert_called_once()
        assert "EXISTS" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_is_not_member(self, mock_db):
        """Test checking if a user is not a member of an organization."""
        repo = OrganizationMemberRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord({"exists": False})

        result = await repo.is_member(org_id=org_id, user_id=user_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_list_members(self, mock_db):
        """Test listing all members of an organization with user info."""
        repo = OrganizationMemberRepository(mock_db)
        org_id = uuid4()
        member1_id = uuid4()
        member2_id = uuid4()
        user1_id = uuid4()
        user2_id = uuid4()
        joined_at = datetime.now(timezone.utc)

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": member1_id,
                    "org_id": org_id,
                    "user_id": user1_id,
                    "role": "owner",
                    "invited_by": None,
                    "joined_at": joined_at,
                    "user_email": "owner@example.com",
                    "user_name": "Owner User",
                }
            ),
            MockRecord(
                {
                    "id": member2_id,
                    "org_id": org_id,
                    "user_id": user2_id,
                    "role": "member",
                    "invited_by": user1_id,
                    "joined_at": joined_at,
                    "user_email": "member@example.com",
                    "user_name": "Member User",
                }
            ),
        ]

        members = await repo.list_members(org_id)

        assert len(members) == 2
        assert members[0]["member"].id == member1_id
        assert members[0]["member"].role == "owner"
        assert members[0]["user_email"] == "owner@example.com"
        assert members[0]["user_name"] == "Owner User"
        assert members[1]["member"].id == member2_id
        assert members[1]["member"].role == "member"
        assert members[1]["user_email"] == "member@example.com"
        mock_db.fetch.assert_called_once()
        assert "JOIN users" in mock_db.fetch.call_args[0][0]

    @pytest.mark.asyncio
    async def test_remove_member(self, mock_db):
        """Test removing a member from an organization."""
        repo = OrganizationMemberRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.execute.return_value = "DELETE 1"

        result = await repo.remove(org_id=org_id, user_id=user_id)

        assert result is True
        mock_db.execute.assert_called_once()
        assert "DELETE FROM organization_members" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_remove_nonexistent_member(self, mock_db):
        """Test removing a member that doesn't exist."""
        repo = OrganizationMemberRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.execute.return_value = "DELETE 0"

        result = await repo.remove(org_id=org_id, user_id=user_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_count_user_memberships(self, mock_db):
        """Test counting a user's organization memberships."""
        repo = OrganizationMemberRepository(mock_db)
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord({"count": 3})

        count = await repo.count_user_memberships(user_id=user_id)

        assert count == 3
        mock_db.fetchrow.assert_called_once()
        assert "COUNT" in mock_db.fetchrow.call_args[0][0]
        assert "organization_members" in mock_db.fetchrow.call_args[0][0]
