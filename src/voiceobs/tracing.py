"""Safe OpenTelemetry tracer initialization for voiceobs.

This module provides utilities for safely initializing OpenTelemetry tracing
without overriding existing user configurations.
"""

from __future__ import annotations

import threading

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import NoOpTracerProvider

from voiceobs.exporters import get_jsonl_exporter_from_config

try:
    from voiceobs.exporters import get_otlp_exporter_from_config
except ImportError:
    # OTLP dependencies not installed
    def get_otlp_exporter_from_config():  # type: ignore[misc]
        return None


# Thread-safe initialization flag
_init_lock = threading.Lock()
_initialized = False


def _is_noop_provider(provider: trace.TracerProvider) -> bool:
    """Check if the current provider is a no-op (default uninitialized) provider."""
    # The default provider before any SDK is set up is NoOpTracerProvider
    # or a ProxyTracerProvider wrapping NoOpTracerProvider
    if isinstance(provider, NoOpTracerProvider):
        return True

    # Check for ProxyTracerProvider (the default before SDK setup)
    provider_class_name = type(provider).__name__
    if provider_class_name == "ProxyTracerProvider":
        # ProxyTracerProvider is used before any real provider is set
        # It delegates to NoOpTracerProvider until a real one is configured
        return True

    return False


def _has_real_provider() -> bool:
    """Check if a real (non-noop) TracerProvider has been configured."""
    provider = trace.get_tracer_provider()
    return not _is_noop_provider(provider)


def ensure_tracing_initialized(force: bool = False) -> bool:
    """Ensure OpenTelemetry tracing is initialized for voiceobs.

    This function safely initializes tracing with sensible defaults if no
    tracing has been configured. It will NOT override existing configurations.

    Args:
        force: If True, initialize even if a provider exists (for testing).
               Default is False.

    Returns:
        True if voiceobs initialized tracing, False if existing config was kept.

    Behavior:
        - If a real TracerProvider is already configured: does nothing, returns False
        - If no provider configured: sets up TracerProvider with ConsoleSpanExporter
        - If JSONL export is enabled in config: also adds JSONLSpanExporter
        - If OTLP export is enabled in config: also adds OTLPSpanExporter
        - Thread-safe: safe to call from multiple threads

    Configuration:
        Create a voiceobs.yaml file with 'voiceobs init' to configure exporters:

        exporters:
          jsonl:
            enabled: true
            path: "./traces.jsonl"
          console:
            enabled: true
          otlp:
            enabled: true
            endpoint: "http://localhost:4317"
            protocol: "grpc"

    Example:
        # At application startup
        from voiceobs import ensure_tracing_initialized

        # This will set up console output if no tracing is configured
        ensure_tracing_initialized()

        # Now use voiceobs normally
        with voice_conversation():
            with voice_turn("user"):
                pass
    """
    global _initialized

    with _init_lock:
        # Already initialized by voiceobs
        if _initialized and not force:
            return False

        # Check if user has configured their own provider
        if _has_real_provider() and not force:
            _initialized = True  # Mark as checked
            return False

        # No provider configured, set up defaults
        from voiceobs.config import get_config

        config = get_config()
        provider = TracerProvider()

        # Add console exporter if enabled in config (default: True)
        if config.exporters.console.enabled:
            console_exporter = ConsoleSpanExporter()
            processor = BatchSpanProcessor(console_exporter)
            provider.add_span_processor(processor)

        # Add JSONL exporter if enabled in config
        jsonl_exporter = get_jsonl_exporter_from_config()
        if jsonl_exporter:
            jsonl_processor = BatchSpanProcessor(jsonl_exporter)
            provider.add_span_processor(jsonl_processor)

        # Add OTLP exporter if enabled in config
        otlp_exporter = get_otlp_exporter_from_config()
        if otlp_exporter:
            # Use the exporter's built-in batching
            otlp_processor = BatchSpanProcessor(otlp_exporter)
            provider.add_span_processor(otlp_processor)

        trace.set_tracer_provider(provider)
        _initialized = True
        return True


def get_tracer_provider_info() -> dict[str, object]:
    """Get information about the current tracer provider.

    Useful for diagnostics and debugging.

    Returns:
        Dictionary with provider information including:
        - provider_type: The class name of the current provider
        - is_noop: Whether it's a no-op provider
        - voiceobs_initialized: Whether voiceobs initialized the provider
    """
    provider = trace.get_tracer_provider()
    return {
        "provider_type": type(provider).__name__,
        "is_noop": _is_noop_provider(provider),
        "voiceobs_initialized": _initialized,
    }


def reset_initialization() -> None:
    """Reset the initialization state (for testing only).

    Warning: This does NOT reset the actual tracer provider, just voiceobs's
    internal tracking of whether it initialized tracing.
    """
    global _initialized
    with _init_lock:
        _initialized = False
