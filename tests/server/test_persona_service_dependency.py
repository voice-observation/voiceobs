"""Tests for PersonaService dependency."""

import pytest


class TestGetPersonaService:
    """Tests for get_persona_service dependency."""

    def test_get_persona_service_returns_service(self):
        """get_persona_service raises RuntimeError when not initialized."""
        from voiceobs.server.dependencies import get_persona_service

        with pytest.raises(RuntimeError, match="Persona service"):
            get_persona_service()
