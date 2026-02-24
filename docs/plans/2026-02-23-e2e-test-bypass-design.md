# E2E Test Account Bypass Design

## Problem

E2E tests that create agents trigger real agent verification (LiveKit SIP calls + LLM conversations), which is slow (~120s polling) and costly. Most e2e tests don't care about verification — they need agents in a known state to test other things.

## Solution

A per-request bypass mechanism that allows the e2e test account to skip agent verification and directly set the desired outcome (verified or failed).

## Design Decisions

- **Selective per-request**: Tests choose per API call whether to bypass or not
- **Request header signal**: `X-Test-Bypass` header on normal endpoints — no endpoint duplication
- **Single test email**: Backend identifies the test account via `TEST_USER_EMAIL` env var
- **Middleware-based detection**: `AuthContext` carries `is_test_account` flag, computed once in `require_org_membership()`
- **Route-level bypass**: Bypass logic lives in agent routes, not in `AgentVerificationService`

## Architecture

### 1. Test Account Detection

Add `test_user_email: str | None = None` to backend settings, reading from the existing `TEST_USER_EMAIL` env var. Defaults to `None`.

Extend `AuthContext`:

```python
@dataclass
class AuthContext:
    user: UserRow
    org: OrganizationRow
    is_test_account: bool = False
    test_bypass: TestBypass | None = None
```

Computed in `require_org_membership()`: if `user.email == settings.test_user_email`, set `is_test_account = True` and parse the bypass header.

### 2. Bypass Header

**Header:** `X-Test-Bypass`

**Format:** `verification:<outcome>` where outcome is `verified` or `failed`.

Examples:
- `X-Test-Bypass: verification:verified` — agent marked verified instantly
- `X-Test-Bypass: verification:failed` — agent marked failed instantly
- No header — normal verification flow, even for test accounts

**Parsing:**

```python
@dataclass
class TestBypass:
    verification: str | None = None  # "verified" or "failed"

def parse_test_bypass(header: str | None) -> TestBypass | None:
    # Returns None if header absent
    # Parses "verification:verified" into TestBypass(verification="verified")
    # Raises 400 if format invalid
```

**Behavior for non-test accounts:** Header is silently ignored (no error, no information leakage).

**Extensibility:** Future bypasses add fields to `TestBypass` and extend the parser. Header supports comma-separated directives: `verification:verified, evaluation:skip`.

### 3. Verification Bypass in Routes

In `create_agent`, `update_agent`, and `verify_agent` routes, check `auth.test_bypass` before calling the verification service:

```python
if auth.test_bypass and auth.test_bypass.verification:
    outcome = auth.test_bypass.verification
    await repo.update(
        agent.id, org_id,
        connection_status=outcome,
        verification_error="Test bypass: failed" if outcome == "failed" else None,
        verification_reasoning="Test bypass" if outcome == "verified" else None,
        verification_transcript=[],
        last_verification_at=datetime.now(timezone.utc),
    )
else:
    await verification_service.verify_agent_background(agent.id, org_id)
```

**Why in the route, not the service:** The bypass skips the entire verification pipeline. The service shouldn't know about test accounts.

**Agent state after bypass:**
- `connection_status`: `"verified"` or `"failed"`
- `verification_attempts`: `0`
- `verification_transcript`: `[]`
- `verification_error`: `None` or `"Test bypass: failed"`
- `verification_reasoning`: `"Test bypass"` or `None`
- `last_verification_at`: current timestamp

### 4. E2E Test Client Changes

API client gets optional bypass parameter:

```typescript
async createAgent(orgId: string, data: AgentCreateData, options?: {
  bypassVerification?: 'verified' | 'failed'
}): Promise<AgentResponse> {
    const headers: Record<string, string> = {};
    if (options?.bypassVerification) {
        headers['X-Test-Bypass'] = `verification:${options.bypassVerification}`;
    }
    // ... existing fetch with added headers
}
```

Two test patterns:
1. **Tests that don't care about verification**: pass `{ bypassVerification: 'verified' }`
2. **Tests that test verification behavior**: don't pass the option

## Security Analysis

| Threat | Mitigation |
|--------|-----------|
| Attacker sends `X-Test-Bypass` in production | `TEST_USER_EMAIL` unset in production → `is_test_account` always `False` → header ignored |
| Attacker creates account with test email | Must authenticate via Supabase with that email — cannot spoof |
| Test email accidentally set in production | Operational concern; add startup warning log if set |
| Header reveals existence via error response | Silent ignore — no information leakage |

**What this does NOT bypass:** Authentication (JWT required), org membership checks, authorization, any other endpoint behavior.

## Affected Files

**Backend (Python):**
- `src/voiceobs/server/config/` — new test settings
- `src/voiceobs/server/auth/context.py` — `AuthContext` extension, bypass parsing
- `src/voiceobs/server/routes/agents.py` — bypass logic in create/update/verify routes

**E2E (TypeScript):**
- `e2e/helpers/api-client.ts` — optional bypass header support
