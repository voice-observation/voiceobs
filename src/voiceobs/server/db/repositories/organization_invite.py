"""Organization invite repository for database operations."""

from __future__ import annotations

import secrets
from datetime import datetime
from typing import Any
from uuid import UUID

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import OrganizationInviteRow


class OrganizationInviteRepository:
    """Repository for organization invite operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the repository with a database connection.

        Args:
            db: The database connection to use for operations.
        """
        self._db = db

    async def create(
        self,
        org_id: UUID,
        email: str,
        invited_by: UUID,
        expires_at: datetime,
    ) -> OrganizationInviteRow:
        """Create an organization invite with a generated token.

        Args:
            org_id: The organization ID.
            email: The email address to invite.
            invited_by: The user ID who is creating the invite.
            expires_at: When the invite expires.

        Returns:
            The created organization invite row.
        """
        token = secrets.token_hex(32)
        row = await self._db.fetchrow(
            """
            INSERT INTO organization_invites (org_id, email, token, invited_by, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, org_id, email, token, invited_by, status, created_at, expires_at
            """,
            org_id,
            email,
            token,
            invited_by,
            expires_at,
        )
        return self._row_to_invite(row)

    async def get_by_token(self, token: str) -> OrganizationInviteRow | None:
        """Get an invite by its token.

        Args:
            token: The invite token.

        Returns:
            The invite if found, None otherwise.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, org_id, email, token, invited_by, status, created_at, expires_at
            FROM organization_invites WHERE token = $1
            """,
            token,
        )
        return self._row_to_invite(row) if row else None

    async def get_by_id(self, invite_id: UUID) -> OrganizationInviteRow | None:
        """Get an invite by its ID.

        Args:
            invite_id: The invite ID.

        Returns:
            The invite if found, None otherwise.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, org_id, email, token, invited_by, status, created_at, expires_at
            FROM organization_invites WHERE id = $1
            """,
            invite_id,
        )
        return self._row_to_invite(row) if row else None

    async def get_pending_for_email(self, org_id: UUID, email: str) -> OrganizationInviteRow | None:
        """Get a pending invite for a specific email in an organization.

        Args:
            org_id: The organization ID.
            email: The email address.

        Returns:
            The pending invite if found, None otherwise.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, org_id, email, token, invited_by, status, created_at, expires_at
            FROM organization_invites
            WHERE org_id = $1 AND email = $2 AND status = 'pending'
            """,
            org_id,
            email,
        )
        return self._row_to_invite(row) if row else None

    async def update_status(self, invite_id: UUID, status: str) -> OrganizationInviteRow | None:
        """Update an invite's status.

        Args:
            invite_id: The invite ID.
            status: The new status (pending, accepted, expired, revoked).

        Returns:
            The updated invite if found, None otherwise.
        """
        row = await self._db.fetchrow(
            """
            UPDATE organization_invites
            SET status = $1
            WHERE id = $2
            RETURNING id, org_id, email, token, invited_by, status, created_at, expires_at
            """,
            status,
            invite_id,
        )
        return self._row_to_invite(row) if row else None

    async def list_pending_for_org(self, org_id: UUID) -> list[OrganizationInviteRow]:
        """List all pending invites for an organization.

        Args:
            org_id: The organization ID.

        Returns:
            List of pending invites for the organization.
        """
        rows = await self._db.fetch(
            """
            SELECT id, org_id, email, token, invited_by, status, created_at, expires_at
            FROM organization_invites
            WHERE org_id = $1 AND status = 'pending'
            ORDER BY created_at ASC
            """,
            org_id,
        )
        return [self._row_to_invite(row) for row in rows]

    async def delete(self, invite_id: UUID) -> bool:
        """Delete an invite.

        Args:
            invite_id: The invite ID to delete.

        Returns:
            True if the invite was deleted, False if not found.
        """
        result = await self._db.execute(
            "DELETE FROM organization_invites WHERE id = $1",
            invite_id,
        )
        return result == "DELETE 1"

    def _row_to_invite(self, row: Any) -> OrganizationInviteRow:
        """Convert a database row to an OrganizationInviteRow.

        Args:
            row: The database row.

        Returns:
            The OrganizationInviteRow instance.
        """
        return OrganizationInviteRow(
            id=row["id"],
            org_id=row["org_id"],
            email=row["email"],
            token=row["token"],
            invited_by=row["invited_by"],
            status=row["status"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )
