"""Tests for timeline tracking and silence detection."""

import time
from unittest.mock import patch

from voiceobs import mark_speech_end, mark_speech_start, voice_conversation, voice_turn
from voiceobs.timeline import ConversationTimeline, TurnTiming


class TestTurnTiming:
    """Tests for the TurnTiming dataclass."""

    def test_duration_ms_when_complete(self):
        """Test duration calculation for completed turn."""
        timing = TurnTiming(
            turn_index=0,
            actor="user",
            start_time_ns=1_000_000_000,  # 1 second in ns
            end_time_ns=1_500_000_000,  # 1.5 seconds in ns
        )
        assert timing.duration_ms == 500.0

    def test_duration_ms_when_incomplete(self):
        """Test duration is None for incomplete turn."""
        timing = TurnTiming(
            turn_index=0,
            actor="user",
            start_time_ns=1_000_000_000,
        )
        assert timing.duration_ms is None


class TestConversationTimeline:
    """Tests for the ConversationTimeline class."""

    def test_start_turn_creates_timing(self):
        """Test that start_turn creates a TurnTiming object."""
        timeline = ConversationTimeline()
        timing = timeline.start_turn(0, "user")

        assert timing.turn_index == 0
        assert timing.actor == "user"
        assert timing.start_time_ns is not None
        assert timing.end_time_ns is None

    def test_end_turn_completes_timing(self):
        """Test that end_turn completes the current timing."""
        timeline = ConversationTimeline()
        timeline.start_turn(0, "user")
        completed = timeline.end_turn()

        assert completed is not None
        assert completed.end_time_ns is not None
        assert len(timeline.turns) == 1

    def test_end_turn_returns_none_when_no_turn(self):
        """Test that end_turn returns None when no turn in progress."""
        timeline = ConversationTimeline()
        assert timeline.end_turn() is None

    def test_get_last_turn_by_actor(self):
        """Test finding the last turn by a specific actor."""
        timeline = ConversationTimeline()

        # Add a user turn
        timeline.start_turn(0, "user")
        timeline.end_turn()

        # Add an agent turn
        timeline.start_turn(1, "agent")
        timeline.end_turn()

        # Add another user turn
        timeline.start_turn(2, "user")
        timeline.end_turn()

        last_user = timeline.get_last_turn_by_actor("user")
        assert last_user is not None
        assert last_user.turn_index == 2

        last_agent = timeline.get_last_turn_by_actor("agent")
        assert last_agent is not None
        assert last_agent.turn_index == 1

    def test_get_last_turn_by_actor_returns_none_when_not_found(self):
        """Test that get_last_turn_by_actor returns None when no matching turn."""
        timeline = ConversationTimeline()
        timeline.start_turn(0, "user")
        timeline.end_turn()

        assert timeline.get_last_turn_by_actor("agent") is None


class TestSilenceComputation:
    """Tests for silence duration computation."""

    def test_compute_silence_with_synthetic_timestamps(self):
        """Test silence computation with controlled timestamps."""
        timeline = ConversationTimeline()

        # Simulate user turn: 0ms to 1000ms
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):  # 1000ms
            timeline.end_turn()

        # Simulate agent turn starting at 1500ms (500ms silence)
        with patch("time.time_ns", return_value=1_500_000_000):  # 1500ms
            timeline.start_turn(1, "agent")

        silence = timeline.compute_silence_after_user_ms()
        assert silence == 500.0

    def test_compute_silence_returns_none_for_user_turn(self):
        """Test that silence is not computed for user turns."""
        timeline = ConversationTimeline()

        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")

        assert timeline.compute_silence_after_user_ms() is None

    def test_compute_silence_returns_none_without_prior_user_turn(self):
        """Test that silence is None when agent turn starts without prior user turn."""
        timeline = ConversationTimeline()

        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "agent")

        assert timeline.compute_silence_after_user_ms() is None

    def test_compute_silence_zero_gap(self):
        """Test silence computation when there's no gap."""
        timeline = ConversationTimeline()

        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=2_000_000_000):
            timeline.end_turn()

        # Agent starts immediately
        with patch("time.time_ns", return_value=2_000_000_000):
            timeline.start_turn(1, "agent")

        silence = timeline.compute_silence_after_user_ms()
        assert silence == 0.0

    def test_compute_silence_before_agent_ms_is_alias(self):
        """Test that compute_silence_before_agent_ms returns same value."""
        timeline = ConversationTimeline()

        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.end_turn()

        with patch("time.time_ns", return_value=1_250_000_000):
            timeline.start_turn(1, "agent")

        after_user = timeline.compute_silence_after_user_ms()
        before_agent = timeline.compute_silence_before_agent_ms()
        assert after_user == before_agent == 250.0


