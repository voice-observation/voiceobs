"""User model for database operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class UserRow:
    """Represents a user row in the database."""

    id: UUID  # Supabase user ID
    email: str
    name: str | None = None
    avatar_url: str | None = None
    auth_provider: str | None = None  # 'email', 'google', 'github'
    is_active: bool = True
    last_active_org_id: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
