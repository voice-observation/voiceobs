# E2E Test Account Verification Bypass — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow the e2e test account to selectively bypass agent verification via a request header, so tests run faster and cheaper.

**Architecture:** A `TestSettings` config reads `TEST_USER_EMAIL` env var. `AuthContext` gains `is_test_account` and `test_bypass` fields, computed in `require_org_membership()`. Agent routes check `test_bypass` before triggering background verification and directly set the desired outcome. E2E API client sends `X-Test-Bypass` header when bypass is requested.

**Tech Stack:** Python 3.12, FastAPI, pydantic-settings, pytest, TypeScript (Playwright e2e)

**Design doc:** `docs/plans/2026-02-23-e2e-test-bypass-design.md`

---

### Task 1: Add TestSettings config

**Files:**
- Create: `src/voiceobs/server/config/testing.py`
- Test: `tests/server/config/test_testing.py`

**Step 1: Write the failing test**

Create `tests/server/config/test_testing.py`:

```python
"""Tests for test bypass configuration."""

import os
from unittest.mock import patch

from voiceobs.server.config.testing import get_test_settings, TestSettings


class TestTestSettings:
    """Tests for TestSettings."""

    def test_default_test_user_email_is_none(self):
        """Test that test_user_email defaults to None when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            settings = TestSettings()
        assert settings.test_user_email is None

    def test_test_user_email_from_env(self):
        """Test that test_user_email reads from TEST_USER_EMAIL env var."""
        with patch.dict(os.environ, {"TEST_USER_EMAIL": "test@example.com"}):
            settings = TestSettings()
        assert settings.test_user_email == "test@example.com"

    def test_get_test_settings_returns_instance(self):
        """Test that get_test_settings returns a TestSettings instance."""
        settings = get_test_settings()
        assert isinstance(settings, TestSettings)
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/config/test_testing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'voiceobs.server.config.testing'`

**Step 3: Write minimal implementation**

Create `src/voiceobs/server/config/testing.py`:

```python
"""Test bypass configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class TestSettings(BaseSettings):
    """Settings for e2e test account bypass.

    Controls which user email is recognized as a test account.
    When test_user_email is None (the default), no test bypass is possible.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    test_user_email: str | None = None


def get_test_settings() -> TestSettings:
    """Get test settings instance.

    Returns:
        TestSettings instance
    """
    return TestSettings()
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/config/test_testing.py -v`
Expected: PASS (3 passed)

**Step 5: Commit**

```bash
git add src/voiceobs/server/config/testing.py tests/server/config/test_testing.py
git commit -m "feat: add TestSettings config for e2e test account bypass"
```

---

### Task 2: Add TestBypass dataclass and parse_test_bypass function

**Files:**
- Modify: `src/voiceobs/server/auth/context.py`
- Test: `tests/server/auth/test_context.py`

**Step 1: Write the failing tests**

Add to `tests/server/auth/test_context.py`:

```python
from voiceobs.server.auth.context import TestBypass, parse_test_bypass


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
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/auth/test_context.py::TestParseTestBypass -v`
Expected: FAIL — `ImportError: cannot import name 'TestBypass' from 'voiceobs.server.auth.context'`

**Step 3: Write minimal implementation**

Add to `src/voiceobs/server/auth/context.py` (after the existing imports, before `AuthContext`):