class TestSpeechEventMarkers:
    """Tests for speech event markers (mark_speech_end, mark_speech_start)."""

    def test_mark_speech_end_sets_timestamp(self):
        """Test that mark_speech_end records a timestamp."""
        timeline = ConversationTimeline()
        timeline.start_turn(0, "user")

        with patch("time.time_ns", return_value=500_000_000):
            timeline.mark_speech_end()

        assert timeline._current_turn.speech_end_time_ns == 500_000_000

    def test_mark_speech_start_sets_timestamp(self):
        """Test that mark_speech_start records a timestamp."""
        timeline = ConversationTimeline()
        timeline.start_turn(0, "agent")

        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_start()

        assert timeline._current_turn.speech_start_time_ns == 1_000_000_000

    def test_response_latency_with_speech_events(self):
        """Test response latency computation using speech events."""
        timeline = ConversationTimeline()

        # User turn with speech_end marked at 1000ms
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.end_turn()

        # Agent turn with speech_start marked at 2500ms
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=2_500_000_000):
            timeline.mark_speech_start()

        # Response latency = speech_start - speech_end = 2500 - 1000 = 1500ms
        latency = timeline.compute_response_latency_ms()
        assert latency == 1500.0

    def test_response_latency_returns_none_without_speech_end(self):
        """Test that response latency is None if speech_end not marked."""
        timeline = ConversationTimeline()

        # User turn without speech_end marked
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.end_turn()

        # Agent turn with speech_start marked
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=2_000_000_000):
            timeline.mark_speech_start()

        assert timeline.compute_response_latency_ms() is None

    def test_response_latency_returns_none_without_speech_start(self):
        """Test that response latency is None if speech_start not marked."""
        timeline = ConversationTimeline()

        # User turn with speech_end marked
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.end_turn()

        # Agent turn without speech_start marked
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")

        assert timeline.compute_response_latency_ms() is None

    def test_silence_prefers_speech_events_when_available(self):
        """Test that compute_silence_after_user_ms uses speech events if available."""
        timeline = ConversationTimeline()

        # User turn: ends at 1100ms, speech_end at 1000ms
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.end_turn()

        # Agent turn: starts at 1200ms, speech_start at 2500ms
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=2_500_000_000):
            timeline.mark_speech_start()

        # With speech events: silence = 2500 - 1000 = 1500ms
        silence = timeline.compute_silence_after_user_ms()
        assert silence == 1500.0

    def test_silence_falls_back_to_turn_boundaries(self):
        """Test that compute_silence_after_user_ms falls back to turn boundaries."""
        timeline = ConversationTimeline()

        # User turn without speech markers
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.end_turn()

        # Agent turn without speech markers
        with patch("time.time_ns", return_value=1_500_000_000):
            timeline.start_turn(1, "agent")

        # Without speech events: silence = agent_start - user_end = 1500 - 1000 = 500ms
        silence = timeline.compute_silence_after_user_ms()
        assert silence == 500.0

    def test_silence_returns_none_when_no_current_turn(self):
        """Test that compute_silence_after_user_ms returns None when no current turn."""
        timeline = ConversationTimeline()

        # User turn that gets ended
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.end_turn()

        # No current turn active
        silence = timeline.compute_silence_after_user_ms()
        assert silence is None

    def test_overlap_returns_none_when_no_current_turn(self):
        """Test that compute_overlap_ms returns None when no current turn."""
        timeline = ConversationTimeline()

        # No turn started at all
        overlap = timeline.compute_overlap_ms()
        assert overlap is None

    def test_overlap_returns_none_when_current_turn_is_user(self):
        """Test that compute_overlap_ms returns None when current turn is user."""
        timeline = ConversationTimeline()

        # Start a user turn
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")

        # Overlap is only computed for agent turns
        overlap = timeline.compute_overlap_ms()
        assert overlap is None


