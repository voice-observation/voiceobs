"""Tests for the persona matcher service."""

from uuid import uuid4

import pytest

from voiceobs.server.db.models import PersonaRow
from voiceobs.server.services.scenario_generation import PersonaMatch, PersonaMatcher


def make_persona(
    name: str,
    traits: list[str],
    is_default: bool = False,
) -> PersonaRow:
    """Create a PersonaRow for testing."""
    return PersonaRow(
        id=uuid4(),
        name=name,
        aggression=0.5,
        patience=0.5,
        verbosity=0.5,
        tts_provider="deepgram",
        traits=traits,
        is_default=is_default,
    )


class TestPersonaMatcher:
    """Tests for the PersonaMatcher class."""

    def test_exact_trait_match_returns_best_persona_with_high_score(self):
        """Test that an exact trait match returns the persona with score 1.0."""
        personas = [
            make_persona("Impatient Customer", ["impatient", "direct"]),
            make_persona("Friendly Helper", ["friendly", "patient"]),
        ]
        matcher = PersonaMatcher(personas)

        result = matcher.find_best_match(["impatient", "direct"])

        assert result.persona.name == "Impatient Customer"
        assert result.score == 1.0

    def test_partial_trait_match_returns_best_persona_with_partial_score(self):
        """Test that partial trait overlap returns best persona with partial score."""
        personas = [
            make_persona("Mixed Persona", ["impatient", "friendly", "verbose"]),
            make_persona("Different", ["calm", "quiet"]),
        ]
        matcher = PersonaMatcher(personas)

        # Jaccard: intersection=1 (impatient), union=4 (impatient, friendly, verbose, direct)
        # Score = 1/4 = 0.25
        result = matcher.find_best_match(["impatient", "direct"])

        assert result.persona.name == "Mixed Persona"
        assert result.score == pytest.approx(0.25)

    def test_empty_traits_returns_default_persona_with_zero_score(self):
        """Test that empty desired traits returns the default persona with score 0.0."""
        default_persona = make_persona("Default", ["neutral"], is_default=True)
        personas = [
            make_persona("Other", ["impatient"]),
            default_persona,
        ]
        matcher = PersonaMatcher(personas)

        result = matcher.find_best_match([])

        assert result.persona.name == "Default"
        assert result.score == 0.0

    def test_low_match_score_falls_back_to_default_persona(self):
        """Test that a match score below threshold falls back to default persona."""
        default_persona = make_persona("Default", ["neutral"], is_default=True)
        personas = [
            make_persona("Other", ["angry", "loud", "demanding", "rude"]),
            default_persona,
        ]
        matcher = PersonaMatcher(personas)

        # Jaccard: intersection=1 (angry), union=5 (angry, loud, demanding, rude, calm)
        # Score = 1/5 = 0.2 < MIN_MATCH_THRESHOLD (0.25)
        result = matcher.find_best_match(["angry", "calm"])

        assert result.persona.name == "Default"
        # Score should still reflect the actual calculation
        assert result.score < 0.25

    def test_empty_persona_list_raises_value_error(self):
        """Test that initializing with empty personas raises ValueError."""
        with pytest.raises(ValueError, match="No personas available"):
            PersonaMatcher([])

    def test_case_insensitive_trait_matching(self):
        """Test that trait matching is case insensitive."""
        personas = [
            make_persona("Test", ["IMPATIENT", "DIRECT"]),
        ]
        matcher = PersonaMatcher(personas)

        result = matcher.find_best_match(["impatient", "direct"])

        assert result.score == 1.0

    def test_falls_back_to_first_persona_when_no_default_marked(self):
        """Test that the first persona is used as fallback when none is marked default."""
        first_persona = make_persona("First", ["friendly"])
        personas = [
            first_persona,
            make_persona("Second", ["angry"]),
        ]
        matcher = PersonaMatcher(personas)

        # Empty traits should return the fallback (first persona since no default)
        result = matcher.find_best_match([])

        assert result.persona.name == "First"

    def test_persona_with_empty_traits_scores_zero(self):
        """Test that a persona with empty traits scores 0 against any desired traits."""
        default_persona = make_persona("Default", [], is_default=True)
        personas = [
            make_persona("Has Traits", ["impatient", "direct"]),
            default_persona,
        ]
        matcher = PersonaMatcher(personas)

        result = matcher.find_best_match(["impatient", "direct"])

        # The persona with traits should match, not the one with empty traits
        assert result.persona.name == "Has Traits"
        assert result.score == 1.0


class TestPersonaMatch:
    """Tests for the PersonaMatch dataclass."""

    def test_persona_match_creation(self):
        """Test creating a PersonaMatch instance."""
        persona = make_persona("Test", ["trait1"])
        match = PersonaMatch(persona=persona, score=0.75)

        assert match.persona == persona
        assert match.score == 0.75
