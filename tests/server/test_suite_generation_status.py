"""Tests for test suite generation status."""

from voiceobs.server.models import TestSuiteResponse


class TestSuiteGenerationStatus:
    """Tests for the test suite generation status field."""

    def test_test_suite_response_accepts_generating_status(self):
        """Test that TestSuiteResponse accepts 'generating' status."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Suite",
            description=None,
            status="generating",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
        )
        assert response.status == "generating"

    def test_test_suite_response_accepts_ready_status(self):
        """Test that TestSuiteResponse accepts 'ready' status."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Suite",
            description=None,
            status="ready",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
        )
        assert response.status == "ready"

    def test_test_suite_response_accepts_generation_failed_status(self):
        """Test that TestSuiteResponse accepts 'generation_failed' status."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Suite",
            description=None,
            status="generation_failed",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
            generation_error="LLM service unavailable",
        )
        assert response.status == "generation_failed"
        assert response.generation_error == "LLM service unavailable"

    def test_test_suite_response_includes_scenario_count(self):
        """Test that TestSuiteResponse includes scenario_count."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Suite",
            description=None,
            status="ready",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
            scenario_count=5,
        )
        assert response.scenario_count == 5

    def test_test_suite_response_generation_error_defaults_to_none(self):
        """Test that generation_error defaults to None."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Suite",
            description=None,
            status="pending",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
        )
        assert response.generation_error is None

    def test_test_suite_response_scenario_count_defaults_to_none(self):
        """Test that scenario_count defaults to None."""
        response = TestSuiteResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="Test Suite",
            description=None,
            status="pending",
            agent_id="550e8400-e29b-41d4-a716-446655440001",
            test_scopes=["core_flows"],
            thoroughness=1,
            edge_cases=[],
            evaluation_strictness="balanced",
            created_at=None,
        )
        assert response.scenario_count is None
