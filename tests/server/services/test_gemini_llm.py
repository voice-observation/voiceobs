"""Tests for the GeminiLLMService class."""

import os
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from voiceobs.server.services.gemini_llm import GeminiLLMService


class TestOutput(BaseModel):
    """Test output schema."""

    name: str
    value: int


class TestGeminiLLMService:
    """Tests for the GeminiLLMService class."""

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("voiceobs.server.services.gemini_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.gemini_llm.get_provider")
    def test_init_success(self, mock_get_provider):
        """Test successful initialization."""
        service = GeminiLLMService()

        assert service._api_key == "test-key"

    @patch.dict(os.environ, {}, clear=True)
    @patch("voiceobs.server.services.gemini_llm.LLM_AVAILABLE", True)
    def test_init_missing_api_key(self):
        """Test initialization fails without API key."""
        with pytest.raises(ValueError, match="GOOGLE_API_KEY environment variable is required"):
            GeminiLLMService()

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("voiceobs.server.services.gemini_llm.LLM_AVAILABLE", False)
    def test_init_llm_not_available(self):
        """Test initialization fails when LLM dependencies not available."""
        with pytest.raises(ValueError, match="LLM dependencies not available"):
            GeminiLLMService()

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("voiceobs.server.services.gemini_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.gemini_llm.get_provider")
    @patch("voiceobs.server.services.gemini_llm.EvalConfig")
    def test_get_structured_llm(self, mock_eval_config, mock_get_provider):
        """Test _get_structured_llm creates correct LLM instance."""
        service = GeminiLLMService()

        # Mock provider and LLM
        mock_provider = MagicMock()
        mock_llm = MagicMock()
        mock_structured_llm = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured_llm
        mock_provider.create_llm.return_value = mock_llm
        mock_get_provider.return_value = mock_provider

        # Mock EvalConfig to return an object with provider attribute
        mock_config = MagicMock()
        mock_config.provider = "gemini"
        mock_eval_config.return_value = mock_config

        result = service._get_structured_llm(TestOutput, temperature=0.8)

        # Verify EvalConfig was created with correct params
        mock_eval_config.assert_called_once_with(
            provider="gemini",
            temperature=0.8,
            api_key="test-key",
        )

        # Verify provider was retrieved and LLM created
        mock_get_provider.assert_called_once()
        mock_provider.create_llm.assert_called_once()
        mock_llm.with_structured_output.assert_called_once_with(TestOutput)

        assert result == mock_structured_llm

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("voiceobs.server.services.gemini_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.gemini_llm.get_provider")
    async def test_generate_structured(self, mock_get_provider):
        """Test generate_structured calls LLM and returns result."""
        service = GeminiLLMService()

        # Mock the structured LLM
        mock_structured_llm = MagicMock()
        expected_output = TestOutput(name="test", value=42)
        mock_structured_llm.invoke.return_value = expected_output

        # Mock _get_structured_llm to return our mock
        with patch.object(service, "_get_structured_llm", return_value=mock_structured_llm):
            result = await service.generate_structured(
                prompt="Test prompt", output_schema=TestOutput, temperature=0.7
            )

        assert result == expected_output
        mock_structured_llm.invoke.assert_called_once_with("Test prompt")

    @pytest.mark.asyncio
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch("voiceobs.server.services.gemini_llm.LLM_AVAILABLE", True)
    @patch("voiceobs.server.services.gemini_llm.get_provider")
    async def test_generate_structured_custom_temperature(self, mock_get_provider):
        """Test generate_structured with custom temperature."""
        service = GeminiLLMService()

        mock_structured_llm = MagicMock()
        expected_output = TestOutput(name="test", value=42)
        mock_structured_llm.invoke.return_value = expected_output

        with patch.object(
            service, "_get_structured_llm", return_value=mock_structured_llm
        ) as mock_get:
            result = await service.generate_structured(
                prompt="Test prompt", output_schema=TestOutput, temperature=0.9
            )

        # Verify temperature was passed to _get_structured_llm
        mock_get.assert_called_once_with(TestOutput, 0.9)
        assert result == expected_output
