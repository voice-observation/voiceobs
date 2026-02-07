"""Organization members routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from voiceobs.server.auth.dependencies import get_current_user
from voiceobs.server.db.models import UserRow
from voiceobs.server.dependencies import get_organization_member_repository
from voiceobs.server.models.response import MemberResponse

router = APIRouter(prefix="/api/v1/orgs/{org_id}/members", tags=["Organization Members"])


@router.get("", response_model=list[MemberResponse])
async def list_members(
    org_id: UUID,
    current_user: UserRow = Depends(get_current_user),
) -> list[MemberResponse]:
    """List organization members.

    Args:
        org_id: The organization's UUID.
        current_user: The authenticated user from the JWT.

    Returns:
        List of organization members with their details.

    Raises:
        HTTPException: 403 if user is not a member.
        HTTPException: 503 if database is not available.
    """
    member_repo = get_organization_member_repository()

    # Check if user is member
    is_member = await member_repo.is_member(org_id=org_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")

    members = await member_repo.list_members(org_id)

    return [
        MemberResponse(
            user_id=str(m["member"].user_id),
            email=m["user_email"],
            name=m["user_name"],
            role=m["member"].role,
            joined_at=m["member"].joined_at.isoformat() if m["member"].joined_at else None,
        )
        for m in members
    ]


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: UUID,
    user_id: UUID,
    current_user: UserRow = Depends(get_current_user),
) -> None:
    """Remove a member from the organization (owner only).

    Args:
        org_id: The organization's UUID.
        user_id: The user ID to remove.
        current_user: The authenticated user from the JWT.

    Raises:
        HTTPException: 400 if trying to remove self as sole owner.
        HTTPException: 403 if user is not a member or not an owner.
        HTTPException: 404 if member not found.
        HTTPException: 503 if database is not available.
    """
    member_repo = get_organization_member_repository()

    # Check if current user is owner
    current_membership = await member_repo.get(org_id=org_id, user_id=current_user.id)
    if not current_membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")

    if current_membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can remove members")

    # Can't remove self if sole owner
    if user_id == current_user.id:
        members = await member_repo.list_members(org_id)
        owner_count = sum(1 for m in members if m["member"].role == "owner")
        if owner_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove yourself as the sole owner. Transfer ownership first.",
            )

    # Remove the member
    removed = await member_repo.remove(org_id=org_id, user_id=user_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
