"""Collects conversation items into a transcript list."""

from __future__ import annotations

import time
from typing import Any


class TranscriptCollector:
    """Collects conversation items into a transcript list."""

    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def __call__(self, event: Any) -> None:
        text = getattr(event.item, "text_content", "") or ""
        role = getattr(event.item, "role", "unknown")
        ts_ms = int(time.monotonic() * 1000)
        mapped_role = "persona" if role == "user" else "agent"
        self.items.append({"role": mapped_role, "text": text, "timestamp_ms": ts_ms})
