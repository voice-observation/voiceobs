"""Tests for Organization model."""

from datetime import datetime
from uuid import uuid4

from voiceobs.server.db.models import OrganizationRow


class TestOrganizationRow:
    """Tests for OrganizationRow dataclass."""

    def test_organization_row_creation(self):
        """Test creating an OrganizationRow with all fields."""
        org_id = uuid4()
        created_by = uuid4()
        now = datetime.now()

        org = OrganizationRow(
            id=org_id,
            name="Test Organization",
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        assert org.id == org_id
        assert org.name == "Test Organization"
        assert org.created_by == created_by
        assert org.created_at == now
        assert org.updated_at == now

    def test_organization_row_defaults(self):
        """Test OrganizationRow with default values."""
        org_id = uuid4()
        created_by = uuid4()

        org = OrganizationRow(
            id=org_id,
            name="Test Org",
            created_by=created_by,
        )

        assert org.id == org_id
        assert org.name == "Test Org"
        assert org.created_by == created_by
        assert org.created_at is None
        assert org.updated_at is None
