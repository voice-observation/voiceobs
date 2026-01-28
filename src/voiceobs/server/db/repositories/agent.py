"""Agent repository for database operations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import AgentRow

# Sentinel value to distinguish between None (set to NULL) and not provided
_NOT_PROVIDED = object()


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
            contact_info: Contact info dict (e.g., {"phone_number": "..."} or {"web_url": "..."})
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
                   verification_error, verification_transcript, verification_reasoning,
                   metadata, created_at, updated_at, created_by, is_active
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
                   verification_error, verification_transcript, verification_reasoning,
                   metadata, created_at, updated_at, created_by, is_active
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
                   verification_error, verification_transcript, verification_reasoning,
                   metadata, created_at, updated_at, created_by, is_active
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
        name: str | None | object = _NOT_PROVIDED,
        agent_type: str | None | object = _NOT_PROVIDED,
        contact_info: dict[str, Any] | None | object = _NOT_PROVIDED,
        goal: str | None | object = _NOT_PROVIDED,
        supported_intents: list[str] | None | object = _NOT_PROVIDED,
        connection_status: str | None | object = _NOT_PROVIDED,
        verification_attempts: int | None | object = _NOT_PROVIDED,
        last_verification_at: datetime | None | object = _NOT_PROVIDED,
        verification_error: str | None | object = _NOT_PROVIDED,
        verification_transcript: list[dict[str, str]] | None | object = _NOT_PROVIDED,
        verification_reasoning: str | None | object = _NOT_PROVIDED,
        metadata: dict[str, Any] | None | object = _NOT_PROVIDED,
        is_active: bool | None | object = _NOT_PROVIDED,
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
            verification_transcript: Conversation transcript from verification
            verification_reasoning: Explanation of verification result
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
            "verification_transcript": verification_transcript,
            "verification_reasoning": verification_reasoning,
            "metadata": metadata,
            "is_active": is_active,
        }

        # Build SQL clauses, handling provided values
        updates = []
        params: list[Any] = []
        param_idx = 1

        for field_name, field_value in field_values.items():
            if field_value is _NOT_PROVIDED:
                continue  # Skip fields not provided

            if field_value is None:
                # Set to NULL explicitly
                updates.append(f"{field_name} = NULL")
            elif field_name in (
                "contact_info",
                "supported_intents",
                "metadata",
                "verification_transcript",
            ):
                updates.append(f"{field_name} = ${param_idx}::jsonb")
                params.append(json.dumps(field_value))
                param_idx += 1
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

    async def delete(self, agent_id: UUID) -> bool:
        """Delete an agent.

        Args:
            agent_id: The agent UUID.

        Returns:
            True if deleted, False if not found.
        """
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

        verification_transcript = row["verification_transcript"]
        if isinstance(verification_transcript, str):
            verification_transcript = (
                json.loads(verification_transcript) if verification_transcript else None
            )

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
            verification_transcript=verification_transcript,
            verification_reasoning=row["verification_reasoning"],
            metadata=metadata,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
            is_active=row["is_active"],
        )