class TestSpeechEventsWithVoiceTurn:
    """Tests for speech event markers integrated with voice_turn."""

    def test_mark_speech_end_in_user_turn(self, span_exporter):
        """Test that mark_speech_end works within voice_turn context."""
        with voice_conversation() as conv:
            with voice_turn("user"):
                time.sleep(0.01)
                mark_speech_end()
                time.sleep(0.01)

        # Verify the speech_end was recorded
        user_turn = conv.timeline.get_last_turn_by_actor("user")
        assert user_turn is not None
        assert user_turn.speech_end_time_ns is not None

    def test_mark_speech_start_in_agent_turn(self, span_exporter):
        """Test that mark_speech_start works within voice_turn context."""
        with voice_conversation() as conv:
            with voice_turn("user"):
                mark_speech_end()

            with voice_turn("agent"):
                time.sleep(0.01)
                mark_speech_start()
                time.sleep(0.01)

        # Verify the speech_start was recorded
        agent_turn = conv.timeline.get_last_turn_by_actor("agent")
        assert agent_turn is not None
        assert agent_turn.speech_start_time_ns is not None

    def test_response_latency_in_span_with_speech_events(self, span_exporter):
        """Test that spans use speech events for accurate latency."""
        with voice_conversation():
            with voice_turn("user"):
                time.sleep(0.02)
                mark_speech_end()  # User stops speaking
                time.sleep(0.02)  # Processing time within user turn

            time.sleep(0.05)  # Gap between turns

            with voice_turn("agent"):
                time.sleep(0.1)  # LLM + TTS processing
                mark_speech_start()  # Agent starts speaking
                time.sleep(0.02)

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]
        agent_span = [s for s in turn_spans if dict(s.attributes).get("voice.actor") == "agent"][0]
        attrs = dict(agent_span.attributes)

        # The silence should be measured from speech_end to speech_start
        # which is ~170ms (20ms + 20ms + 50ms + 100ms - 20ms from mark)
        assert "voice.silence.after_user_ms" in attrs
        silence_ms = attrs["voice.silence.after_user_ms"]
        # Should capture the full latency from speech_end to speech_start
        assert silence_ms > 100  # At least the 100ms processing + 50ms gap


class TestSilenceInSpans:
    """Tests for silence attributes in OpenTelemetry spans."""

    def test_agent_turn_has_silence_attributes(self, span_exporter):
        """Test that agent turn spans have silence attributes."""
        with voice_conversation():
            with voice_turn("user"):
                time.sleep(0.05)  # 50ms user turn

            time.sleep(0.1)  # 100ms silence gap

            with voice_turn("agent"):
                pass

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]

        # Find agent turn span
        agent_span = None
        for span in turn_spans:
            if dict(span.attributes).get("voice.actor") == "agent":
                agent_span = span
                break

        assert agent_span is not None
        attrs = dict(agent_span.attributes)

        # Should have silence attributes
        assert "voice.silence.after_user_ms" in attrs
        assert "voice.silence.before_agent_ms" in attrs

        # Silence should be roughly 100ms (with some tolerance for test execution)
        silence_ms = attrs["voice.silence.after_user_ms"]
        assert 50 < silence_ms < 500  # Allow for timing variations

    def test_user_turn_does_not_have_silence_attributes(self, span_exporter):
        """Test that user turn spans don't have silence attributes."""
        with voice_conversation():
            with voice_turn("user"):
                pass

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]
        user_span = turn_spans[0]
        attrs = dict(user_span.attributes)

        assert "voice.silence.after_user_ms" not in attrs
        assert "voice.silence.before_agent_ms" not in attrs

    def test_first_agent_turn_without_user_has_no_silence(self, span_exporter):
        """Test that an agent turn without prior user turn has no silence."""
        with voice_conversation():
            with voice_turn("agent"):
                pass

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]
        agent_span = turn_spans[0]
        attrs = dict(agent_span.attributes)

        assert "voice.silence.after_user_ms" not in attrs

    def test_multiple_turn_pairs_each_have_silence(self, span_exporter):
        """Test that each user-agent pair has its own silence measurement."""
        with voice_conversation():
            # First pair
            with voice_turn("user"):
                time.sleep(0.02)
            time.sleep(0.05)  # ~50ms silence
            with voice_turn("agent"):
                time.sleep(0.02)

            # Second pair
            with voice_turn("user"):
                time.sleep(0.02)
            time.sleep(0.1)  # ~100ms silence
            with voice_turn("agent"):
                pass

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]

        agent_spans = [s for s in turn_spans if dict(s.attributes).get("voice.actor") == "agent"]
        assert len(agent_spans) == 2

        # Both should have silence attributes
        for span in agent_spans:
            attrs = dict(span.attributes)
            assert "voice.silence.after_user_ms" in attrs


