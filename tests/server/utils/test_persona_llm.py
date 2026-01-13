"""Tests for persona_llm module."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import AsyncMock, patch

import pytest

from voiceobs.server.utils.persona_llm import (
    PersonaAttributesOutput,
    generate_persona_attributes_with_llm,
)


class TestPersonaAttributesOutput:
    """Tests for PersonaAttributesOutput model."""

    def test_valid_output(self):
        """Test creating valid PersonaAttributesOutput."""
        output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.7,
            verbosity=0.3,
            tts_provider="openai",
            tts_model_key="tts-1",
        )

        assert output.aggression == 0.5
        assert output.patience == 0.7
        assert output.verbosity == 0.3
        assert output.tts_provider == "openai"
        assert output.tts_model_key == "tts-1"

    def test_aggression_bounds(self):
        """Test aggression must be between 0 and 1."""
        # Valid
        PersonaAttributesOutput(
            aggression=0.0,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="tts-1",
        )
        PersonaAttributesOutput(
            aggression=1.0,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="tts-1",
        )

        # Invalid
        with pytest.raises(Exception):  # Pydantic validation error
            PersonaAttributesOutput(
                aggression=-0.1,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
                tts_model_key="tts-1",
            )

        with pytest.raises(Exception):
            PersonaAttributesOutput(
                aggression=1.1,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
                tts_model_key="tts-1",
            )


class TestGeneratePersonaAttributesWithLLM:
    """Tests for generate_persona_attributes_with_llm function."""

    @pytest.fixture
    def mock_models_file(self):
        """Create a temporary models JSON file."""
        models_data = {
            "models": {
                "openai": {
                    "tts-1": {"model": "tts-1", "voice": "alloy", "speed": 1.0},
                    "tts-1-hd": {"model": "tts-1-hd", "voice": "alloy", "speed": 1.0},
                },
                "elevenlabs": {
                    "eleven_multilingual_v2": {
                        "voice_id": "test-voice",
                        "model_id": "eleven_multilingual_v2",
                    }
                },
            }
        }

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(models_data, f)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        temp_path.unlink()

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_success(self, mock_factory, mock_models_file):
        """Test successful persona attribute generation."""
        # Mock LLM service
        mock_llm_service = AsyncMock()
        mock_output = PersonaAttributesOutput(
            aggression=0.8,
            patience=0.2,
            verbosity=0.6,
            tts_provider="openai",
            tts_model_key="tts-1",
        )
        mock_llm_service.generate_structured.return_value = mock_output
        mock_factory.create.return_value = mock_llm_service

        result = await generate_persona_attributes_with_llm(
            name="Angry Customer", description="Very aggressive", models_path=mock_models_file
        )

        assert result[0] == 0.8  # aggression
        assert result[1] == 0.2  # patience
        assert result[2] == 0.6  # verbosity
        assert result[3] == "openai"  # tts_provider
        assert result[4] == {"model": "tts-1", "voice": "alloy", "speed": 1.0}  # tts_config

        # Verify LLM was called with correct prompt
        mock_llm_service.generate_structured.assert_called_once()
        call_args = mock_llm_service.generate_structured.call_args
        assert "Angry Customer" in call_args.kwargs["prompt"]
        assert "Very aggressive" in call_args.kwargs["prompt"]

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_with_none_description(self, mock_factory, mock_models_file):
        """Test generation with None description."""
        mock_llm_service = AsyncMock()
        mock_output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="tts-1",
        )
        mock_llm_service.generate_structured.return_value = mock_output
        mock_factory.create.return_value = mock_llm_service

        result = await generate_persona_attributes_with_llm(
            name="Test Persona", description=None, models_path=mock_models_file
        )

        assert result[0] == 0.5
        # Verify prompt includes "No description provided"
        call_args = mock_llm_service.generate_structured.call_args
        assert "No description provided" in call_args.kwargs["prompt"]

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", False)
    async def test_generate_attributes_llm_not_available(self, mock_models_file):
        """Test generation fails when LLM dependencies not available."""
        with pytest.raises(ValueError, match="LLM dependencies not available"):
            await generate_persona_attributes_with_llm(
                name="Test", description="Test", models_path=mock_models_file
            )

    @pytest.mark.asyncio
    async def test_generate_attributes_file_not_found(self):
        """Test generation fails when models file not found."""
        non_existent_path = Path("/nonexistent/path/models.json")

        with pytest.raises(ValueError, match="TTS models file not found"):
            await generate_persona_attributes_with_llm(
                name="Test", description="Test", models_path=non_existent_path
            )

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_fallback_to_first_model(
        self, mock_factory, mock_models_file
    ):
        """Test fallback to first model when selected model not found."""
        mock_llm_service = AsyncMock()
        # LLM returns a model key that doesn't exist
        mock_output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="nonexistent-model",
        )
        mock_llm_service.generate_structured.return_value = mock_output
        mock_factory.create.return_value = mock_llm_service

        result = await generate_persona_attributes_with_llm(
            name="Test", description="Test", models_path=mock_models_file
        )

        # Should fallback to first available model (tts-1)
        assert result[3] == "openai"
        assert result[4] == {"model": "tts-1", "voice": "alloy", "speed": 1.0}

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_provider_no_models(self, mock_factory):
        """Test generation fails when provider has no models."""
        # Create models file with empty provider
        models_data = {"models": {"openai": {}}}
        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(models_data, f)
            temp_path = Path(f.name)

        try:
            mock_llm_service = AsyncMock()
            mock_output = PersonaAttributesOutput(
                aggression=0.5,
                patience=0.5,
                verbosity=0.5,
                tts_provider="openai",
                tts_model_key="tts-1",
            )
            mock_llm_service.generate_structured.return_value = mock_output
            mock_factory.create.return_value = mock_llm_service

            with pytest.raises(ValueError, match="No models available for provider"):
                await generate_persona_attributes_with_llm(
                    name="Test", description="Test", models_path=temp_path
                )
        finally:
            temp_path.unlink()

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_llm_exception(self, mock_factory, mock_models_file):
        """Test generation handles LLM exceptions."""
        mock_llm_service = AsyncMock()
        mock_llm_service.generate_structured.side_effect = Exception("LLM error")
        mock_factory.create.return_value = mock_llm_service

        with pytest.raises(ValueError, match="Failed to generate persona attributes with LLM"):
            await generate_persona_attributes_with_llm(
                name="Test", description="Test", models_path=mock_models_file
            )

    @pytest.mark.asyncio
    @patch("voiceobs.server.utils.persona_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.utils.persona_llm.LLMServiceFactory")
    async def test_generate_attributes_uses_correct_temperature(
        self, mock_factory, mock_models_file
    ):
        """Test generation uses correct temperature."""
        mock_llm_service = AsyncMock()
        mock_output = PersonaAttributesOutput(
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            tts_model_key="tts-1",
        )
        mock_llm_service.generate_structured.return_value = mock_output
        mock_factory.create.return_value = mock_llm_service

        await generate_persona_attributes_with_llm(
            name="Test", description="Test", models_path=mock_models_file
        )

        # Verify temperature is 0.7
        call_args = mock_llm_service.generate_structured.call_args
        assert call_args.kwargs["temperature"] == 0.7
