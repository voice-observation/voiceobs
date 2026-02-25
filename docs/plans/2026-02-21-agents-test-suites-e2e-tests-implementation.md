# E2E Tests for Org-Scoped Agents and Test Suites — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add 42 Playwright e2e tests across 6 spec files to verify org-scoped agents and test-suites work correctly in the UI.

**Architecture:** Backend auto-pass flag for agent verification, page object model for UI interaction, API client for test setup/teardown, mirroring existing persona e2e patterns.

**Tech Stack:** Playwright, TypeScript, FastAPI (backend flag), pydantic-settings

**TDD Approach:** Backend flag follows RED-GREEN-REFACTOR. E2e test files are the tests themselves — write them, run them, fix until green.

---

## Task 1: Add Backend Auto-Pass Verification Flag

The backend auto-triggers phone verification on every agent create/update. E2e tests need agents to become "verified" instantly without calling real phone services.

**Files:**
- Modify: `src/voiceobs/server/config/verification.py:6-26`
- Modify: `src/voiceobs/server/services/agent_verification/service.py:36-60`
- Test: `tests/server/services/agent_verification/test_service.py`

**Step 1: Write failing test**

Add test to `tests/server/services/agent_verification/test_service.py`:

```python
@pytest.mark.asyncio
async def test_auto_pass_verification_skips_actual_verification(self, mock_agent_repo):
    """When auto_pass_verification is True, verify_agent should immediately mark agent as verified."""
    agent_id = uuid4()
    org_id = uuid4()
    mock_agent = MagicMock()
    mock_agent.id = agent_id
    mock_agent.org_id = org_id
    mock_agent.connection_status = "saved"
    mock_agent.verification_attempts = 0
    mock_agent.agent_type = "phone"
    mock_agent.contact_info = {"phone_number": "+15551234567"}
    mock_agent_repo.get.return_value = mock_agent

    with patch(
        "voiceobs.server.services.agent_verification.service.get_verification_settings"
    ) as mock_settings:
        settings = MagicMock()
        settings.auto_pass_verification = True
        mock_settings.return_value = settings

        service = AgentVerificationService(mock_agent_repo)
        await service.verify_agent(agent_id, org_id)

    # Should update to verified without calling any verifier
    mock_agent_repo.update.assert_called_once()
    call_kwargs = mock_agent_repo.update.call_args
    # Check positional args: agent_id, org_id
    assert call_kwargs[0][0] == agent_id
    assert call_kwargs[0][1] == org_id
    # Check keyword args
    assert call_kwargs[1]["connection_status"] == "verified"
```

**Step 2: Run test to verify it fails**

```bash
uv run python -m pytest tests/server/services/agent_verification/test_service.py::TestAgentVerificationService::test_auto_pass_verification_skips_actual_verification -v
```

Expected: FAIL — `VerificationSettings` has no `auto_pass_verification` field

**Step 3: Add `auto_pass_verification` to VerificationSettings**

In `src/voiceobs/server/config/verification.py`, add after the existing fields:

```python
class VerificationSettings(BaseSettings):
    """Settings for agent verification.

    All settings can be configured via environment variables.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LiveKit settings
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    sip_outbound_trunk_id: str

    # Verification behavior
    verification_max_turns: int = 3
    verification_max_retries: int = 3
    verification_call_timeout: int = 30
    verification_retry_base_delay: int = 30
    verification_initial_wait_timeout: float = 4.5

    # Testing
    auto_pass_verification: bool = False  # Set True to skip real verification (e2e tests)

    def get_retry_delay(self, attempt: int) -> int:
        """Calculate retry delay with exponential backoff.

        Args:
            attempt: Current attempt number (1-based)

        Returns:
            Delay in seconds before next retry
        """
        return self.verification_retry_base_delay * (2 ** (attempt - 1))
```

**Step 4: Add auto-pass early return to `verify_agent()`**

In `src/voiceobs/server/services/agent_verification/service.py`, add after `self._settings = get_verification_settings()` (line 49) and before the agent fetch:

```python
    async def verify_agent(self, agent_id: UUID, org_id: UUID, force: bool = False) -> None:
        """Verify an agent's connection asynchronously."""
        try:
            # Refresh settings for each verification attempt
            self._settings = get_verification_settings()

            # Auto-pass for testing: skip real verification
            if self._settings.auto_pass_verification:
                logger.info(f"Auto-pass verification for agent {agent_id} (test mode)")
                await self._agent_repo.update(
                    agent_id,
                    org_id,
                    connection_status="verified",
                    verification_error=None,
                    verification_reasoning="Auto-pass enabled for testing",
                )
                return

            # Get agent from repository
            agent = await self._agent_repo.get(agent_id, org_id)
            # ... rest of method unchanged
```

**Step 5: Run test to verify it passes**

```bash
uv run python -m pytest tests/server/services/agent_verification/test_service.py::TestAgentVerificationService::test_auto_pass_verification_skips_actual_verification -v
```

Expected: PASS

**Step 6: Run full test suite and lint**

```bash
uv run ruff check src/voiceobs/ --fix
uv run python -m pytest tests/ -v
```

**Step 7: Commit**

```bash
git add src/voiceobs/server/config/verification.py src/voiceobs/server/services/agent_verification/service.py tests/server/services/agent_verification/test_service.py
git commit -m "feat: add auto_pass_verification flag for e2e testing

When AUTO_PASS_VERIFICATION=true, agents are immediately marked
as verified without calling the real phone service."
```

---

## Task 2: Add Test Data Helpers

**Files:**
- Modify: `e2e/helpers/test-data.ts`

**Step 1: Add agent and test-suite data generators**

Append to `e2e/helpers/test-data.ts`:

```typescript
/** Agent create payload matching backend AgentCreateRequest */
export interface AgentCreateData {
  name: string;
  goal: string;  // backend uses "goal", frontend shows as "description"
  agent_type: string;
  contact_info: { phone_number: string };
  supported_intents: string[];
  context?: string;
}

/** Default intents from AgentConfigForm */
export const E2E_DEFAULT_INTENTS = [
  "Book",
  "Reschedule",
  "Cancel",
  "Ask hours",
  "Talk to human",
] as const;

export function generateAgentName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2E Test Agent ${timestamp}-${random}`;
}

