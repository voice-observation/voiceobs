#!/usr/bin/env python3
"""
Seed predefined personas into Postgres.

- Reads personas_catalog_v0_1.json
- For each base persona + provider variant:
  - upserts into personas table keyed by (tts_provider, metadata.base_persona_key)

Database URL is read from (in order):
  1. VOICEOBS_DATABASE_URL environment variable
  2. server.database_url in voiceobs.yaml config file

The script also loads .env file from project root if it exists.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Default catalog path relative to this script's directory
CATALOG_PATH_DEFAULT = str(Path(__file__).parent / "personas_catalog_v0_1.json")
MODELS_PATH_DEFAULT = str(Path(__file__).parent / "tts_provider_models.json")


def _get_database_url() -> str:
    """Get the database URL from environment or config.

    Checks in order:
    1. VOICEOBS_DATABASE_URL environment variable
    2. DATABASE_URL environment variable (for backward compatibility)
    3. server.database_url in voiceobs.yaml config file

    Returns:
        Database URL string.

    Raises:
        RuntimeError: If no database URL is configured.
    """
    # First check VOICEOBS_DATABASE_URL environment variable
    env_url = os.environ.get("VOICEOBS_DATABASE_URL")
    if env_url:
        return env_url

    # Then try config file
    try:
        from voiceobs.config import get_config

        config = get_config()
        if config.server.database_url:
            return config.server.database_url
    except Exception:
        pass

    raise RuntimeError(
        "Database URL not configured. Set VOICEOBS_DATABASE_URL environment variable "
        "or configure server.database_url in voiceobs.yaml"
    )


def load_catalog(path: str) -> dict[str, Any]:
    """Load persona catalog from JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_models(path: str) -> dict[str, dict[str, dict[str, Any]]]:
    """Load TTS provider models from JSON file.

    Returns:
        Dictionary with structure: {provider: {model_name: {config}}}
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
        return data.get("models", {})


def upsert_persona_row(
    engine: Engine,
    *,
    name: str,
    description: str | None,
    aggression: float,
    patience: float,
    verbosity: float,
    traits: Any,
    tts_provider: str,
    tts_config: dict[str, Any],
    preview_audio_text: str | None,
    metadata: dict[str, Any],
    created_by: str = "system",
) -> None:
    """
    Upsert into personas table using (tts_provider, metadata->>'base_persona_key') as unique key.
    If you don't yet have a unique index, this still works but may duplicate under concurrency.
    """
    # Ensure metadata has base_persona_key and is_predefined
    if "base_persona_key" not in metadata:
        raise ValueError("metadata.base_persona_key is required for upsert key")
    metadata.setdefault("is_predefined", True)

    # Best-effort upsert using Postgres ON CONFLICT requires a unique index.
    # The unique index personas_provider_base_key_uq must exist for this to work.
    # We'll attempt ON CONFLICT; if it errors, we fallback to update-then-insert logic.
    # Note: The index uses a functional expression, so we must match it exactly.
    sql_upsert = text(
        """
        INSERT INTO personas
          (name, description, aggression, patience, verbosity, traits, tts_provider, tts_config,
           preview_audio_text, metadata, created_by, is_active, created_at, updated_at)
        VALUES
          (:name, :description, :aggression, :patience, :verbosity,
           CAST(:traits AS jsonb),
           :tts_provider,
           CAST(:tts_config AS jsonb),
           :preview_audio_text,
           CAST(:metadata AS jsonb),
           :created_by,
           true,
           NOW(), NOW())
        ON CONFLICT (tts_provider, (metadata->>'base_persona_key'))
        DO UPDATE SET
          name = EXCLUDED.name,
          description = EXCLUDED.description,
          aggression = EXCLUDED.aggression,
          patience = EXCLUDED.patience,
          verbosity = EXCLUDED.verbosity,
          traits = EXCLUDED.traits,
          tts_config = EXCLUDED.tts_config,
          preview_audio_text = EXCLUDED.preview_audio_text,
          metadata = EXCLUDED.metadata,
          updated_at = NOW(),
          is_active = true;
        """
    )

    payload = {
        "name": name,
        "description": description,
        "aggression": aggression,
        "patience": patience,
        "verbosity": verbosity,
        "traits": json.dumps(traits if traits is not None else []),
        "tts_provider": tts_provider,
        "tts_config": json.dumps(tts_config if tts_config is not None else {}),
        "preview_audio_text": preview_audio_text,
        "metadata": json.dumps(metadata if metadata is not None else {}),
        "created_by": created_by,
    }

    with engine.begin() as conn:
        # Use a savepoint to handle ON CONFLICT errors gracefully
        savepoint = conn.begin_nested()
        try:
            conn.execute(sql_upsert, payload)
            savepoint.commit()
        except Exception as e:
            # Rollback the savepoint to recover from the error
            savepoint.rollback()
            # Fallback if unique index doesn't exist yet.
            print(f"[warn] ON CONFLICT upsert failed; falling back. Error: {e}", file=sys.stderr)

            # 1) Try update existing by key
            sql_update = text(
                """
                UPDATE personas
                SET
                  name = :name,
                  description = :description,
                  aggression = :aggression,
                  patience = :patience,
                  verbosity = :verbosity,
                  traits = CAST(:traits AS jsonb),
                  tts_config = CAST(:tts_config AS jsonb),
                  preview_audio_text = :preview_audio_text,
                  metadata = CAST(:metadata AS jsonb),
                  updated_at = NOW(),
                  is_active = true
                WHERE
                  tts_provider = :tts_provider
                  AND (metadata->>'base_persona_key') = :base_persona_key;
                """
            )
            upd = dict(payload)
            upd["base_persona_key"] = metadata["base_persona_key"]
            res = conn.execute(sql_update, upd)
            if res.rowcount and res.rowcount > 0:
                return

            # 2) Insert if no rows updated
            sql_insert = text(
                """
                INSERT INTO personas
                  (name, description, aggression, patience, verbosity, traits,
                   tts_provider, tts_config, preview_audio_text, metadata,
                   created_by, is_active, created_at, updated_at)
                VALUES
                  (:name, :description, :aggression, :patience, :verbosity,
                   CAST(:traits AS jsonb),
                   :tts_provider,
                   CAST(:tts_config AS jsonb),
                   :preview_audio_text,
                   CAST(:metadata AS jsonb),
                   :created_by,
                   true,
                   NOW(), NOW());
                """
            )
            conn.execute(sql_insert, payload)


def ensure_unique_index(engine: Engine) -> None:
    """Ensure the unique index exists for ON CONFLICT upsert logic."""
    with engine.begin() as conn:
        # Check if index exists
        check_sql = text(
            """
            SELECT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE indexname = 'personas_provider_base_key_uq'
            );
            """
        )
        result = conn.execute(check_sql)
        index_exists = result.scalar()

        if not index_exists:
            print("[info] Creating unique index for personas upsert...", file=sys.stderr)
            create_index_sql = text(
                """
                CREATE UNIQUE INDEX personas_provider_base_key_uq
                ON personas (tts_provider, (metadata->>'base_persona_key'))
                WHERE metadata->>'base_persona_key' IS NOT NULL;
                """
            )
            conn.execute(create_index_sql)
            print("[ok] Unique index created.", file=sys.stderr)


def resolve_provider_config(
    provider_name: str,
    provider_value: str | dict[str, Any],
    models: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Resolve provider configuration from model reference or direct config.

    Args:
        provider_name: Name of the TTS provider (e.g., "elevenlabs", "openai").
        provider_value: Either a model name string or a direct config dict.
        models: Dictionary of provider models loaded from tts_provider_models.json.

    Returns:
        Resolved TTS configuration dictionary.

    Raises:
        ValueError: If model reference is not found.
    """
    # If provider_value is a string, it's a model reference
    if isinstance(provider_value, str):
        provider_models = models.get(provider_name, {})
        if provider_value not in provider_models:
            raise ValueError(
                f"Model '{provider_value}' not found for provider '{provider_name}'. "
                f"Available models: {list(provider_models.keys())}"
            )
        # Return a copy of the model config
        return dict(provider_models[provider_value])

    # Otherwise, it's a direct config dict (backward compatibility)
    return dict(provider_value or {})