```python
@dataclass
class TestBypass:
    """Parsed test bypass directives from X-Test-Bypass header.

    Each field corresponds to a bypassable operation.
    None means no bypass for that operation.
    """

    verification: str | None = None  # "verified" or "failed"


_VALID_VERIFICATION_OUTCOMES = {"verified", "failed"}


def parse_test_bypass(header: str | None) -> TestBypass | None:
    """Parse the X-Test-Bypass header into a TestBypass object.

    Args:
        header: Raw header value, e.g., "verification:verified"

    Returns:
        TestBypass with parsed directives, or None if header is absent/empty.

    Raises:
        ValueError: If the header format is invalid.
    """
    if not header or not header.strip():
        return None

    bypass = TestBypass()
    directives = [d.strip() for d in header.split(",")]

    for directive in directives:
        if ":" not in directive:
            raise ValueError(f"Invalid bypass directive format: '{directive}'. Expected 'type:value'.")

        dtype, value = directive.split(":", 1)
        dtype = dtype.strip()
        value = value.strip()

        if dtype == "verification":
            if value not in _VALID_VERIFICATION_OUTCOMES:
                raise ValueError(
                    f"Invalid verification outcome: '{value}'. Must be one of: {_VALID_VERIFICATION_OUTCOMES}"
                )
            bypass.verification = value
        else:
            raise ValueError(f"Unknown bypass directive: '{dtype}'")

    return bypass
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/auth/test_context.py::TestParseTestBypass -v`
Expected: PASS (8 passed)

**Step 5: Commit**

```bash
git add src/voiceobs/server/auth/context.py tests/server/auth/test_context.py
git commit -m "feat: add TestBypass dataclass and parse_test_bypass parser"
```

---

### Task 3: Extend AuthContext and require_org_membership with test account detection

**Files:**
- Modify: `src/voiceobs/server/auth/context.py:20-25` (AuthContext dataclass)
- Modify: `src/voiceobs/server/auth/context.py:96-142` (require_org_membership function)
- Test: `tests/server/auth/test_context.py`

**Step 1: Write the failing tests**

Add to `tests/server/auth/test_context.py`:

```python
from voiceobs.server.auth.context import (
    AuthContext,
    TestBypass,
    parse_test_bypass,
    require_org_membership,
)


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

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user), \
             patch("voiceobs.server.auth.context.get_organization_repository", return_value=mock_org_repo), \
             patch("voiceobs.server.auth.context.get_organization_member_repository", return_value=mock_member_repo), \
             patch("voiceobs.server.auth.context.get_user_repository", return_value=mock_user_repo), \
             patch("voiceobs.server.auth.context.get_test_settings") as mock_settings:
            mock_settings.return_value.test_user_email = "test@e2e.com"
            ctx = await require_org_membership(org_id=org_id, authorization="Bearer token")

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

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user), \
             patch("voiceobs.server.auth.context.get_organization_repository", return_value=mock_org_repo), \
             patch("voiceobs.server.auth.context.get_organization_member_repository", return_value=mock_member_repo), \
             patch("voiceobs.server.auth.context.get_user_repository", return_value=mock_user_repo), \
             patch("voiceobs.server.auth.context.get_test_settings") as mock_settings:
            mock_settings.return_value.test_user_email = "test@e2e.com"
            ctx = await require_org_membership(org_id=org_id, authorization="Bearer token")

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

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user), \
             patch("voiceobs.server.auth.context.get_organization_repository", return_value=mock_org_repo), \
             patch("voiceobs.server.auth.context.get_organization_member_repository", return_value=mock_member_repo), \
             patch("voiceobs.server.auth.context.get_user_repository", return_value=mock_user_repo), \
             patch("voiceobs.server.auth.context.get_test_settings") as mock_settings:
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

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user), \
             patch("voiceobs.server.auth.context.get_organization_repository", return_value=mock_org_repo), \
             patch("voiceobs.server.auth.context.get_organization_member_repository", return_value=mock_member_repo), \
             patch("voiceobs.server.auth.context.get_user_repository", return_value=mock_user_repo), \
             patch("voiceobs.server.auth.context.get_test_settings") as mock_settings:
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

        with patch("voiceobs.server.auth.context.get_current_user", return_value=user), \
             patch("voiceobs.server.auth.context.get_organization_repository", return_value=mock_org_repo), \
             patch("voiceobs.server.auth.context.get_organization_member_repository", return_value=mock_member_repo), \
             patch("voiceobs.server.auth.context.get_user_repository", return_value=mock_user_repo), \
             patch("voiceobs.server.auth.context.get_test_settings") as mock_settings:
            mock_settings.return_value.test_user_email = None
            ctx = await require_org_membership(
                org_id=org_id,
                authorization="Bearer token",
                x_test_bypass="verification:verified",
            )

        assert ctx.is_test_account is False
        assert ctx.test_bypass is None
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/auth/test_context.py::TestAuthContextTestBypass -v`
Expected: FAIL — `AuthContext` doesn't accept `is_test_account` / `require_org_membership` doesn't accept `x_test_bypass`

