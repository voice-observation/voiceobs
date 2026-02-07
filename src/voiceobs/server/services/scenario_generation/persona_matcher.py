"""Service for matching scenarios to the best available persona."""

from __future__ import annotations

from dataclasses import dataclass

from voiceobs.server.db.models import PersonaRow

# Minimum score threshold for accepting a trait match
MIN_MATCH_THRESHOLD = 0.25


@dataclass
class PersonaMatch:
    """Result of a persona match operation."""

    persona: PersonaRow
    score: float  # 0.0 to 1.0, how well the persona matches desired traits


class PersonaMatcher:
    """Matches desired persona traits to available personas."""

    def __init__(self, personas: list[PersonaRow]) -> None:
        """Initialize the persona matcher.

        Args:
            personas: List of available personas to match against.

        Raises:
            ValueError: If no personas are provided.
        """
        if not personas:
            raise ValueError("No personas available for matching")
        self._personas = personas
        # Find the default persona for fallback
        self._default_persona = next(
            (p for p in personas if p.is_default),
            personas[0],  # Fallback to first if no default marked
        )

    def find_best_match(self, desired_traits: list[str]) -> PersonaMatch:
        """Find the persona that best matches the desired traits.

        Uses Jaccard similarity to score trait matches. If no traits are
        specified or the best match score is below MIN_MATCH_THRESHOLD,
        returns the default persona.

        Args:
            desired_traits: List of trait strings to match.

        Returns:
            PersonaMatch with best matching persona and score.
        """
        if not desired_traits:
            return PersonaMatch(persona=self._default_persona, score=0.0)

        best_match: PersonaMatch | None = None
        desired_set = {t.lower() for t in desired_traits}

        for persona in self._personas:
            persona_traits = {t.lower() for t in persona.traits}

            if not persona_traits:
                score = 0.0
            else:
                # Calculate Jaccard similarity
                intersection = len(desired_set & persona_traits)
                union = len(desired_set | persona_traits)
                score = intersection / union if union > 0 else 0.0

            if best_match is None or score > best_match.score:
                best_match = PersonaMatch(persona=persona, score=score)

        assert best_match is not None

        # If best score is below threshold, fall back to default persona
        if best_match.score < MIN_MATCH_THRESHOLD:
            return PersonaMatch(persona=self._default_persona, score=best_match.score)

        return best_match
