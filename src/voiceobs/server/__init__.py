"""voiceobs server module.

This module provides a REST API server for voiceobs using FastAPI.
"""

from voiceobs.server.app import create_app

__all__ = ["create_app"]