**Step 3: Write minimal implementation**

Modify `src/voiceobs/server/auth/context.py`:

1. Add import at top:
```python
from voiceobs.server.config.testing import get_test_settings
```

2. Update `AuthContext` dataclass (lines 20-25):
```python
@dataclass
class AuthContext:
    """Authentication context containing user and active organization."""

    user: UserRow
    org: OrganizationRow
    is_test_account: bool = False
    test_bypass: TestBypass | None = None
```

3. Update `require_org_membership` signature and add test-account logic at the end (before `return`). Add `x_test_bypass` as an optional `Header` parameter:

```python
async def require_org_membership(
    org_id: UUID,
    authorization: str | None = Header(None, alias="Authorization"),
    x_test_bypass: str | None = Header(None, alias="X-Test-Bypass"),
) -> AuthContext:
```

Add before the final `return` statement (after the `last_active_org_id` update block):

```python
    # Test account detection
    is_test_account = False
    test_bypass = None
    test_settings = get_test_settings()
    if test_settings.test_user_email and user.email == test_settings.test_user_email:
        is_test_account = True
        if x_test_bypass:
            test_bypass = parse_test_bypass(x_test_bypass)

    return AuthContext(
        user=user, org=org, is_test_account=is_test_account, test_bypass=test_bypass
    )
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/auth/test_context.py -v`
Expected: ALL PASS (existing + new tests)

**Step 5: Commit**

```bash
git add src/voiceobs/server/auth/context.py tests/server/auth/test_context.py
git commit -m "feat: extend AuthContext with test account detection and bypass parsing"
```

---

### Task 4: Add verification bypass logic to agent routes

**Files:**
- Modify: `src/voiceobs/server/routes/agents.py:45-118` (create_agent)
- Modify: `src/voiceobs/server/routes/agents.py:237-346` (update_agent)
- Modify: `src/voiceobs/server/routes/agents.py:431-519` (verify_agent)
- Test: `tests/server/routes/test_agents.py`

**Step 1: Write the failing tests**

Add to `tests/server/routes/test_agents.py`. First update `setup_auth` and imports:

The existing `setup_auth` fixture creates `AuthContext(user=self.user, org=self.org)`. For bypass tests, we need to create contexts with `is_test_account=True` and `test_bypass` set. Add a new test class:

