"""Organization request models."""

from pydantic import BaseModel, Field


class CreateOrgRequest(BaseModel):
    """Request to create an organization."""

    name: str = Field(..., min_length=1, max_length=255)


class UpdateOrgRequest(BaseModel):
    """Request to update an organization."""

    name: str = Field(..., min_length=1, max_length=255)


class SendInviteRequest(BaseModel):
    """Request to send an invite."""

    email: str = Field(..., description="Email address to invite")
