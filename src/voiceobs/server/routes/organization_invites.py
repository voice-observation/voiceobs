"""Organization invites routes."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from voiceobs.server.auth.dependencies import get_current_user
from voiceobs.server.db.models import UserRow
from voiceobs.server.dependencies import (
    get_organization_invite_repository,
    get_organization_member_repository,
    get_organization_repository,
)
from voiceobs.server.models.request import SendInviteRequest
from voiceobs.server.models.response import (
    AcceptInviteResponse,
    InviteResponse,
    PublicInviteResponse,
)

router = APIRouter(tags=["Organization Invites"])


# Org-scoped routes: /api/v1/orgs/{org_id}/invites
@router.get("/api/v1/orgs/{org_id}/invites", response_model=list[InviteResponse])
async def list_invites(
    org_id: UUID,
    current_user: UserRow = Depends(get_current_user),
) -> list[InviteResponse]:
    """List pending invites for organization.

    Args:
        org_id: The organization's UUID.
        current_user: The authenticated user from the JWT.

    Returns:
        List of pending invites for the organization.

    Raises:
        HTTPException: 403 if user is not a member.
        HTTPException: 503 if database is not available.
    """
    member_repo = get_organization_member_repository()
    invite_repo = get_organization_invite_repository()

    is_member = await member_repo.is_member(org_id=org_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    invites = await invite_repo.list_pending_for_org(org_id)

    return [
        InviteResponse(
            id=str(inv.id),
            email=inv.email,
            status=inv.status,
            created_at=inv.created_at.isoformat() if inv.created_at else None,
            expires_at=inv.expires_at.isoformat() if inv.expires_at else None,
        )
        for inv in invites
    ]


@router.post(
    "/api/v1/orgs/{org_id}/invites",
    response_model=InviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_invite(
    org_id: UUID,
    request: SendInviteRequest,
    current_user: UserRow = Depends(get_current_user),
) -> InviteResponse:
    """Send an invite (owner only).

    Args:
        org_id: The organization's UUID.
        request: The invite request containing the email.
        current_user: The authenticated user from the JWT.

    Returns:
        The created invite.

    Raises:
        HTTPException: 403 if user is not a member or not an owner.
        HTTPException: 503 if database is not available.
    """
    member_repo = get_organization_member_repository()
    invite_repo = get_organization_invite_repository()

    membership = await member_repo.get(org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can send invites")

    # Default expiration: 7 days from now
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invite = await invite_repo.create(
        org_id=org_id,
        email=request.email,
        invited_by=current_user.id,
        expires_at=expires_at,
    )

    return InviteResponse(
        id=str(invite.id),
        email=invite.email,
        status=invite.status,
        created_at=invite.created_at.isoformat() if invite.created_at else None,
        expires_at=invite.expires_at.isoformat() if invite.expires_at else None,
    )


@router.delete(
    "/api/v1/orgs/{org_id}/invites/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_invite(
    org_id: UUID,
    invite_id: UUID,
    current_user: UserRow = Depends(get_current_user),
) -> None:
    """Revoke an invite (owner only).

    Args:
        org_id: The organization's UUID.
        invite_id: The invite's UUID.
        current_user: The authenticated user from the JWT.

    Raises:
        HTTPException: 403 if user is not a member or not an owner.
        HTTPException: 404 if invite not found.
        HTTPException: 503 if database is not available.
    """
    member_repo = get_organization_member_repository()
    invite_repo = get_organization_invite_repository()

    membership = await member_repo.get(org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can revoke invites")

    invite = await invite_repo.get_by_id(invite_id)
    if not invite or invite.org_id != org_id:
        raise HTTPException(status_code=404, detail="Invite not found")

    await invite_repo.update_status(invite_id, "revoked")


# Public routes (no auth required for viewing, auth required for accepting)
@router.get("/api/v1/invites/{token}", response_model=PublicInviteResponse)
async def get_invite_by_token(token: str) -> PublicInviteResponse:
    """Get invite details by token (public).

    Args:
        token: The invite token.

    Returns:
        Public invite details including organization name.

    Raises:
        HTTPException: 400 if invite is not pending.
        HTTPException: 404 if invite not found or expired.
        HTTPException: 503 if database is not available.
    """
    invite_repo = get_organization_invite_repository()
    org_repo = get_organization_repository()

    invite = await invite_repo.get_by_token(token)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or expired")

    if invite.status != "pending":
        raise HTTPException(status_code=400, detail=f"Invite is {invite.status}")

    org = await org_repo.get(invite.org_id)
    org_name = org.name if org else "Unknown Organization"

    return PublicInviteResponse(
        org_name=org_name,
        email=invite.email,
        status=invite.status,
        invited_by_name=None,  # Could fetch user name if needed
    )


@router.post("/api/v1/invites/{token}/accept", response_model=AcceptInviteResponse)
async def accept_invite(
    token: str,
    current_user: UserRow = Depends(get_current_user),
) -> AcceptInviteResponse:
    """Accept an invite and join the organization.

    Args:
        token: The invite token.
        current_user: The authenticated user from the JWT.

    Returns:
        Details of the organization joined.

    Raises:
        HTTPException: 400 if invite is not pending or already a member.
        HTTPException: 403 if email doesn't match.
        HTTPException: 404 if invite not found or expired.
        HTTPException: 503 if database is not available.
    """
    invite_repo = get_organization_invite_repository()
    org_repo = get_organization_repository()
    member_repo = get_organization_member_repository()

    invite = await invite_repo.get_by_token(token)
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or expired")

    if invite.status != "pending":
        raise HTTPException(status_code=400, detail=f"Invite is {invite.status}")

    # Verify email matches (optional, could allow any authenticated user)
    if invite.email.lower() != current_user.email.lower():
        raise HTTPException(status_code=403, detail="This invite is for a different email address")

    # Check if already a member
    is_member = await member_repo.is_member(org_id=invite.org_id, user_id=current_user.id)
    if is_member:
        raise HTTPException(status_code=400, detail="You are already a member of this organization")

    # Add as member
    await member_repo.add(org_id=invite.org_id, user_id=current_user.id, role="member")

    # Mark invite as accepted
    await invite_repo.update_status(invite.id, "accepted")

    # Get org details
    org = await org_repo.get(invite.org_id)
    org_name = org.name if org else "Unknown"

    return AcceptInviteResponse(
        org_id=str(invite.org_id),
        org_name=org_name,
        role="member",
    )
