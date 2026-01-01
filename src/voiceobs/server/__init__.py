"""voiceobs server module.

This module provides a REST API server for voiceobs using FastAPI.
"""


# Lazy import to avoid requiring FastAPI when only using database modules
def create_app():
    """Create FastAPI application (lazy import)."""
    from voiceobs.server.app import create_app as _create_app

    return _create_app()


__all__ = ["create_app"]
