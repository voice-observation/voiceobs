"""Persona repository for database operations."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID, uuid4

from voiceobs.server.db.connection import Database
from voiceobs.server.db.models import PersonaRow

# Supported TTS providers
SUPPORTED_TTS_PROVIDERS = {"openai", "elevenlabs", "deepgram"}


class PersonaRepository:
    """Repository for persona operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the persona repository.

        Args:
            db: Database connection manager.
        """
        self._db = db

    async def create(
        self,
        name: str,
        aggression: float,
        patience: float,
        verbosity: float,
        tts_provider: str | None = None,
        tts_config: dict[str, Any] | None = None,
        description: str | None = None,
        traits: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        created_by: str | None = None,
        preview_audio_url: str | None = None,
        preview_audio_text: str | None = None,
    ) -> PersonaRow:
        """Create a new persona.

        Args:
            name: Persona name.
            aggression: Aggression level (0.0-1.0).
            patience: Patience level (0.0-1.0).
            verbosity: Verbosity level (0.0-1.0).
            tts_provider: TTS provider identifier.
            tts_config: Provider-specific TTS configuration.
            description: Persona description.
            traits: List of personality traits.
            metadata: Additional metadata.
            created_by: User identifier who created the persona.
            preview_audio_url: URL to pregenerated preview audio.
            preview_audio_text: Text used for preview audio generation.

        Returns:
            The created persona row.

        Raises:
            ValueError: If tts_provider is not supported.
        """
        # Validate TTS provider only if provided
        if tts_provider is not None:
            if tts_provider.lower() not in SUPPORTED_TTS_PROVIDERS:
                supported = ", ".join(sorted(SUPPORTED_TTS_PROVIDERS))
                raise ValueError(
                    f"Unsupported TTS provider: {tts_provider}. Supported providers: {supported}"
                )

        persona_id = uuid4()
        tts_config = tts_config or {}
        traits = traits or []
        metadata = metadata or {}

        await self._db.execute(
            """
            INSERT INTO personas (
                id, name, description, aggression, patience, verbosity,
                traits, tts_provider, tts_config, preview_audio_url,
                preview_audio_text, metadata, created_by, is_active
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb, $8, $9::jsonb,
                $10, $11, $12::jsonb, $13, true
            )
            """,
            persona_id,
            name,
            description,
            aggression,
            patience,
            verbosity,
            json.dumps(traits),  # Convert list to JSON string for JSONB column
            tts_provider,
            json.dumps(tts_config),  # Convert dict to JSON string for JSONB column
            preview_audio_url,
            preview_audio_text,
            json.dumps(metadata),  # Convert dict to JSON string for JSONB column
            created_by,
        )

        row = await self._db.fetchrow(
            """
            SELECT id, name, description, aggression, patience, verbosity,
                   traits, tts_provider, tts_config, preview_audio_url,
                   preview_audio_text, metadata, created_at, updated_at,
                   created_by, is_active
            FROM personas WHERE id = $1
            """,
            persona_id,
        )

        if row is None:
            raise RuntimeError("Failed to create persona")

        return self._row_to_persona(row)

    async def get(self, persona_id: UUID) -> PersonaRow | None:
        """Get persona by UUID.

        Args:
            persona_id: The persona UUID.

        Returns:
            The persona row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, description, aggression, patience, verbosity,
                   traits, tts_provider, tts_config, preview_audio_url,
                   preview_audio_text, metadata, created_at, updated_at,
                   created_by, is_active
            FROM personas WHERE id = $1
            """,
            persona_id,
        )

        if row is None:
            return None

        return self._row_to_persona(row)

    async def get_by_name(self, name: str) -> PersonaRow | None:
        """Get active persona by name.

        Args:
            name: The persona name.

        Returns:
            The persona row, or None if not found.
        """
        row = await self._db.fetchrow(
            """
            SELECT id, name, description, aggression, patience, verbosity,
                   traits, tts_provider, tts_config, preview_audio_url,
                   preview_audio_text, metadata, created_at, updated_at,
                   created_by, is_active
            FROM personas WHERE name = $1 AND is_active = true
            """,
            name,
        )

        if row is None:
            return None

        return self._row_to_persona(row)

    async def list_all(
        self,
        is_active: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[PersonaRow]:
        """List all personas with optional filtering.

        Args:
            is_active: Filter by active status. None for all personas.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of persona rows.
        """
        conditions = []
        params: list[Any] = []
        param_idx = 1

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

        rows = await self._db.fetch(
            f"""
            SELECT id, name, description, aggression, patience, verbosity,
                   traits, tts_provider, tts_config, preview_audio_url,
                   preview_audio_text, metadata, created_at, updated_at,
                   created_by, is_active
            FROM personas
            {where_clause}
            ORDER BY created_at DESC
            {limit_clause} {offset_clause}
            """,
            *params,
        )

        return [self._row_to_persona(row) for row in rows]

    async def update(
        self,
        persona_id: UUID,
        name: str | None = None,
        description: str | None = None,
        aggression: float | None = None,
        patience: float | None = None,
        verbosity: float | None = None,
        traits: list[str] | None = None,
        tts_provider: str | None = None,
        tts_config: dict[str, Any] | None = None,
        preview_audio_url: str | None = None,
        preview_audio_text: str | None = None,
        metadata: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> PersonaRow | None:
        """Update an existing persona.

        Args:
            persona_id: The persona UUID.
            name: New name (optional).
            description: New description (optional).
            aggression: New aggression level (optional).
            patience: New patience level (optional).
            verbosity: New verbosity level (optional).
            traits: New traits list (optional).
            tts_provider: New TTS provider (optional).
            tts_config: New TTS configuration (optional).
            preview_audio_url: New preview audio URL (optional).
            preview_audio_text: New preview audio text (optional).
            metadata: New metadata (optional).

        Returns:
            The updated persona row, or None if not found.

        Raises:
            ValueError: If tts_provider is not supported.
        """
        # Validate TTS provider if provided
        if tts_provider is not None and tts_provider.lower() not in SUPPORTED_TTS_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_TTS_PROVIDERS))
            raise ValueError(
                f"Unsupported TTS provider: {tts_provider}. Supported providers: {supported}"
            )

        # Build update fields dynamically using a dictionary
        field_values = {
            "name": name,
            "description": description,
            "aggression": aggression,
            "patience": patience,
            "verbosity": verbosity,
            "traits": traits,
            "tts_provider": tts_provider,
            "tts_config": tts_config,
            "preview_audio_url": preview_audio_url,
            "preview_audio_text": preview_audio_text,
            "metadata": metadata,
            "is_active": is_active,
        }

        # Filter out None values and build SQL clauses
        updates = []
        params: list[Any] = []
        param_idx = 1

        for field_name, field_value in field_values.items():
            if field_value is not None:
                if field_name == "traits":
                    updates.append(f"{field_name} = ${param_idx}::jsonb")
                    params.append(json.dumps(field_value))
                elif field_name in ("tts_config", "metadata"):
                    updates.append(f"{field_name} = ${param_idx}::jsonb")
                    params.append(json.dumps(field_value))
                else:
                    updates.append(f"{field_name} = ${param_idx}")
                    params.append(field_value)
                param_idx += 1

        if not updates:
            # No updates, just return the existing persona
            return await self.get(persona_id)

        # Add updated_at timestamp
        updates.append("updated_at = NOW()")

        params.append(persona_id)
        await self._db.execute(
            f"""
            UPDATE personas
            SET {", ".join(updates)}
            WHERE id = ${param_idx}
            """,
            *params,
        )

        return await self.get(persona_id)

    async def delete(self, persona_id: UUID, soft: bool = True) -> bool:
        """Delete a persona.

        Args:
            persona_id: The persona UUID.
            soft: If True, soft delete (set is_active=False). If False, hard delete.

        Returns:
            True if deleted, False if not found.
        """
        if soft:
            result = await self._db.execute(
                """
                UPDATE personas
                SET is_active = false, updated_at = NOW()
                WHERE id = $1
                """,
                persona_id,
            )
            return result == "UPDATE 1"
        else:
            result = await self._db.execute(
                """
                DELETE FROM personas WHERE id = $1
                """,
                persona_id,
            )
            return result == "DELETE 1"

    async def count(self, is_active: bool | None = True) -> int:
        """Count personas.

        Args:
            is_active: Filter by active status. None for all personas.

        Returns:
            Count of personas.
        """
        if is_active is None:
            count = await self._db.fetchval(
                """
                SELECT COUNT(*) FROM personas
                """
            )
        else:
            count = await self._db.fetchval(
                """
                SELECT COUNT(*) FROM personas WHERE is_active = $1
                """,
                is_active,
            )

        return count or 0

    def _row_to_persona(self, row: Any) -> PersonaRow:
        """Convert a database row to a PersonaRow.

        Args:
            row: Database row.

        Returns:
            PersonaRow instance.
        """
        # Parse JSONB fields if they come as strings (asyncpg might return them as strings)
        traits = row["traits"]
        if isinstance(traits, str):
            traits = json.loads(traits) if traits else []
        elif traits is None:
            traits = []

        # Ensure traits is a list of strings (not objects)
        # If traits contains objects, extract string values or convert to strings
        if traits and isinstance(traits, list):
            parsed_traits = []
            for trait in traits:
                if isinstance(trait, str):
                    parsed_traits.append(trait)
                elif isinstance(trait, dict):
                    # If it's an object, try to extract a meaningful string representation
                    # For seed data format: {"key": "...", "value": ...}
                    if "key" in trait:
                        parsed_traits.append(str(trait["key"]))
                    elif "value" in trait:
                        parsed_traits.append(str(trait["value"]))
                    else:
                        # Fallback: convert entire object to string
                        parsed_traits.append(str(trait))
                else:
                    parsed_traits.append(str(trait))
            traits = parsed_traits

        tts_config = row["tts_config"]
        if isinstance(tts_config, str):
            tts_config = json.loads(tts_config) if tts_config else {}
        elif tts_config is None:
            tts_config = {}

        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata) if metadata else {}
        elif metadata is None:
            metadata = {}

        return PersonaRow(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            aggression=row["aggression"],
            patience=row["patience"],
            verbosity=row["verbosity"],
            traits=traits,
            tts_provider=row["tts_provider"],
            tts_config=tts_config,
            preview_audio_url=row["preview_audio_url"],
            preview_audio_text=row["preview_audio_text"],
            metadata=metadata,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
            is_active=row["is_active"],
        )
