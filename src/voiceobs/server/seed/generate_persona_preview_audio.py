#!/usr/bin/env python3
"""
Generate preview audio for personas.

- Reads personas from the database that have preview_audio_text but no preview_audio_url
- For each persona:
  - Uses the appropriate TTS service (based on tts_provider) to synthesize audio
  - Stores the audio file using audio storage
  - Updates the persona with the preview_audio_url

Usage:
    # Generate preview audio for all personas missing preview audio
    python generate_persona_preview_audio.py

    # Generate preview audio for a specific persona by ID
    python generate_persona_preview_audio.py --persona-id <uuid>

Database URL is read from (in order):
  1. VOICEOBS_DATABASE_URL environment variable
  2. server.database_url in voiceobs.yaml config file

The script also loads .env file from project root if it exists.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Import TTS services to register them with the factory
# This import triggers the registration of providers in services/__init__.py
from voiceobs.server.services import (  # noqa: F401
    TTSServiceFactory,
)
from voiceobs.server.storage import AudioStorage
from voiceobs.server.utils.storage import get_audio_storage_from_env


def _get_database_url() -> str:
    """Get the database URL from config file.

    Returns:
        Database URL string.

    Raises:
        RuntimeError: If no database URL is configured.
    """
    try:
        from voiceobs.config import get_config

        config = get_config()
        if config.server.database_url:
            return config.server.database_url
    except Exception as e:
        raise RuntimeError(
            f"Failed to read database URL from config: {e}. "
            "Configure server.database_url in voiceobs.yaml"
        ) from e

    raise RuntimeError(
        "Database URL not configured. Configure server.database_url in voiceobs.yaml"
    )

async def generate_preview_audio_for_persona(
    persona_id: UUID,
    persona_name: str,
    tts_provider: str,
    tts_config: dict[str, Any],
    preview_audio_text: str,
    audio_storage: AudioStorage,
) -> str | None:
    """Generate preview audio for a persona.

    Args:
        persona_id: Persona UUID.
        persona_name: Persona name (for logging).
        tts_provider: TTS provider identifier.
        tts_config: Provider-specific TTS configuration.
        preview_audio_text: Text to synthesize.
        audio_storage: Audio storage instance.

    Returns:
        Preview audio URL, or None if generation failed.
    """
    try:
        # Get TTS service for the provider
        tts_service = TTSServiceFactory.create(tts_provider)

        # Synthesize audio
        print(f"[info] Generating audio for '{persona_name}' using {tts_provider}...", file=sys.stderr)
        audio_bytes, mime_type, duration_ms = await tts_service.synthesize(
            preview_audio_text, tts_config
        )

        print(
            f"[info] Generated audio: {len(audio_bytes)} bytes, "
            f"{mime_type}, {duration_ms:.2f}ms",
            file=sys.stderr,
        )

        # Store audio with prefix based on persona ID
        prefix = f"personas/preview/{persona_id}"
        preview_audio_url = await audio_storage.store_audio(
            audio_bytes, prefix=prefix, content_type=mime_type
        )

        print(f"[ok] Stored audio for '{persona_name}': {preview_audio_url}", file=sys.stderr)
        return preview_audio_url

    except Exception as e:
        print(
            f"[error] Failed to generate audio for '{persona_name}': {e}",
            file=sys.stderr,
        )
        return None


async def process_personas(
    engine: Engine, audio_storage: AudioStorage, persona_id: UUID | None = None
) -> tuple[int, int]:
    """Process personas and generate preview audio.

    Args:
        engine: SQLAlchemy engine.
        audio_storage: Audio storage instance.
        persona_id: Optional persona UUID to process a single persona.
                   If None, processes all personas missing preview audio.

    Returns:
        Tuple of (processed_count, success_count).
    """
    # Query personas that need preview audio
    # They must have preview_audio_text but no preview_audio_url
    if persona_id:
        query = text(
            """
            SELECT id, name, tts_provider, tts_config, preview_audio_text
            FROM personas
            WHERE id = :persona_id
              AND preview_audio_text IS NOT NULL
              AND preview_audio_text != ''
              AND is_active = true
            """
        )
        query_params = {"persona_id": persona_id}
    else:
        query = text(
            """
            SELECT id, name, tts_provider, tts_config, preview_audio_text
            FROM personas
            WHERE preview_audio_text IS NOT NULL
              AND preview_audio_text != ''
              AND (preview_audio_url IS NULL OR preview_audio_url = '')
              AND is_active = true
            ORDER BY created_at ASC
            """
        )
        query_params = {}

    with engine.connect() as conn:
        if query_params:
            result = conn.execute(query, query_params)
        else:
            result = conn.execute(query)
        # Use mappings() to get dictionary-like rows
        personas = result.mappings().fetchall()

    if not personas:
        if persona_id:
            print(
                f"[error] Persona with ID {persona_id} not found, or it doesn't meet the criteria "
                "(must have preview_audio_text and be active).",
                file=sys.stderr,
            )
        else:
            print("[info] No personas need preview audio generation.", file=sys.stderr)
        return 0, 0

    if persona_id:
        print(f"[info] Processing persona {persona_id}...", file=sys.stderr)
    else:
        print(f"[info] Found {len(personas)} persona(s) needing preview audio.", file=sys.stderr)

    processed_count = 0
    success_count = 0

    for persona_row in personas:
        persona_id = persona_row["id"]
        persona_name = persona_row["name"]
        tts_provider = persona_row["tts_provider"]
        tts_config = persona_row["tts_config"] or {}
        preview_audio_text = persona_row["preview_audio_text"]

        processed_count += 1

        # Generate preview audio
        preview_audio_url = await generate_preview_audio_for_persona(
            persona_id=persona_id,
            persona_name=persona_name,
            tts_provider=tts_provider,
            tts_config=tts_config,
            preview_audio_text=preview_audio_text,
            audio_storage=audio_storage,
        )

        if preview_audio_url:
            # Update persona with preview_audio_url
            update_query = text(
                """
                UPDATE personas
                SET preview_audio_url = :preview_audio_url,
                    updated_at = NOW()
                WHERE id = :persona_id
                """
            )

            with engine.begin() as conn:
                conn.execute(
                    update_query,
                    {"preview_audio_url": preview_audio_url, "persona_id": persona_id},
                )

            success_count += 1
        else:
            print(
                f"[warn] Skipping update for '{persona_name}' due to generation failure.",
                file=sys.stderr,
            )

    return processed_count, success_count


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate preview audio for personas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--persona-id",
        type=str,
        help="UUID of a specific persona to generate preview audio for. "
        "If not provided, processes all personas missing preview audio.",
    )

    args = parser.parse_args()

    # Parse persona_id if provided
    persona_id: UUID | None = None
    if args.persona_id:
        try:
            persona_id = UUID(args.persona_id)
        except ValueError as e:
            print(
                f"[error] Invalid persona ID format: {args.persona_id}. "
                "Expected a valid UUID.",
                file=sys.stderr,
            )
            return 1

    # Load environment variables from .env file in project root
    project_root = Path(__file__).parent.parent.parent.parent.parent
    print(f"[info] Project root: {project_root}", file=sys.stderr)
    env_path = project_root / ".env"
    load_dotenv(env_path, override=False)  # Don't override existing env vars

    db_url = _get_database_url()
    engine = create_engine(db_url, pool_pre_ping=True)

    # Get audio storage from environment configuration
    audio_storage = get_audio_storage_from_env()

    # Process personas asynchronously
    processed_count, success_count = asyncio.run(
        process_personas(engine, audio_storage, persona_id=persona_id)
    )

    if processed_count == 0:
        print("[ok] No personas needed processing.")
        return 0

    if success_count == processed_count:
        print(f"[ok] Successfully generated preview audio for {success_count} persona(s).")
        return 0
    elif success_count > 0:
        print(
            f"[warn] Generated preview audio for {success_count} out of {processed_count} persona(s).",
            file=sys.stderr,
        )
        return 1
    else:
        print(
            f"[error] Failed to generate preview audio for any persona.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

