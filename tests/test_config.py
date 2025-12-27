"""Tests for voiceobs configuration system."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from voiceobs.config import (
    ConfigValidationError,
    EvalConfig,
    ExporterJsonlConfig,
    ExportersConfig,
    FailuresConfig,
    RegressionConfig,
    RegressionLatencyConfig,
    VoiceobsConfig,
    _deep_merge,
    _dict_to_config,
    _validate_config,
    generate_default_config,
    load_config,
    load_yaml_file,
)


class TestDeepMerge:
    """Tests for _deep_merge function."""

    def test_simple_merge(self) -> None:
        """Test merging simple dictionaries."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self) -> None:
        """Test merging nested dictionaries."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 10, "z": 20}}
        result = _deep_merge(base, override)
        assert result == {"a": {"x": 1, "y": 10, "z": 20}, "b": 3}

    def test_override_replaces_non_dict(self) -> None:
        """Test that non-dict values are replaced entirely."""
        base = {"a": {"x": 1}}
        override = {"a": "replaced"}
        result = _deep_merge(base, override)
        assert result == {"a": "replaced"}

    def test_empty_override(self) -> None:
        """Test merging with empty override."""
        base = {"a": 1, "b": 2}
        result = _deep_merge(base, {})
        assert result == {"a": 1, "b": 2}

    def test_empty_base(self) -> None:
        """Test merging with empty base."""
        override = {"a": 1, "b": 2}
        result = _deep_merge({}, override)
        assert result == {"a": 1, "b": 2}


class TestDictToConfig:
    """Tests for _dict_to_config function."""

    def test_empty_dict_returns_defaults(self) -> None:
        """Test that empty dict returns default config."""
        config = _dict_to_config({}, VoiceobsConfig)
        assert isinstance(config, VoiceobsConfig)
        assert config.failures.excessive_silence_ms == 3000.0

    def test_partial_config(self) -> None:
        """Test partial configuration."""
        data = {"failures": {"excessive_silence_ms": 5000.0}}
        config = _dict_to_config(data, VoiceobsConfig)
        assert config.failures.excessive_silence_ms == 5000.0
        # Other values should be defaults
        assert config.failures.slow_asr_ms == 2000.0

    def test_nested_config(self) -> None:
        """Test deeply nested configuration."""
        data = {"failures": {"severity": {"interruption": {"low_max_ms": 100.0}}}}
        config = _dict_to_config(data, VoiceobsConfig)
        assert config.failures.severity.interruption.low_max_ms == 100.0

    def test_unknown_key_raises_error(self) -> None:
        """Test that unknown keys raise validation error."""
        data = {"unknown_key": "value"}
        with pytest.raises(ConfigValidationError) as exc_info:
            _dict_to_config(data, VoiceobsConfig)
        assert "Unknown config key: unknown_key" in str(exc_info.value)

    def test_nested_unknown_key_raises_error(self) -> None:
        """Test that nested unknown keys raise validation error."""
        data = {"failures": {"unknown_nested": 123}}
        with pytest.raises(ConfigValidationError) as exc_info:
            _dict_to_config(data, VoiceobsConfig)
        assert "Unknown config key: failures.unknown_nested" in str(exc_info.value)


class TestValidateConfig:
    """Tests for _validate_config function."""

    def test_valid_default_config(self) -> None:
        """Test that default config passes validation."""
        config = VoiceobsConfig()
        errors = _validate_config(config)
        assert errors == []

    def test_negative_threshold_fails(self) -> None:
        """Test that negative thresholds fail validation."""
        config = VoiceobsConfig(
            failures=FailuresConfig(interruption_overlap_ms=-1.0)
        )
        errors = _validate_config(config)
        assert any("interruption_overlap_ms" in e for e in errors)

    def test_confidence_out_of_range_fails(self) -> None:
        """Test that confidence > 1 fails validation."""
        config = VoiceobsConfig(failures=FailuresConfig(asr_min_confidence=1.5))
        errors = _validate_config(config)
        assert any("asr_min_confidence" in e for e in errors)

    def test_invalid_provider_fails(self) -> None:
        """Test that invalid provider fails validation."""
        config = VoiceobsConfig(eval=EvalConfig(provider="invalid"))  # type: ignore
        errors = _validate_config(config)
        assert any("provider" in e for e in errors)

    def test_temperature_out_of_range_fails(self) -> None:
        """Test that temperature > 2 fails validation."""
        config = VoiceobsConfig(eval=EvalConfig(temperature=3.0))
        errors = _validate_config(config)
        assert any("temperature" in e for e in errors)

    def test_regression_warning_greater_than_critical_fails(self) -> None:
        """Test that warning > critical fails validation."""
        config = VoiceobsConfig(
            regression=RegressionConfig(
                latency=RegressionLatencyConfig(warning_pct=30.0, critical_pct=10.0)
            )
        )
        errors = _validate_config(config)
        assert any("critical_pct must be >= warning_pct" in e for e in errors)

    def test_jsonl_enabled_without_path_fails(self) -> None:
        """Test that enabling jsonl without path fails."""
        config = VoiceobsConfig(
            exporters=ExportersConfig(
                jsonl=ExporterJsonlConfig(enabled=True, path="")
            )
        )
        errors = _validate_config(config)
        assert any("path is required" in e for e in errors)


class TestLoadYamlFile:
    """Tests for load_yaml_file function."""

    def test_nonexistent_file_returns_empty(self) -> None:
        """Test that nonexistent file returns empty dict."""
        result = load_yaml_file(Path("/nonexistent/path.yaml"))
        assert result == {}

    def test_empty_file_returns_empty(self) -> None:
        """Test that empty file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            temp_path = Path(f.name)
        try:
            result = load_yaml_file(temp_path)
            assert result == {}
        finally:
            temp_path.unlink()

    def test_valid_yaml_file(self) -> None:
        """Test loading valid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("failures:\n  excessive_silence_ms: 5000.0\n")
            temp_path = Path(f.name)
        try:
            result = load_yaml_file(temp_path)
            assert result == {"failures": {"excessive_silence_ms": 5000.0}}
        finally:
            temp_path.unlink()


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_default_config(self) -> None:
        """Test loading config with no files."""
        config = load_config(
            project_path=Path("/nonexistent/project.yaml"),
            user_path=Path("/nonexistent/user.yaml"),
        )
        assert isinstance(config, VoiceobsConfig)
        assert config.failures.excessive_silence_ms == 3000.0

    def test_load_project_config(self) -> None:
        """Test loading project config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("failures:\n  excessive_silence_ms: 4000.0\n")
            temp_path = Path(f.name)
        try:
            config = load_config(
                project_path=temp_path,
                user_path=Path("/nonexistent/user.yaml"),
            )
            assert config.failures.excessive_silence_ms == 4000.0
        finally:
            temp_path.unlink()

    def test_project_overrides_user(self) -> None:
        """Test that project config overrides user config."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as uf:
            uf.write("failures:\n  excessive_silence_ms: 4000.0\n  slow_asr_ms: 1000.0\n")
            user_path = Path(uf.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as pf:
            pf.write("failures:\n  excessive_silence_ms: 5000.0\n")
            project_path = Path(pf.name)

        try:
            config = load_config(project_path=project_path, user_path=user_path)
            # Project overrides user
            assert config.failures.excessive_silence_ms == 5000.0
            # User value preserved where not overridden
            assert config.failures.slow_asr_ms == 1000.0
        finally:
            user_path.unlink()
            project_path.unlink()

    def test_validation_can_be_disabled(self) -> None:
        """Test that validation can be disabled."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("failures:\n  asr_min_confidence: 5.0\n")  # Invalid value
            temp_path = Path(f.name)
        try:
            # Should not raise with validation disabled
            config = load_config(project_path=temp_path, validate=False)
            assert config.failures.asr_min_confidence == 5.0
        finally:
            temp_path.unlink()

    def test_validation_enabled_by_default(self) -> None:
        """Test that validation is enabled by default."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("failures:\n  asr_min_confidence: 5.0\n")  # Invalid value
            temp_path = Path(f.name)
        try:
            with pytest.raises(ConfigValidationError):
                load_config(project_path=temp_path)
        finally:
            temp_path.unlink()


class TestGenerateDefaultConfig:
    """Tests for generate_default_config function."""

    def test_generates_valid_yaml(self) -> None:
        """Test that generated config is valid YAML."""
        import yaml

        config_str = generate_default_config()
        parsed = yaml.safe_load(config_str)
        assert isinstance(parsed, dict)
        assert "exporters" in parsed
        assert "failures" in parsed
        assert "regression" in parsed
        assert "eval" in parsed

    def test_generated_config_loads_successfully(self) -> None:
        """Test that generated config can be loaded."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(generate_default_config())
            temp_path = Path(f.name)
        try:
            config = load_config(project_path=temp_path)
            assert isinstance(config, VoiceobsConfig)
        finally:
            temp_path.unlink()


