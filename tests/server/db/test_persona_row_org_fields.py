"""Tests for PersonaRow org-scoped fields."""

from uuid import uuid4

from voiceobs.server.db.models.persona import PersonaRow


class TestPersonaRowOrgFields:
    """Tests for org_id and persona_type on PersonaRow."""

    def test_persona_row_has_org_id(self):
        """PersonaRow must accept org_id."""
        org_id = uuid4()
        row = PersonaRow(
            id=uuid4(),
            name="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            org_id=org_id,
        )
        assert row.org_id == org_id

    def test_persona_row_has_persona_type_default_custom(self):
        """PersonaRow persona_type defaults to 'custom'."""
        row = PersonaRow(
            id=uuid4(),
            name="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            org_id=uuid4(),
        )
        assert row.persona_type == "custom"

    def test_persona_row_persona_type_system(self):
        """PersonaRow accepts persona_type='system'."""
        row = PersonaRow(
            id=uuid4(),
            name="Test",
            aggression=0.5,
            patience=0.5,
            verbosity=0.5,
            tts_provider="openai",
            org_id=uuid4(),
            persona_type="system",
        )
        assert row.persona_type == "system"
