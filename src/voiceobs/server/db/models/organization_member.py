"""Organization member model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class OrganizationMemberRow:
    """Represents an organization member row in the database."""

    id: UUID
    org_id: UUID
    user_id: UUID
    role: str = "member"
    invited_by: UUID | None = None
    joined_at: datetime | None = None
