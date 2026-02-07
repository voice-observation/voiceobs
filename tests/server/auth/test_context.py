"""Tests for AuthContext and get_auth_context."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from voiceobs.server.auth.context import AuthContext, get_auth_context
from voiceobs.server.db.models import OrganizationRow, UserRow


class TestAuthContext:
    """Tests for AuthContext dataclass."""

    def test_auth_context_creation(self):
        """Test creating an AuthContext."""
        user = UserRow(id=uuid4(), email="test@example.com")
        org = OrganizationRow(id=uuid4(), name="Test Org", created_by=uuid4())

        ctx = AuthContext(user=user, org=org)

        assert ctx.user == user
        assert ctx.org == org


class TestGetAuthContext:
    """Tests for get_auth_context dependency."""

    @pytest.mark.asyncio
    async def test_get_auth_context_with_header(self):
        """Test getting auth context with X-Organization-Id header."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", last_active_org_id=None)
        org = OrganizationRow(id=org_id, name="Test Org", created_by=user_id)

        mock_user_repo = AsyncMock()
        mock_user_repo.update = AsyncMock()

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with patch(
                    "voiceobs.server.auth.context.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.auth.context.get_user_repository",
                        return_value=mock_user_repo,
                    ):
                        ctx = await get_auth_context(
                            x_organization_id=str(org_id),
                            authorization="Bearer token",
                        )

        assert ctx.user == user
        assert ctx.org == org
        mock_member_repo.is_member.assert_called_once_with(org_id=org_id, user_id=user_id)

    @pytest.mark.asyncio
    async def test_get_auth_context_with_last_active_org(self):
        """Test getting auth context using last_active_org_id."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Test Org", created_by=user_id)

        mock_user_repo = AsyncMock()
        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with patch(
                    "voiceobs.server.auth.context.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.auth.context.get_user_repository",
                        return_value=mock_user_repo,
                    ):
                        ctx = await get_auth_context(
                            x_organization_id=None,
                            authorization="Bearer token",
                        )

        assert ctx.org == org

    @pytest.mark.asyncio
    async def test_get_auth_context_not_member(self):
        """Test error when user is not member of requested org."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com")
        org = OrganizationRow(id=org_id, name="Test Org", created_by=uuid4())

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=False)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with patch(
                    "voiceobs.server.auth.context.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with pytest.raises(HTTPException) as exc_info:
                        await get_auth_context(
                            x_organization_id=str(org_id),
                            authorization="Bearer token",
                        )

        assert exc_info.value.status_code == 403
        assert "not a member" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_auth_context_no_org_selected(self):
        """Test error when no organization is selected."""
        user_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", last_active_org_id=None)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with pytest.raises(HTTPException) as exc_info:
                await get_auth_context(
                    x_organization_id=None,
                    authorization="Bearer token",
                )

        assert exc_info.value.status_code == 400
        assert "no organization selected" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_auth_context_org_not_found(self):
        """Test error when organization doesn't exist."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com")

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=None)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await get_auth_context(
                        x_organization_id=str(org_id),
                        authorization="Bearer token",
                    )

        assert exc_info.value.status_code == 404
        assert "organization not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_auth_context_invalid_org_id_format(self):
        """Test error when organization ID is invalid format."""
        user_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com")

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with pytest.raises(HTTPException) as exc_info:
                await get_auth_context(
                    x_organization_id="not-a-valid-uuid",
                    authorization="Bearer token",
                )

        assert exc_info.value.status_code == 400
        assert "invalid" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_auth_context_updates_last_active_org(self):
        """Test that last_active_org_id is updated when different."""
        user_id = uuid4()
        org_id = uuid4()
        old_org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", last_active_org_id=old_org_id)
        org = OrganizationRow(id=org_id, name="Test Org", created_by=user_id)

        mock_user_repo = AsyncMock()
        mock_user_repo.update = AsyncMock()

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with patch(
                    "voiceobs.server.auth.context.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.auth.context.get_user_repository",
                        return_value=mock_user_repo,
                    ):
                        await get_auth_context(
                            x_organization_id=str(org_id),
                            authorization="Bearer token",
                        )

        mock_user_repo.update.assert_called_once_with(user_id, last_active_org_id=org_id)

    @pytest.mark.asyncio
    async def test_get_auth_context_does_not_update_same_org(self):
        """Test that last_active_org_id is not updated when same."""
        user_id = uuid4()
        org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Test Org", created_by=user_id)

        mock_user_repo = AsyncMock()
        mock_user_repo.update = AsyncMock()

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with patch(
                    "voiceobs.server.auth.context.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.auth.context.get_user_repository",
                        return_value=mock_user_repo,
                    ):
                        await get_auth_context(
                            x_organization_id=str(org_id),
                            authorization="Bearer token",
                        )

        mock_user_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_auth_context_user_repo_not_available_still_works(self):
        """Test that auth context works even when user repo is not available."""
        user_id = uuid4()
        org_id = uuid4()
        old_org_id = uuid4()

        user = UserRow(id=user_id, email="test@example.com", last_active_org_id=old_org_id)
        org = OrganizationRow(id=org_id, name="Test Org", created_by=user_id)

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)

        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user):
            with patch(
                "voiceobs.server.auth.context.get_organization_repository",
                return_value=mock_org_repo,
            ):
                with patch(
                    "voiceobs.server.auth.context.get_organization_member_repository",
                    return_value=mock_member_repo,
                ):
                    with patch(
                        "voiceobs.server.auth.context.get_user_repository",
                        return_value=None,
                    ):
                        ctx = await get_auth_context(
                            x_organization_id=str(org_id),
                            authorization="Bearer token",
                        )

        # Should still return valid context even without updating last_active_org_id
        assert ctx.user == user
        assert ctx.org == org
