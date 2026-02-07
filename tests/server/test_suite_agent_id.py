"""Tests for test suite agent_id field."""

import pytest
from pydantic import ValidationError

from voiceobs.server.models import TestSuiteCreateRequest, TestSuiteResponse


class TestSuiteAgentIdField:
    """Tests for the test suite agent_id field."""

    def test_test_suite_create_request_requires_agent_id(self):
        """Test that TestSuiteCreateRequest requires agent_id."""
        with pytest.raises(ValidationError) as exc_info:
            TestSuiteCreateRequest(
                name="Test Suite",
                description="A test suite",
                # Missing agent_id
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("agent_id",) for e in errors)

    def test_test_suite_create_request_accepts_agent_id(self):
        """Test that TestSuiteCreateRequest accepts agent_id."""
        request = TestSuiteCreateRequest(
            name="Test Suite",
            description="A test suite",
            agent_id="550e8400-e29b-41d4-a716-446655440000",
        )

        assert request.agent_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_test_suite_response_includes_agent_id(self):
        """Test that TestSuiteResponse includes agent_id."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Suite",
            description=None,
            status="pending",
            agent_id="550e8400-e29b-41d4-a716-446655440000",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
        )

        assert response.agent_id == "550e8400-e29b-41d4-a716-446655440000"
