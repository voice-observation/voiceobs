"""Configuration management for voiceobs.

Supports YAML configuration files with the following precedence:
1. CLI arguments (highest priority)
2. Project config: ./voiceobs.yaml
3. User config: ~/.config/voiceobs/config.yaml (lowest priority)
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Literal, Optional, get_type_hints

import yaml

# Config file locations
PROJECT_CONFIG_NAME = "voiceobs.yaml"
USER_CONFIG_DIR = Path.home() / ".config" / "voiceobs"
USER_CONFIG_PATH = USER_CONFIG_DIR / "config.yaml"


@dataclass
class ExporterJsonlConfig:
    """JSONL exporter configuration."""

    enabled: bool = False
    path: str = "./voiceobs_run.jsonl"


@dataclass
class ExporterConsoleConfig:
    """Console exporter configuration."""

    enabled: bool = True


@dataclass
class ExportersConfig:
    """All exporter configurations."""

    jsonl: ExporterJsonlConfig = field(default_factory=ExporterJsonlConfig)
    console: ExporterConsoleConfig = field(default_factory=ExporterConsoleConfig)


@dataclass
class FailureSeverityInterruptionConfig:
    """Severity thresholds for interruption failures."""

    low_max_ms: float = 200.0
    medium_max_ms: float = 500.0


@dataclass
class FailureSeveritySilenceConfig:
    """Severity thresholds for silence failures."""

    low_max_ms: float = 5000.0
    medium_max_ms: float = 8000.0


@dataclass
class FailureSeveritySlowResponseConfig:
    """Severity thresholds for slow response failures."""

    low_max_ms: float = 3000.0
    medium_max_ms: float = 5000.0


@dataclass
class FailureSeverityConfig:
    """All severity threshold configurations."""

    interruption: FailureSeverityInterruptionConfig = field(
        default_factory=FailureSeverityInterruptionConfig
    )
    silence: FailureSeveritySilenceConfig = field(default_factory=FailureSeveritySilenceConfig)
    slow_response: FailureSeveritySlowResponseConfig = field(
        default_factory=FailureSeveritySlowResponseConfig
    )


@dataclass
class FailuresConfig:
    """Failure detection configuration."""

    # Detection thresholds
    interruption_overlap_ms: float = 0.0
    excessive_silence_ms: float = 3000.0
    slow_asr_ms: float = 2000.0
    slow_llm_ms: float = 2000.0
    slow_tts_ms: float = 2000.0
    asr_min_confidence: float = 0.7
    llm_min_relevance: float = 0.5

    # Severity thresholds
    severity: FailureSeverityConfig = field(default_factory=FailureSeverityConfig)


@dataclass
class RegressionLatencyConfig:
    """Latency regression thresholds."""

    warning_pct: float = 10.0
    critical_pct: float = 25.0


@dataclass
class RegressionSilenceConfig:
    """Silence regression thresholds."""

    warning_pct: float = 15.0
    critical_pct: float = 30.0


@dataclass
class RegressionInterruptionConfig:
    """Interruption rate regression thresholds."""

    warning_pct: float = 5.0
    critical_pct: float = 15.0


@dataclass
class RegressionIntentConfig:
    """Intent correctness regression thresholds."""

    warning_pct: float = 5.0
    critical_pct: float = 15.0


@dataclass
class RegressionRelevanceConfig:
    """Relevance regression thresholds."""

    warning_pct: float = 10.0
    critical_pct: float = 20.0


@dataclass
class RegressionConfig:
    """Regression detection configuration."""

    latency: RegressionLatencyConfig = field(default_factory=RegressionLatencyConfig)
    silence: RegressionSilenceConfig = field(default_factory=RegressionSilenceConfig)
    interruption_rate: RegressionInterruptionConfig = field(
        default_factory=RegressionInterruptionConfig
    )
    intent_correct: RegressionIntentConfig = field(default_factory=RegressionIntentConfig)
    relevance: RegressionRelevanceConfig = field(default_factory=RegressionRelevanceConfig)


@dataclass
class EvalCacheConfig:
    """Evaluation cache configuration."""

    enabled: bool = True
    dir: str = ".voiceobs_cache"


@dataclass
class EvalConfig:
    """LLM evaluator configuration."""

    provider: Literal["gemini", "openai", "anthropic"] = "gemini"
    model: Optional[str] = None  # None = use provider default
    temperature: float = 0.0
    cache: EvalCacheConfig = field(default_factory=EvalCacheConfig)


@dataclass
class VoiceobsConfig:
    """Root configuration for voiceobs."""

    exporters: ExportersConfig = field(default_factory=ExportersConfig)
    failures: FailuresConfig = field(default_factory=FailuresConfig)
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    eval: EvalConfig = field(default_factory=EvalConfig)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _dict_to_config(data: dict[str, Any], cls: type, path: str = "") -> Any:
    """Convert a dictionary to a dataclass config, with validation."""
    if not data:
        return cls()

    errors: list[str] = []
    kwargs: dict[str, Any] = {}

    # Get field names from dataclass
    field_names = {f.name for f in fields(cls)}

    # Get resolved type hints (handles forward references from __future__ annotations)
    type_hints = get_type_hints(cls)

    for key, value in data.items():
        full_path = f"{path}.{key}" if path else key

        if key not in field_names:
            errors.append(f"Unknown config key: {full_path}")
            continue

        field_type = type_hints.get(key)

        # Handle nested dataclass
        if field_type and hasattr(field_type, "__dataclass_fields__"):
            if isinstance(value, dict):
                try:
                    kwargs[key] = _dict_to_config(value, field_type, full_path)
                except ConfigValidationError as e:
                    errors.extend(e.errors)
            else:
                errors.append(f"{full_path}: expected object, got {type(value).__name__}")
        else:
            # Basic type validation
            kwargs[key] = value

    if errors:
        raise ConfigValidationError(errors)

    # Fill in missing fields with defaults by creating instance with only provided kwargs
    # First create default instance, then override with provided values
    default_instance = cls()
    for field_name in field_names:
        if field_name not in kwargs:
            kwargs[field_name] = getattr(default_instance, field_name)

    return cls(**kwargs)


def _validate_config(config: VoiceobsConfig) -> list[str]:
    """Validate configuration values and return list of errors."""
    errors: list[str] = []

    # Validate exporters
    if config.exporters.jsonl.enabled and not config.exporters.jsonl.path:
        errors.append("exporters.jsonl.path is required when jsonl exporter is enabled")

    # Validate failures thresholds (must be non-negative)
    failures = config.failures
    if failures.interruption_overlap_ms < 0:
        errors.append("failures.interruption_overlap_ms must be >= 0")
    if failures.excessive_silence_ms < 0:
        errors.append("failures.excessive_silence_ms must be >= 0")
    if failures.slow_asr_ms < 0:
        errors.append("failures.slow_asr_ms must be >= 0")
    if failures.slow_llm_ms < 0:
        errors.append("failures.slow_llm_ms must be >= 0")
    if failures.slow_tts_ms < 0:
        errors.append("failures.slow_tts_ms must be >= 0")

    # Validate confidence/relevance thresholds (must be 0-1)
    if not 0 <= failures.asr_min_confidence <= 1:
        errors.append("failures.asr_min_confidence must be between 0 and 1")
    if not 0 <= failures.llm_min_relevance <= 1:
        errors.append("failures.llm_min_relevance must be between 0 and 1")

    # Validate regression thresholds (must be positive)
    regression = config.regression
    if regression.latency.warning_pct < 0:
        errors.append("regression.latency.warning_pct must be >= 0")
    if regression.latency.critical_pct < regression.latency.warning_pct:
        errors.append("regression.latency.critical_pct must be >= warning_pct")

    # Validate eval config
    if config.eval.provider not in ("gemini", "openai", "anthropic"):
        errors.append("eval.provider must be one of: gemini, openai, anthropic")
    if not 0 <= config.eval.temperature <= 2:
        errors.append("eval.temperature must be between 0 and 2")

    return errors


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents as a dictionary."""
    if not path.exists():
        return {}

    with open(path) as f:
        content = yaml.safe_load(f)
        return content if content else {}


