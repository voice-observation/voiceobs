"""Tests for OrganizationRepository."""

from uuid import uuid4

import pytest

from voiceobs.server.db.repositories.organization import OrganizationRepository

from .conftest import MockRecord


class TestOrganizationRepository:
    """Tests for the OrganizationRepository class."""

    @pytest.mark.asyncio
    async def test_create_organization(self, mock_db):
        """Test creating an organization."""
        repo = OrganizationRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": org_id,
                "name": "Test Org",
                "created_by": user_id,
                "created_at": None,
                "updated_at": None,
            }
        )

        org = await repo.create(name="Test Org", created_by=user_id)

        assert org.id == org_id
        assert org.name == "Test Org"
        assert org.created_by == user_id
        mock_db.fetchrow.assert_called_once()
        assert "INSERT INTO organizations" in mock_db.fetchrow.call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_organization_by_id(self, mock_db):
        """Test getting an organization by ID."""
        repo = OrganizationRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": org_id,
                "name": "Test Org",
                "created_by": user_id,
                "created_at": None,
                "updated_at": None,
            }
        )

        org = await repo.get(org_id)

        assert org is not None
        assert org.id == org_id
        assert org.name == "Test Org"

    @pytest.mark.asyncio
    async def test_get_nonexistent_organization(self, mock_db):
        """Test getting an organization that doesn't exist."""
        repo = OrganizationRepository(mock_db)
        mock_db.fetchrow.return_value = None

        org = await repo.get(uuid4())

        assert org is None

    @pytest.mark.asyncio
    async def test_update_organization(self, mock_db):
        """Test updating an organization."""
        repo = OrganizationRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": org_id,
                "name": "Updated Org",
                "created_by": user_id,
                "created_at": None,
                "updated_at": None,
            }
        )

        org = await repo.update(org_id, name="Updated Org")

        assert org is not None
        assert org.name == "Updated Org"
        mock_db.execute.assert_called_once()
        assert "UPDATE organizations" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_update_organization_no_changes(self, mock_db):
        """Test updating an organization with no changes returns existing org."""
        repo = OrganizationRepository(mock_db)
        org_id = uuid4()
        user_id = uuid4()

        mock_db.fetchrow.return_value = MockRecord(
            {
                "id": org_id,
                "name": "Existing Org",
                "created_by": user_id,
                "created_at": None,
                "updated_at": None,
            }
        )

        # Call update with no name - should just get existing org
        org = await repo.update(org_id)

        assert org is not None
        assert org.name == "Existing Org"
        # Should only call fetchrow (for get), not execute (for update)
        mock_db.execute.assert_not_called()
        mock_db.fetchrow.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_organization(self, mock_db):
        """Test deleting an organization."""
        repo = OrganizationRepository(mock_db)
        org_id = uuid4()

        mock_db.execute.return_value = "DELETE 1"

        result = await repo.delete(org_id)

        assert result is True
        mock_db.execute.assert_called_once()
        assert "DELETE FROM organizations" in mock_db.execute.call_args[0][0]

    @pytest.mark.asyncio
    async def test_delete_nonexistent_organization(self, mock_db):
        """Test deleting an organization that doesn't exist."""
        repo = OrganizationRepository(mock_db)
        org_id = uuid4()

        mock_db.execute.return_value = "DELETE 0"

        result = await repo.delete(org_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_list_organizations_for_user(self, mock_db):
        """Test listing organizations for a user."""
        repo = OrganizationRepository(mock_db)
        user_id = uuid4()
        org1_id = uuid4()
        org2_id = uuid4()

        mock_db.fetch.return_value = [
            MockRecord(
                {
                    "id": org1_id,
                    "name": "Org 1",
                    "created_by": user_id,
                    "created_at": None,
                    "updated_at": None,
                    "role": "owner",
                }
            ),
            MockRecord(
                {
                    "id": org2_id,
                    "name": "Org 2",
                    "created_by": uuid4(),
                    "created_at": None,
                    "updated_at": None,
                    "role": "member",
                }
            ),
        ]

        orgs = await repo.list_for_user(user_id)

        assert len(orgs) == 2
        assert orgs[0]["org"].id == org1_id
        assert orgs[0]["role"] == "owner"
        assert orgs[1]["org"].id == org2_id
        assert orgs[1]["role"] == "member"
