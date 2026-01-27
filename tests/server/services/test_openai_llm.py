"""Tests for OpenAI LLM service."""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from voiceobs.server.services.openai_llm import OpenAILLMService


class TestOutputSchema(BaseModel):
    """Test output schema for structured output."""

    result: str = "test"


class TestOpenAILLMService:
    """Tests for OpenAILLMService."""

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("voiceobs.server.services.openai_llm.LLM_AVAILABLE", True)
    def test_init_with_api_key(self):
        """Should initialize when API key is present."""
        service = OpenAILLMService()
        assert service._api_key == "test-key"

    @patch.dict(os.environ, {}, clear=True)
    @patch("voiceobs.server.services.openai_llm.LLM_AVAILABLE", True)
    def test_init_without_api_key_raises(self):
        """Should raise ValueError when API key is missing."""
        os.environ.pop("OPENAI_API_KEY", None)
        with pytest.raises(ValueError) as exc_info:
            OpenAILLMService()
        assert "OPENAI_API_KEY environment variable is required" in str(exc_info.value)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("voiceobs.server.services.openai_llm.LLM_AVAILABLE", False)
    def test_init_without_llm_available_raises(self):
        """Should raise ValueError when LLM dependencies not available."""
        with pytest.raises(ValueError) as exc_info:
            OpenAILLMService()
        assert "LLM dependencies not available" in str(exc_info.value)

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("voiceobs.server.services.openai_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.openai_llm.get_provider")
    @patch("voiceobs.server.services.openai_llm.EvalConfig")
    def test_get_structured_llm(self, mock_eval_config, mock_get_provider):
        """Should create structured LLM with correct configuration."""
        mock_provider = MagicMock()
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_config = MagicMock()
        mock_config.provider = "openai"
        mock_eval_config.return_value = mock_config
        mock_get_provider.return_value = mock_provider
        mock_provider.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm

        service = OpenAILLMService()
        result = service._get_structured_llm(TestOutputSchema, temperature=0.5)

        mock_eval_config.assert_called_once_with(
            provider="openai",
            temperature=0.5,
            api_key="test-key",
        )
        # get_provider is called with config.provider
        mock_get_provider.assert_called_once_with("openai")
        mock_llm.with_structured_output.assert_called_once_with(TestOutputSchema)
        assert result is mock_structured_llm

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("voiceobs.server.services.openai_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.openai_llm.get_provider")
    @patch("voiceobs.server.services.openai_llm.EvalConfig")
    async def test_generate_structured(self, mock_eval_config, mock_get_provider):
        """Should generate structured output from prompt."""
        mock_provider = MagicMock()
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        expected_output = TestOutputSchema(result="generated")

        mock_get_provider.return_value = mock_provider
        mock_provider.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = expected_output

        service = OpenAILLMService()
        result = await service.generate_structured(
            prompt="test prompt",
            output_schema=TestOutputSchema,
            temperature=0.8,
        )

        assert result is expected_output
        mock_structured_llm.invoke.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("voiceobs.server.services.openai_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.openai_llm.get_provider")
    @patch("voiceobs.server.services.openai_llm.EvalConfig")
    async def test_generate_structured_uses_default_temperature(
        self, mock_eval_config, mock_get_provider
    ):
        """Should use default temperature of 0.7 when not specified."""
        mock_provider = MagicMock()
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_get_provider.return_value = mock_provider
        mock_provider.create_llm.return_value = mock_llm
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_structured_llm.invoke.return_value = TestOutputSchema()

        service = OpenAILLMService()
        await service.generate_structured(
            prompt="test prompt",
            output_schema=TestOutputSchema,
        )

        # Check that EvalConfig was called with default temperature
        mock_eval_config.assert_called_once_with(
            provider="openai",
            temperature=0.7,
            api_key="test-key",
        )
