"""Auth response models."""

from pydantic import BaseModel

from voiceobs.server.db.models import UserRow


class UserResponse(BaseModel):
    """User profile response."""

    id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None
    auth_provider: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_user_row(cls, user: UserRow) -> "UserResponse":
        """Convert UserRow to UserResponse.

        Args:
            user: The user row from the database.

        Returns:
            UserResponse model with formatted fields.
        """
        return cls(
            id=str(user.id),
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            auth_provider=user.auth_provider,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
            updated_at=user.updated_at.isoformat() if user.updated_at else None,
        )


class OrgSummary(BaseModel):
    """Organization summary for user's org list."""

    id: str
    name: str
    role: str


class ActiveOrgResponse(BaseModel):
    """Active organization response."""

    id: str
    name: str


class AuthMeResponse(BaseModel):
    """Response for /auth/me endpoint."""

    user: UserResponse
    active_org: ActiveOrgResponse | None = None
    orgs: list[OrgSummary] = []
