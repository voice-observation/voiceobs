"""PersonaDNA class for defining personality traits."""

from __future__ import annotations


class PersonaDNA:
    """Represents personality traits for simulation LLM."""

    def __init__(
        self,
        aggression: float,
        patience: float,
        verbosity: float,
        traits: list[str] | None = None,
    ) -> None:
        """Initialize PersonaDNA with trait values.

        Args:
            aggression: Aggression level between 0 and 1 (0=passive, 1=aggressive)
            patience: Patience level between 0 and 1 (0=impatient, 1=patient)
            verbosity: Verbosity level between 0 and 1 (0=concise, 1=verbose)
            traits: Optional list of additional trait descriptors

        Raises:
            ValueError: If any trait value is outside [0, 1] range
        """
        if not 0 <= aggression <= 1:
            raise ValueError("aggression must be between 0 and 1")
        if not 0 <= patience <= 1:
            raise ValueError("patience must be between 0 and 1")
        if not 0 <= verbosity <= 1:
            raise ValueError("verbosity must be between 0 and 1")

        self.aggression = aggression
        self.patience = patience
        self.verbosity = verbosity
        self.traits = traits or []

    def get_personality_directives(self) -> str:
        """Convert traits into personality directive text.

        Returns:
            Formatted string describing personality traits
        """
        directives = []

        # Aggression description
        if self.aggression >= 0.7:
            msg = f"High aggression ({self.aggression}): You interrupt if responses are slow"
            directives.append(msg)
        elif self.aggression >= 0.4:
            msg = f"Moderate aggression ({self.aggression}): You may interrupt if necessary"
            directives.append(msg)
        else:
            directives.append(f"Low aggression ({self.aggression}): You wait for responses")

        # Patience description
        if self.patience <= 0.3:
            directives.append(f"Low patience ({self.patience}): You expect quick answers")
        elif self.patience <= 0.6:
            directives.append(f"Moderate patience ({self.patience}): You can wait for responses")
        else:
            directives.append(f"High patience ({self.patience}): You are willing to wait")

        # Verbosity description
        if self.verbosity >= 0.7:
            directives.append(f"High verbosity ({self.verbosity}): You speak in detail")
        elif self.verbosity >= 0.4:
            msg = f"Moderate verbosity ({self.verbosity}): You provide balanced responses"
            directives.append(msg)
        else:
            directives.append(f"Low verbosity ({self.verbosity}): You are concise")

        # Additional traits
        if self.traits:
            traits_str = ", ".join(self.traits)
            directives.append(f"Additional traits: {traits_str}")

        return "\n".join(f"- {d}" for d in directives)
