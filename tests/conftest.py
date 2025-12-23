"""Pytest configuration and fixtures."""

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

# Global exporter that can be accessed and cleared between tests
_global_exporter = InMemorySpanExporter()
_provider_initialized = False


def _ensure_tracer_provider():
    """Ensure tracer provider is initialized once."""
    global _provider_initialized
    if not _provider_initialized:
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(_global_exporter))
        trace.set_tracer_provider(provider)
        _provider_initialized = True


# Initialize provider at module load time, before any tests run
_ensure_tracer_provider()


@pytest.fixture
def span_exporter():
    """Provide access to the global span exporter and clear it after test."""
    _global_exporter.clear()
    yield _global_exporter
    _global_exporter.clear()
