"""Tests for test suite generation_error field."""

from uuid import uuid4

from voiceobs.server.db.models import TestSuiteRow


class TestSuiteGenerationError:
    """Tests for the test suite generation_error field."""

    def test_test_suite_row_has_generation_error(self):
        """Test that TestSuiteRow has generation_error field."""
        suite = TestSuiteRow(
            id=uuid4(),
            org_id=uuid4(),
            name="Test Suite",
            status="generation_failed",
            generation_error="LLM service unavailable",
        )

        assert suite.generation_error == "LLM service unavailable"

    def test_test_suite_row_generation_error_optional(self):
        """Test that generation_error is optional."""
        suite = TestSuiteRow(
            id=uuid4(),
            org_id=uuid4(),
            name="Test Suite",
            status="ready",
        )

        assert suite.generation_error is None