def find_project_config() -> Optional[Path]:
    """Find the project config file by searching up from the current directory."""
    current = Path.cwd()
    while current != current.parent:
        config_path = current / PROJECT_CONFIG_NAME
        if config_path.exists():
            return config_path
        current = current.parent

    # Also check current directory
    config_path = Path.cwd() / PROJECT_CONFIG_NAME
    if config_path.exists():
        return config_path

    return None


def load_config(
    project_path: Optional[Path] = None,
    user_path: Optional[Path] = None,
    validate: bool = True,
) -> VoiceobsConfig:
    """Load and merge configuration from all sources.

    Args:
        project_path: Override path to project config file.
        user_path: Override path to user config file.
        validate: Whether to validate the configuration.

    Returns:
        Merged VoiceobsConfig instance.

    Raises:
        ConfigValidationError: If validation fails.
    """
    # Load user config (lowest priority)
    user_config_path = user_path or USER_CONFIG_PATH
    user_config = load_yaml_file(user_config_path)

    # Load project config (higher priority)
    project_config_path = project_path or find_project_config()
    project_config = load_yaml_file(project_config_path) if project_config_path else {}

    # Merge configs (project overrides user)
    merged = _deep_merge(user_config, project_config)

    # Convert to config object
    config = _dict_to_config(merged, VoiceobsConfig)

    # Validate
    if validate:
        errors = _validate_config(config)
        if errors:
            raise ConfigValidationError(errors)

    return config


