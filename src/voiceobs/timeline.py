"""Timeline tracking for voice conversations.

This module tracks the timing of turns within a conversation to compute
silence and overlap metrics.

Key timing events for voice latency:
- user_speech_end: When the user stops speaking (VAD silence detection)
- agent_speech_start: When the agent's TTS audio playback begins

The "response latency" that users perceive is the gap between these two events.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Literal

from voiceobs.types import Actor

# Event types that can be marked in the timeline
EventType = Literal["speech_end", "speech_start"]


@dataclass
class TurnTiming:
    """Timing information for a single turn."""

    turn_index: int
    actor: Actor
    start_time_ns: int
    end_time_ns: int | None = None

    # Speech timing events (optional, for more accurate latency tracking)
    speech_end_time_ns: int | None = None
    speech_start_time_ns: int | None = None

    @property
    def duration_ms(self) -> float | None:
        """Get the duration of this turn in milliseconds."""
        if self.end_time_ns is None:
            return None
        return (self.end_time_ns - self.start_time_ns) / 1_000_000


@dataclass
class ConversationTimeline:
    """Tracks timing of turns within a conversation.

    Used to compute silence duration between turns. For accurate latency
    measurement, users should call mark_speech_end() when user stops speaking
    and mark_speech_start() when agent audio begins.
    """

    turns: list[TurnTiming] = field(default_factory=list)
    _current_turn: TurnTiming | None = field(default=None, repr=False)

    def start_turn(self, turn_index: int, actor: Actor) -> TurnTiming:
        """Record the start of a turn.

        Args:
            turn_index: The index of this turn in the conversation.
            actor: The actor for this turn.

        Returns:
            The TurnTiming object for this turn.
        """
        timing = TurnTiming(
            turn_index=turn_index,
            actor=actor,
            start_time_ns=time.time_ns(),
        )
        self._current_turn = timing
        return timing

    def end_turn(self) -> TurnTiming | None:
        """Record the end of the current turn.

        Returns:
            The completed TurnTiming, or None if no turn was in progress.
        """
        if self._current_turn is None:
            return None

        self._current_turn.end_time_ns = time.time_ns()
        self.turns.append(self._current_turn)
        completed = self._current_turn
        self._current_turn = None
        return completed

    def mark_speech_end(self) -> None:
        """Mark when speech ends in the current turn.

        For user turns, this should be called when the user stops speaking
        (e.g., when VAD detects silence or recording stops).
        """
        if self._current_turn is not None:
            self._current_turn.speech_end_time_ns = time.time_ns()

    def mark_speech_start(self, timestamp_ns: int | None = None) -> None:
        """Mark when speech starts in the current turn.

        For agent turns, this should be called when TTS audio playback begins.

        Args:
            timestamp_ns: Optional timestamp in nanoseconds. If not provided,
                uses the current time. This can be used to backdate the speech
                start for barge-in scenarios where the agent logically started
                responding earlier than actual playback.
        """
        if self._current_turn is not None:
            self._current_turn.speech_start_time_ns = timestamp_ns or time.time_ns()

    def get_last_turn_by_actor(self, actor: Actor) -> TurnTiming | None:
        """Get the most recent completed turn by a specific actor.

        Args:
            actor: The actor to find.

        Returns:
            The most recent TurnTiming for that actor, or None.
        """
        for turn in reversed(self.turns):
            if turn.actor == actor:
                return turn
        return None

    def compute_response_latency_ms(self) -> float | None:
        """Compute the response latency from user speech end to agent speech start.

        This is the latency that users actually perceive - the time between
        when they stop speaking and when the agent's response starts playing.

        Returns:
            Response latency in milliseconds, or None if events not marked.
        """
        if self._current_turn is None or self._current_turn.actor != "agent":
            return None

        # Need speech_start marked on current agent turn
        if self._current_turn.speech_start_time_ns is None:
            return None

        # Need speech_end marked on last user turn
        last_user_turn = self.get_last_turn_by_actor("user")
        if last_user_turn is None or last_user_turn.speech_end_time_ns is None:
            return None

        latency_ns = self._current_turn.speech_start_time_ns - last_user_turn.speech_end_time_ns
        return max(0, latency_ns / 1_000_000)

    def compute_silence_after_user_ms(self) -> float | None:
        """Compute silence duration after the last user turn ended.

        If speech_end was marked on the user turn and speech_start on the agent
        turn, returns the actual response latency. Otherwise, falls back to
        measuring the gap between turn context boundaries.

        Returns:
            Silence duration in milliseconds, or None if not applicable.
        """
        # Try to use precise speech events first
        latency = self.compute_response_latency_ms()
        if latency is not None:
            return latency

        # Fall back to turn boundary timing
        if self._current_turn is None:
            return None

        if self._current_turn.actor != "agent":
            return None

        last_user_turn = self.get_last_turn_by_actor("user")
        if last_user_turn is None or last_user_turn.end_time_ns is None:
            return None

        silence_ns = self._current_turn.start_time_ns - last_user_turn.end_time_ns
        return max(0, silence_ns / 1_000_000)

    def compute_silence_before_agent_ms(self) -> float | None:
        """Alias for compute_silence_after_user_ms.

        Both measure the same gap from different perspectives.
        """
        return self.compute_silence_after_user_ms()

    def compute_overlap_ms(self) -> float | None:
        """Compute overlap duration when agent starts speaking before user finishes.

        Overlap occurs when the agent's speech starts before the user's speech ends.
        This is common in real-time/streaming voice pipelines where the agent may
        start responding while the user is still speaking (interruption).

        Returns:
            Overlap duration in milliseconds (positive = overlap, negative = gap),
            or None if speech events not marked.

        Note:
            - Positive value: Agent started speaking before user finished (interruption)
            - Zero or negative: No overlap (normal turn-taking)
        """
        if self._current_turn is None or self._current_turn.actor != "agent":
            return None

        # Need speech_start marked on current agent turn
        if self._current_turn.speech_start_time_ns is None:
            return None

        # Need speech_end marked on last user turn
        last_user_turn = self.get_last_turn_by_actor("user")
        if last_user_turn is None or last_user_turn.speech_end_time_ns is None:
            return None

        # Overlap = user_speech_end - agent_speech_start
        # If positive, agent started speaking before user finished
        overlap_ns = last_user_turn.speech_end_time_ns - self._current_turn.speech_start_time_ns
        return overlap_ns / 1_000_000

    def is_interruption(self) -> bool:
        """Check if the current agent turn is an interruption.

        An interruption occurs when the agent starts speaking before the user
        finishes speaking (overlap > 0).

        Returns:
            True if the agent interrupted the user, False otherwise.
        """
        overlap = self.compute_overlap_ms()
        if overlap is None:
            return False
        return overlap > 0