export function generateAgentData(
  overrides?: Partial<AgentCreateData>
): AgentCreateData {
  return {
    name: generateAgentName(),
    goal: "E2E test agent for automated testing",
    agent_type: "phone",
    contact_info: { phone_number: "+15551234567" },
    supported_intents: ["Book", "Cancel"],
    context: "Test agent for e2e testing",
    ...overrides,
  };
}

/** Test suite create payload matching backend TestSuiteCreateRequest */
export interface TestSuiteCreateData {
  name: string;
  description?: string;
  agent_id: string;
  test_scopes?: string[];
  thoroughness?: number;
  edge_cases?: string[];
  evaluation_strictness?: string;
}

export function generateTestSuiteName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2E Test Suite ${timestamp}-${random}`;
}

export function generateTestSuiteData(
  agentId: string,
  overrides?: Partial<TestSuiteCreateData>
): TestSuiteCreateData {
  return {
    name: generateTestSuiteName(),
    description: "E2E test suite for automated testing",
    agent_id: agentId,
    test_scopes: ["core_flows"],
    thoroughness: 0, // Light - fastest generation
    edge_cases: [],
    evaluation_strictness: "balanced",
    ...overrides,
  };
}
```

**Step 2: Commit**

```bash
git add e2e/helpers/test-data.ts
git commit -m "feat: add agent and test-suite data generators for e2e tests"
```

---

## Task 3: Add Agent Methods to API Client

**Files:**
- Modify: `e2e/helpers/api-client.ts`

**Step 1: Add agent CRUD methods**

Add these methods to the `ApiClient` class in `e2e/helpers/api-client.ts`:

```typescript
  // ─── Agents ────────────────────────────────────────

  /**
   * List agents for an organization
   */
  async listAgents(orgId: string, authToken: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/orgs/${orgId}/agents`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to list agents: ${response.statusText}`);
    }

    const data = await response.json();
    return data.agents || [];
  }

  /**
   * Create an agent in an organization
   */
  async createAgent(orgId: string, data: any, authToken: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/orgs/${orgId}/agents`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create agent (${response.status}): ${errorBody}`);
    }

    return await response.json();
  }

  /**
   * Get a specific agent by ID
   */
  async getAgent(orgId: string, agentId: string, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get agent: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Update an agent
   */
  async updateAgent(
    orgId: string,
    agentId: string,
    data: any,
    authToken: string
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update agent: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Delete an agent
   */
  async deleteAgent(orgId: string, agentId: string, authToken: string): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete agent: ${response.statusText}`);
    }
  }
