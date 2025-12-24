"""Tests for stage-level spans (ASR, LLM, TTS)."""

import pytest
from opentelemetry.trace import SpanKind

from voiceobs import (
    voice_conversation,
    voice_stage,
    voice_turn,
)
from voiceobs.context import VOICE_SCHEMA_VERSION


class TestVoiceStage:
    """Tests for the voice_stage context manager."""

    def test_stage_creates_span(self, span_exporter):
        """Test that voice_stage creates an OpenTelemetry span."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass

        spans = span_exporter.get_finished_spans()
        stage_spans = [s for s in spans if s.name == "voice.asr"]
        assert len(stage_spans) == 1

    def test_stage_span_names(self, span_exporter):
        """Test that stage spans have correct canonical names."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass
            with voice_turn("agent"):
                with voice_stage("llm"):
                    pass
                with voice_stage("tts"):
                    pass

        spans = span_exporter.get_finished_spans()
        span_names = {s.name for s in spans}

        assert "voice.asr" in span_names
        assert "voice.llm" in span_names
        assert "voice.tts" in span_names

    def test_stage_has_schema_version(self, span_exporter):
        """Test that stage spans have schema version attribute."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.schema.version"] == VOICE_SCHEMA_VERSION

    def test_stage_has_conversation_id(self, span_exporter):
        """Test that stage spans have conversation ID when in conversation."""
        with voice_conversation(conversation_id="test-conv-123"):
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.conversation.id"] == "test-conv-123"

    def test_stage_has_type_attribute(self, span_exporter):
        """Test that stage spans have stage type attribute."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.stage.type"] == "asr"

    def test_stage_provider_attribute(self, span_exporter):
        """Test that stage spans have provider attribute when specified."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr", provider="deepgram"):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.stage.provider"] == "deepgram"

    def test_stage_model_attribute(self, span_exporter):
        """Test that stage spans have model attribute when specified."""
        with voice_conversation():
            with voice_turn("agent"):
                with voice_stage("llm", model="gpt-4"):
                    pass

        spans = span_exporter.get_finished_spans()
        llm_span = [s for s in spans if s.name == "voice.llm"][0]
        attrs = dict(llm_span.attributes)

        assert attrs["voice.stage.model"] == "gpt-4"

    def test_stage_input_size_attribute(self, span_exporter):
        """Test that stage spans have input_size attribute when specified."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr", input_size=32000):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.stage.input_size"] == 32000

    def test_stage_all_attributes(self, span_exporter):
        """Test that stage spans have all attributes when specified."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage(
                    "asr",
                    provider="deepgram",
                    model="nova-2",
                    input_size=32000,
                ):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.stage.type"] == "asr"
        assert attrs["voice.stage.provider"] == "deepgram"
        assert attrs["voice.stage.model"] == "nova-2"
        assert attrs["voice.stage.input_size"] == 32000


class TestStageContext:
    """Tests for the StageContext class."""

    def test_set_output_size(self, span_exporter):
        """Test that set_output sets the output_size attribute."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr") as asr:
                    asr.set_output(42)

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]
        attrs = dict(asr_span.attributes)

        assert attrs["voice.stage.output_size"] == 42

    def test_set_error(self, span_exporter):
        """Test that set_error sets the error attribute."""
        with voice_conversation():
            with voice_turn("agent"):
                with voice_stage("llm") as llm:
                    llm.set_error("Rate limit exceeded")

        spans = span_exporter.get_finished_spans()
        llm_span = [s for s in spans if s.name == "voice.llm"][0]
        attrs = dict(llm_span.attributes)

        assert attrs["voice.stage.error"] == "Rate limit exceeded"

    def test_exception_records_error(self, span_exporter):
        """Test that exceptions are recorded on the span."""
        with pytest.raises(ValueError):
            with voice_conversation():
                with voice_turn("agent"):
                    with voice_stage("tts"):
                        raise ValueError("TTS service unavailable")

        spans = span_exporter.get_finished_spans()
        tts_span = [s for s in spans if s.name == "voice.tts"][0]
        attrs = dict(tts_span.attributes)

        assert attrs["voice.stage.error"] == "TTS service unavailable"

    def test_stage_context_has_stage_type(self):
        """Test that StageContext has stage type attribute."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr") as ctx:
                    assert ctx.stage == "asr"


class TestStageSpanHierarchy:
    """Tests for stage span parent-child relationships."""

    def test_stage_span_is_child_of_turn(self, span_exporter):
        """Test that stage spans are children of turn spans."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass

        spans = span_exporter.get_finished_spans()
        turn_span = [s for s in spans if s.name == "voice.turn"][0]
        asr_span = [s for s in spans if s.name == "voice.asr"][0]

        assert asr_span.parent is not None
        assert asr_span.parent.span_id == turn_span.context.span_id

    def test_multiple_stages_share_same_turn_parent(self, span_exporter):
        """Test that multiple stages in a turn share the same parent."""
        with voice_conversation():
            with voice_turn("agent"):
                with voice_stage("llm"):
                    pass
                with voice_stage("tts"):
                    pass

        spans = span_exporter.get_finished_spans()
        turn_span = [s for s in spans if s.name == "voice.turn"][0]
        llm_span = [s for s in spans if s.name == "voice.llm"][0]
        tts_span = [s for s in spans if s.name == "voice.tts"][0]

        assert llm_span.parent.span_id == turn_span.context.span_id
        assert tts_span.parent.span_id == turn_span.context.span_id

    def test_all_stages_share_same_trace_id(self, span_exporter):
        """Test that all stages share the same trace_id."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass
            with voice_turn("agent"):
                with voice_stage("llm"):
                    pass
                with voice_stage("tts"):
                    pass

        spans = span_exporter.get_finished_spans()
        trace_ids = {s.context.trace_id for s in spans}

        assert len(trace_ids) == 1

    def test_stage_span_kind_is_client(self, span_exporter):
        """Test that stage spans have CLIENT kind (calling external services)."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_stage("asr"):
                    pass

        spans = span_exporter.get_finished_spans()
        asr_span = [s for s in spans if s.name == "voice.asr"][0]

        assert asr_span.kind == SpanKind.CLIENT


class TestStageWithoutTurn:
    """Tests for stage spans outside of turn context."""

    def test_stage_works_without_turn(self, span_exporter):
        """Test that voice_stage works even without voice_turn."""
        with voice_conversation():
            with voice_stage("asr"):
                pass

        spans = span_exporter.get_finished_spans()
        asr_spans = [s for s in spans if s.name == "voice.asr"]
        assert len(asr_spans) == 1

    def test_stage_works_without_conversation(self, span_exporter):
        """Test that voice_stage works even without voice_conversation."""
        with voice_stage("asr", provider="deepgram"):
            pass

        spans = span_exporter.get_finished_spans()
        asr_spans = [s for s in spans if s.name == "voice.asr"]
        assert len(asr_spans) == 1

        # Should not have conversation ID
        attrs = dict(asr_spans[0].attributes)
        assert "voice.conversation.id" not in attrs
