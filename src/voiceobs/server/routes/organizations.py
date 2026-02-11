"""Organization routes."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from voiceobs.server.auth.dependencies import get_current_user
from voiceobs.server.db.models import UserRow
from voiceobs.server.dependencies import (
    get_organization_member_repository,
    get_organization_repository,
    get_persona_service,
)
from voiceobs.server.models.request import CreateOrgRequest, UpdateOrgRequest
from voiceobs.server.models.response import OrgResponse

router = APIRouter(prefix="/api/v1/orgs", tags=["Organizations"])


@router.get("", response_model=list[OrgResponse])
async def list_orgs(
    current_user: UserRow = Depends(get_current_user),
) -> list[OrgResponse]:
    """List user's organizations.

    Args:
        current_user: The authenticated user from the JWT.

    Returns:
        List of organizations the user is a member of.

    Raises:
        HTTPException: 503 if database is not available.
    """
    org_repo = get_organization_repository()

    memberships = await org_repo.list_for_user(current_user.id)

    return [
        OrgResponse(
            id=str(m["org"].id),
            name=m["org"].name,
            role=m["role"],
            created_at=m["org"].created_at.isoformat() if m["org"].created_at else None,
        )
        for m in memberships
    ]


@router.post("", response_model=OrgResponse, status_code=status.HTTP_201_CREATED)
async def create_org(
    request: CreateOrgRequest,
    current_user: UserRow = Depends(get_current_user),
) -> OrgResponse:
    """Create a new organization.

    Args:
        request: The request containing the organization name.
        current_user: The authenticated user from the JWT.

    Returns:
        The created organization with owner role.

    Raises:
        HTTPException: 503 if database is not available.
    """
    org_repo = get_organization_repository()
    member_repo = get_organization_member_repository()

    org = await org_repo.create(name=request.name, created_by=current_user.id)
    await member_repo.add(org_id=org.id, user_id=current_user.id, role="owner")

    # Seed system personas for the new organization
    persona_service = get_persona_service()
    await persona_service.seed_org_personas(org.id)

    return OrgResponse(
        id=str(org.id),
        name=org.name,
        role="owner",
        created_at=org.created_at.isoformat() if org.created_at else None,
    )


@router.get("/{org_id}", response_model=OrgResponse)
async def get_org(
    org_id: UUID,
    current_user: UserRow = Depends(get_current_user),
) -> OrgResponse:
    """Get organization details.

    Args:
        org_id: The organization's UUID.
        current_user: The authenticated user from the JWT.

    Returns:
        The organization details with user's role.

    Raises:
        HTTPException: 404 if organization not found.
        HTTPException: 403 if user is not a member.
        HTTPException: 503 if database is not available.
    """
    org_repo = get_organization_repository()
    member_repo = get_organization_member_repository()

    org = await org_repo.get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    is_member = await member_repo.is_member(org_id=org_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")

    membership = await member_repo.get(org_id=org_id, user_id=current_user.id)

    return OrgResponse(
        id=str(org.id),
        name=org.name,
        role=membership.role if membership else None,
        created_at=org.created_at.isoformat() if org.created_at else None,
    )


@router.patch("/{org_id}", response_model=OrgResponse)
async def update_org(
    org_id: UUID,
    request: UpdateOrgRequest,
    current_user: UserRow = Depends(get_current_user),
) -> OrgResponse:
    """Update organization.

    Args:
        org_id: The organization's UUID.
        request: The request containing the new organization name.
        current_user: The authenticated user from the JWT.

    Returns:
        The updated organization details.

    Raises:
        HTTPException: 404 if organization not found.
        HTTPException: 403 if user is not a member.
        HTTPException: 503 if database is not available.
    """
    org_repo = get_organization_repository()
    member_repo = get_organization_member_repository()

    is_member = await member_repo.is_member(org_id=org_id, user_id=current_user.id)
    if not is_member:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")

    org = await org_repo.update(org_id, name=request.name)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    membership = await member_repo.get(org_id=org_id, user_id=current_user.id)

    return OrgResponse(
        id=str(org.id),
        name=org.name,
        role=membership.role if membership else None,
        created_at=org.created_at.isoformat() if org.created_at else None,
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_org(
    org_id: UUID,
    current_user: UserRow = Depends(get_current_user),
) -> None:
    """Delete organization (owner only).

    Args:
        org_id: The organization's UUID.
        current_user: The authenticated user from the JWT.

    Raises:
        HTTPException: 404 if organization not found.
        HTTPException: 403 if user is not a member or not an owner.
        HTTPException: 503 if database is not available.
    """
    org_repo = get_organization_repository()
    member_repo = get_organization_member_repository()

    membership = await member_repo.get(org_id=org_id, user_id=current_user.id)
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this organization")

    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete organizations")

    deleted = await org_repo.delete(org_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Organization not found")