def main() -> int:
    db_url = _get_database_url()
    catalog_path = os.getenv("PERSONA_CATALOG_PATH", CATALOG_PATH_DEFAULT)
    models_path = os.getenv("TTS_MODELS_PATH", MODELS_PATH_DEFAULT)

    catalog = load_catalog(catalog_path)
    personas = catalog.get("personas", [])
    if not personas:
        print("[error] No personas found in catalog.")
        return 2

    # Load models file (may not exist for backward compatibility)
    models: dict[str, dict[str, dict[str, Any]]] = {}
    if os.path.exists(models_path):
        try:
            models = load_models(models_path)
            print(f"[info] Loaded TTS models from {models_path}", file=sys.stderr)
        except Exception as e:
            print(
                f"[warn] Failed to load models file {models_path}: {e}. "
                "Continuing with direct config format.",
                file=sys.stderr,
            )
    else:
        print(
            f"[info] Models file not found at {models_path}. "
            "Using direct config format (backward compatibility).",
            file=sys.stderr,
        )

    engine = create_engine(db_url, pool_pre_ping=True)

    # Ensure unique index exists for ON CONFLICT upsert
    ensure_unique_index(engine)

    total = 0
    for p in personas:
        base_key = p["base_persona_key"]
        common_metadata = dict(p.get("metadata") or {})
        common_metadata["base_persona_key"] = base_key

        providers = p.get("providers") or {}
        for provider_name, provider_value in providers.items():
            try:
                tts_config = resolve_provider_config(provider_name, provider_value, models)
            except ValueError as e:
                print(f"[error] {e}", file=sys.stderr)
                continue

            upsert_persona_row(
                engine,
                name=p["name"],
                description=p.get("description"),
                aggression=float(p["aggression"]),
                patience=float(p["patience"]),
                verbosity=float(p["verbosity"]),
                traits=p.get("traits") or [],
                tts_provider=provider_name,
                tts_config=tts_config,
                preview_audio_text=p.get("preview_audio_text"),
                metadata=common_metadata,
                created_by="system",
            )
            total += 1

    print(f"[ok] Seeded/updated {total} persona provider-variants.")
    print(
        "[note] preview_audio_url is not generated here. "
        "Run your separate preview generation job to fill it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
