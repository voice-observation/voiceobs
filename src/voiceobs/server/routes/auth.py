"""Authentication routes."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends

from voiceobs.server.auth.dependencies import get_current_user
from voiceobs.server.db.models import UserRow
from voiceobs.server.dependencies import get_organization_repository, get_user_repository
from voiceobs.server.models.request import UserUpdateRequest
from voiceobs.server.models.response import (
    ActiveOrgResponse,
    AuthMeResponse,
    OrgSummary,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

logger = logging.getLogger(__name__)


@router.get(
    "/me",
    response_model=AuthMeResponse,
    summary="Get current user",
    description="Get the currently authenticated user's profile with organizations.",
)
async def get_me(
    current_user: UserRow = Depends(get_current_user),
) -> AuthMeResponse:
    """Get current user profile with organizations.

    Args:
        current_user: The authenticated user from the JWT.

    Returns:
        The user's profile information with organizations.
    """
    logger.debug(f"Fetching profile for user ID: {current_user.id}")
    user_response = UserResponse.from_user_row(current_user)
    logger.debug(f"User profile fetched: {user_response}")

    # Get user's organizations
    org_repo = get_organization_repository()
    orgs_list: list[OrgSummary] = []
    active_org: ActiveOrgResponse | None = None

    if org_repo:
        org_memberships = await org_repo.list_for_user(current_user.id)
        orgs_list = [
            OrgSummary(
                id=str(m["org"].id),
                name=m["org"].name,
                role=m["role"],
            )
            for m in org_memberships
        ]

        # Get active org
        if current_user.last_active_org_id:
            active = await org_repo.get(current_user.last_active_org_id)
            if active:
                active_org = ActiveOrgResponse(id=str(active.id), name=active.name)

    return AuthMeResponse(
        user=user_response,
        active_org=active_org,
        orgs=orgs_list,
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    description="Update the currently authenticated user's profile.",
)
async def update_me(
    request: UserUpdateRequest,
    current_user: UserRow = Depends(get_current_user),
) -> UserResponse:
    """Update current user profile.

    Args:
        request: The update request with optional name and avatar_url.
        current_user: The authenticated user from the JWT.

    Returns:
        The updated user profile.

    Raises:
        RuntimeError: If the user repository is not available or user not found.
    """
    repo = get_user_repository()
    if repo is None:
        # This shouldn't happen since get_current_user checks it
        raise RuntimeError("User repository not available")

    # Parse last_active_org_id if provided
    last_active_org_id = None
    if request.last_active_org_id:
        last_active_org_id = UUID(request.last_active_org_id)

    user = await repo.update(
        user_id=current_user.id,
        name=request.name,
        avatar_url=request.avatar_url,
        last_active_org_id=last_active_org_id,
    )

    if user is None:
        # This shouldn't happen since user was just validated
        raise RuntimeError("User not found after authentication")

    return UserResponse.from_user_row(user)
