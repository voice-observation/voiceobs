"""Organization response models."""

from pydantic import BaseModel


class OrgResponse(BaseModel):
    """Organization response."""

    id: str
    name: str
    role: str | None = None
    created_at: str | None = None


class InviteResponse(BaseModel):
    """Invite response."""

    id: str
    email: str
    status: str
    created_at: str | None = None
    expires_at: str | None = None


class PublicInviteResponse(BaseModel):
    """Public invite details (for accepting)."""

    org_name: str
    email: str
    status: str
    invited_by_name: str | None = None


class AcceptInviteResponse(BaseModel):
    """Response after accepting an invite."""

    org_id: str
    org_name: str
    role: str


class MemberResponse(BaseModel):
    """Organization member response."""

    user_id: str
    email: str
    name: str | None = None
    role: str
    joined_at: str | None = None
