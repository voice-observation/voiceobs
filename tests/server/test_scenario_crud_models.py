"""Tests for test scenario CRUD Pydantic models.

This file tests the new CRUD fields for TestScenario models:
- caller_behaviors
- tags
- status
"""

from voiceobs.server.models import (
    TestScenarioCreateRequest,
    TestScenarioResponse,
    TestScenarioUpdateRequest,
)


class TestScenarioCreateRequestWithCrudFields:
    """Tests for TestScenarioCreateRequest with new CRUD fields."""

    def test_accepts_caller_behaviors(self):
        """Test that request accepts caller_behaviors field."""
        request = TestScenarioCreateRequest(
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            caller_behaviors=["Provide destination", "Confirm booking"],
        )
        assert request.caller_behaviors == ["Provide destination", "Confirm booking"]

    def test_accepts_tags(self):
        """Test that request accepts tags field."""
        request = TestScenarioCreateRequest(
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            tags=["happy-path", "booking", "high-priority"],
        )
        assert request.tags == ["happy-path", "booking", "high-priority"]

    def test_all_new_fields_together(self):
        """Test that request accepts all new CRUD fields together."""
        request = TestScenarioCreateRequest(
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Flight Booking",
            goal="User books a flight",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            max_turns=10,
            timeout=300,
            caller_behaviors=["Ask for flight to NYC", "Provide dates", "Confirm booking"],
            tags=["happy-path", "booking"],
        )
        assert request.caller_behaviors == [
            "Ask for flight to NYC",
            "Provide dates",
            "Confirm booking",
        ]
        assert request.tags == ["happy-path", "booking"]

    def test_new_fields_are_optional(self):
        """Test that new fields are optional."""
        request = TestScenarioCreateRequest(
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
        )
        # New fields should default to None or empty list
        assert request.caller_behaviors is None
        assert request.tags is None


class TestScenarioUpdateRequestWithCrudFields:
    """Tests for TestScenarioUpdateRequest with new CRUD fields."""

    def test_accepts_caller_behaviors(self):
        """Test that update request accepts caller_behaviors field."""
        request = TestScenarioUpdateRequest(
            caller_behaviors=["Updated step 1", "Updated step 2"],
        )
        assert request.caller_behaviors == ["Updated step 1", "Updated step 2"]

    def test_accepts_tags(self):
        """Test that update request accepts tags field."""
        request = TestScenarioUpdateRequest(
            tags=["updated-tag-1", "updated-tag-2"],
        )
        assert request.tags == ["updated-tag-1", "updated-tag-2"]

    def test_all_new_fields_together(self):
        """Test that update request accepts all new CRUD fields together."""
        request = TestScenarioUpdateRequest(
            name="Updated Name",
            goal="Updated goal",
            caller_behaviors=["Step A", "Step B"],
            tags=["tag-a", "tag-b"],
        )
        assert request.name == "Updated Name"
        assert request.goal == "Updated goal"
        assert request.caller_behaviors == ["Step A", "Step B"]
        assert request.tags == ["tag-a", "tag-b"]

    def test_new_fields_are_optional(self):
        """Test that new update fields are optional."""
        request = TestScenarioUpdateRequest()
        assert request.caller_behaviors is None
        assert request.tags is None


class TestScenarioResponseWithCrudFields:
    """Tests for TestScenarioResponse with new CRUD fields."""

    def test_includes_caller_behaviors(self):
        """Test that response includes caller_behaviors field."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            caller_behaviors=["Step 1", "Step 2"],
        )
        assert response.caller_behaviors == ["Step 1", "Step 2"]

    def test_includes_tags(self):
        """Test that response includes tags field."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            tags=["happy-path", "booking"],
        )
        assert response.tags == ["happy-path", "booking"]

    def test_includes_status(self):
        """Test that response includes status field."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            status="ready",
        )
        assert response.status == "ready"

    def test_status_defaults_to_draft(self):
        """Test that status defaults to 'draft' when not provided."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
        )
        assert response.status == "draft"

    def test_all_new_fields_together(self):
        """Test response with all new CRUD fields."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Flight Booking",
            goal="User books a flight",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
            max_turns=10,
            timeout=300,
            intent="book_flight",
            persona_traits=["impatient", "direct"],
            persona_match_score=0.85,
            caller_behaviors=["Ask for destination", "Provide dates", "Confirm"],
            tags=["happy-path", "booking"],
            status="ready",
        )
        assert response.id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.name == "Flight Booking"
        assert response.caller_behaviors == [
            "Ask for destination",
            "Provide dates",
            "Confirm",
        ]
        assert response.tags == ["happy-path", "booking"]
        assert response.status == "ready"

    def test_new_fields_are_optional(self):
        """Test that new response fields have reasonable defaults."""
        response = TestScenarioResponse(
            id="550e8400-e29b-41d4-a716-446655440000",
            suite_id="550e8400-e29b-41d4-a716-446655440001",
            name="Test Scenario",
            goal="Test goal",
            persona_id="550e8400-e29b-41d4-a716-446655440002",
        )
        # These should be None or have default values
        assert response.caller_behaviors is None
        assert response.tags is None
        assert response.status == "draft"  # status has a default
