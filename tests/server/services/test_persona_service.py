"""Tests for PersonaService."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from voiceobs.server.services.persona_service import PersonaService


class TestPersonaServiceSeedOrgPersonas:
    """Tests for seeding system personas on org creation."""

    @pytest.fixture
    def mock_persona_repo(self):
        """Create a mock persona repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_persona_repo):
        """Create a PersonaService instance with mocked repo."""
        return PersonaService(persona_repo=mock_persona_repo)

    @pytest.fixture
    def catalog_path(self):
        """Path to the personas catalog JSON file."""
        return (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "voiceobs"
            / "server"
            / "seed"
            / "personas_catalog_v0_1.json"
        )

    @pytest.fixture
    def models_path(self):
        """Path to the TTS provider models JSON file."""
        return (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "voiceobs"
            / "server"
            / "seed"
            / "tts_provider_models.json"
        )

    @pytest.mark.asyncio
    async def test_seed_org_personas_creates_personas_from_catalog(
        self, service, mock_persona_repo, catalog_path
    ):
        """seed_org_personas creates one persona per catalog entry."""
        org_id = uuid4()

        # Load actual catalog to know expected count
        with open(catalog_path) as f:
            catalog = json.load(f)
        expected_count = len(catalog["personas"])

        await service.seed_org_personas(org_id)

        assert mock_persona_repo.create.call_count == expected_count

    @pytest.mark.asyncio
    async def test_seed_org_personas_sets_persona_type_system(self, service, mock_persona_repo):
        """All seeded personas have persona_type='system'."""
        org_id = uuid4()

        await service.seed_org_personas(org_id)

        for call in mock_persona_repo.create.call_args_list:
            assert call.kwargs["persona_type"] == "system"

    @pytest.mark.asyncio
    async def test_seed_org_personas_sets_org_id(self, service, mock_persona_repo):
        """All seeded personas have the correct org_id."""
        org_id = uuid4()

        await service.seed_org_personas(org_id)

        for call in mock_persona_repo.create.call_args_list:
            assert call.kwargs["org_id"] == org_id

    @pytest.mark.asyncio
    async def test_seed_org_personas_sets_one_default(self, service, mock_persona_repo):
        """Exactly one seeded persona has is_default=True."""
        org_id = uuid4()

        await service.seed_org_personas(org_id)

        defaults = [
            call
            for call in mock_persona_repo.create.call_args_list
            if call.kwargs.get("is_default") is True
        ]
        assert len(defaults) == 1

    @pytest.mark.asyncio
    async def test_seed_org_personas_passes_name(self, service, mock_persona_repo, catalog_path):
        """Seeded personas have names from the catalog."""
        org_id = uuid4()

        with open(catalog_path) as f:
            catalog = json.load(f)
        expected_names = [p["name"] for p in catalog["personas"]]

        await service.seed_org_personas(org_id)

        actual_names = [call.kwargs["name"] for call in mock_persona_repo.create.call_args_list]
        assert actual_names == expected_names

    @pytest.mark.asyncio
    async def test_seed_org_personas_passes_numeric_fields(
        self, service, mock_persona_repo, catalog_path
    ):
        """Seeded personas have correct aggression, patience, verbosity from catalog."""
        org_id = uuid4()

        with open(catalog_path) as f:
            catalog = json.load(f)

        await service.seed_org_personas(org_id)

        for idx, call in enumerate(mock_persona_repo.create.call_args_list):
            persona_data = catalog["personas"][idx]
            assert call.kwargs["aggression"] == float(persona_data["aggression"])
            assert call.kwargs["patience"] == float(persona_data["patience"])
            assert call.kwargs["verbosity"] == float(persona_data["verbosity"])

    @pytest.mark.asyncio
    async def test_seed_org_personas_resolves_tts_provider(self, service, mock_persona_repo):
        """Seeded personas resolve TTS provider from the providers dict."""
        org_id = uuid4()

        await service.seed_org_personas(org_id)

        # All catalog personas use elevenlabs
        for call in mock_persona_repo.create.call_args_list:
            assert call.kwargs["tts_provider"] == "elevenlabs"

    @pytest.mark.asyncio
    async def test_seed_org_personas_resolves_tts_config(
        self, service, mock_persona_repo, models_path
    ):
        """Seeded personas resolve TTS config from the models file."""
        org_id = uuid4()

        with open(models_path) as f:
            models_data = json.load(f)

        await service.seed_org_personas(org_id)

        # First persona uses daniel_turbo (Polite customer)
        first_call = mock_persona_repo.create.call_args_list[0]
        expected_config = models_data["models"]["elevenlabs"]["daniel_turbo"]
        assert first_call.kwargs["tts_config"] == expected_config

    @pytest.mark.asyncio
    async def test_seed_org_personas_sets_created_by_none(self, service, mock_persona_repo):
        """System-seeded personas have created_by=None."""
        org_id = uuid4()

        await service.seed_org_personas(org_id)

        for call in mock_persona_repo.create.call_args_list:
            assert call.kwargs["created_by"] is None

    @pytest.mark.asyncio
    async def test_seed_org_personas_passes_traits(self, service, mock_persona_repo, catalog_path):
        """Seeded personas have traits from the catalog."""
        org_id = uuid4()

        with open(catalog_path) as f:
            catalog = json.load(f)

        await service.seed_org_personas(org_id)

        for idx, call in enumerate(mock_persona_repo.create.call_args_list):
            persona_data = catalog["personas"][idx]
            assert call.kwargs["traits"] == persona_data.get("traits", [])

    @pytest.mark.asyncio
    async def test_seed_org_personas_passes_description(
        self, service, mock_persona_repo, catalog_path
    ):
        """Seeded personas have descriptions from the catalog."""
        org_id = uuid4()

        with open(catalog_path) as f:
            catalog = json.load(f)

        await service.seed_org_personas(org_id)

        for idx, call in enumerate(mock_persona_repo.create.call_args_list):
            persona_data = catalog["personas"][idx]
            assert call.kwargs["description"] == persona_data.get("description")

    @pytest.mark.asyncio
    async def test_seed_org_personas_passes_preview_audio_text(
        self, service, mock_persona_repo, catalog_path
    ):
        """Seeded personas have preview_audio_text from the catalog."""
        org_id = uuid4()

        with open(catalog_path) as f:
            catalog = json.load(f)

        await service.seed_org_personas(org_id)

        for idx, call in enumerate(mock_persona_repo.create.call_args_list):
            persona_data = catalog["personas"][idx]
            assert call.kwargs["preview_audio_text"] == persona_data.get("preview_audio_text")

    @pytest.mark.asyncio
    async def test_seed_org_personas_passes_metadata(
        self, service, mock_persona_repo, catalog_path
    ):
        """Seeded personas have metadata from the catalog."""
        org_id = uuid4()

        with open(catalog_path) as f:
            catalog = json.load(f)

        await service.seed_org_personas(org_id)

        for idx, call in enumerate(mock_persona_repo.create.call_args_list):
            persona_data = catalog["personas"][idx]
            assert call.kwargs["metadata"] == persona_data.get("metadata", {})

    @pytest.mark.asyncio
    async def test_seed_org_personas_default_is_first_persona(self, service, mock_persona_repo):
        """The first persona in the catalog is the default."""
        org_id = uuid4()

        await service.seed_org_personas(org_id)

        first_call = mock_persona_repo.create.call_args_list[0]
        assert first_call.kwargs["is_default"] is True

        # All others should not be default
        for call in mock_persona_repo.create.call_args_list[1:]:
            assert call.kwargs["is_default"] is False

    @pytest.mark.asyncio
    async def test_seed_org_personas_with_missing_models_file(self, mock_persona_repo):
        """seed_org_personas works even if TTS models file is missing."""
        service = PersonaService(persona_repo=mock_persona_repo)
        org_id = uuid4()

        with patch.object(
            PersonaService,
            "_load_models",
            return_value={},
        ):
            await service.seed_org_personas(org_id)

        # Should still create personas, but with empty tts_config
        assert mock_persona_repo.create.call_count > 0
        for call in mock_persona_repo.create.call_args_list:
            # Provider is set but config might be empty if models can't resolve
            assert "tts_provider" in call.kwargs

    @pytest.mark.asyncio
    async def test_seed_org_personas_with_no_providers_in_persona(self, mock_persona_repo):
        """Persona with no providers gets default openai provider."""
        service = PersonaService(persona_repo=mock_persona_repo)
        org_id = uuid4()

        catalog_no_providers = {
            "personas": [
                {
                    "name": "Test Persona",
                    "description": "A test persona",
                    "aggression": 0.5,
                    "patience": 0.5,
                    "verbosity": 0.5,
                    "traits": [],
                    "metadata": {},
                }
            ]
        }

        with patch.object(
            PersonaService,
            "_load_catalog",
            return_value=catalog_no_providers,
        ):
            await service.seed_org_personas(org_id)

        call = mock_persona_repo.create.call_args_list[0]
        assert call.kwargs["tts_provider"] == "openai"
        assert call.kwargs["tts_config"] == {}


