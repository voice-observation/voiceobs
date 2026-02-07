"""User repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import UserRow


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the user repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def upsert(
        self,
        user_id: UUID,
        email: str,
        name: str | None = None,
        avatar_url: str | None = None,
        auth_provider: str | None = None,
    ) -> UserRow:
        """Create or update a user.

        On first login, creates the user. On subsequent logins,
        updates email/name/avatar if changed in Supabase.

        Args:
            user_id: The user's UUID (from Supabase).
            email: User's email address.
            name: User's display name.
            avatar_url: URL to user's avatar image.
            auth_provider: Authentication provider ('email', 'google', 'github').

        Returns:
            The created or updated user row.

        Raises:
            RuntimeError: If the upsert operation fails.
        """
        await self._db.execute(
            """
            INSERT INTO users (id, email, name, avatar_url, auth_provider)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                name = COALESCE(EXCLUDED.name, users.name),
                avatar_url = COALESCE(EXCLUDED.avatar_url, users.avatar_url),
                auth_provider = COALESCE(EXCLUDED.auth_provider, users.auth_provider),
                updated_at = NOW()
            """,
            user_id,
            email,
            name,
            avatar_url,
            auth_provider,
        )

        user = await self.get(user_id)
        if user is None:
            raise RuntimeError("Failed to upsert user")
        return user

    async def get(self, user_id: UUID) -> UserRow | None:
        """Get user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The user row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, email, name, avatar_url, auth_provider,
                   is_active, last_active_org_id, created_at, updated_at
            FROM users WHERE id = $1
            """,
            user_id,
        )

        if row is None:
            return None

        return self._row_to_user(row)

    async def update(
        self,
        user_id: UUID,
        name: str | None = None,
        avatar_url: str | None = None,
        is_active: bool | None = None,
        last_active_org_id: UUID | None = None,
    ) -> UserRow | None:
        """Update user profile fields.

        Args:
            user_id: The user's UUID.
            name: New display name (optional).
            avatar_url: New avatar URL (optional).
            is_active: New active status (optional).
            last_active_org_id: New last active organization ID (optional).

        Returns:
            The updated user row, or None if not found.
        """
        updates = []
        params: list[Any] = []
        param_idx = 1

        if name is not None:
            updates.append(f"name = ${param_idx}")
            params.append(name)
            param_idx += 1

        if avatar_url is not None:
            updates.append(f"avatar_url = ${param_idx}")
            params.append(avatar_url)
            param_idx += 1

        if is_active is not None:
            updates.append(f"is_active = ${param_idx}")
            params.append(is_active)
            param_idx += 1

        if last_active_org_id is not None:
            updates.append(f"last_active_org_id = ${param_idx}")
            params.append(last_active_org_id)
            param_idx += 1

        if not updates:
            return await self.get(user_id)

        updates.append("updated_at = NOW()")
        params.append(user_id)

        await self._db.execute(
            f"""
            UPDATE users SET {", ".join(updates)}
            WHERE id = ${param_idx}
            """,
            *params,
        )

        return await self.get(user_id)

    def _row_to_user(self, row: Any) -> UserRow:
        """Convert database row to UserRow.

        Args:
            row: Database row from asyncpg.

        Returns:
            UserRow instance.
        """
        return UserRow(
            id=row["id"],
            email=row["email"],
            name=row["name"],
            avatar_url=row["avatar_url"],
            auth_provider=row["auth_provider"],
            is_active=row["is_active"],
            last_active_org_id=row["last_active_org_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
