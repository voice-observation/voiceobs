"""Tests for conversation and turn context management."""

import uuid

import pytest

from voiceobs import (
    VOICE_SCHEMA_VERSION,
    get_current_conversation,
    get_current_turn,
    voice_conversation,
    voice_turn,
)


class TestVoiceConversation:
    """Tests for voice_conversation context manager."""

    def test_auto_generates_uuid(self):
        """Test that conversation_id is auto-generated if not provided."""
        with voice_conversation() as conv:
            # Should be a valid UUID
            uuid.UUID(conv.conversation_id)

    def test_uses_provided_id(self):
        """Test that provided conversation_id is used."""
        custom_id = "my-custom-conversation-123"
        with voice_conversation(conversation_id=custom_id) as conv:
            assert conv.conversation_id == custom_id

    def test_context_available_inside(self):
        """Test that conversation context is available inside the context manager."""
        with voice_conversation() as conv:
            current = get_current_conversation()
            assert current is conv
            assert current.conversation_id == conv.conversation_id

    def test_context_none_outside(self):
        """Test that conversation context is None outside the context manager."""
        assert get_current_conversation() is None
        with voice_conversation():
            pass
        assert get_current_conversation() is None

    def test_turn_counter_starts_at_zero(self):
        """Test that turn counter starts at zero."""
        with voice_conversation() as conv:
            assert conv.turn_counter == 0

    def test_next_turn_index_increments(self):
        """Test that next_turn_index increments the counter."""
        with voice_conversation() as conv:
            assert conv.next_turn_index() == 0
            assert conv.next_turn_index() == 1
            assert conv.next_turn_index() == 2
            assert conv.turn_counter == 3


class TestVoiceTurn:
    """Tests for voice_turn context manager."""

    def test_requires_conversation_context(self):
        """Test that voice_turn raises error without conversation context."""
        with pytest.raises(RuntimeError, match="voice_conversation"):
            with voice_turn("user"):
                pass

    def test_turn_has_uuid(self):
        """Test that turn_id is a valid UUID."""
        with voice_conversation():
            with voice_turn("user") as turn:
                uuid.UUID(turn.turn_id)

    def test_turn_index_increments(self):
        """Test that turn indices increment within a conversation."""
        with voice_conversation():
            with voice_turn("user") as turn1:
                assert turn1.turn_index == 0
            with voice_turn("agent") as turn2:
                assert turn2.turn_index == 1
            with voice_turn("user") as turn3:
                assert turn3.turn_index == 2

    def test_turn_actor_set_correctly(self):
        """Test that actor is set correctly for each turn type."""
        with voice_conversation():
            with voice_turn("user") as turn:
                assert turn.actor == "user"
            with voice_turn("agent") as turn:
                assert turn.actor == "agent"
            with voice_turn("system") as turn:
                assert turn.actor == "system"

    def test_turn_context_available_inside(self):
        """Test that turn context is available inside the context manager."""
        with voice_conversation():
            with voice_turn("user") as turn:
                current = get_current_turn()
                assert current is turn

    def test_turn_context_none_outside(self):
        """Test that turn context is None outside the context manager."""
        assert get_current_turn() is None
        with voice_conversation():
            assert get_current_turn() is None
            with voice_turn("user"):
                pass
            assert get_current_turn() is None
        assert get_current_turn() is None


class TestNestedTurns:
    """Tests for nested turn scenarios."""

    def test_nested_turns_get_sequential_indices(self):
        """Test that nested turns still get sequential indices."""
        with voice_conversation():
            with voice_turn("user") as outer:
                assert outer.turn_index == 0
                with voice_turn("system") as inner:
                    assert inner.turn_index == 1
            with voice_turn("agent") as after:
                assert after.turn_index == 2

    def test_inner_turn_context_shadows_outer(self):
        """Test that inner turn context shadows the outer one."""
        with voice_conversation():
            with voice_turn("user") as outer:
                assert get_current_turn() is outer
                with voice_turn("system") as inner:
                    assert get_current_turn() is inner
                assert get_current_turn() is outer


class TestOpenTelemetrySpans:
    """Tests for OpenTelemetry span generation."""

    def test_turn_creates_span(self, span_exporter):
        """Test that voice_turn creates an OpenTelemetry span."""
        with voice_conversation():
            with voice_turn("user"):
                pass

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "voice.turn"

    def test_span_has_correct_attributes(self, span_exporter):
        """Test that span has all required attributes."""
        conv_id = "test-conversation-123"
        with voice_conversation(conversation_id=conv_id):
            with voice_turn("agent") as turn:
                turn_id = turn.turn_id

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 1
        attrs = dict(spans[0].attributes)

        assert attrs["voice.schema.version"] == VOICE_SCHEMA_VERSION
        assert attrs["voice.conversation.id"] == conv_id
        assert attrs["voice.turn.id"] == turn_id
        assert attrs["voice.turn.index"] == 0
        assert attrs["voice.actor"] == "agent"

    def test_multiple_turns_create_multiple_spans(self, span_exporter):
        """Test that multiple turns create multiple spans."""
        with voice_conversation():
            with voice_turn("user"):
                pass
            with voice_turn("agent"):
                pass
            with voice_turn("user"):
                pass

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 3

        # Check turn indices
        indices = [dict(s.attributes)["voice.turn.index"] for s in spans]
        assert indices == [0, 1, 2]

    def test_nested_turns_create_parent_child_spans(self, span_exporter):
        """Test that nested turns create parent-child span relationships."""
        with voice_conversation():
            with voice_turn("user"):
                with voice_turn("system"):
                    pass

        spans = span_exporter.get_finished_spans()
        assert len(spans) == 2

        # Inner span should have outer span as parent
        inner_span = spans[0]  # Finished first
        outer_span = spans[1]  # Finished last

        assert inner_span.parent is not None
        assert inner_span.parent.span_id == outer_span.context.span_id

    def test_span_kind_is_internal(self, span_exporter):
        """Test that span kind is INTERNAL."""
        from opentelemetry.trace import SpanKind

        with voice_conversation():
            with voice_turn("user"):
                pass

        spans = span_exporter.get_finished_spans()
        assert spans[0].kind == SpanKind.INTERNAL
