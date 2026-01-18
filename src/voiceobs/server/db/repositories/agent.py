"""Agent repository for database operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import AgentRow


class AgentRepository:
    """Repository for agent operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the agent repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(
        self,
        name: str,
        agent_type: str,
        contact_info: dict[str, Any],
        goal: str,
        supported_intents: list[str],
        metadata: dict[str, Any] | None = None,
        created_by: str | None = None,
    ) -> AgentRow:
        """Create a new agent with 'saved' status.

        Args:
            name: Agent name
            agent_type: Agent type ('phone', 'web', etc.)
            contact_info: Contact information dict (e.g., {"phone_number": "..."} or {"web_url": "..."})
            goal: Agent goal
            supported_intents: List of supported intents
            metadata: Additional metadata
            created_by: Creator identifier

        Returns:
            The created agent row.

        Raises:
            ValueError: If contact_info doesn't contain required fields for agent_type
        """
        # Validate contact_info contains required fields based on agent_type
        if agent_type == "phone" and "phone_number" not in contact_info:
            raise ValueError("contact_info must contain 'phone_number' for phone agents")

        agent_id = uuid4()
        contact_info = contact_info or {}
        supported_intents = supported_intents or []
        metadata = metadata or {}

        await self._db.execute(
            """
            INSERT INTO agents (
                id, name, agent_type, contact_info, goal, supported_intents,
                connection_status, metadata, created_by, is_active
            )
            VALUES (
                $1, $2, $3, $4::jsonb, $5, $6::jsonb, 'saved', $7::jsonb, $8, true
            )
            """,
            agent_id,
            name,
            agent_type,
            json.dumps(contact_info),
            goal,
            json.dumps(supported_intents),
            json.dumps(metadata),
            created_by,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, name, agent_type, contact_info, goal, supported_intents,
                   connection_status, verification_attempts, last_verification_at,
                   verification_error, metadata, created_at, updated_at,
                   created_by, is_active
            FROM agents WHERE id = $1
            """,
            agent_id,
        )

        if row is None:
            raise RuntimeError("Failed to create agent")

        return self._row_to_agent(row)

    async def get(self, agent_id: UUID) -> AgentRow | None:
        """Get agent by UUID.

        Args:
            agent_id: The agent UUID.

        Returns:
            The agent row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, agent_type, contact_info, goal, supported_intents,
                   connection_status, verification_attempts, last_verification_at,
                   verification_error, metadata, created_at, updated_at,
                   created_by, is_active
            FROM agents WHERE id = $1
            """,
            agent_id,
        )

        if row is None:
            return None

        return self._row_to_agent(row)

    async def list_all(
        self,
        connection_status: str | None = None,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[AgentRow]:
        """List all agents with optional filtering.

        Args:
            connection_status: Filter by connection status. None for all statuses.
            is_active: Filter by active status. None for all agents.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of agent rows.
        """
        conditions = []
        params: list[Any] = []
        param_idx = 1

        if connection_status is not None:
            conditions.append(f"connection_status = ${param_idx}")
            params.append(connection_status)
            param_idx += 1

        if is_active is not None:
            conditions.append(f"is_active = ${param_idx}")
            params.append(is_active)
            param_idx += 1

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        limit_clause = ""
        if limit is not None:
            limit_clause = f"LIMIT ${param_idx}"
            params.append(limit)
            param_idx += 1

        offset_clause = ""
        if offset is not None:
            offset_clause = f"OFFSET ${param_idx}"
            params.append(offset)
            param_idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT id, name, agent_type, contact_info, goal, supported_intents,
                   connection_status, verification_attempts, last_verification_at,
                   verification_error, metadata, created_at, updated_at,
                   created_by, is_active
            FROM agents
            {where_clause}
            ORDER BY created_at DESC
            {limit_clause} {offset_clause}
            """,
            *params,
        )

        return [self._row_to_agent(row) for row in rows]

    async def update(
        self,
        agent_id: UUID,
        name: str | None = None,
        agent_type: str | None = None,
        contact_info: dict[str, Any] | None = None,
        goal: str | None = None,
        supported_intents: list[str] | None = None,
        connection_status: str | None = None,
        verification_attempts: int | None = None,
        last_verification_at: datetime | None = None,
        verification_error: str | None = None,
        metadata: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> AgentRow | None:
        """Update an existing agent.

        Args:
            agent_id: Agent UUID
            name: Agent name
            agent_type: Agent type (if changed, contact_info must be updated too)
            contact_info: Contact information (will merge with existing if partial update)
            goal: Agent goal
            supported_intents: Supported intents
            connection_status: Connection status
            verification_attempts: Number of verification attempts
            last_verification_at: Last verification timestamp
            verification_error: Verification error message
            metadata: Additional metadata
            is_active: Active status

        Returns:
            The updated agent row, or None if not found.

        Note: If contact_info is provided, it can be a partial update (merged with existing).
        If agent_type is updated, ensure contact_info contains required fields.
        """
        # Build update fields dynamically
        field_values = {
            "name": name,
            "agent_type": agent_type,
            "contact_info": contact_info,
            "goal": goal,
            "supported_intents": supported_intents,
            "connection_status": connection_status,
            "verification_attempts": verification_attempts,
            "last_verification_at": last_verification_at,
            "verification_error": verification_error,
            "metadata": metadata,
            "is_active": is_active,
        }

        # Filter out None values and build SQL clauses
        updates = []
        params: list[Any] = []
        param_idx = 1

        for field_name, field_value in field_values.items():
            if field_value is not None:
                if field_name in ("contact_info", "supported_intents", "metadata"):
                    updates.append(f"{field_name} = ${param_idx}::jsonb")
                    params.append(json.dumps(field_value))
                else:
                    updates.append(f"{field_name} = ${param_idx}")
                    params.append(field_value)
                param_idx += 1

        if not updates:
            # No updates, just return the existing agent
            return await self.get(agent_id)

        # Add updated_at timestamp
        updates.append("updated_at = NOW()")

        params.append(agent_id)
        await self._db.execute(
            f"""
            UPDATE agents
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            """,
            *params,
        )

        return await self.get(agent_id)

    async def update_status(
        self,
        agent_id: UUID,
        status: str,
        error: str | None = None,
    ) -> AgentRow | None:
        """Update agent connection status.

        Args:
            agent_id: Agent UUID
            status: New connection status
            error: Optional error message

        Returns:
            The updated agent row, or None if not found.
        """
        return await self.update(
            agent_id,
            connection_status=status,
            verification_error=error,
        )

    async def delete(self, agent_id: UUID, soft: bool = True) -> bool:
        """Delete an agent.

        Args:
            agent_id: The agent UUID.
            soft: If True, soft delete (set is_active=False). If False, hard delete.

        Returns:
            True if deleted, False if not found.
        """
        if soft:
            result = await self._db.execute(
                """
                UPDATE agents
                SET is_active = false, updated_at = NOW()
                WHERE id = $1
                """,
                agent_id,
            )
            return result == "UPDATE 1"
        else:
            result = await self._db.execute(
                """
                DELETE FROM agents WHERE id = $1
                """,
                agent_id,
            )
            return result == "DELETE 1"

    async def count(self, is_active: bool | None = True) -> int:
        """Count agents.

        Args:
            is_active: Filter by active status. None for all agents.

        Returns:
            Count of agents.
        """
        if is_active is None:
            count = await self._db.fetchval(
                """
                SELECT COUNT(*) FROM agents
                """
            )
        else:
            count = await self._db.fetchval(
                """
                SELECT COUNT(*) FROM agents WHERE is_active = $1
                """,
                is_active,
            )

        return count or 0

    def _row_to_agent(self, row: Any) -> AgentRow:
        """Convert a database row to an AgentRow.

        Args:
            row: Database row.

        Returns:
            AgentRow instance.
        """
        # Parse JSONB fields if they come as strings (asyncpg might return them as strings)
        contact_info = row["contact_info"]
        if isinstance(contact_info, str):
            contact_info = json.loads(contact_info) if contact_info else {}
        elif contact_info is None:
            contact_info = {}

        supported_intents = row["supported_intents"]
        if isinstance(supported_intents, str):
            supported_intents = json.loads(supported_intents) if supported_intents else []
        elif supported_intents is None:
            supported_intents = []

        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata) if metadata else {}
        elif metadata is None:
            metadata = {}

        return AgentRow(
            id=row["id"],
            name=row["name"],
            agent_type=row["agent_type"],
            contact_info=contact_info,
            goal=row["goal"],
            supported_intents=supported_intents,
            connection_status=row["connection_status"],
            verification_attempts=row["verification_attempts"],
            last_verification_at=row["last_verification_at"],
            verification_error=row["verification_error"],
            metadata=metadata,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
            is_active=row["is_active"],
        )

