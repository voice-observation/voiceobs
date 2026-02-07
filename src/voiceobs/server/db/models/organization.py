"""Organization model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class OrganizationRow:
    """Represents an organization row in the database."""

    id: UUID
    name: str
    created_by: UUID
    created_at: datetime | None = None
    updated_at: datetime | None = None