```python
from voiceobs.server.auth.context import TestBypass


class TestAgentVerificationBypass:
    """Tests for test account verification bypass in agent routes."""

    @pytest.fixture(autouse=True)
    def setup_auth(self, client):
        """Set up auth context with test account enabled."""
        self.user = make_user(email="test@e2e.com")
        self.org = make_org()
        self.app = client.app
        yield
        self.app.dependency_overrides.pop(require_org_membership, None)

    def _set_auth(self, test_bypass=None, is_test_account=True):
        """Helper to set auth context with specific bypass config."""
        auth = AuthContext(
            user=self.user,
            org=self.org,
            is_test_account=is_test_account,
            test_bypass=test_bypass,
        )

        async def override():
            return auth

        self.app.dependency_overrides[require_org_membership] = override

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_create_agent_bypass_verified(self, mock_get_agent_repo, client):
        """Create agent with verification bypass sets status to verified immediately."""
        self._set_auth(test_bypass=TestBypass(verification="verified"))
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id, org_id=self.org.id, name="Test Agent", goal="Goal",
            agent_type="phone", contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"], connection_status="saved",
            verification_attempts=0, last_verification_at=None,
            verification_error=None, verification_transcript=None,
            verification_reasoning=None, metadata={},
            created_at=now, updated_at=now, created_by=None, is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_agent
        mock_repo.update.return_value = mock_agent  # Return value after bypass update
        mock_get_agent_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents",
            json={
                "name": "Test Agent", "agent_type": "phone",
                "phone_number": "+1234567890", "goal": "Goal",
                "supported_intents": ["intent1"],
            },
        )

        assert response.status_code == 201
        # Verify repo.update was called with bypass status
        mock_repo.update.assert_called_once()
        call_kwargs = mock_repo.update.call_args[1]
        assert call_kwargs["connection_status"] == "verified"
        assert call_kwargs["verification_reasoning"] == "Test bypass"
        assert call_kwargs["verification_error"] is None
        assert call_kwargs["verification_transcript"] == []

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_create_agent_bypass_failed(self, mock_get_agent_repo, client):
        """Create agent with bypass=failed sets status to failed immediately."""
        self._set_auth(test_bypass=TestBypass(verification="failed"))
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id, org_id=self.org.id, name="Test Agent", goal="Goal",
            agent_type="phone", contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"], connection_status="saved",
            verification_attempts=0, last_verification_at=None,
            verification_error=None, verification_transcript=None,
            verification_reasoning=None, metadata={},
            created_at=now, updated_at=now, created_by=None, is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_agent
        mock_repo.update.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents",
            json={
                "name": "Test Agent", "agent_type": "phone",
                "phone_number": "+1234567890", "goal": "Goal",
                "supported_intents": ["intent1"],
            },
        )

        assert response.status_code == 201
        mock_repo.update.assert_called_once()
        call_kwargs = mock_repo.update.call_args[1]
        assert call_kwargs["connection_status"] == "failed"
        assert call_kwargs["verification_error"] == "Test bypass: failed"

    @patch("voiceobs.server.routes.agents.get_agent_verification_service")
    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_create_agent_no_bypass_still_verifies(
        self, mock_get_agent_repo, mock_get_verification_service, client
    ):
        """Test account without bypass header still triggers real verification."""
        self._set_auth(test_bypass=None, is_test_account=True)
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id, org_id=self.org.id, name="Test Agent", goal="Goal",
            agent_type="phone", contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"], connection_status="saved",
            verification_attempts=0, last_verification_at=None,
            verification_error=None, verification_transcript=None,
            verification_reasoning=None, metadata={},
            created_at=now, updated_at=now, created_by=None, is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.create.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        mock_verification_service = AsyncMock()
        mock_get_verification_service.return_value = mock_verification_service

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents",
            json={
                "name": "Test Agent", "agent_type": "phone",
                "phone_number": "+1234567890", "goal": "Goal",
                "supported_intents": ["intent1"],
            },
        )

        assert response.status_code == 201
        # Real verification was triggered
        mock_verification_service.verify_agent_background.assert_called_once()

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_verify_agent_bypass_verified(self, mock_get_agent_repo, client):
        """Manual verify with bypass sets status immediately."""
        self._set_auth(test_bypass=TestBypass(verification="verified"))
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        mock_agent = AgentRow(
            id=agent_id, org_id=self.org.id, name="Test Agent", goal="Goal",
            agent_type="phone", contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"], connection_status="saved",
            verification_attempts=0, last_verification_at=None,
            verification_error=None, verification_transcript=None,
            verification_reasoning=None, metadata={},
            created_at=now, updated_at=now, created_by=None, is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = mock_agent
        mock_repo.update.return_value = mock_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.post(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}/verify",
            json={"force": False},
        )

        assert response.status_code == 200
        mock_repo.update.assert_called_once()
        call_kwargs = mock_repo.update.call_args[1]
        assert call_kwargs["connection_status"] == "verified"

    @patch("voiceobs.server.routes.agents.get_agent_repository")
    def test_update_agent_contact_info_bypass_verified(self, mock_get_agent_repo, client):
        """Update agent with changed contact_info and bypass sets status immediately."""
        self._set_auth(test_bypass=TestBypass(verification="verified"))
        agent_id = uuid4()
        now = datetime.now(timezone.utc)

        existing_agent = AgentRow(
            id=agent_id, org_id=self.org.id, name="Agent", goal="Goal",
            agent_type="phone", contact_info={"phone_number": "+1234567890"},
            supported_intents=["intent1"], connection_status="saved",
            verification_attempts=0, last_verification_at=None,
            verification_error=None, verification_transcript=None,
            verification_reasoning=None, metadata={},
            created_at=now, updated_at=now, created_by=None, is_active=True,
        )
        updated_agent = AgentRow(
            id=agent_id, org_id=self.org.id, name="Agent", goal="Goal",
            agent_type="phone", contact_info={"phone_number": "+9876543210"},
            supported_intents=["intent1"], connection_status="saved",
            verification_attempts=0, last_verification_at=None,
            verification_error=None, verification_transcript=None,
            verification_reasoning=None, metadata={},
            created_at=now, updated_at=now, created_by=None, is_active=True,
        )

        mock_repo = AsyncMock()
        mock_repo.get.return_value = existing_agent
        mock_repo.update.return_value = updated_agent
        mock_get_agent_repo.return_value = mock_repo

        response = client.put(
            f"/api/v1/orgs/{self.org.id}/agents/{agent_id}",
            json={"phone_number": "+9876543210"},
        )

        assert response.status_code == 200
        # update called twice: once for the field update, once for the bypass status
        assert mock_repo.update.call_count == 2
        # Second call should be the bypass
        bypass_call_kwargs = mock_repo.update.call_args_list[1][1]
        assert bypass_call_kwargs["connection_status"] == "verified"
```

