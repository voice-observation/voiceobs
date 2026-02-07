"""Tests for persona request model validation."""

import pytest
from pydantic import ValidationError

from voiceobs.server.models.request.persona import PersonaCreateRequest, PersonaUpdateRequest


class TestPersonaCreateRequestTraitValidation:
    """Tests for trait validation in PersonaCreateRequest."""

    def test_accepts_valid_traits(self):
        """Test that valid traits are accepted."""
        request = PersonaCreateRequest(
            name="Test Persona",
            traits=["angry", "impatient", "demanding"],
        )
        assert request.traits == ["angry", "impatient", "demanding"]

    def test_rejects_invalid_traits(self):
        """Test that invalid traits raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaCreateRequest(
                name="Test Persona",
                traits=["angry", "made_up_trait"],
            )
        assert "Invalid traits" in str(exc_info.value)
        assert "made_up_trait" in str(exc_info.value)

    def test_accepts_empty_traits(self):
        """Test that empty traits list is accepted."""
        request = PersonaCreateRequest(
            name="Test Persona",
            traits=[],
        )
        assert request.traits == []

    def test_case_sensitive_trait_validation(self):
        """Test that trait validation is case sensitive (lowercase only)."""
        # Valid lowercase
        request = PersonaCreateRequest(
            name="Test Persona",
            traits=["angry"],
        )
        assert request.traits == ["angry"]


class TestPersonaUpdateRequestTraitValidation:
    """Tests for trait validation in PersonaUpdateRequest."""

    def test_accepts_valid_traits(self):
        """Test that valid traits are accepted."""
        request = PersonaUpdateRequest(
            traits=["calm", "cooperative", "polite"],
        )
        assert request.traits == ["calm", "cooperative", "polite"]

    def test_rejects_invalid_traits(self):
        """Test that invalid traits raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PersonaUpdateRequest(
                traits=["calm", "nonexistent_trait"],
            )
        assert "Invalid traits" in str(exc_info.value)

    def test_accepts_none_traits(self):
        """Test that None traits (no update) is accepted."""
        request = PersonaUpdateRequest(
            name="Updated Name",
            traits=None,
        )
        assert request.traits is None