class TestOverlapComputation:
    """Tests for overlap/interruption detection."""

    def test_compute_overlap_no_overlap(self):
        """Test overlap computation when there's no overlap (normal turn-taking)."""
        timeline = ConversationTimeline()

        # User turn: speech ends at 1000ms
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.end_turn()

        # Agent turn: speech starts at 2000ms (after user finished)
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=2_000_000_000):
            timeline.mark_speech_start()

        # Overlap = user_speech_end - agent_speech_start = 1000 - 2000 = -1000ms
        overlap = timeline.compute_overlap_ms()
        assert overlap == -1000.0
        assert not timeline.is_interruption()

    def test_compute_overlap_with_interruption(self):
        """Test overlap computation when agent interrupts user."""
        timeline = ConversationTimeline()

        # User turn: speech ends at 2000ms
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=2_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=2_100_000_000):
            timeline.end_turn()

        # Agent turn: speech starts at 1500ms (before user finished!)
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=1_500_000_000):
            timeline.mark_speech_start()

        # Overlap = user_speech_end - agent_speech_start = 2000 - 1500 = 500ms
        overlap = timeline.compute_overlap_ms()
        assert overlap == 500.0
        assert timeline.is_interruption()

    def test_compute_overlap_returns_none_without_speech_end(self):
        """Test that overlap is None if speech_end not marked."""
        timeline = ConversationTimeline()

        # User turn without speech_end
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.end_turn()

        # Agent turn with speech_start
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=1_500_000_000):
            timeline.mark_speech_start()

        assert timeline.compute_overlap_ms() is None
        assert not timeline.is_interruption()

    def test_compute_overlap_returns_none_without_speech_start(self):
        """Test that overlap is None if speech_start not marked."""
        timeline = ConversationTimeline()

        # User turn with speech_end
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.end_turn()

        # Agent turn without speech_start
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")

        assert timeline.compute_overlap_ms() is None
        assert not timeline.is_interruption()

    def test_compute_overlap_zero_overlap(self):
        """Test overlap computation when agent starts exactly when user ends."""
        timeline = ConversationTimeline()

        # User turn: speech ends at 1000ms
        with patch("time.time_ns", return_value=0):
            timeline.start_turn(0, "user")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_end()
        with patch("time.time_ns", return_value=1_100_000_000):
            timeline.end_turn()

        # Agent turn: speech starts at exactly 1000ms
        with patch("time.time_ns", return_value=1_200_000_000):
            timeline.start_turn(1, "agent")
        with patch("time.time_ns", return_value=1_000_000_000):
            timeline.mark_speech_start()

        overlap = timeline.compute_overlap_ms()
        assert overlap == 0.0
        assert not timeline.is_interruption()  # Zero overlap is not an interruption


class TestOverlapInSpans:
    """Tests for overlap attributes in OpenTelemetry spans."""

    def test_agent_turn_has_overlap_attributes_with_speech_events(self, span_exporter):
        """Test that agent turn spans have overlap attributes when speech events are marked."""
        with voice_conversation():
            with voice_turn("user"):
                time.sleep(0.02)
                mark_speech_end()
                time.sleep(0.02)

            with voice_turn("agent"):
                time.sleep(0.05)
                mark_speech_start()
                time.sleep(0.02)

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]
        agent_span = [s for s in turn_spans if dict(s.attributes).get("voice.actor") == "agent"][0]
        attrs = dict(agent_span.attributes)

        # Should have overlap attributes
        assert "voice.turn.overlap_ms" in attrs
        assert "voice.interruption.detected" in attrs
        # Normal turn-taking: overlap should be negative (no interruption)
        assert attrs["voice.turn.overlap_ms"] < 0
        assert attrs["voice.interruption.detected"] is False

    def test_agent_turn_no_overlap_without_speech_events(self, span_exporter):
        """Test that agent turn spans don't have overlap without speech events."""
        with voice_conversation():
            with voice_turn("user"):
                time.sleep(0.02)

            with voice_turn("agent"):
                time.sleep(0.02)

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]
        agent_span = [s for s in turn_spans if dict(s.attributes).get("voice.actor") == "agent"][0]
        attrs = dict(agent_span.attributes)

        # Should not have overlap attributes without speech events
        assert "voice.turn.overlap_ms" not in attrs
        assert "voice.interruption.detected" not in attrs

    def test_user_turn_does_not_have_overlap_attributes(self, span_exporter):
        """Test that user turn spans don't have overlap attributes."""
        with voice_conversation():
            with voice_turn("user"):
                mark_speech_end()

        spans = span_exporter.get_finished_spans()
        turn_spans = [s for s in spans if s.name == "voice.turn"]
        user_span = turn_spans[0]
        attrs = dict(user_span.attributes)

        assert "voice.turn.overlap_ms" not in attrs
        assert "voice.interruption.detected" not in attrs
