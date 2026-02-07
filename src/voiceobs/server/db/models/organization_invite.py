"""Organization invite model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class OrganizationInviteRow:
    """Represents an organization invite row in the database."""

    id: UUID
    org_id: UUID
    email: str
    token: str
    invited_by: UUID
    status: str = "pending"  # pending, accepted, expired, revoked
    created_at: datetime | None = None
    expires_at: datetime | None = None
