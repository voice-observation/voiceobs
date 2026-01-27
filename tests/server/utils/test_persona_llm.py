"""Tests for persona LLM utilities."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voiceobs.server.utils.persona_llm import PersonaAttributesOutput


class TestPersonaAttributesOutput:
    """Tests for PersonaAttributesOutput model."""

    def test_valid_output(self):
        """Should accept valid persona attributes."""
        output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.7,
            verbosity=0.3,
            tts_provider="openai",
            tts_model_key="alloy",
        )
        assert output.aggression == 0.5
        assert output.patience == 0.7
        assert output.verbosity == 0.3
        assert output.tts_provider == "openai"
        assert output.tts_model_key == "alloy"

    def test_boundary_values(self):
        """Should accept boundary values (0.0 and 1.0)."""
        output = PersonaAttributesOutput(
            aggression=0.0,
            patience=1.0,
            verbosity=0.0,
            tts_provider="elevenlabs",
            tts_model_key="rachel",
        )
        assert output.aggression == 0.0
        assert output.patience == 1.0

    def test_rejects_values_above_one(self):
        """Should reject aggression/patience/verbosity above 1.0."""
        with pytest.raises(ValueError):
            PersonaAttributesOutput(
                aggression=1.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
                tts_model_key="alloy",
            )

    def test_rejects_negative_values(self):
        """Should reject negative aggression/patience/verbosity."""
        with pytest.raises(ValueError):
            PersonaAttributesOutput(
                aggression=-0.1,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
                tts_model_key="alloy",
            )


class TestGeneratePersonaAttributesWithLLM:
    """Tests for generate_persona_attributes_with_llm function."""

    @pytest.fixture
    def temp_models_file(self, tmp_path):
        """Create a temporary models file."""
        models_data = {
            "models": {
                "openai": {
                    "alloy": {"voice": "alloy", "model": "tts-1"},
                    "echo": {"voice": "echo", "model": "tts-1"},
                },
                "elevenlabs": {
                    "rachel": {"voice_id": "21m00Tcm4TlvDq8ikWAM"},
                },
                "deepgram": {
                    "aura": {"model": "aura-asteria-en"},
                },
            }
        }
        models_file = tmp_path / "tts_models.json"
        models_file.write_text(json.dumps(models_data))
        return models_file

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_success(self, mock_factory, temp_models_file):
        """Should generate persona attributes successfully."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        mock_service = MagicMock()
        mock_output = PersonaAttributesOutput(
            aggression=0.6,
            patience=0.4,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="alloy",
        )
        mock_service.generate_structured = AsyncMock(return_value=mock_output)
        mock_factory.create.return_value = mock_service

        result = await generate_persona_attributes_with_llm(
            name="Angry Customer",
            description="A frustrated customer who is impatient",
            models_path=temp_models_file,
        )

        aggression, patience, verbosity, provider, tts_config = result
        assert aggression == 0.6
        assert patience == 0.4
        assert verbosity == 0.5
        assert provider == "openai"
        assert tts_config == {"voice": "alloy", "model": "tts-1"}

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_with_no_description(self, mock_factory, temp_models_file):
        """Should handle None description."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        mock_service = MagicMock()
        mock_output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="elevenlabs",
            tts_model_key="rachel",
        )
        mock_service.generate_structured = AsyncMock(return_value=mock_output)
        mock_factory.create.return_value = mock_service

        result = await generate_persona_attributes_with_llm(
            name="Default Persona",
            description=None,
            models_path=temp_models_file,
        )

        assert result[3] == "elevenlabs"

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", False)
    async def test_raises_when_llm_not_available(self, temp_models_file):
        """Should raise ValueError when LLM is not available."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        with pytest.raises(ValueError, match="LLM dependencies not available"):
            await generate_persona_attributes_with_llm(
                name="Test",
                description="Test",
                models_path=temp_models_file,
            )

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    async def test_raises_when_models_file_not_found(self, tmp_path):
        """Should raise ValueError when models file is not found."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        non_existent_path = tmp_path / "non_existent.json"

        with pytest.raises(ValueError, match="TTS models file not found"):
            await generate_persona_attributes_with_llm(
                name="Test",
                description="Test",
                models_path=non_existent_path,
            )

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_fallback_when_model_not_found(self, mock_factory, temp_models_file):
        """Should fallback to first model when selected model not found."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        mock_service = MagicMock()
        # LLM returns a model key that doesn't exist
        mock_output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="non_existent_model",
        )
        mock_service.generate_structured = AsyncMock(return_value=mock_output)
        mock_factory.create.return_value = mock_service

        result = await generate_persona_attributes_with_llm(
            name="Test",
            description="Test",
            models_path=temp_models_file,
        )

        # Should fallback to first available model for openai
        assert result[4] == {"voice": "alloy", "model": "tts-1"}

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_raises_when_provider_has_no_models(self, mock_factory, tmp_path):
        """Should raise ValueError when provider has no models."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        # Create models file with empty provider
        models_data = {"models": {"openai": {}}}
        models_file = tmp_path / "empty_models.json"
        models_file.write_text(json.dumps(models_data))

        mock_service = MagicMock()
        mock_output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="alloy",
        )
        mock_service.generate_structured = AsyncMock(return_value=mock_output)
        mock_factory.create.return_value = mock_service

        with pytest.raises(ValueError, match="No models available for provider"):
            await generate_persona_attributes_with_llm(
                name="Test",
                description="Test",
                models_path=models_file,
            )

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_wraps_llm_errors(self, mock_factory, temp_models_file):
        """Should wrap LLM errors in ValueError."""
        from voiceobs.server.utils.persona_llm import generate_persona_attributes_with_llm

        mock_service = MagicMock()
        mock_service.generate_structured = AsyncMock(side_effect=Exception("LLM API Error"))
        mock_factory.create.return_value = mock_service

        with pytest.raises(ValueError, match="Failed to generate persona attributes"):
            await generate_persona_attributes_with_llm(
                name="Test",
                description="Test",
                models_path=temp_models_file,
            )
