"""Shared fixtures for server tests."""

import pytest
from fastapi.testclient import TestClient

from voiceobs.server.app import create_app
from voiceobs.server.dependencies import reset_dependencies


@pytest.fixture(autouse=True)
def prevent_database_access(request, monkeypatch):
    """Prevent tests from accessing real PostgreSQL databases.

    This fixture runs automatically for all tests in the server test suite.
    It removes the database URL from the environment and mocks database
    initialization to prevent tests from accidentally writing to a real
    PostgreSQL database.

    Tests in TestGetDatabaseUrl are excluded from the mock since they
    explicitly test the _get_database_url function.
    """
    # Remove database URL from environment if set
    monkeypatch.delenv("VOICEOBS_DATABASE_URL", raising=False)

    # Skip mocking for tests that explicitly test _get_database_url
    test_class = getattr(request.node, "cls", None)
    if test_class and test_class.__name__ == "TestGetDatabaseUrl":
        yield
        return

    # Mock init_database to prevent actual database connections
    # Instead of connecting to a real database, we set up the module-level
    # repository/service variables with mock objects
    # IMPORTANT: Patch where the function is USED (app.py), not where it's defined
    async def mock_init_database():
        """Mock database initialization that sets up mock repositories."""
        from unittest.mock import AsyncMock
        from uuid import uuid4

        import voiceobs.server.dependencies as deps

        # Set up all module-level repository variables with mocks
        deps._conversation_repo = AsyncMock()
        deps._turn_repo = AsyncMock()
        deps._failure_repo = AsyncMock()
        deps._metrics_repo = AsyncMock()
        deps._persona_repo = AsyncMock()
        deps._agent_repo = AsyncMock()
        deps._test_suite_repo = AsyncMock()
        deps._test_scenario_repo = AsyncMock()
        deps._test_execution_repo = AsyncMock()
        deps._user_repo = AsyncMock()
        deps._organization_repo = AsyncMock()
        deps._organization_member_repo = AsyncMock()
        deps._organization_invite_repo = AsyncMock()
        deps._organization_service = AsyncMock()
        deps._agent_verification_service = AsyncMock()
        deps._scenario_generation_service = AsyncMock()

        # Create a simple stateful mock storage adapter
        from voiceobs.server.db.models.span import SpanRow

        class MockStorage:
            """Simple in-memory storage for testing."""

            def __init__(self):
                self.spans = {}

            async def add_span(
                self,
                name: str,
                start_time: str | None = None,
                end_time: str | None = None,
                duration_ms: float | None = None,
                attributes: dict | None = None,
                trace_id: str | None = None,
                span_id: str | None = None,
                parent_span_id: str | None = None,
            ):
                """Add a span and return its ID."""
                from datetime import datetime

                new_span_id = uuid4()
                span = SpanRow(
                    id=new_span_id,
                    name=name,
                    start_time=datetime.fromisoformat(start_time) if start_time else None,
                    end_time=datetime.fromisoformat(end_time) if end_time else None,
                    duration_ms=duration_ms,
                    attributes=attributes or {},
                    trace_id=trace_id,
                    span_id=span_id,
                    parent_span_id=parent_span_id,
                    conversation_id=None,
                    created_at=datetime.now(),
                )
                self.spans[new_span_id] = span
                return new_span_id

            async def get_span(self, span_id):
                """Get a span by ID."""
                return self.spans.get(span_id)

            async def get_all_spans(self):
                """Get all spans."""
                return list(self.spans.values())

            async def get_spans_as_dicts(self, **kwargs):
                """Get spans as dicts with optional filtering."""
                return [
                    {
                        "id": str(span.id),
                        "name": span.name,
                        "start_time": span.start_time.isoformat() if span.start_time else None,
                        "end_time": span.end_time.isoformat() if span.end_time else None,
                        "duration_ms": span.duration_ms,
                        "attributes": span.attributes,
                        "trace_id": span.trace_id,
                        "span_id": span.span_id,
                        "parent_span_id": span.parent_span_id,
                    }
                    for span in self.spans.values()
                ]

            async def count(self):
                """Get count of spans."""
                return len(self.spans)

            async def clear(self):
                """Clear all spans."""
                count = len(self.spans)
                self.spans.clear()
                return count

        deps._span_storage = MockStorage()

        # Mark as using postgres (so getters don't fail)
        deps._using_postgres = True

    monkeypatch.setattr(
        "voiceobs.server.app.init_database",
        mock_init_database,
    )

    # Also mock shutdown_database
    async def mock_shutdown_database():
        """Mock database shutdown that cleans up."""
        pass

    monkeypatch.setattr(
        "voiceobs.server.app.shutdown_database",
        mock_shutdown_database,
    )

    yield


@pytest.fixture
def client():
    """Create a test client for the server."""
    reset_dependencies()
    app = create_app()
    with TestClient(app) as client:
        yield client
    reset_dependencies()