**Step 2: Run test to verify it fails**

Run: `uv run python -m pytest tests/server/routes/test_agents.py::TestAgentVerificationBypass -v`
Expected: FAIL — bypass logic doesn't exist yet in routes, verification service will be called (or missing)

**Step 3: Write minimal implementation**

Modify `src/voiceobs/server/routes/agents.py`:

1. Add import at top:
```python
from datetime import datetime, timezone
```

2. In `create_agent` (around line 76-95), replace the verification block with:

```python
    # Start verification in background (or bypass for test accounts)
    if auth.test_bypass and auth.test_bypass.verification:
        # Test account bypass: set verification status directly
        outcome = auth.test_bypass.verification
        await repo.update(
            agent.id,
            org_id,
            connection_status=outcome,
            verification_error="Test bypass: failed" if outcome == "failed" else None,
            verification_reasoning="Test bypass" if outcome == "verified" else None,
            verification_transcript=[],
            last_verification_at=datetime.now(timezone.utc),
        )
    else:
        logger.info(f"Starting verification for agent {agent.id} (name: {agent.name}) in org {org_id}")
        verification_service = get_agent_verification_service()
        if not verification_service:
            logger.error(
                f"Verification service is None - cannot verify agent {agent.id}. "
                "PostgreSQL must be configured."
            )
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=(
                    "Agent verification requires PostgreSQL database. "
                    "Configure server.database_url in voiceobs.yaml or "
                    "set VOICEOBS_DATABASE_URL environment variable."
                ),
            )

        logger.info(
            f"Verification service available, triggering background verification for agent {agent.id}"
        )
        await verification_service.verify_agent_background(agent.id, agent.org_id)
```

3. In `update_agent` (around line 297-323), replace the re-verification block with:

```python
    # Re-verify if contact_info changed (or bypass for test accounts)
    contact_info_changed = contact_info_update and contact_info_update != existing.contact_info
    if contact_info_changed:
        if auth.test_bypass and auth.test_bypass.verification:
            outcome = auth.test_bypass.verification
            await repo.update(
                agent_uuid,
                org_id,
                connection_status=outcome,
                verification_error="Test bypass: failed" if outcome == "failed" else None,
                verification_reasoning="Test bypass" if outcome == "verified" else None,
                verification_transcript=[],
                last_verification_at=datetime.now(timezone.utc),
            )
        else:
            verification_service = get_agent_verification_service()
            if not verification_service:
                raise HTTPException(
                    status_code=status.HTTP_501_NOT_IMPLEMENTED,
                    detail=(
                        "Agent verification requires PostgreSQL database. "
                        "Configure server.database_url in voiceobs.yaml or "
                        "set VOICEOBS_DATABASE_URL environment variable."
                    ),
                )
            await verification_service.verify_agent_background(agent_uuid, org_id)
```

