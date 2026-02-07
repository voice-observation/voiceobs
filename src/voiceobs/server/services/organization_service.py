"""Organization service for business logic."""

from __future__ import annotations

from voiceobs.server.db.models import OrganizationRow, UserRow
from voiceobs.server.db.repositories.organization import OrganizationRepository
from voiceobs.server.db.repositories.organization_member import OrganizationMemberRepository
from voiceobs.server.db.repositories.user import UserRepository


class OrganizationService:
    """Service for organization-related business logic."""

    def __init__(
        self,
        org_repo: OrganizationRepository,
        member_repo: OrganizationMemberRepository,
        user_repo: UserRepository,
    ) -> None:
        """Initialize the organization service.

        Args:
            org_repo: Organization repository.
            member_repo: Organization member repository.
            user_repo: User repository.
        """
        self._org_repo = org_repo
        self._member_repo = member_repo
        self._user_repo = user_repo

    async def ensure_user_has_org(self, user: UserRow) -> OrganizationRow | None:
        """Ensure user has at least one organization.

        If user has no organization memberships, creates a personal organization
        and adds them as owner.

        Args:
            user: The user to check.

        Returns:
            The created organization if one was created, None otherwise.
        """
        # Check if user already has orgs
        membership_count = await self._member_repo.count_user_memberships(user.id)
        if membership_count > 0:
            return None

        # Create personal organization
        name = user.name or user.email.split("@")[0]
        org_name = f"{name}'s Organization"

        org = await self._org_repo.create(name=org_name, created_by=user.id)

        # Add user as owner
        await self._member_repo.add(org_id=org.id, user_id=user.id, role="owner")

        # Set as last active org
        await self._user_repo.update(user.id, last_active_org_id=org.id)

        return org
