"""Tests for the FastAPI app creation."""

from fastapi import FastAPI

from voiceobs._version import __version__
from voiceobs.server.app import create_app


class TestAppCreation:
    """Tests for the FastAPI app creation."""

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance."""
        app = create_app()

        assert isinstance(app, FastAPI)

    def test_app_has_correct_metadata(self):
        """Test that app has correct metadata."""
        app = create_app()

        assert app.title == "voiceobs"
        assert app.version == __version__

    def test_app_has_docs_endpoints(self, client):
        """Test that docs endpoints are available."""
        # OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200

        # Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200