```

**Step 2: Commit**

```bash
git add e2e/helpers/api-client.ts
git commit -m "feat: add agent CRUD methods to e2e API client"
```

---

## Task 4: Add Test Suite Methods to API Client

**Files:**
- Modify: `e2e/helpers/api-client.ts`

**Step 1: Add test suite CRUD and generation methods**

Add these methods to the `ApiClient` class:

```typescript
  // ─── Test Suites ───────────────────────────────────

  /**
   * List test suites for an organization
   */
  async listTestSuites(orgId: string, authToken: string): Promise<any[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to list test suites: ${response.statusText}`);
    }

    const data = await response.json();
    return data.suites || [];
  }

  /**
   * Create a test suite
   */
  async createTestSuite(orgId: string, data: any, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create test suite (${response.status}): ${errorBody}`);
    }

    return await response.json();
  }

  /**
   * Get a test suite by ID
   */
  async getTestSuite(orgId: string, suiteId: string, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get test suite: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Update a test suite
   */
  async updateTestSuite(
    orgId: string,
    suiteId: string,
    data: any,
    authToken: string
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update test suite: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Delete a test suite
   */
  async deleteTestSuite(
    orgId: string,
    suiteId: string,
    authToken: string
  ): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete test suite: ${response.statusText}`);
    }
  }

  /**
   * Get generation status of a test suite.
   * Used for polling until generation completes.
   */
  async getGenerationStatus(
    orgId: string,
    suiteId: string,
    authToken: string
  ): Promise<{ status: string; scenario_count: number; error: string | null }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}/generation-status`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get generation status: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Poll until test suite generation completes (status becomes "ready" or "generation_failed").
   * @param timeoutMs Maximum time to wait (default 120s)
   * @param intervalMs Polling interval (default 2s)
   */
  async waitForGeneration(
    orgId: string,
    suiteId: string,
    authToken: string,
    timeoutMs: number = 120000,
    intervalMs: number = 2000,
  ): Promise<{ status: string; scenario_count: number }> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const result = await this.getGenerationStatus(orgId, suiteId, authToken);
      if (result.status === 'ready' || result.status === 'generation_failed') {
        return { status: result.status, scenario_count: result.scenario_count };
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error(`Generation timed out after ${timeoutMs}ms for suite ${suiteId}`);
  }
```

**Step 2: Commit**

```bash
git add e2e/helpers/api-client.ts
git commit -m "feat: add test suite CRUD and generation polling to e2e API client"
```

---

## Task 5: Create Agent Page Objects

**Files:**
- Create: `e2e/pages/agent-list.page.ts`
- Create: `e2e/pages/agent-detail.page.ts`
- Create: `e2e/pages/agent-form.page.ts`

**Note on selectors:** Agent components do not have `data-testid` attributes (unlike persona components). Page objects use text-based, role-based, and `id` attribute selectors. If tests prove fragile, add `data-testid` attributes to agent components in a follow-up task.

**Step 1: Create agent-list.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

export class AgentListPage {
  readonly page: Page;
  readonly newAgentButton: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newAgentButton = page.getByRole('button', { name: 'New Agent' });
    // Empty state has "Create Your First Agent" text
    this.emptyState = page.getByText('Create Your First Agent');
  }

  async goto(orgId: string) {
    await this.page.goto(`/orgs/${orgId}/agents`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/agents(\?|$)/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickNewAgent() {
    await this.newAgentButton.click();
  }

  /**
   * Get all agent cards on the page.
   * Agent cards are rendered inside a grid. Each card has a CardTitle with the agent name.
   */
  async getAgentCards(): Promise<{ name: string; element: Locator }[]> {
    // Wait for either cards or empty state to appear
    await this.page.waitForTimeout(1000);
    const cards = this.page.locator('.grid > div').filter({ has: this.page.locator('h3') });
    const count = await cards.count();
    const result: { name: string; element: Locator }[] = [];

    for (let i = 0; i < count; i++) {
      const card = cards.nth(i);
      const name = await card.locator('h3').first().textContent();
      if (name) {
        result.push({ name: name.trim(), element: card });
      }
    }

    return result;
  }

  /**
   * Find an agent card by name.
   */
  getAgentCardByName(name: string): Locator {
    return this.page.locator(`.grid > div`).filter({
      has: this.page.locator(`h3:has-text("${name}")`),
    });
  }

  /**
   * Open the dropdown menu on an agent card and click an action.
   */
  async clickCardAction(agentName: string, action: string) {
    const card = this.getAgentCardByName(agentName);
    // The dropdown trigger is a button with MoreVertical icon inside the card
    const menuTrigger = card.locator('button[aria-haspopup="menu"]');
    await menuTrigger.click();
    await this.page.locator('[role="menu"]').waitFor({ state: 'visible' });
    await this.page.locator(`[role="menuitem"]:has-text("${action}")`).click();
  }

  async clickView(agentName: string) {
    await this.clickCardAction(agentName, 'View');
  }

  async clickEdit(agentName: string) {
    await this.clickCardAction(agentName, 'Edit');
  }

  async clickDelete(agentName: string) {
    await this.clickCardAction(agentName, 'Delete');
  }

  async clickVerify(agentName: string) {
    await this.clickCardAction(agentName, 'Verify');
  }

  async clickDeactivate(agentName: string) {
    await this.clickCardAction(agentName, 'Deactivate');
  }

  async clickActivate(agentName: string) {
    await this.clickCardAction(agentName, 'Activate');
  }

  /**
   * Get the status badge text for an agent card.
   */
  async getStatusBadgeText(agentName: string): Promise<string> {
    const card = this.getAgentCardByName(agentName);
    // Status badge is the first Badge component in the card
    const badge = card.locator('[class*="badge"]').first();
    return (await badge.textContent())?.trim() || '';
  }

  /**
   * Check if phone number is displayed on an agent card.
   */
  async getPhoneNumber(agentName: string): Promise<string | null> {
    const card = this.getAgentCardByName(agentName);
    // Phone is displayed with Phone icon
    const phoneEl = card.locator('text=/\\+\\d/');
    if (await phoneEl.isVisible().catch(() => false)) {
      return (await phoneEl.textContent())?.trim() || null;
    }
    return null;
  }
}
```

**Step 2: Create agent-detail.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

export class AgentDetailPage {
  readonly page: Page;
  readonly editButton: Locator;
  readonly deleteButton: Locator;
  readonly verifyButton: Locator;
  readonly activeToggle: Locator;
  readonly backButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.editButton = page.getByRole('button', { name: 'Edit', exact: true });
    this.deleteButton = page.getByRole('button', { name: 'Delete', exact: true });
    this.verifyButton = page.getByRole('button', { name: /Verify Again/ });
    this.activeToggle = page.locator('#active-toggle');
    this.backButton = page.getByRole('link', { name: /Back to Agents/ });
  }

  async goto(orgId: string, agentId: string) {
    await this.page.goto(`/orgs/${orgId}/agents/${agentId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/agents\/[^/]+$/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async getName(): Promise<string> {
    // Agent name is in the first h1 or large heading
    const heading = this.page.locator('h1, h2').first();
    return (await heading.textContent())?.trim() || '';
  }

  async getDescription(): Promise<string> {
    // Description is in the first card body after "Description" or the agent goal text
    const descEl = this.page.locator('p').filter({ hasText: /\w{10,}/ }).first();
    return (await descEl.textContent())?.trim() || '';
  }

  async getPhoneNumber(): Promise<string | null> {
    const phoneEl = this.page.locator('text=/\\+\\d{5,}/').first();
    if (await phoneEl.isVisible().catch(() => false)) {
      return (await phoneEl.textContent())?.trim() || null;
    }
    return null;
  }

  async getConnectionStatusBadge(): Promise<string> {
    // First badge near the top of the page shows connection status
    const badge = this.page.locator('[class*="badge"]').first();
    return (await badge.textContent())?.trim() || '';
  }

  async getActiveToggleState(): Promise<boolean> {
    const checked = await this.activeToggle.getAttribute('data-state');
    return checked === 'checked';
  }

  async toggleActive() {
    await this.activeToggle.click();
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickDelete() {
    await this.deleteButton.click();
  }

  async clickVerify() {
    await this.verifyButton.click();
  }

  async clickBack() {
    await this.backButton.click();
  }

  /**
   * Get intent badge texts.
   */
  async getIntents(): Promise<string[]> {
    const section = this.page.locator('text=Supported Intents').locator('..');
    const badges = section.locator('[class*="badge"]');
    const count = await badges.count();
    const intents: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await badges.nth(i).textContent();
      if (text) intents.push(text.trim());
    }
    return intents;
  }

  /**
   * Check if verification section is visible.
   */
  async isVerificationSectionVisible(): Promise<boolean> {
    return this.page.getByText('Verification Status').isVisible().catch(() => false);
  }
}
```

**Step 3: Create agent-form.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

/**
 * Wraps the AgentConfigForm component, used in both:
 * - Create dialog (from list page "New Agent" button)
 * - Edit page (/orgs/{orgId}/agents/{id}/edit)
 *
 * Form input IDs: name, description, context, phone
 * Intent checkboxes: Book, Reschedule, Cancel, Ask hours, Talk to human
 */
export class AgentFormPage {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly contextInput: Locator;
  readonly phoneInput: Locator;
  readonly createButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly validationErrors: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.locator('#name');
    this.descriptionInput = page.locator('#description');
    this.contextInput = page.locator('#context');
    this.phoneInput = page.locator('#phone');
    this.createButton = page.getByRole('button', { name: /Create Agent/ });
    this.saveButton = page.getByRole('button', { name: /Save Changes/ });
    this.cancelButton = page.getByRole('button', { name: 'Cancel' });
    this.validationErrors = page.locator('.text-destructive');
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async fillDescription(description: string) {
    await this.descriptionInput.fill(description);
  }

  async fillPhone(phone: string) {
    await this.phoneInput.fill(phone);
  }

  async fillContext(context: string) {
    await this.contextInput.fill(context);
  }

  /**
   * Select a predefined intent checkbox by label text.
   * Valid labels: "Book", "Reschedule", "Cancel", "Ask hours", "Talk to human"
   */
  async selectIntent(label: string) {
    await this.page.getByLabel(label).check();
  }

  /**
   * Add a custom intent via the text input + Add button.
   */
  async addCustomIntent(intent: string) {
    await this.page.getByPlaceholder('Add custom intent...').fill(intent);
    // Click the "Add" button next to the input
    await this.page.getByRole('button', { name: 'Add', exact: true }).click();
  }

  /**
   * Fill the complete agent form for creation.
   */
  async fillCreateForm(data: {
    name: string;
    description: string;
    phone: string;
    intents?: string[];
    customIntents?: string[];
    context?: string;
  }) {
    await this.fillName(data.name);
    await this.fillDescription(data.description);
    await this.fillPhone(data.phone);
    if (data.context) {
      await this.fillContext(data.context);
    }
    for (const intent of data.intents || ['Book']) {
      await this.selectIntent(intent);
    }
    for (const ci of data.customIntents || []) {
      await this.addCustomIntent(ci);
    }
  }

  async clickCreate() {
    await this.createButton.click();
  }

  async clickSave() {
    await this.saveButton.click();
  }

  async clickCancel() {
    await this.cancelButton.click();
  }

  async isCreateDisabled(): Promise<boolean> {
    return await this.createButton.isDisabled();
  }

  async isSaveDisabled(): Promise<boolean> {
    return await this.saveButton.isDisabled();
  }

  async getValidationErrors(): Promise<string[]> {
    const count = await this.validationErrors.count();
    const errors: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await this.validationErrors.nth(i).textContent();
      if (text) errors.push(text.trim());
    }
    return errors;
  }
}
```

**Step 4: Commit**

```bash
git add e2e/pages/agent-list.page.ts e2e/pages/agent-detail.page.ts e2e/pages/agent-form.page.ts
git commit -m "feat: add agent page objects for e2e tests"
```

---

## Task 6: Create Test Suite Page Objects

**Files:**
- Create: `e2e/pages/test-suite-list.page.ts`
- Create: `e2e/pages/test-suite-detail.page.ts`
- Create: `e2e/pages/test-suite-create-dialog.page.ts`

**Step 1: Create test-suite-list.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

export class TestSuiteListPage {
  readonly page: Page;
  readonly newSuiteButton: Locator;
  readonly emptyState: Locator;
  readonly suiteTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newSuiteButton = page.getByRole('button', { name: 'New Suite' });
    this.emptyState = page.getByText('Create Your First Test Suite');
    this.suiteTable = page.locator('table');
  }

  async goto(orgId: string) {
    await this.page.goto(`/orgs/${orgId}/test-suites`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/test-suites(\?|$)/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickNewSuite() {
    await this.newSuiteButton.click();
  }

  /**
   * Get all suite rows from the table.
   */
  async getSuiteRows(): Promise<{ name: string; element: Locator }[]> {
    await this.page.waitForTimeout(1000);
    const rows = this.suiteTable.locator('tbody tr');
    const count = await rows.count();
    const result: { name: string; element: Locator }[] = [];

    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      // First cell contains suite name
      const name = await row.locator('td').first().textContent();
      if (name) {
        result.push({ name: name.trim(), element: row });
      }
    }

    return result;
  }

  /**
   * Find a suite row by name.
   */
  getSuiteRowByName(name: string): Locator {
    return this.suiteTable.locator('tbody tr').filter({
      has: this.page.locator(`td:has-text("${name}")`),
    });
  }

  /**
   * Get the status badge text for a suite row.
   */
  async getStatusBadge(suiteName: string): Promise<string> {
    const row = this.getSuiteRowByName(suiteName);
    const badge = row.locator('[class*="badge"]').first();
    return (await badge.textContent())?.trim() || '';
  }

  /**
   * Click an action button on a suite row by title attribute.
   */
  async clickView(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.locator('button[title="View details"]').click();
  }

  async clickEdit(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.locator('button[title="Edit suite"]').click();
  }

  async clickRun(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.locator('button[title="Run suite"]').click();
  }

  async clickDelete(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.locator('button[title="Delete suite"]').click();
  }
}
```

**Step 2: Create test-suite-detail.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

export class TestSuiteDetailPage {
  readonly page: Page;
  readonly editButton: Locator;
  readonly runButton: Locator;
  readonly generateMoreButton: Locator;
  readonly backButton: Locator;
  readonly moreMenu: Locator;

  constructor(page: Page) {
    this.page = page;
    this.editButton = page.getByRole('button', { name: 'Edit', exact: true });
    this.runButton = page.getByRole('button', { name: /Run Suite/ });
    this.generateMoreButton = page.getByRole('button', { name: /Generate More/ });
    this.backButton = page.getByRole('link', { name: /Back to Test Suites/ });
    this.moreMenu = page.getByRole('button', { name: /more/i }).or(
      page.locator('button[aria-haspopup="menu"]').last()
    );
  }

  async goto(orgId: string, suiteId: string) {
    await this.page.goto(`/orgs/${orgId}/test-suites/${suiteId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/test-suites\/[^/]+$/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async getName(): Promise<string> {
    const heading = this.page.locator('h1, h2').first();
    return (await heading.textContent())?.trim() || '';
  }

  async getDescription(): Promise<string | null> {
    // Description appears below the heading
    const desc = this.page.locator('h1 + p, h2 + p').first();
    if (await desc.isVisible().catch(() => false)) {
      return (await desc.textContent())?.trim() || null;
    }
    return null;
  }

  async getStatusBadge(): Promise<string> {
    const badge = this.page.locator('[class*="badge"]').first();
    return (await badge.textContent())?.trim() || '';
  }

  /**
   * Get the test count from the "Tests: N" badge.
   */
  async getTestCount(): Promise<number> {
    const testsEl = this.page.getByText(/Tests:\s*\d+/);
    const text = await testsEl.textContent();
    const match = text?.match(/Tests:\s*(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /**
   * Get scenario count from the scenarios table rows.
   */
  async getScenarioRowCount(): Promise<number> {
    const table = this.page.locator('table');
    if (!(await table.isVisible().catch(() => false))) return 0;
    const rows = table.locator('tbody tr');
    return await rows.count();
  }

  /**
   * Check if the "Generating..." indicator is visible.
   */
  async isGenerating(): Promise<boolean> {
    return this.page.getByText('Generating Test Scenarios').isVisible().catch(() => false);
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickRun() {
    await this.runButton.click();
  }

  async clickGenerateMore() {
    await this.generateMoreButton.click();
  }

  async clickDelete() {
    // Delete is in the "more" dropdown menu
    await this.moreMenu.click();
    await this.page.locator('[role="menu"]').waitFor({ state: 'visible' });
    await this.page.locator('[role="menuitem"]:has-text("Delete")').click();
  }

  async clickBack() {
    await this.backButton.click();
  }
}
```

**Step 3: Create test-suite-create-dialog.page.ts**

```typescript
import { Page, Locator } from '@playwright/test';

/**
 * Wraps the CreateTestSuiteDialog component.
 *
 * Form input IDs: suiteName, description, agent
 * Checkboxes: test scopes, edge cases
 * Slider: thoroughness
 * Radio: evaluation strictness
 */
export class TestSuiteCreateDialogPage {
  readonly page: Page;
  readonly dialog: Locator;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly agentSelect: Locator;
  readonly generateButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.dialog = page.getByRole('dialog');
    this.nameInput = page.locator('#suiteName');
    this.descriptionInput = page.locator('#description');
    this.agentSelect = page.locator('#agent');
    this.generateButton = page.getByRole('button', { name: /Generate Tests/ });
    this.saveButton = page.getByRole('button', { name: /Save Changes/ });
    this.cancelButton = this.dialog.getByRole('button', { name: 'Cancel' });
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async fillDescription(description: string) {
    await this.descriptionInput.fill(description);
  }

  /**
   * Select an agent from the dropdown by agent name text.
   */
  async selectAgent(agentName: string) {
    await this.agentSelect.click();
    // Select dropdown opens as a listbox/combobox
    await this.page.getByRole('option', { name: new RegExp(agentName, 'i') }).first().click();
  }

  /**
   * Select test scope checkboxes by label text.
   * Valid: "Core flows (happy paths)", "Common user mistakes", etc.
   */
  async selectTestScope(label: string) {
    await this.dialog.getByLabel(new RegExp(label, 'i')).check();
  }

  /**
   * Set thoroughness slider.
   * 0=Light, 1=Standard, 2=Exhaustive
   */
  async setThoroughness(label: string) {
    // Click the label text for the thoroughness level
    await this.dialog.getByText(label, { exact: true }).click();
  }

  /**
   * Select edge case checkboxes by label text.
   */
  async selectEdgeCase(label: string) {
    await this.dialog.getByLabel(new RegExp(label, 'i')).check();
  }

  /**
   * Select evaluation strictness radio button by label text.
   */
  async setStrictness(label: string) {
    await this.dialog.getByLabel(new RegExp(label, 'i')).click();
  }

  /**
   * Fill the complete create form.
   */
  async fillCreateForm(data: {
    name: string;
    description?: string;
    agentName: string;
    testScopes?: string[];
    thoroughness?: string;
    edgeCases?: string[];
    strictness?: string;
  }) {
    await this.fillName(data.name);
    if (data.description) {
      await this.fillDescription(data.description);
    }
    await this.selectAgent(data.agentName);
    for (const scope of data.testScopes || ['Core flows']) {
      await this.selectTestScope(scope);
    }
    if (data.thoroughness) {
      await this.setThoroughness(data.thoroughness);
    }
    for (const ec of data.edgeCases || []) {
      await this.selectEdgeCase(ec);
    }
    if (data.strictness) {
      await this.setStrictness(data.strictness);
    }
  }

  async clickGenerate() {
    await this.generateButton.click();
  }

  async clickSave() {
    await this.saveButton.click();
  }

  async clickCancel() {
    await this.cancelButton.click();
  }

  async isGenerateDisabled(): Promise<boolean> {
    return await this.generateButton.isDisabled();
  }
}
```

**Step 4: Commit**

```bash
git add e2e/pages/test-suite-list.page.ts e2e/pages/test-suite-detail.page.ts e2e/pages/test-suite-create-dialog.page.ts
git commit -m "feat: add test suite page objects for e2e tests"
```

---

## Task 7: Write agents-crud.spec.ts

**Files:**
- Create: `e2e/specs/agents/agents-crud.spec.ts`

**Step 1: Create the spec file**

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
import { AgentListPage } from '../../pages/agent-list.page';
import { AgentDetailPage } from '../../pages/agent-detail.page';
import { AgentFormPage } from '../../pages/agent-form.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateAgentData, generateOrgName } from '../../helpers/test-data';

type CreatedAgent = { orgId: string; agentId: string };

test.describe('Agents CRUD', () => {
  let apiClient: ApiClient;
  let createdAgents: CreatedAgent[] = [];
  let createdOrgIds: string[] = [];

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdAgents = [];
    createdOrgIds = [];
  });

  test.afterEach(async ({ authToken }) => {
    for (const { orgId, agentId } of createdAgents) {
      try { await apiClient.deleteAgent(orgId, agentId, authToken); } catch {}
    }
    for (const orgId of createdOrgIds) {
      try { await apiClient.deleteOrganization(orgId, authToken); } catch {}
    }
  });

  test('should show empty state on fresh org', async ({ authenticatedPage, authToken }) => {
    const sidebar = new SidebarPage(authenticatedPage);
    const listPage = new AgentListPage(authenticatedPage);

    // Create fresh org to guarantee no agents
    const orgName = generateOrgName();
    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    await sidebar.createOrg(orgName);
    await authenticatedPage.waitForTimeout(1000);

    const orgs = await apiClient.getUserOrgs(authToken);
    const org = orgs.find((o: any) => o.name === orgName);
    if (org) createdOrgIds.push(org.id);

    await listPage.goto(org.id);
    await expect(listPage.emptyState).toBeVisible({ timeout: 10000 });
  });

  test('should create agent with all fields', async ({ authenticatedPage, authToken }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    await listPage.goto(orgId);
    await listPage.clickNewAgent();

    // Wait for dialog to open
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    const agentData = generateAgentData();
    await form.fillCreateForm({
      name: agentData.name,
      description: agentData.goal,
      phone: agentData.contact_info.phone_number,
      intents: ['Book', 'Cancel'],
      customIntents: ['Custom E2E Intent'],
      context: agentData.context || '',
    });

    await form.clickCreate();

    // Wait for dialog to close and agent to appear in list
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'hidden', timeout: 15000 });
    await authenticatedPage.waitForTimeout(2000);

    const cards = await listPage.getAgentCards();
    const created = cards.find((c) => c.name === agentData.name);
    expect(created).toBeDefined();

    // Cleanup: find agent ID via API
    const agents = await apiClient.listAgents(orgId, authToken);
    const apiAgent = agents.find((a: any) => a.name === agentData.name);
    if (apiAgent) createdAgents.push({ orgId, agentId: apiAgent.id });
  });

  test('should view agent detail', async ({ authenticatedPage, authToken }) => {
    const detailPage = new AgentDetailPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken);
    createdAgents.push({ orgId, agentId: created.id });

    await detailPage.goto(orgId, created.id);
    expect(await detailPage.isLoaded()).toBe(true);

    const name = await detailPage.getName();
    expect(name).toContain(agentData.name);
  });

  test('should edit agent via dialog', async ({ authenticatedPage, authToken }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken);
    createdAgents.push({ orgId, agentId: created.id });

    await listPage.goto(orgId);
    // Wait for agent card to appear
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 10000 });

    await listPage.clickEdit(agentData.name);
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    const newName = generateAgentData().name;
    await form.fillName(newName);
    await form.clickSave();

    await authenticatedPage.getByRole('dialog').waitFor({ state: 'hidden', timeout: 10000 });
    await authenticatedPage.waitForTimeout(1000);

    const cards = await listPage.getAgentCards();
    expect(cards.find((c) => c.name === newName)).toBeDefined();
  });

  test('should edit agent via edit page', async ({ authenticatedPage, authToken }) => {
    const detailPage = new AgentDetailPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken);
    createdAgents.push({ orgId, agentId: created.id });

    await detailPage.goto(orgId, created.id);
    await detailPage.clickEdit();

    // Should navigate to edit page
    await authenticatedPage.waitForURL(/\/edit$/, { timeout: 10000 });

    const newPhone = '+15559876543';
    await form.fillPhone(newPhone);
    await form.clickSave();

    // Should navigate back to detail
    await authenticatedPage.waitForURL(/\/agents\/[^/]+$/, { timeout: 10000 });
    await authenticatedPage.waitForTimeout(2000);
    const phone = await detailPage.getPhoneNumber();
    expect(phone).toContain('9876543');
  });

  test('should delete agent', async ({ authenticatedPage, authToken }) => {
    const listPage = new AgentListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken);
    // Don't push to createdAgents — we're deleting it

    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 10000 });

    await listPage.clickDelete(agentData.name);

    // Confirm in alert dialog
    const confirmButton = authenticatedPage.locator('[role="alertdialog"] button:has-text("Delete")');
    await confirmButton.waitFor({ state: 'visible', timeout: 3000 });
    await confirmButton.click();

    await authenticatedPage.waitForTimeout(2000);
    const cards = await listPage.getAgentCards();
    expect(cards.find((c) => c.name === agentData.name)).toBeUndefined();
  });

  test('should show form validation errors for required fields', async ({ authenticatedPage }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    await listPage.goto(orgId);
    await listPage.clickNewAgent();
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    // Try to submit empty form
    await form.clickCreate();

    const errors = await form.getValidationErrors();
    expect(errors.length).toBeGreaterThan(0);
    // Should have errors for name, description, phone, intents
    const errorText = errors.join(' ');
    expect(errorText).toContain('required');
  });

  test('should show form validation error for invalid phone', async ({ authenticatedPage }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    await listPage.goto(orgId);
    await listPage.clickNewAgent();
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    await form.fillName('Test Agent');
    await form.fillDescription('Test description');
    await form.fillPhone('not-a-phone');
    await form.selectIntent('Book');
    await form.clickCreate();

    const errors = await form.getValidationErrors();
    const errorText = errors.join(' ');
    expect(errorText.toLowerCase()).toContain('phone');
  });

  test('should cancel create operation', async ({ authenticatedPage }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    await listPage.goto(orgId);
    const initialCards = await listPage.getAgentCards();
    const initialCount = initialCards.length;

    await listPage.clickNewAgent();
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    await form.fillName('Should Not Be Created');
    await form.fillDescription('Cancel test');
    await form.clickCancel();

    await authenticatedPage.getByRole('dialog').waitFor({ state: 'hidden', timeout: 5000 });
    await authenticatedPage.waitForTimeout(500);

    const finalCards = await listPage.getAgentCards();
    expect(finalCards.length).toBe(initialCount);
  });

  test('should cancel edit and preserve original', async ({ authenticatedPage, authToken }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken);
    createdAgents.push({ orgId, agentId: created.id });

    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 10000 });

    await listPage.clickEdit(agentData.name);
    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    await form.fillName('Should Not Be Saved');
    await form.clickCancel();

    await authenticatedPage.getByRole('dialog').waitFor({ state: 'hidden', timeout: 5000 });
    await authenticatedPage.waitForTimeout(500);

    const cards = await listPage.getAgentCards();
    expect(cards.find((c) => c.name === agentData.name)).toBeDefined();
    expect(cards.find((c) => c.name === 'Should Not Be Saved')).toBeUndefined();
  });
});
```

**Step 2: Run the tests**

```bash
cd e2e && npx playwright test specs/agents/agents-crud.spec.ts --reporter=list
```

Expected: All 10 tests pass (assumes backend running with `AUTO_PASS_VERIFICATION=true`)

**Step 3: Commit**

```bash
git add e2e/specs/agents/agents-crud.spec.ts
git commit -m "test: add e2e CRUD tests for org-scoped agents (10 tests)"
```

---

## Task 8: Write agents-features.spec.ts

**Files:**
- Create: `e2e/specs/agents/agents-features.spec.ts`

**Pattern:** Same as agents-crud.spec.ts. Uses `apiClient.createAgent()` for setup, verifies UI rendering.

**Tests to implement (6 tests):**

1. **`should show Verified connection status badge`** — Create agent via API → `listPage.goto(orgId)` → `listPage.getStatusBadgeText(name)` → expect "Verified"

2. **`should show verification section on detail page`** — Create agent via API → `detailPage.goto(orgId, id)` → `expect(detailPage.isVerificationSectionVisible()).toBe(true)` → `expect(detailPage.verifyButton).toBeVisible()`

3. **`should toggle agent inactive from detail page`** — Create agent → detail page → `detailPage.toggleActive()` → verify toggle state changed → `page.reload()` → verify state persisted

4. **`should toggle agent inactive from list dropdown`** — Create agent → list page → `listPage.clickDeactivate(name)` → wait → verify "Inactive" badge visible on card

5. **`should show phone number on agent card`** — Create agent with phone → list page → `listPage.getPhoneNumber(name)` → expect contains phone digits

6. **`should navigate between list, detail, and edit pages`** — Create agent → `listPage.goto()` → click card → verify detail URL → `detailPage.clickEdit()` → verify edit URL → `page.goBack()` → verify detail URL → `detailPage.clickBack()` → verify list URL

**Step 1: Create the file following the pattern from Task 7**

Use same imports, same cleanup pattern. Each test creates agent via API, interacts via page objects, asserts UI state.

**Step 2: Run and commit**

```bash
cd e2e && npx playwright test specs/agents/agents-features.spec.ts --reporter=list
git add e2e/specs/agents/agents-features.spec.ts
git commit -m "test: add e2e feature tests for agents (6 tests)"
```

---

## Task 9: Write agents-isolation.spec.ts

**Files:**
- Create: `e2e/specs/agents/agents-isolation.spec.ts`

**Pattern:** Mirrors `personas-isolation.spec.ts`. Creates two orgs via `sidebar.createOrg()`, creates agents in each, verifies isolation.

**Tests to implement (6 tests):**

1. **`should show only active org agents when switching`** — Create org1, create agent in org1. Create org2, create different agent in org2. Switch to org1 → see org1's agent only. Switch to org2 → see org2's agent only.

2. **`should not affect org2 when deleting agent in org1`** — Create same-named agent in both orgs. Delete from org1 via API. Verify org2 still has it via `apiClient.listAgents(org2Id)`.

3. **`should reject cross-org update via API`** — Create agent in org1. Call `apiClient.updateAgent(org2Id, agentId, ...)`. Expect throw. Verify agent unchanged in org1.

4. **`should reject cross-org delete via API`** — Create agent in org1. Call `apiClient.deleteAgent(org2Id, agentId, ...)`. Verify agent still exists in org1.

5. **`should allow same name in different orgs`** — Create "Support Agent" in org1 and org2. Both succeed. Then try creating duplicate "Support Agent" in org1 → expect error from `apiClient.createAgent()`.

6. **`should return 404 for agent from different org`** — Create agent in org1. Call `apiClient.getAgent(org2Id, agentId, ...)`. Expect throw.

**Cleanup:** `afterEach` deletes created orgs (cascades agents).

**Step 1: Create the file following the isolation pattern from personas-isolation.spec.ts**

Key imports: `SidebarPage`, `AgentListPage`, `ApiClient`, `getOrgIdFromPage`, `generateOrgName`, `generateAgentData`

**Step 2: Run and commit**

```bash
cd e2e && npx playwright test specs/agents/agents-isolation.spec.ts --reporter=list
git add e2e/specs/agents/agents-isolation.spec.ts
git commit -m "test: add e2e isolation tests for agents (6 tests)"
```

---

## Task 10: Write test-suites-crud.spec.ts

**Files:**
- Create: `e2e/specs/test-suites/test-suites-crud.spec.ts`

**Key difference from agent tests:** Test suites require a verified agent. Create agent via API first (auto-passes to "verified"). Suite creation triggers generation — use `apiClient.waitForGeneration()` to poll.

**Tests to implement (8 tests):**

1. **`should show empty state on fresh org`** — Create fresh org → `testSuiteListPage.goto(orgId)` → `expect(emptyState).toBeVisible()`

2. **`should create suite with full config and wait for generation`** — Create agent via API. Open create dialog via `listPage.clickNewSuite()`. Fill form via `TestSuiteCreateDialogPage.fillCreateForm({ name, description, agentName, testScopes: ['Core flows'], thoroughness: 'Light', strictness: 'Balanced' })`. Click Generate. Wait for dialog to close. Navigate to detail page. Poll until status is "ready" (use `expect` with polling or `page.waitForFunction`). Verify scenarios table has rows.

3. **`should view suite detail with scenarios`** — Create agent + suite via API. `apiClient.waitForGeneration(orgId, suiteId, authToken)`. Navigate to detail. Verify name, description, badge, scenario rows > 0.

4. **`should edit suite name and description`** — Create agent + suite via API. From list → `listPage.clickEdit(name)`. Change name/description in edit dialog. Save. Verify list updated.

5. **`should delete test suite`** — Create agent + suite via API. From list → `listPage.clickDelete(name)`. Confirm in alert dialog. Verify removed.

6. **`should show form validation for required fields`** — Open create dialog. Click Generate without filling. Expect validation errors for name and agent.

7. **`should cancel create`** — Open dialog, fill, cancel. Verify no suite created.

8. **`should show verified agents in dropdown`** — Create agent via API (auto-verified). Open create dialog. Click agent dropdown. Expect agent name visible in options.

**Cleanup:** Delete suites then agents then orgs in afterEach.

**Step 1: Create the file**

```typescript
import { test, expect } from '../../fixtures/auth.fixture';
import { TestSuiteListPage } from '../../pages/test-suite-list.page';
import { TestSuiteDetailPage } from '../../pages/test-suite-detail.page';
import { TestSuiteCreateDialogPage } from '../../pages/test-suite-create-dialog.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import {
  generateAgentData,
  generateTestSuiteData,
  generateOrgName,
} from '../../helpers/test-data';

