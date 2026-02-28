"""JSON utility functions (e.g. JSONB parsing from asyncpg rows)."""

from __future__ import annotations

import json
from typing import Any


def parse_jsonb_list(value: Any) -> list[dict[str, Any]] | None:
    """Parse JSONB list from DB row (asyncpg may return str or list).

    Args:
        value: Raw value from DB (None, list, or JSON string).

    Returns:
        List of dicts, or None if value is None or not parseable as list.
    """
    if value is None:
        return None
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        parsed = json.loads(value) if value else None
        return parsed if isinstance(parsed, list) else None
    return None


def parse_jsonb_dict(value: Any) -> dict[str, Any] | None:
    """Parse JSONB dict from DB row (asyncpg may return str or dict).

    Args:
        value: Raw value from DB (None, dict, or JSON string).

    Returns:
        Dict, or None if value is None or not parseable as dict.
    """
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        parsed = json.loads(value) if value else None
        return parsed if isinstance(parsed, dict) else None
    return None
