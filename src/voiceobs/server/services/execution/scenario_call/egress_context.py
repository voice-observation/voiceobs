"""Mutable state shared between before_dial and after_conversation hooks."""

from __future__ import annotations

from dataclasses import dataclass

from livekit import api


@dataclass
class EgressContext:
    """Mutable state shared between before_dial and after_conversation hooks."""

    api_client: api.LiveKitAPI | None = None
    egress_id: str | None = None
    audio_url: str | None = None
