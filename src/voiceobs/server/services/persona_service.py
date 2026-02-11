"""Persona service for organization-scoped persona operations."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from voiceobs.server.db.repositories.persona import PersonaRepository

logger = logging.getLogger(__name__)

# Path to the seed catalog
CATALOG_PATH = Path(__file__).parent.parent / "seed" / "personas_catalog_v0_1.json"
MODELS_PATH = Path(__file__).parent.parent / "seed" / "tts_provider_models.json"

# The first persona in the catalog is the default
DEFAULT_PERSONA_INDEX = 0


class PersonaService:
    """Service for persona business logic."""

    def __init__(self, persona_repo: PersonaRepository) -> None:
        """Initialize the persona service.

        Args:
            persona_repo: Persona repository instance.
        """
        self._persona_repo = persona_repo

    async def seed_org_personas(self, org_id: UUID) -> None:
        """Seed system personas for a new organization.

        Reads the persona catalog and creates system personas for the org.
        The first persona in the catalog is set as the default.

        Args:
            org_id: The organization UUID to seed personas for.
        """
        catalog = self._load_catalog()
        models = self._load_models()
        personas: list[dict[str, Any]] = catalog.get("personas", []) or []

        for idx, persona_data in enumerate(personas):
            tts_provider, tts_config = self._resolve_tts(persona_data, models)

            name = persona_data.get("name", "")
            description = persona_data.get("description")
            traits_raw = persona_data.get("traits", [])
            traits: list[str] = (
                [x for x in traits_raw if isinstance(x, str)]
                if isinstance(traits_raw, list)
                else []
            )
            metadata_raw = persona_data.get("metadata", {})
            metadata: dict[str, Any] = metadata_raw if isinstance(metadata_raw, dict) else {}

            await self._persona_repo.create(
                org_id=org_id,
                persona_type="system",
                name=name,
                description=description,
                aggression=float(persona_data["aggression"]),
                patience=float(persona_data["patience"]),
                verbosity=float(persona_data["verbosity"]),
                traits=traits,
                tts_provider=tts_provider,
                tts_config=tts_config,
                preview_audio_text=persona_data.get("preview_audio_text"),
                metadata=metadata,
                created_by=None,
                is_default=(idx == DEFAULT_PERSONA_INDEX),
            )

    def _load_catalog(self) -> dict[str, Any]:
        """Load persona catalog from JSON file.

        Returns:
            The parsed catalog dictionary.
        """
        with open(CATALOG_PATH, encoding="utf-8") as f:
            return json.load(f)

    def _load_models(self) -> dict[str, Any]:
        """Load TTS provider models from JSON file.

        Returns:
            The models dictionary, or empty dict if file not found.
        """
        try:
            with open(MODELS_PATH, encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)
                return data.get("models", {}) or {}
        except FileNotFoundError:
            return {}

    def _resolve_tts(
        self, persona_data: dict[str, Any], models: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Resolve TTS provider and config from persona data.

        Takes the first provider entry from the persona's providers dict
        and looks up the model reference in the models dictionary.

        Args:
            persona_data: Persona entry from the catalog.
            models: TTS models dictionary keyed by provider name.

        Returns:
            Tuple of (tts_provider, tts_config).
        """
        providers_raw = persona_data.get("providers", {})
        if not isinstance(providers_raw, dict) or not providers_raw:
            return ("openai", {})

        # Take the first provider (cast for Pylance: providers is dict[str, Any])
        providers = cast(dict[str, Any], providers_raw)
        provider_name, provider_value = next(iter(providers.items()))

        # Resolve model reference (string key -> look up in models dict)
        if isinstance(provider_value, str):
            provider_models = models.get(provider_name, {}) or {}
            model_config = (
                provider_models.get(provider_value) if isinstance(provider_models, dict) else None
            )
            if isinstance(model_config, dict):
                return (provider_name, dict(model_config))

        # Direct config dict
        if isinstance(provider_value, dict):
            return (provider_name, dict(provider_value))

        return (provider_name, {})