4. In `verify_agent` (around line 473-495), replace the verification trigger block with:

```python
    # Start verification (or bypass for test accounts)
    if auth.test_bypass and auth.test_bypass.verification:
        outcome = auth.test_bypass.verification
        await repo.update(
            agent_uuid,
            org_id,
            connection_status=outcome,
            verification_error="Test bypass: failed" if outcome == "failed" else None,
            verification_reasoning="Test bypass" if outcome == "verified" else None,
            verification_transcript=[],
            last_verification_at=datetime.now(timezone.utc),
        )
    else:
        logger.info(f"Manual verification requested for agent {agent_id} (force={request.force})")
        verification_service = get_agent_verification_service()
        if not verification_service:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=(
                    "Agent verification requires PostgreSQL database. "
                    "Configure server.database_url in voiceobs.yaml or "
                    "set VOICEOBS_DATABASE_URL environment variable."
                ),
            )
        await verification_service.verify_agent_background(
            agent_uuid, org_id, force=request.force
        )
```

**Step 4: Run test to verify it passes**

Run: `uv run python -m pytest tests/server/routes/test_agents.py -v`
Expected: ALL PASS (existing + new tests)

**Step 5: Commit**

```bash
git add src/voiceobs/server/routes/agents.py tests/server/routes/test_agents.py
git commit -m "feat: add verification bypass logic to agent routes for test accounts"
```

---

### Task 5: Update E2E API client with bypass header support

**Files:**
- Modify: `e2e/helpers/api-client.ts:241-257` (createAgent method)
- Modify: `e2e/helpers/api-client.ts:334-357` (updateAgent method)

**Step 1: Update createAgent signature and implementation**

In `e2e/helpers/api-client.ts`, change the `createAgent` method:

```typescript
  /**
   * Create an agent in an organization.
   * Pass bypassVerification to skip real verification for test speed.
   */
  async createAgent(
    orgId: string,
    data: any,
    authToken: string,
    options?: { bypassVerification?: 'verified' | 'failed' }
  ): Promise<any> {
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    };
    if (options?.bypassVerification) {
      headers['X-Test-Bypass'] = `verification:${options.bypassVerification}`;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/orgs/${orgId}/agents`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create agent (${response.status}): ${errorBody}`);
    }

    return await response.json();
  }
```

**Step 2: Update updateAgent signature similarly**

```typescript
  /**
   * Update an agent.
   * Pass bypassVerification to skip real re-verification when contact info changes.
   */
  async updateAgent(
    orgId: string,
    agentId: string,
    data: any,
    authToken: string,
    options?: { bypassVerification?: 'verified' | 'failed' }
  ): Promise<any> {
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    };
    if (options?.bypassVerification) {
      headers['X-Test-Bypass'] = `verification:${options.bypassVerification}`;
    }

    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update agent: ${response.statusText}`);
    }

    return await response.json();
  }
```

**Step 3: Commit**

```bash
git add e2e/helpers/api-client.ts
git commit -m "feat: add bypass verification option to e2e API client"
```

---

### Task 6: Run full test suite and lint

**Step 1: Lint backend**

```bash
uv run ruff check src/voiceobs/ --fix
uv run ruff check tests/ --fix
```

**Step 2: Run all unit tests**

```bash
uv run python -m pytest tests/ -v
```

Expected: ALL PASS

**Step 3: Check coverage**

```bash
uv run python -m pytest tests/ --cov=src/voiceobs/server/auth/context --cov=src/voiceobs/server/routes/agents --cov=src/voiceobs/server/config/testing --cov-report=term-missing --cov-branch
```

Expected: >95% line and branch coverage for changed modules.

**Step 4: Fix any issues and commit**

If lint or test issues arise, fix and commit:

```bash
git add -u
git commit -m "chore: lint and test fixes for verification bypass"
```