def generate_default_config() -> str:
    """Generate a default configuration file with comments."""
    return """# voiceobs configuration file
# Documentation: https://github.com/voice-observation/voiceobs

# Exporter settings
exporters:
  # JSONL file exporter (for offline analysis)
  jsonl:
    enabled: false
    path: "./voiceobs_run.jsonl"

  # Console exporter (prints spans to stdout)
  console:
    enabled: true

# Failure detection thresholds
failures:
  # Any overlap triggers an interruption failure
  interruption_overlap_ms: 0.0

  # Silence after user turn that triggers failure
  excessive_silence_ms: 3000.0

  # Stage latency thresholds
  slow_asr_ms: 2000.0
  slow_llm_ms: 2000.0
  slow_tts_ms: 2000.0

  # Quality thresholds (0.0 to 1.0)
  asr_min_confidence: 0.7
  llm_min_relevance: 0.5

  # Severity classification thresholds
  severity:
    interruption:
      low_max_ms: 200.0      # 0-200ms = LOW
      medium_max_ms: 500.0   # 200-500ms = MEDIUM, >500ms = HIGH

    silence:
      low_max_ms: 5000.0     # 3000-5000ms = LOW
      medium_max_ms: 8000.0  # 5000-8000ms = MEDIUM, >8000ms = HIGH

    slow_response:
      low_max_ms: 3000.0     # 2000-3000ms = LOW
      medium_max_ms: 5000.0  # 3000-5000ms = MEDIUM, >5000ms = HIGH

# Regression detection thresholds (for voiceobs compare)
regression:
  latency:
    warning_pct: 10.0   # Warn if latency increases by 10%
    critical_pct: 25.0  # Critical if latency increases by 25%

  silence:
    warning_pct: 15.0
    critical_pct: 30.0

  interruption_rate:
    warning_pct: 5.0
    critical_pct: 15.0

  intent_correct:
    warning_pct: 5.0    # Warn if correctness drops by 5%
    critical_pct: 15.0

  relevance:
    warning_pct: 10.0
    critical_pct: 20.0

# LLM evaluator settings (for semantic evaluation)
eval:
  # Provider: gemini, openai, or anthropic
  provider: "gemini"

  # Model name (null = use provider default)
  # Defaults: gemini-2.0-flash, gpt-4o-mini, claude-3-5-haiku-latest
  model: null

  # Sampling temperature (0.0 = deterministic)
  temperature: 0.0

  # Evaluation result caching
  cache:
    enabled: true
    dir: ".voiceobs_cache"
"""


# Global config instance (lazy loaded)
_config: Optional[VoiceobsConfig] = None


def get_config() -> VoiceobsConfig:
    """Get the global configuration instance.

    Loads configuration on first access. Use reload_config() to refresh.
    """
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> VoiceobsConfig:
    """Reload the global configuration from files."""
    global _config
    _config = load_config()
    return _config


def set_config(config: VoiceobsConfig) -> None:
    """Set the global configuration instance (useful for testing)."""
    global _config
    _config = config