class TestConfigDefaults:
    """Tests for default configuration values."""

    def test_exporter_defaults(self) -> None:
        """Test default exporter configuration."""
        config = VoiceobsConfig()
        assert config.exporters.jsonl.enabled is False
        assert config.exporters.jsonl.path == "./voiceobs_run.jsonl"
        assert config.exporters.console.enabled is True

    def test_failure_defaults(self) -> None:
        """Test default failure thresholds."""
        config = VoiceobsConfig()
        assert config.failures.interruption_overlap_ms == 0.0
        assert config.failures.excessive_silence_ms == 3000.0
        assert config.failures.slow_asr_ms == 2000.0
        assert config.failures.slow_llm_ms == 2000.0
        assert config.failures.slow_tts_ms == 2000.0
        assert config.failures.asr_min_confidence == 0.7
        assert config.failures.llm_min_relevance == 0.5

    def test_severity_defaults(self) -> None:
        """Test default severity thresholds."""
        config = VoiceobsConfig()
        severity = config.failures.severity
        assert severity.interruption.low_max_ms == 200.0
        assert severity.interruption.medium_max_ms == 500.0
        assert severity.silence.low_max_ms == 5000.0
        assert severity.silence.medium_max_ms == 8000.0
        assert severity.slow_response.low_max_ms == 3000.0
        assert severity.slow_response.medium_max_ms == 5000.0

    def test_regression_defaults(self) -> None:
        """Test default regression thresholds."""
        config = VoiceobsConfig()
        reg = config.regression
        assert reg.latency.warning_pct == 10.0
        assert reg.latency.critical_pct == 25.0
        assert reg.silence.warning_pct == 15.0
        assert reg.silence.critical_pct == 30.0
        assert reg.interruption_rate.warning_pct == 5.0
        assert reg.interruption_rate.critical_pct == 15.0
        assert reg.intent_correct.warning_pct == 5.0
        assert reg.intent_correct.critical_pct == 15.0
        assert reg.relevance.warning_pct == 10.0
        assert reg.relevance.critical_pct == 20.0

    def test_eval_defaults(self) -> None:
        """Test default eval configuration."""
        config = VoiceobsConfig()
        assert config.eval.provider == "gemini"
        assert config.eval.model is None
        assert config.eval.temperature == 0.0
        assert config.eval.cache.enabled is True
        assert config.eval.cache.dir == ".voiceobs_cache"
