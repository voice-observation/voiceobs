"""Authentication context for organization-scoped requests."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Header, HTTPException, status

from voiceobs.server.auth.dependencies import get_current_user
from voiceobs.server.db.models import OrganizationRow, UserRow
from voiceobs.server.dependencies import (
    get_organization_member_repository,
    get_organization_repository,
    get_user_repository,
)


@dataclass
class AuthContext:
    """Authentication context containing user and active organization."""

    user: UserRow
    org: OrganizationRow


async def get_auth_context(
    x_organization_id: str | None = Header(None, alias="X-Organization-Id"),
    authorization: str | None = Header(None, alias="Authorization"),
) -> AuthContext:
    """Get authentication context with user and active organization.

    Resolves the active organization from:
    1. X-Organization-Id header (if provided)
    2. User's last_active_org_id (fallback)

    Args:
        x_organization_id: Organization ID from header.
        authorization: Authorization header for JWT.

    Returns:
        AuthContext with user and organization.

    Raises:
        HTTPException: If no org selected, org not found, or user not a member.
    """
    # Get current user
    user = await get_current_user(authorization)

    # Determine which org to use
    org_id: UUID | None = None

    if x_organization_id:
        try:
            org_id = UUID(x_organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization ID format",
            )
    elif user.last_active_org_id:
        org_id = user.last_active_org_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No organization selected",
        )

    # Get organization
    org_repo = get_organization_repository()
    org = await org_repo.get(org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Verify membership
    member_repo = get_organization_member_repository()
    is_member = await member_repo.is_member(org_id=org_id, user_id=user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    # Update last_active_org_id if different
    if user.last_active_org_id != org_id:
        user_repo = get_user_repository()
        if user_repo:
            await user_repo.update(user.id, last_active_org_id=org_id)

    return AuthContext(user=user, org=org)


async def require_org_membership(
    org_id: UUID,
    authorization: str | None = Header(None, alias="Authorization"),
) -> AuthContext:
    """Require that the authenticated user is a member of the specified organization.

    This dependency is used for org-scoped endpoints where the org_id comes from
    the URL path (e.g., /api/v1/orgs/{org_id}/personas).

    Args:
        org_id: Organization ID from the URL path.
        authorization: Authorization header for JWT.

    Returns:
        AuthContext with user and organization.

    Raises:
        HTTPException: If user is not authenticated, org not found, or user not a member.
    """
    # Get current user
    user = await get_current_user(authorization)

    # Get organization
    org_repo = get_organization_repository()
    org = await org_repo.get(org_id)
    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Verify membership
    member_repo = get_organization_member_repository()
    is_member = await member_repo.is_member(org_id=org_id, user_id=user.id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization",
        )

    # Update last_active_org_id if different (convenience for user)
    if user.last_active_org_id != org_id:
        user_repo = get_user_repository()
        if user_repo:
            await user_repo.update(user.id, last_active_org_id=org_id)

    return AuthContext(user=user, org=org)
