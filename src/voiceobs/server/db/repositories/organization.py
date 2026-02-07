"""Organization repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import OrganizationRow


class OrganizationRepository:
    """Repository for organization operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the organization repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(self, name: str, created_by: UUID) -> OrganizationRow:
        """Create a new organization.

        Args:
            name: Organization name.
            created_by: UUID of the user creating the organization.

        Returns:
            The created organization row.
        """
        row = await self._db.fetchrow(
            """
            INSERT INTO organizations (name, created_by)
            VALUES ($1, $2)
            RETURNING id, name, created_by, created_at, updated_at
            """,
            name,
            created_by,
        )
        return self._row_to_org(row)

    async def get(self, org_id: UUID) -> OrganizationRow | None:
        """Get organization by ID.

        Args:
            org_id: The organization's UUID.

        Returns:
            The organization row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, created_by, created_at, updated_at
            FROM organizations WHERE id = $1
            """,
            org_id,
        )

        if row is None:
            return None

        return self._row_to_org(row)

    async def update(self, org_id: UUID, name: str | None = None) -> OrganizationRow | None:
        """Update organization fields.

        Args:
            org_id: The organization's UUID.
            name: New organization name (optional).

        Returns:
            The updated organization row, or None if not found.
        """
        if name is None:
            return await self.get(org_id)

        await self._db.execute(
            """
            UPDATE organizations SET name = $1, updated_at = NOW()
            WHERE id = $2
            """,
            name,
            org_id,
        )

        return await self.get(org_id)

    async def delete(self, org_id: UUID) -> bool:
        """Delete an organization.

        Args:
            org_id: The organization's UUID.

        Returns:
            True if deleted, False otherwise.
        """
        result = await self._db.execute(
            "DELETE FROM organizations WHERE id = $1",
            org_id,
        )
        return result == "DELETE 1"

    async def list_for_user(self, user_id: UUID) -> list[dict[str, Any]]:
        """List all organizations a user is a member of.

        Args:
            user_id: The user's UUID.

        Returns:
            List of dicts with 'org' (OrganizationRow) and 'role' (str).
        """
        rows = await self._db.fetch(
            """
            SELECT o.id, o.name, o.created_by, o.created_at, o.updated_at, m.role
            FROM organizations o
            JOIN organization_members m ON o.id = m.org_id
            WHERE m.user_id = $1
            ORDER BY o.created_at ASC
            """,
            user_id,
        )

        return [{"org": self._row_to_org(row), "role": row["role"]} for row in rows]

    def _row_to_org(self, row: Any) -> OrganizationRow:
        """Convert database row to OrganizationRow.

        Args:
            row: Database row from asyncpg.

        Returns:
            OrganizationRow instance.
        """
        return OrganizationRow(
            id=row["id"],
            name=row["name"],
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
