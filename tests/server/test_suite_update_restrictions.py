"""Tests for test suite update restrictions."""

import pytest
from pydantic import ValidationError

from voiceobs.server.models import TestSuiteUpdateRequest


class TestSuiteUpdateRestrictions:
    """Tests for test suite update field restrictions."""

    def test_update_request_only_allows_name_and_description(self):
        """Test that TestSuiteUpdateRequest only has name and description."""
        request = TestSuiteUpdateRequest(
            name="Updated Name",
            description="Updated description",
        )

        assert request.name == "Updated Name"
        assert request.description == "Updated description"

        # These fields should not exist on the model
        assert not hasattr(request, "agent_id")
        assert not hasattr(request, "test_scopes")
        assert not hasattr(request, "thoroughness")
        assert not hasattr(request, "edge_cases")
        assert not hasattr(request, "evaluation_strictness")
        assert not hasattr(request, "status")

    def test_update_request_allows_partial_update_name_only(self):
        """Test that only name can be updated."""
        request = TestSuiteUpdateRequest(name="Updated Name")

        assert request.name == "Updated Name"
        assert request.description is None

    def test_update_request_allows_partial_update_description_only(self):
        """Test that only description can be updated."""
        request = TestSuiteUpdateRequest(description="Updated description")

        assert request.name is None
        assert request.description == "Updated description"

    def test_update_request_name_requires_min_length(self):
        """Test that name requires minimum length of 1."""
        with pytest.raises(ValidationError) as exc_info:
            TestSuiteUpdateRequest(name="")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name",) for e in errors)

    def test_update_request_model_fields_are_restricted(self):
        """Test that the model only exposes name and description fields."""
        # Get all field names from the model
        field_names = set(TestSuiteUpdateRequest.model_fields.keys())

        # Should only have name and description
        assert field_names == {"name", "description"}