class TestPersonaServiceLoadModels:
    """Tests for _load_models edge cases."""

    def test_load_models_returns_empty_dict_on_file_not_found(self):
        """_load_models returns empty dict when the models file is missing."""
        service = PersonaService(persona_repo=AsyncMock())

        with patch(
            "voiceobs.server.services.persona_service.MODELS_PATH",
            Path("/nonexistent/path/models.json"),
        ):
            result = service._load_models()

        assert result == {}


class TestPersonaServiceResolveTts:
    """Tests for _resolve_tts edge cases."""

    def test_resolve_tts_with_direct_config_dict(self):
        """_resolve_tts handles direct config dict in providers."""
        service = PersonaService(persona_repo=AsyncMock())
        persona_data = {"providers": {"openai": {"model": "tts-1", "voice": "alloy", "speed": 1.0}}}
        models = {}

        provider, config = service._resolve_tts(persona_data, models)

        assert provider == "openai"
        assert config == {"model": "tts-1", "voice": "alloy", "speed": 1.0}

    def test_resolve_tts_with_unresolved_string_reference(self):
        """_resolve_tts returns empty config for unresolved model reference."""
        service = PersonaService(persona_repo=AsyncMock())
        persona_data = {"providers": {"elevenlabs": "nonexistent_model_key"}}
        models = {"elevenlabs": {"some_other_key": {"voice_id": "abc"}}}

        provider, config = service._resolve_tts(persona_data, models)

        assert provider == "elevenlabs"
        assert config == {}

    def test_resolve_tts_with_empty_providers(self):
        """_resolve_tts defaults to openai when providers is empty."""
        service = PersonaService(persona_repo=AsyncMock())
        persona_data = {"providers": {}}
        models = {}

        provider, config = service._resolve_tts(persona_data, models)

        assert provider == "openai"
        assert config == {}

    def test_resolve_tts_with_no_providers_key(self):
        """_resolve_tts defaults to openai when providers key is absent."""
        service = PersonaService(persona_repo=AsyncMock())
        persona_data = {}
        models = {}

        provider, config = service._resolve_tts(persona_data, models)

        assert provider == "openai"
        assert config == {}
