"""Authentication context for organization-scoped requests."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Header, HTTPException, status

from voiceobs.server.auth.dependencies import get_current_user
from voiceobs.server.config.testing import get_test_settings
from voiceobs.server.db.models import OrganizationRow, UserRow
from voiceobs.server.dependencies import (
    get_organization_member_repository,
    get_organization_repository,
    get_user_repository,
)


@dataclass
class TestBypass:
    """Parsed test bypass directives from X-Test-Bypass header.

    Each field corresponds to a bypassable operation.
    None means no bypass for that operation.
    """

    verification: str | None = None  # "verified" or "failed"


_VALID_VERIFICATION_OUTCOMES = {"verified", "failed"}


def parse_test_bypass(header: str | None) -> TestBypass | None:
    """Parse the X-Test-Bypass header into a TestBypass object.

    Args:
        header: Raw header value, e.g., "verification:verified"

    Returns:
        TestBypass with parsed directives, or None if header is absent/empty.

    Raises:
        ValueError: If the header format is invalid.
    """
    if not header or not header.strip():
        return None

    bypass = TestBypass()
    directives = [d.strip() for d in header.split(",")]

    for directive in directives:
        if ":" not in directive:
            raise ValueError(
                f"Invalid bypass directive format: '{directive}'. Expected 'type:value'."
            )

        dtype, value = directive.split(":", 1)
        dtype = dtype.strip()
        value = value.strip()

        if dtype == "verification":
            if value not in _VALID_VERIFICATION_OUTCOMES:
                raise ValueError(
                    f"Invalid verification outcome: '{value}'. "
                    f"Must be one of: {_VALID_VERIFICATION_OUTCOMES}"
                )
            bypass.verification = value
        else:
            raise ValueError(f"Unknown bypass directive: '{dtype}'")

    return bypass


@dataclass
class AuthContext:
    """Authentication context containing user and active organization."""

    user: UserRow
    org: OrganizationRow
    is_test_account: bool = False
    test_bypass: TestBypass | None = None


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
    x_test_bypass: str | None = Header(None, alias="X-Test-Bypass"),
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

    # Test account detection
    is_test_account = False
    test_bypass = None
    test_settings = get_test_settings()
    if test_settings.test_user_email and user.email == test_settings.test_user_email:
        is_test_account = True
        if x_test_bypass:
            test_bypass = parse_test_bypass(x_test_bypass)

    return AuthContext(user=user, org=org, is_test_account=is_test_account, test_bypass=test_bypass)
