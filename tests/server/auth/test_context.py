"""Tests for AuthContext and get_auth_context."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from voiceobs.server.auth.context import (
    AuthContext,
    TestBypass,
    get_auth_context,
    parse_test_bypass,
    require_org_membership,
)
from voiceobs.server.db.models import OrganizationRow, UserRow

_AUTH_CTX = "voiceobs.server.auth.context"


class TestParseTestBypass:
    """Tests for parse_test_bypass function."""

    def test_returns_none_when_header_is_none(self):
        """No header means no bypass."""
        assert parse_test_bypass(None) is None

    def test_returns_none_when_header_is_empty(self):
        """Empty header means no bypass."""
        assert parse_test_bypass("") is None

    def test_parses_verification_verified(self):
        """Parses 'verification:verified' correctly."""
        result = parse_test_bypass("verification:verified")
        assert result == TestBypass(verification="verified")

    def test_parses_verification_failed(self):
        """Parses 'verification:failed' correctly."""
        result = parse_test_bypass("verification:failed")
        assert result == TestBypass(verification="failed")

    def test_strips_whitespace(self):
        """Strips whitespace around directives."""
        result = parse_test_bypass("  verification:verified  ")
        assert result == TestBypass(verification="verified")

    def test_raises_on_invalid_verification_outcome(self):
        """Raises ValueError for invalid verification outcome."""
        with pytest.raises(ValueError, match="Invalid verification outcome"):
            parse_test_bypass("verification:invalid")

    def test_raises_on_unknown_directive(self):
        """Raises ValueError for unknown directive type."""
        with pytest.raises(ValueError, match="Unknown bypass directive"):
            parse_test_bypass("unknown:value")

    def test_raises_on_malformed_directive(self):
        """Raises ValueError for directive without colon separator."""
        with pytest.raises(ValueError, match="Invalid bypass directive format"):
            parse_test_bypass("nocolon")


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


class TestAuthContextTestBypass:
    """Tests for test account detection in AuthContext."""

    def test_auth_context_defaults_not_test_account(self):
        """AuthContext defaults to is_test_account=False, test_bypass=None."""
        user = UserRow(id=uuid4(), email="user@example.com")
        org = OrganizationRow(id=uuid4(), name="Org", created_by=uuid4())
        ctx = AuthContext(user=user, org=org)
        assert ctx.is_test_account is False
        assert ctx.test_bypass is None

    @pytest.mark.asyncio
    async def test_require_org_membership_sets_is_test_account_true(self):
        """When user email matches TEST_USER_EMAIL, is_test_account is True."""
        user_id = uuid4()
        org_id = uuid4()
        user = UserRow(id=user_id, email="test@e2e.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Org", created_by=user_id)

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)
        mock_user_repo = AsyncMock()

        with (
            patch(f"{_AUTH_CTX}.get_current_user", return_value=user),
            patch(f"{_AUTH_CTX}.get_organization_repository", return_value=mock_org_repo),
            patch(
                f"{_AUTH_CTX}.get_organization_member_repository",
                return_value=mock_member_repo,
            ),
            patch(f"{_AUTH_CTX}.get_user_repository", return_value=mock_user_repo),
            patch(f"{_AUTH_CTX}.get_test_settings") as mock_settings,
        ):
            mock_settings.return_value.test_user_email = "test@e2e.com"
            ctx = await require_org_membership(
                org_id=org_id, authorization="Bearer token", x_test_bypass=None
            )

        assert ctx.is_test_account is True

    @pytest.mark.asyncio
    async def test_require_org_membership_sets_is_test_account_false_when_no_match(self):
        """When user email does not match TEST_USER_EMAIL, is_test_account is False."""
        user_id = uuid4()
        org_id = uuid4()
        user = UserRow(id=user_id, email="real@user.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Org", created_by=user_id)

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)
        mock_user_repo = AsyncMock()

        with (
            patch(f"{_AUTH_CTX}.get_current_user", return_value=user),
            patch(f"{_AUTH_CTX}.get_organization_repository", return_value=mock_org_repo),
            patch(
                f"{_AUTH_CTX}.get_organization_member_repository",
                return_value=mock_member_repo,
            ),
            patch(f"{_AUTH_CTX}.get_user_repository", return_value=mock_user_repo),
            patch(f"{_AUTH_CTX}.get_test_settings") as mock_settings,
        ):
            mock_settings.return_value.test_user_email = "test@e2e.com"
            ctx = await require_org_membership(
                org_id=org_id, authorization="Bearer token", x_test_bypass=None
            )

        assert ctx.is_test_account is False
        assert ctx.test_bypass is None

    @pytest.mark.asyncio
    async def test_require_org_membership_parses_bypass_header_for_test_account(self):
        """When test account sends X-Test-Bypass header, test_bypass is parsed."""
        user_id = uuid4()
        org_id = uuid4()
        user = UserRow(id=user_id, email="test@e2e.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Org", created_by=user_id)

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)
        mock_user_repo = AsyncMock()

        with (
            patch(f"{_AUTH_CTX}.get_current_user", return_value=user),
            patch(f"{_AUTH_CTX}.get_organization_repository", return_value=mock_org_repo),
            patch(
                f"{_AUTH_CTX}.get_organization_member_repository",
                return_value=mock_member_repo,
            ),
            patch(f"{_AUTH_CTX}.get_user_repository", return_value=mock_user_repo),
            patch(f"{_AUTH_CTX}.get_test_settings") as mock_settings,
        ):
            mock_settings.return_value.test_user_email = "test@e2e.com"
            ctx = await require_org_membership(
                org_id=org_id,
                authorization="Bearer token",
                x_test_bypass="verification:verified",
            )

        assert ctx.is_test_account is True
        assert ctx.test_bypass == TestBypass(verification="verified")

    @pytest.mark.asyncio
    async def test_require_org_membership_ignores_bypass_header_for_non_test_account(self):
        """When non-test account sends X-Test-Bypass header, it is silently ignored."""
        user_id = uuid4()
        org_id = uuid4()
        user = UserRow(id=user_id, email="real@user.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Org", created_by=user_id)

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)
        mock_user_repo = AsyncMock()

        with (
            patch(f"{_AUTH_CTX}.get_current_user", return_value=user),
            patch(f"{_AUTH_CTX}.get_organization_repository", return_value=mock_org_repo),
            patch(
                f"{_AUTH_CTX}.get_organization_member_repository",
                return_value=mock_member_repo,
            ),
            patch(f"{_AUTH_CTX}.get_user_repository", return_value=mock_user_repo),
            patch(f"{_AUTH_CTX}.get_test_settings") as mock_settings,
        ):
            mock_settings.return_value.test_user_email = "test@e2e.com"
            ctx = await require_org_membership(
                org_id=org_id,
                authorization="Bearer token",
                x_test_bypass="verification:verified",
            )

        assert ctx.is_test_account is False
        assert ctx.test_bypass is None

    @pytest.mark.asyncio
    async def test_require_org_membership_no_bypass_when_test_user_email_unset(self):
        """When TEST_USER_EMAIL is not configured, is_test_account is always False."""
        user_id = uuid4()
        org_id = uuid4()
        user = UserRow(id=user_id, email="anyone@example.com", last_active_org_id=org_id)
        org = OrganizationRow(id=org_id, name="Org", created_by=user_id)

        mock_org_repo = AsyncMock()
        mock_org_repo.get = AsyncMock(return_value=org)
        mock_member_repo = AsyncMock()
        mock_member_repo.is_member = AsyncMock(return_value=True)
        mock_user_repo = AsyncMock()

        with (
            patch(f"{_AUTH_CTX}.get_current_user", return_value=user),
            patch(f"{_AUTH_CTX}.get_organization_repository", return_value=mock_org_repo),
            patch(
                f"{_AUTH_CTX}.get_organization_member_repository",
                return_value=mock_member_repo,
            ),
            patch(f"{_AUTH_CTX}.get_user_repository", return_value=mock_user_repo),
            patch(f"{_AUTH_CTX}.get_test_settings") as mock_settings,
        ):
            mock_settings.return_value.test_user_email = None
            ctx = await require_org_membership(
                org_id=org_id,
                authorization="Bearer token",
                x_test_bypass="verification:verified",
            )

        assert ctx.is_test_account is False
        assert ctx.test_bypass is None
