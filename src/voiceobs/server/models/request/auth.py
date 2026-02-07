"""Auth request models."""

from pydantic import BaseModel, Field


class UserUpdateRequest(BaseModel):
    """Request to update user profile."""

    name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = Field(None, max_length=2048)
    last_active_org_id: str | None = Field(None, description="ID of the last active organization")
