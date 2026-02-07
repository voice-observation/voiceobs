"""Organization member repository for database operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import OrganizationMemberRow


class OrganizationMemberRepository:
    """Repository for organization member operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the repository with a database connection.

        Args:
            db: The database connection to use for operations.
        """
        self._db = db

    async def add(
        self,
        org_id: UUID,
        user_id: UUID,
        role: str = "member",
        invited_by: UUID | None = None,
    ) -> OrganizationMemberRow:
        """Add a member to an organization.

        Args:
            org_id: The organization ID.
            user_id: The user ID to add as a member.
            role: The member's role (default: "member").
            invited_by: The user ID who invited this member.

        Returns:
            The created organization member row.
        """
        row = await self._db.fetchrow(
            """
            INSERT INTO organization_members (org_id, user_id, role, invited_by)
            VALUES ($1, $2, $3, $4)
            RETURNING id, org_id, user_id, role, invited_by, joined_at
            """,
            org_id,
            user_id,
            role,
            invited_by,
        )
        return self._row_to_member(row)

    async def get(self, org_id: UUID, user_id: UUID) -> OrganizationMemberRow | None:
        """Get a specific membership.

        Args:
            org_id: The organization ID.
            user_id: The user ID.

        Returns:
            The membership if found, None otherwise.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, org_id, user_id, role, invited_by, joined_at
            FROM organization_members WHERE org_id = $1 AND user_id = $2
            """,
            org_id,
            user_id,
        )
        return self._row_to_member(row) if row else None

    async def is_member(self, org_id: UUID, user_id: UUID) -> bool:
        """Check if user is member of organization.

        Args:
            org_id: The organization ID.
            user_id: The user ID.

        Returns:
            True if user is a member, False otherwise.
        """
        row = await self._db.fetchrow(
            """
            SELECT EXISTS(
                SELECT 1 FROM organization_members WHERE org_id = $1 AND user_id = $2
            ) as exists
            """,
            org_id,
            user_id,
        )
        return row["exists"]

    async def list_members(self, org_id: UUID) -> list[dict[str, Any]]:
        """List all members with user info.

        Args:
            org_id: The organization ID.

        Returns:
            List of dictionaries containing member and user info.
        """
        rows = await self._db.fetch(
            """
            SELECT m.id, m.org_id, m.user_id, m.role, m.invited_by, m.joined_at,
                   u.email as user_email, u.name as user_name
            FROM organization_members m
            JOIN users u ON m.user_id = u.id
            WHERE m.org_id = $1
            ORDER BY m.joined_at ASC
            """,
            org_id,
        )
        return [
            {
                "member": self._row_to_member(row),
                "user_email": row["user_email"],
                "user_name": row["user_name"],
            }
            for row in rows
        ]

    async def remove(self, org_id: UUID, user_id: UUID) -> bool:
        """Remove member from organization.

        Args:
            org_id: The organization ID.
            user_id: The user ID to remove.

        Returns:
            True if member was removed, False if not found.
        """
        result = await self._db.execute(
            "DELETE FROM organization_members WHERE org_id = $1 AND user_id = $2",
            org_id,
            user_id,
        )
        return result == "DELETE 1"

    async def count_user_memberships(self, user_id: UUID) -> int:
        """Count user's organization memberships.

        Args:
            user_id: The user ID.

        Returns:
            The number of organizations the user is a member of.
        """
        row = await self._db.fetchrow(
            "SELECT COUNT(*) as count FROM organization_members WHERE user_id = $1",
            user_id,
        )
        return row["count"]

    def _row_to_member(self, row: Any) -> OrganizationMemberRow:
        """Convert a database row to an OrganizationMemberRow.

        Args:
            row: The database row.

        Returns:
            The OrganizationMemberRow instance.
        """
        return OrganizationMemberRow(
            id=row["id"],
            org_id=row["org_id"],
            user_id=row["user_id"],
            role=row["role"],
            invited_by=row["invited_by"],
            joined_at=row["joined_at"],
        )
