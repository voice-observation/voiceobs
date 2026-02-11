"""Tests for OrganizationService."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from voiceobs.server.db.models import OrganizationMemberRow, OrganizationRow, UserRow
from voiceobs.server.services.organization_service import OrganizationService


class TestOrganizationService:
    """Tests for OrganizationService."""

    @pytest.fixture
    def mock_org_repo(self):
        """Create a mock organization repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_member_repo(self):
        """Create a mock organization member repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return AsyncMock()

    @pytest.fixture
    def mock_persona_service(self):
        """Create a mock persona service."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_org_repo, mock_member_repo, mock_user_repo, mock_persona_service):
        """Create an OrganizationService instance with mocked dependencies."""
        return OrganizationService(
            org_repo=mock_org_repo,
            member_repo=mock_member_repo,
            user_repo=mock_user_repo,
            persona_service=mock_persona_service,
        )

    @pytest.mark.asyncio
    async def test_ensure_user_has_org_creates_new(
        self, service, mock_org_repo, mock_member_repo, mock_user_repo
    ):
        """Test that ensure_user_has_org creates org for new user."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", name="Test User")

        mock_member_repo.count_user_memberships = AsyncMock(return_value=0)
        mock_org_repo.create = AsyncMock(
            return_value=OrganizationRow(
                id=org_id, name="Test User's Organization", created_by=user_id
            )
        )
        mock_member_repo.add = AsyncMock(
            return_value=OrganizationMemberRow(
                id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
            )
        )
        mock_user_repo.update = AsyncMock()

        org = await service.ensure_user_has_org(user)

        assert org is not None
        assert org.id == org_id
        mock_org_repo.create.assert_called_once()
        mock_member_repo.add.assert_called_once_with(org_id=org_id, user_id=user_id, role="owner")
        mock_user_repo.update.assert_called_once_with(user_id, last_active_org_id=org_id)

    @pytest.mark.asyncio
    async def test_ensure_user_has_org_existing_member(self, service, mock_member_repo):
        """Test that ensure_user_has_org returns None if user already has orgs."""
        user_id = uuid4()
        user = UserRow(id=user_id, email="test@example.com")

        mock_member_repo.count_user_memberships = AsyncMock(return_value=1)

        org = await service.ensure_user_has_org(user)

        assert org is None
        mock_member_repo.count_user_memberships.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_ensure_user_has_org_uses_name(
        self, service, mock_org_repo, mock_member_repo, mock_user_repo
    ):
        """Test that org name uses user's name."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", name="Alice Smith")

        mock_member_repo.count_user_memberships = AsyncMock(return_value=0)
        mock_org_repo.create = AsyncMock(
            return_value=OrganizationRow(
                id=org_id, name="Alice Smith's Organization", created_by=user_id
            )
        )
        mock_member_repo.add = AsyncMock(
            return_value=OrganizationMemberRow(
                id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
            )
        )
        mock_user_repo.update = AsyncMock()

        await service.ensure_user_has_org(user)

        call_args = mock_org_repo.create.call_args
        assert "Alice Smith's Organization" in call_args[1]["name"]

    @pytest.mark.asyncio
    async def test_ensure_user_has_org_uses_email_fallback(
        self, service, mock_org_repo, mock_member_repo, mock_user_repo
    ):
        """Test that org name falls back to email if no name."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", name=None)

        mock_member_repo.count_user_memberships = AsyncMock(return_value=0)
        mock_org_repo.create = AsyncMock(
            return_value=OrganizationRow(id=org_id, name="test's Organization", created_by=user_id)
        )
        mock_member_repo.add = AsyncMock(
            return_value=OrganizationMemberRow(
                id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
            )
        )
        mock_user_repo.update = AsyncMock()

        await service.ensure_user_has_org(user)

        call_args = mock_org_repo.create.call_args
        assert "test's Organization" in call_args[1]["name"]

    @pytest.mark.asyncio
    async def test_ensure_user_has_org_seeds_personas(
        self, service, mock_org_repo, mock_member_repo, mock_user_repo, mock_persona_service
    ):
        """When a new org is auto-created, personas are seeded."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", name="Test User")

        mock_member_repo.count_user_memberships = AsyncMock(return_value=0)
        mock_org_repo.create = AsyncMock(
            return_value=OrganizationRow(
                id=org_id, name="Test User's Organization", created_by=user_id
            )
        )
        mock_member_repo.add = AsyncMock(
            return_value=OrganizationMemberRow(
                id=uuid4(), org_id=org_id, user_id=user_id, role="owner"
            )
        )
        mock_user_repo.update = AsyncMock()

        await service.ensure_user_has_org(user)

        mock_persona_service.seed_org_personas.assert_called_once_with(org_id)

    @pytest.mark.asyncio
    async def test_ensure_user_has_org_skips_seeding_if_user_has_org(
        self, service, mock_member_repo, mock_persona_service
    ):
        """When user already has orgs, no seeding happens."""
        user_id = uuid4()
        user = UserRow(id=user_id, email="test@example.com")

        mock_member_repo.count_user_memberships = AsyncMock(return_value=1)

        result = await service.ensure_user_has_org(user)

        assert result is None
        mock_persona_service.seed_org_personas.assert_not_called()
