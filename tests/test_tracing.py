"""Tests for safe OpenTelemetry tracer initialization."""

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from voiceobs.tracing import (
    _has_real_provider,
    _is_noop_provider,
    ensure_tracing_initialized,
    get_tracer_provider_info,
    reset_initialization,
)


class TestProviderDetection:
    """Tests for detecting existing tracer providers."""

    def test_has_real_provider_returns_true_when_sdk_configured(self):
        """Test that _has_real_provider returns True when SDK is set up."""
        # Our conftest.py sets up a TracerProvider before tests run
        assert _has_real_provider() is True

    def test_is_noop_provider_returns_false_for_sdk_provider(self):
        """Test that SDK TracerProvider is not detected as noop."""
        provider = trace.get_tracer_provider()
        assert _is_noop_provider(provider) is False

    def test_get_tracer_provider_info_returns_dict(self):
        """Test that get_tracer_provider_info returns expected structure."""
        info = get_tracer_provider_info()

        assert isinstance(info, dict)
        assert "provider_type" in info
        assert "is_noop" in info
        assert "voiceobs_initialized" in info

    def test_get_tracer_provider_info_shows_sdk_provider(self):
        """Test that info correctly identifies SDK provider."""
        info = get_tracer_provider_info()

        # Our conftest sets up TracerProvider
        assert info["provider_type"] == "TracerProvider"
        assert info["is_noop"] is False


class TestEnsureTracingInitialized:
    """Tests for ensure_tracing_initialized function."""

    def test_does_not_override_existing_provider(self):
        """Test that ensure_tracing_initialized does not override existing provider."""
        # Get the current provider (set by conftest.py)
        original_provider = trace.get_tracer_provider()

        # Call ensure_tracing_initialized - should not override
        result = ensure_tracing_initialized()

        # Should return False (didn't initialize, kept existing)
        assert result is False

        # Provider should still be the same
        current_provider = trace.get_tracer_provider()
        assert current_provider is original_provider

    def test_returns_false_when_provider_exists(self):
        """Test return value when provider already exists."""
        # Our conftest.py already set up a provider
        result = ensure_tracing_initialized()
        assert result is False

    def test_is_idempotent(self):
        """Test that calling multiple times is safe."""
        # Call multiple times - should all return False and not raise
        for _ in range(5):
            result = ensure_tracing_initialized()
            assert result is False

    def test_reset_initialization_resets_flag(self):
        """Test that reset_initialization resets the internal flag."""
        # First ensure we've marked as initialized
        ensure_tracing_initialized()

        # Reset the flag
        reset_initialization()

        # Get info - the provider still exists but our flag is reset
        info = get_tracer_provider_info()
        # Note: provider still exists from conftest, so this will still show False
        # because we detect the existing provider
        assert info["voiceobs_initialized"] is False


class TestSpanTimestampsAndAttributes:
    """Tests verifying spans have timestamps and attributes."""

    def test_spans_have_timestamps(self, span_exporter):
        """Test that emitted spans have start and end timestamps."""
        from voiceobs import voice_conversation, voice_turn

        with voice_conversation():
            with voice_turn("user"):
                pass

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1

        span = spans[0]
        # Timestamps are in nanoseconds since epoch
        assert span.start_time is not None
        assert span.end_time is not None
        assert span.start_time > 0
        assert span.end_time >= span.start_time

    def test_spans_have_all_required_attributes(self, span_exporter):
        """Test that spans have all voice observability attributes."""
        from voiceobs import VOICE_SCHEMA_VERSION, voice_conversation, voice_turn

        with voice_conversation(conversation_id="test-conv-123"):
            with voice_turn("agent"):
                pass

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1

        attrs = dict(spans[0].attributes)

        # All required attributes should be present
        required_attrs = [
            "voice.schema.version",
            "voice.conversation.id",
            "voice.turn.id",
            "voice.turn.index",
            "voice.actor",
        ]
        for attr in required_attrs:
            assert attr in attrs, f"Missing required attribute: {attr}"

        # Verify attribute values
        assert attrs["voice.schema.version"] == VOICE_SCHEMA_VERSION
        assert attrs["voice.conversation.id"] == "test-conv-123"
        assert attrs["voice.actor"] == "agent"
        assert attrs["voice.turn.index"] == 0
        # turn.id should be a UUID string
        assert len(attrs["voice.turn.id"]) == 36  # UUID format

    def test_span_duration_is_reasonable(self, span_exporter):
        """Test that span duration is tracked correctly."""
        import time

        from voiceobs import voice_conversation, voice_turn

        with voice_conversation():
            with voice_turn("user"):
                time.sleep(0.01)  # Sleep 10ms

        spans = span_exporter.get_finished_spans()
        span = spans[0]

        duration_ns = span.end_time - span.start_time
        duration_ms = duration_ns / 1_000_000

        # Should be at least 10ms (our sleep time)
        assert duration_ms >= 10, f"Expected >= 10ms, got {duration_ms}ms"
        # But not too long (sanity check)
        assert duration_ms < 1000, f"Duration too long: {duration_ms}ms"
