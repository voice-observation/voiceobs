"""Tests for the semantic evaluation module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from voiceobs.eval.types import EvalConfig, EvalInput, EvalResult


class TestEvalInput:
    """Tests for EvalInput dataclass."""

    def test_create_basic_input(self) -> None:
        """Should create input with required fields."""
        inp = EvalInput(
            user_transcript="What's the weather?",
            agent_response="It's sunny and 72 degrees.",
        )
        assert inp.user_transcript == "What's the weather?"
        assert inp.agent_response == "It's sunny and 72 degrees."
        assert inp.expected_intent is None
        assert inp.conversation_context is None

    def test_create_input_with_optional_fields(self) -> None:
        """Should create input with all optional fields."""
        inp = EvalInput(
            user_transcript="What's the weather?",
            agent_response="It's sunny and 72 degrees.",
            expected_intent="get_weather",
            conversation_context="User is planning outdoor activities.",
            conversation_id="conv-123",
            turn_id="turn-456",
        )
        assert inp.expected_intent == "get_weather"
        assert inp.conversation_context == "User is planning outdoor activities."
        assert inp.conversation_id == "conv-123"
        assert inp.turn_id == "turn-456"

    def test_content_hash_deterministic(self) -> None:
        """Content hash should be deterministic for same content."""
        inp1 = EvalInput(
            user_transcript="Hello",
            agent_response="Hi there!",
        )
        inp2 = EvalInput(
            user_transcript="Hello",
            agent_response="Hi there!",
        )
        assert inp1.content_hash() == inp2.content_hash()

    def test_content_hash_different_for_different_content(self) -> None:
        """Content hash should differ for different content."""
        inp1 = EvalInput(
            user_transcript="Hello",
            agent_response="Hi there!",
        )
        inp2 = EvalInput(
            user_transcript="Hello",
            agent_response="Goodbye!",
        )
        assert inp1.content_hash() != inp2.content_hash()

    def test_content_hash_ignores_ids(self) -> None:
        """Content hash should ignore conversation_id and turn_id."""
        inp1 = EvalInput(
            user_transcript="Hello",
            agent_response="Hi there!",
            conversation_id="conv-1",
            turn_id="turn-1",
        )
        inp2 = EvalInput(
            user_transcript="Hello",
            agent_response="Hi there!",
            conversation_id="conv-2",
            turn_id="turn-2",
        )
        assert inp1.content_hash() == inp2.content_hash()


class TestEvalResult:
    """Tests for EvalResult dataclass."""

    def test_create_result(self) -> None:
        """Should create result with all fields."""
        result = EvalResult(
            intent_correct=True,
            relevance_score=0.85,
            explanation="Good response.",
            conversation_id="conv-1",
            turn_id="turn-1",
            content_hash="abc123",
            cached=False,
        )
        assert result.intent_correct is True
        assert result.relevance_score == 0.85
        assert result.explanation == "Good response."

    def test_passed_property(self) -> None:
        """passed should be True when intent correct and relevance >= 0.5."""
        result_pass = EvalResult(
            intent_correct=True,
            relevance_score=0.7,
            explanation="Good.",
        )
        assert result_pass.passed is True

        result_fail_intent = EvalResult(
            intent_correct=False,
            relevance_score=0.9,
            explanation="Wrong intent.",
        )
        assert result_fail_intent.passed is False

        result_fail_relevance = EvalResult(
            intent_correct=True,
            relevance_score=0.4,
            explanation="Low relevance.",
        )
        assert result_fail_relevance.passed is False

    def test_to_dict(self) -> None:
        """to_dict should serialize all fields."""
        result = EvalResult(
            intent_correct=True,
            relevance_score=0.85,
            explanation="Good response.",
            conversation_id="conv-1",
            turn_id="turn-1",
            content_hash="abc123",
            cached=True,
        )
        d = result.to_dict()
        assert d["intent_correct"] is True
        assert d["relevance_score"] == 0.85
        assert d["explanation"] == "Good response."
        assert d["conversation_id"] == "conv-1"
        assert d["cached"] is True


class TestEvalConfig:
    """Tests for EvalConfig dataclass."""

    def test_default_config(self) -> None:
        """Default config should use gemini provider."""
        config = EvalConfig()
        assert config.provider == "gemini"
        assert config.temperature == 0.0
        assert config.cache_enabled is True

    def test_get_model_default(self) -> None:
        """get_model should return default model for provider."""
        config = EvalConfig(provider="gemini")
        assert config.get_model() == "gemini-2.0-flash"

        config = EvalConfig(provider="openai")
        assert config.get_model() == "gpt-4o-mini"

        config = EvalConfig(provider="anthropic")
        assert config.get_model() == "claude-3-5-haiku-latest"

    def test_get_model_custom(self) -> None:
        """get_model should return custom model if specified."""
        config = EvalConfig(provider="openai", model="gpt-4o")
        assert config.get_model() == "gpt-4o"


class TestSemanticEvaluatorMocked:
    """Tests for SemanticEvaluator with mocked LLM."""

    @pytest.fixture
    def mock_eval_output(self):
        """Create a mock EvalOutput response."""
        from voiceobs.eval.evaluator import EvalOutput

        return EvalOutput(
            intent_correct=True,
            relevance_score=0.9,
            explanation="The agent correctly understood the weather request.",
        )

    @pytest.fixture
    def mock_llm(self, mock_eval_output):
        """Create a mock structured LLM."""
        mock = MagicMock()
        mock.invoke.return_value = mock_eval_output
        return mock

    def test_evaluate_returns_result(self, mock_llm, mock_eval_output) -> None:
        """evaluate should return EvalResult from LLM response."""
        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            # Setup mock provider
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            evaluator = SemanticEvaluator(config)

            result = evaluator.evaluate(
                EvalInput(
                    user_transcript="What's the weather?",
                    agent_response="It's sunny and 72 degrees.",
                )
            )

            assert result.intent_correct is True
            assert result.relevance_score == 0.9
            assert "weather" in result.explanation.lower()
            assert result.cached is False

    def test_evaluate_caches_result(self, mock_llm, tmp_path: Path) -> None:
        """evaluate should cache results when enabled."""
        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator
        from voiceobs.eval.evaluator import EvalOutput

        mock_output = EvalOutput(
            intent_correct=True,
            relevance_score=0.85,
            explanation="Cached response.",
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=True, cache_dir=str(tmp_path))
            evaluator = SemanticEvaluator(config)

            inp = EvalInput(
                user_transcript="Hello",
                agent_response="Hi there!",
            )

            # First call - should hit LLM
            result1 = evaluator.evaluate(inp)
            assert result1.cached is False
            assert mock_llm.invoke.call_count == 1

            # Second call - should hit cache
            result2 = evaluator.evaluate(inp)
            assert result2.cached is True
            assert mock_llm.invoke.call_count == 1  # No additional call

            # Results should match
            assert result1.intent_correct == result2.intent_correct
            assert result1.relevance_score == result2.relevance_score

    def test_evaluate_batch(self, mock_llm) -> None:
        """evaluate_batch should evaluate multiple inputs."""
        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator
        from voiceobs.eval.evaluator import EvalOutput

        mock_output = EvalOutput(
            intent_correct=True,
            relevance_score=0.8,
            explanation="Good.",
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=False)
            evaluator = SemanticEvaluator(config)

            inputs = [
                EvalInput(user_transcript="Q1", agent_response="A1"),
                EvalInput(user_transcript="Q2", agent_response="A2"),
                EvalInput(user_transcript="Q3", agent_response="A3"),
            ]

            results = evaluator.evaluate_batch(inputs)

            assert len(results) == 3
            assert mock_llm.invoke.call_count == 3

    def test_clear_cache(self, mock_llm, tmp_path: Path) -> None:
        """clear_cache should remove cached results."""
        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator
        from voiceobs.eval.evaluator import EvalOutput

        mock_output = EvalOutput(
            intent_correct=True,
            relevance_score=0.9,
            explanation="Test.",
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=True, cache_dir=str(tmp_path))
            evaluator = SemanticEvaluator(config)

            inp = EvalInput(user_transcript="Test", agent_response="Response")

            # Populate cache
            evaluator.evaluate(inp)
            assert mock_llm.invoke.call_count == 1

            # Clear cache
            evaluator.clear_cache()

            # Should hit LLM again
            evaluator.evaluate(inp)
            assert mock_llm.invoke.call_count == 2


class TestPromptBuilding:
    """Tests for prompt building with optional fields."""

    def test_prompt_includes_context_section(self) -> None:
        """Prompt should include context section when conversation_context provided."""
        from voiceobs.eval.evaluator import _build_prompt

        inp = EvalInput(
            user_transcript="What's the weather?",
            agent_response="It's sunny.",
            conversation_context="User is planning a picnic.",
        )

        prompt = _build_prompt(inp)
        assert "## Prior Context" in prompt
        assert "User is planning a picnic." in prompt

    def test_prompt_includes_expected_intent_section(self) -> None:
        """Prompt should include expected intent section when provided."""
        from voiceobs.eval.evaluator import _build_prompt

        inp = EvalInput(
            user_transcript="What's the weather?",
            agent_response="It's sunny.",
            expected_intent="get_weather",
        )

        prompt = _build_prompt(inp)
        assert "## Expected Intent" in prompt
        assert "get_weather" in prompt


class TestCachePersistence:
    """Tests for cache loading and saving to disk."""

    @pytest.fixture
    def mock_llm(self):
        """Create a mock structured LLM."""
        mock = MagicMock()
        return mock

    def test_cache_loaded_from_disk_on_init(self, tmp_path, mock_llm) -> None:
        """Should load cache from disk when cache file exists."""
        import json

        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator

        # Create a cache file with pre-existing data
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "eval_cache.json"

        # Generate a content hash for the test input
        inp = EvalInput(user_transcript="Hello", agent_response="Hi!")
        content_hash = inp.content_hash()

        cache_data = {
            content_hash: {
                "intent_correct": True,
                "relevance_score": 0.99,
                "explanation": "Pre-cached result.",
                "conversation_id": None,
                "turn_id": None,
            }
        }
        cache_file.write_text(json.dumps(cache_data))

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=True, cache_dir=str(cache_dir))
            evaluator = SemanticEvaluator(config)

            result = evaluator.evaluate(inp)

            # Should return cached result, not call LLM
            assert result.cached is True
            assert result.relevance_score == 0.99
            assert result.explanation == "Pre-cached result."
            assert mock_llm.invoke.call_count == 0

    def test_invalid_cache_file_starts_fresh(self, tmp_path, mock_llm) -> None:
        """Should start with empty cache if cache file is invalid."""
        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator
        from voiceobs.eval.evaluator import EvalOutput

        # Create an invalid cache file
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "eval_cache.json"
        cache_file.write_text("this is not valid json")

        mock_output = EvalOutput(
            intent_correct=True,
            relevance_score=0.75,
            explanation="Fresh result.",
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=True, cache_dir=str(cache_dir))
            evaluator = SemanticEvaluator(config)

            inp = EvalInput(user_transcript="Hello", agent_response="Hi!")
            result = evaluator.evaluate(inp)

            # Should call LLM since cache was invalid
            assert result.cached is False
            assert mock_llm.invoke.call_count == 1

    def test_missing_key_in_cache_starts_fresh(self, tmp_path, mock_llm) -> None:
        """Should start with empty cache if cache file has missing keys."""
        import json

        from voiceobs.eval import EvalConfig, EvalInput, SemanticEvaluator
        from voiceobs.eval.evaluator import EvalOutput

        # Create a cache file with missing required keys
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        cache_file = cache_dir / "eval_cache.json"
        cache_data = {"some_hash": {"incomplete": "data"}}  # Missing required keys
        cache_file.write_text(json.dumps(cache_data))

        mock_output = EvalOutput(
            intent_correct=True,
            relevance_score=0.75,
            explanation="Fresh result.",
        )
        mock_llm.invoke.return_value = mock_output

        with patch("voiceobs.eval.evaluator.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_base_llm = MagicMock()
            mock_base_llm.with_structured_output.return_value = mock_llm
            mock_provider.create_llm.return_value = mock_base_llm
            mock_get_provider.return_value = mock_provider

            config = EvalConfig(cache_enabled=True, cache_dir=str(cache_dir))
            evaluator = SemanticEvaluator(config)

            inp = EvalInput(user_transcript="Hello", agent_response="Hi!")
            result = evaluator.evaluate(inp)

            # Should call LLM since cache was invalid
            assert result.cached is False
            assert mock_llm.invoke.call_count == 1


class TestRegisterProvider:
    """Tests for register_provider convenience function."""

    def test_register_provider_adds_to_registry(self) -> None:
        """register_provider should add provider to default registry."""
        from voiceobs.eval.providers import LLMProvider, get_registry, register_provider

        class TestProvider(LLMProvider):
            @property
            def name(self) -> str:
                return "test_register_provider"

            @property
            def default_model(self) -> str:
                return "test-model"

            def create_llm(self, config):
                return MagicMock()

        register_provider(TestProvider())

        registry = get_registry()
        assert registry.is_registered("test_register_provider")


class TestGeminiProviderCreateLLM:
    """Tests for GeminiProvider.create_llm method."""

    def test_create_llm_with_default_model(self) -> None:
        """Should create LLM with default model when not specified."""
        import sys

        from voiceobs.eval.providers.gemini import GeminiProvider

        provider = GeminiProvider()
        config = EvalConfig(provider="gemini", api_key="test-api-key")

        # Create mock module with mock class
        mock_chat_class = MagicMock()
        mock_module = MagicMock()
        mock_module.ChatGoogleGenerativeAI = mock_chat_class

        with patch.dict(sys.modules, {"langchain_google_genai": mock_module}):
            provider.create_llm(config)

            mock_chat_class.assert_called_once_with(
                model="gemini-2.0-flash",
                temperature=0.0,
                google_api_key="test-api-key",
            )

    def test_create_llm_with_custom_model(self) -> None:
        """Should create LLM with custom model when specified."""
        import sys

        from voiceobs.eval.providers.gemini import GeminiProvider

        provider = GeminiProvider()
        config = EvalConfig(provider="gemini", model="gemini-1.5-pro", temperature=0.5)

        mock_chat_class = MagicMock()
        mock_module = MagicMock()
        mock_module.ChatGoogleGenerativeAI = mock_chat_class

        with patch.dict(sys.modules, {"langchain_google_genai": mock_module}):
            provider.create_llm(config)

            mock_chat_class.assert_called_once_with(
                model="gemini-1.5-pro",
                temperature=0.5,
            )

    def test_create_llm_raises_import_error(self) -> None:
        """Should raise ImportError when langchain-google-genai not installed."""
        import sys

        from voiceobs.eval.providers.gemini import GeminiProvider

        provider = GeminiProvider()
        config = EvalConfig(provider="gemini")

        # Remove the module from sys.modules to trigger ImportError
        with patch.dict(sys.modules, {"langchain_google_genai": None}):
            with pytest.raises(ImportError, match="langchain-google-genai"):
                provider.create_llm(config)


class TestOpenAIProviderCreateLLM:
    """Tests for OpenAIProvider.create_llm method."""

    def test_create_llm_with_default_model(self) -> None:
        """Should create LLM with default model when not specified."""
        import sys

        from voiceobs.eval.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        config = EvalConfig(provider="openai", api_key="test-api-key")

        mock_chat_class = MagicMock()
        mock_module = MagicMock()
        mock_module.ChatOpenAI = mock_chat_class

        with patch.dict(sys.modules, {"langchain_openai": mock_module}):
            provider.create_llm(config)

            mock_chat_class.assert_called_once_with(
                model="gpt-4o-mini",
                temperature=0.0,
                api_key="test-api-key",
            )

    def test_create_llm_with_custom_model(self) -> None:
        """Should create LLM with custom model when specified."""
        import sys

        from voiceobs.eval.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        config = EvalConfig(provider="openai", model="gpt-4o", temperature=0.3)

        mock_chat_class = MagicMock()
        mock_module = MagicMock()
        mock_module.ChatOpenAI = mock_chat_class

        with patch.dict(sys.modules, {"langchain_openai": mock_module}):
            provider.create_llm(config)

            mock_chat_class.assert_called_once_with(
                model="gpt-4o",
                temperature=0.3,
            )

    def test_create_llm_raises_import_error(self) -> None:
        """Should raise ImportError when langchain-openai not installed."""
        import sys

        from voiceobs.eval.providers.openai import OpenAIProvider

        provider = OpenAIProvider()
        config = EvalConfig(provider="openai")

        with patch.dict(sys.modules, {"langchain_openai": None}):
            with pytest.raises(ImportError, match="langchain-openai"):
                provider.create_llm(config)


class TestAnthropicProviderCreateLLM:
    """Tests for AnthropicProvider.create_llm method."""

    def test_create_llm_with_default_model(self) -> None:
        """Should create LLM with default model when not specified."""
        import sys

        from voiceobs.eval.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        config = EvalConfig(provider="anthropic", api_key="test-api-key")

        mock_chat_class = MagicMock()
        mock_module = MagicMock()
        mock_module.ChatAnthropic = mock_chat_class

        with patch.dict(sys.modules, {"langchain_anthropic": mock_module}):
            provider.create_llm(config)

            mock_chat_class.assert_called_once_with(
                model="claude-3-5-haiku-latest",
                temperature=0.0,
                api_key="test-api-key",
            )

    def test_create_llm_with_custom_model(self) -> None:
        """Should create LLM with custom model when specified."""
        import sys

        from voiceobs.eval.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        config = EvalConfig(provider="anthropic", model="claude-3-5-sonnet-latest", temperature=0.7)

        mock_chat_class = MagicMock()
        mock_module = MagicMock()
        mock_module.ChatAnthropic = mock_chat_class

        with patch.dict(sys.modules, {"langchain_anthropic": mock_module}):
            provider.create_llm(config)

            mock_chat_class.assert_called_once_with(
                model="claude-3-5-sonnet-latest",
                temperature=0.7,
            )

    def test_create_llm_raises_import_error(self) -> None:
        """Should raise ImportError when langchain-anthropic not installed."""
        import sys

        from voiceobs.eval.providers.anthropic import AnthropicProvider

        provider = AnthropicProvider()
        config = EvalConfig(provider="anthropic")

        with patch.dict(sys.modules, {"langchain_anthropic": None}):
            with pytest.raises(ImportError, match="langchain-anthropic"):
                provider.create_llm(config)


class TestProviderRegistry:
    """Tests for the provider registry."""

    def test_list_providers(self) -> None:
        """Should list all built-in providers."""
        from voiceobs.eval.providers import list_providers

        providers = list_providers()
        assert "gemini" in providers
        assert "openai" in providers
        assert "anthropic" in providers

    def test_get_provider(self) -> None:
        """Should get a provider by name."""
        from voiceobs.eval.providers import get_provider

        provider = get_provider("gemini")
        assert provider.name == "gemini"
        assert provider.default_model == "gemini-2.0-flash"

    def test_get_unknown_provider_raises(self) -> None:
        """Should raise ValueError for unknown provider."""
        from voiceobs.eval.providers import get_provider

        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown_provider")

    def test_register_custom_provider(self) -> None:
        """Should allow registering custom providers."""
        from voiceobs.eval.providers import LLMProvider, get_registry

        class CustomProvider(LLMProvider):
            @property
            def name(self) -> str:
                return "custom_test"

            @property
            def default_model(self) -> str:
                return "custom-model"

            def create_llm(self, config):
                return MagicMock()

        registry = get_registry()
        registry.register(CustomProvider())

        assert registry.is_registered("custom_test")
        provider = registry.get("custom_test")
        assert provider.default_model == "custom-model"
