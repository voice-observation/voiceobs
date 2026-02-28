"""Utility functions for the voiceobs server."""

from __future__ import annotations

# Import lightweight modules first. Defer common/persona to avoid circular import
# when utils is loaded early (e.g. agent_verification.phone_verifier -> async_helpers)
from voiceobs.server.utils.async_helpers import log_timing, safe_cleanup
from voiceobs.server.utils.json_utils import parse_jsonb_dict, parse_jsonb_list
from voiceobs.server.utils.media import get_extension_from_content_type
from voiceobs.server.utils.queue_utils import region_from_queue_url
from voiceobs.server.utils.storage import get_audio_storage_from_env

__all__ = [
    "analysis_result_to_response",
    "get_extension_from_content_type",
    "parse_jsonb_dict",
    "parse_jsonb_list",
    "log_timing",
    "parse_iso_datetime",
    "parse_uuid",
    "region_from_queue_url",
    "resolve_persona_for_scenario",
    "safe_cleanup",
    "get_audio_storage_from_env",
]


def __getattr__(name: str) -> object:
    """Lazy import for modules that depend on voiceobs.server.models."""
    if name == "analysis_result_to_response":
        from voiceobs.server.utils.common import analysis_result_to_response

        return analysis_result_to_response
    if name == "parse_iso_datetime":
        from voiceobs.server.utils.common import parse_iso_datetime

        return parse_iso_datetime
    if name == "parse_uuid":
        from voiceobs.server.utils.common import parse_uuid

        return parse_uuid
    if name == "resolve_persona_for_scenario":
        from voiceobs.server.utils.persona import resolve_persona_for_scenario

        return resolve_persona_for_scenario
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
