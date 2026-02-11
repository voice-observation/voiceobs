"""Persona resolution utility functions."""

from __future__ import annotations

from voiceobs.server.db.models import TestScenarioRow
from voiceobs.server.db.repositories.persona import PersonaRepository
from voiceobs.sim.persona import PersonaDNA


async def resolve_persona_for_scenario(
    scenario: TestScenarioRow,
    persona_repo: PersonaRepository,
) -> PersonaDNA:
    """Resolve persona for a test scenario.

    Fetches the persona from the database using scenario.persona_id,
    validates that it exists and is active, and returns a PersonaDNA instance.

    Args:
        scenario: The test scenario containing the persona_id reference.
        persona_repo: The persona repository for database operations.

    Returns:
        PersonaDNA instance with traits from the persona.

    Raises:
        ValueError: If persona is not found or is not active.
    """
    # TODO: Once test scenarios are org-scoped, pass org_id here
    persona_row = await persona_repo._get_by_id_unchecked(scenario.persona_id)

    if not persona_row:
        raise ValueError(f"Persona {scenario.persona_id} not found")

    if not persona_row.is_active:
        raise ValueError(f"Persona {scenario.persona_id} is not active")

    return PersonaDNA(
        aggression=persona_row.aggression,
        patience=persona_row.patience,
        verbosity=persona_row.verbosity,
        traits=persona_row.traits,
    )