// ... follow same cleanup pattern as agents-crud.spec.ts
// but track createdSuites and createdAgents separately
```

**Step 2: Run and commit**

```bash
cd e2e && npx playwright test specs/test-suites/test-suites-crud.spec.ts --reporter=list
git add e2e/specs/test-suites/test-suites-crud.spec.ts
git commit -m "test: add e2e CRUD tests for org-scoped test suites (8 tests)"
```

---

## Task 11: Write test-suites-features.spec.ts

**Files:**
- Create: `e2e/specs/test-suites/test-suites-features.spec.ts`

**Tests to implement (6 tests):**

1. **`should show generation status polling from Generating to Ready`** — Create agent via API. Create suite via UI. Immediately after dialog closes, observe "Generating..." badge in list (use `expect().toBeVisible()`). Then wait for badge to change to "Never Run" (use `expect().toHaveText()` with timeout up to 120s).

2. **`should show correct status badge after generation`** — Create suite via API + `waitForGeneration()`. Navigate to list. Verify badge shows "Never Run".

3. **`should generate more scenarios`** — Create suite + wait for generation. Navigate to detail. Note `getScenarioRowCount()`. Click "Generate More". Fill optional prompt in dialog. Click Generate. Wait for generation. Verify row count increased.

4. **`should show test count matching scenario rows`** — Create suite + wait for generation. Detail page. `getTestCount()` should match `getScenarioRowCount()`.

5. **`should trigger run from list`** — Create suite with scenarios. From list → `clickRun(name)`. Verify badge changes (may show "Running" briefly).

6. **`should show read-only note in edit dialog`** — Create suite via API. From list → `clickEdit(name)`. Verify dialog shows text about only name/description being editable. Verify no agent/scope/thoroughness fields visible.

**Step 1: Create the file following the established pattern**

**Step 2: Run and commit**

```bash
cd e2e && npx playwright test specs/test-suites/test-suites-features.spec.ts --reporter=list
git add e2e/specs/test-suites/test-suites-features.spec.ts
git commit -m "test: add e2e feature tests for test suites (6 tests)"
```

---

## Task 12: Write test-suites-isolation.spec.ts

**Files:**
- Create: `e2e/specs/test-suites/test-suites-isolation.spec.ts`

**Pattern:** Same as agents-isolation. Two orgs, each with an agent and a test suite.

**Tests to implement (6 tests):**

1. **`should show only active org suites when switching`** — Create suite in org1, different suite in org2. Switch orgs. Verify isolation in list.

2. **`should not affect org2 when deleting suite in org1`** — Same-named suites in both orgs. Delete from org1. Verify org2 still has it.

3. **`should reject cross-org update via API`** — Create suite in org1. `updateTestSuite(org2Id, suiteId, ...)` → expect throw. Verify org1's suite unchanged.

4. **`should reject cross-org delete via API`** — Create suite in org1. `deleteTestSuite(org2Id, suiteId, ...)` → verify still exists in org1.

5. **`should allow same name in different orgs`** — Same suite name in both orgs succeeds. Duplicate in same org fails.

6. **`should reject creating suite with agent from different org`** — Create agent in org1. Call `createTestSuite(org2Id, { agent_id: org1AgentId, ... }, ...)` → expect error (400 or 404).

**Step 1: Create the file following the isolation pattern**

**Step 2: Run and commit**

```bash
cd e2e && npx playwright test specs/test-suites/test-suites-isolation.spec.ts --reporter=list
git add e2e/specs/test-suites/test-suites-isolation.spec.ts
git commit -m "test: add e2e isolation tests for test suites (6 tests)"
```

---

## Task 13: Run Full E2E Suite and Final Verification

**Step 1: Run all e2e tests**

```bash
cd e2e && npx playwright test --reporter=list
```

Expected: All tests pass (existing persona tests + new 42 agent/test-suite tests)

**Step 2: Run backend linting and tests (ensure auto-pass flag didn't break anything)**

```bash
uv run ruff check src/voiceobs/ --fix
uv run ruff check tests/ --fix
uv run python -m pytest tests/ -v
uv run python -m pytest tests/ --cov=src/voiceobs --cov-report=term-missing --cov-branch
```

Expected: All pass, >95% coverage for modified modules

**Step 3: Final commit if needed**

```bash
git add -A && git status
# Only commit if there are changes
```

---

## Completion Checklist

- [ ] Task 1: Backend auto-pass verification flag (TDD)
- [ ] Task 2: Test data helpers
- [ ] Task 3: API client — agent methods
- [ ] Task 4: API client — test suite methods
- [ ] Task 5: Agent page objects (list, detail, form)
- [ ] Task 6: Test suite page objects (list, detail, create dialog)
- [ ] Task 7: agents-crud.spec.ts (10 tests)
- [ ] Task 8: agents-features.spec.ts (6 tests)
- [ ] Task 9: agents-isolation.spec.ts (6 tests)
- [ ] Task 10: test-suites-crud.spec.ts (8 tests)
- [ ] Task 11: test-suites-features.spec.ts (6 tests)
- [ ] Task 12: test-suites-isolation.spec.ts (6 tests)
- [ ] Task 13: Full e2e suite run + backend verification

## Environment Setup

Before running e2e tests, ensure:

1. Backend running with `AUTO_PASS_VERIFICATION=true` environment variable
2. Frontend running at `http://localhost:3000`
3. Backend running at `http://localhost:8765`
4. `e2e/.env.test` has valid `TEST_USER_EMAIL` and `TEST_USER_PASSWORD`
5. Database migrated to latest (agents and test-suites have org_id)
