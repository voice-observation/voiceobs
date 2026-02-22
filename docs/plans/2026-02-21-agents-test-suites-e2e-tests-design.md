# E2E Tests for Organization-Scoped Agents and Test Suites

## Problem

Agents and test-suites have been moved to organization-level scoping. We need e2e UI tests to verify the frontend behaves correctly: CRUD operations work through the org-scoped routes, features render properly, and data is isolated between organizations.

## Decisions

| Decision | Choice |
|----------|--------|
| Test structure | Mirror persona e2e pattern: 3 spec files per entity (crud, features, isolation) |
| Agent verification in tests | Auto-pass via backend flag (`SKIP_AGENT_VERIFICATION=true`) — agents immediately get "verified" status |
| Test suite generation | Full flow — wait for AI generation to complete and verify scenarios appear |
| Test scenario CRUD | Out of scope — suite-level operations only |
| Total tests | 42 across 6 spec files |

## Backend Test Mode Flag

**Environment variable:** `SKIP_AGENT_VERIFICATION=true`

When set, the `create_agent` and `verify_agent` routes auto-pass verification instead of calling the external phone service. Agents immediately transition to `verified` status with zero latency.

This is required because every agent create triggers background verification. Without auto-pass, e2e tests would depend on an external phone service and be flaky.

## File Structure

```
e2e/
  pages/
    agent-list.page.ts
    agent-detail.page.ts
    agent-form.page.ts
    test-suite-list.page.ts
    test-suite-detail.page.ts
    test-suite-create-dialog.page.ts
  specs/
    agents/
      agents-crud.spec.ts          (10 tests)
      agents-features.spec.ts      (6 tests)
      agents-isolation.spec.ts     (6 tests)
    test-suites/
      test-suites-crud.spec.ts     (8 tests)
      test-suites-features.spec.ts (6 tests)
      test-suites-isolation.spec.ts(6 tests)
  helpers/
    api-client.ts                  (add agent + test-suite methods)
    test-data.ts                   (add generateAgentData, generateTestSuiteData)
```

## Page Objects

### agent-list.page.ts

Wraps `/orgs/{orgId}/agents` list page.

- `goto(orgId)` — navigate to list
- `getAgentCards()` — all agent card locators
- `getAgentCardByName(name)` — find specific card
- `clickNewAgent()` — open create dialog
- `getEmptyState()` — empty state locator
- `getAgentDropdownMenu(name)` — open actions dropdown
- `clickView(name)`, `clickEdit(name)`, `clickDelete(name)`, `clickVerify(name)`, `clickToggleActive(name)` — dropdown actions
- `getStatusBadge(name)` — connection status badge on card

### agent-detail.page.ts

Wraps `/orgs/{orgId}/agents/{id}` detail page.

- `goto(orgId, agentId)` — navigate to detail
- `getName()`, `getPhoneNumber()`, `getDescription()` — read fields
- `getConnectionStatusBadge()`, `getActiveToggle()` — status elements
- `clickEdit()`, `clickDelete()`, `clickVerify()` — action buttons
- `getVerificationSection()` — verification status card
- `getTranscriptViewer()` — transcript viewer section
- `getIntentBadges()` — supported intent badges

### agent-form.page.ts

Wraps AgentConfigForm (used in create dialog and edit page).

- `fillName(name)`, `fillDescription(desc)`, `fillPhone(phone)`, `fillContext(ctx)` — form inputs
- `selectIntent(intent)`, `addCustomIntent(intent)` — intent management
- `submit()`, `cancel()` — form actions
- `getValidationError(field)` — error messages
- `isSubmitDisabled()` — button state

### test-suite-list.page.ts

Wraps `/orgs/{orgId}/test-suites` list page.

- `goto(orgId)` — navigate
- `getSuiteRows()` — table row locators
- `getSuiteRowByName(name)` — find specific row
- `clickNewSuite()` — open create dialog
- `getEmptyState()` — empty state
- `getStatusBadge(name)` — status badge in row
- `getPassRate(name)` — pass rate display
- `clickView(name)`, `clickEdit(name)`, `clickRun(name)`, `clickDelete(name)` — row actions

### test-suite-detail.page.ts

Wraps `/orgs/{orgId}/test-suites/{id}` detail page.

- `goto(orgId, suiteId)` — navigate
- `getName()`, `getDescription()`, `getStatusBadge()` — read fields
- `getTestCount()`, `getPassRate()` — metrics
- `clickEdit()`, `clickDelete()`, `clickRun()`, `clickGenerateMore()` — actions
- `getGeneratingIndicator()` — generation in-progress state
- `getScenariosTable()` — scenarios table locator
- `getScenarioCount()` — count of visible scenarios

### test-suite-create-dialog.page.ts

Wraps CreateTestSuiteDialog.

- `fillName(name)`, `fillDescription(desc)` — form inputs
- `selectAgent(agentName)` — agent dropdown
- `selectTestScopes(scopes[])` — checkboxes
- `setThoroughness(level)` — slider
- `selectEdgeCases(cases[])` — checkboxes
- `setStrictness(level)` — radio buttons
- `submit()`, `cancel()` — actions
- `isSubmitDisabled()` — button state

## API Client Additions

New methods in `e2e/helpers/api-client.ts`:

- `listAgents(orgId)`, `createAgent(orgId, data)`, `getAgent(orgId, id)`, `updateAgent(orgId, id, data)`, `deleteAgent(orgId, id)`
- `listTestSuites(orgId)`, `createTestSuite(orgId, data)`, `getTestSuite(orgId, id)`, `updateTestSuite(orgId, id, data)`, `deleteTestSuite(orgId, id)`, `getGenerationStatus(orgId, id)`

## Test Data Helpers

New functions in `e2e/helpers/test-data.ts`:

- `generateAgentData()` — returns `{ name, description, phone, intents, context }` with timestamp-based unique name
- `generateTestSuiteData(agentId)` — returns `{ name, description, agentId, testScopes, thoroughness, edgeCases, evaluationStrictness }` with unique name

## Test Specifications

### agents-crud.spec.ts (10 tests)

Setup: authenticated page, default org. Cleanup deletes created agents via API.

1. **Show empty state on fresh org** — navigate to agents page on new org, see empty state and "New Agent" CTA
2. **Create agent with all fields** — open create dialog, fill name/description/phone/context, select intents + custom intent, submit, see card in list with name, phone, "Verified" badge
3. **View agent detail** — create via API, navigate to detail, verify all fields render
4. **Edit agent via dialog** — create via API, open edit from list dropdown, change name/description, save, verify list updated
5. **Edit agent via edit page** — create via API, detail page, click Edit, change phone, save, verify detail shows new phone
6. **Delete agent** — create via API, delete from list dropdown, confirm, verify removed
7. **Form validation - required fields** — try submit with empty form, see errors on name/description/phone/intents
8. **Form validation - invalid phone** — enter invalid phone, see E.164 format error
9. **Cancel create** — fill dialog, cancel, no agent created
10. **Cancel edit** — open edit, change name, cancel, original persists

### agents-features.spec.ts (6 tests)

Setup: creates agents via API. Cleanup via API.

1. **Connection status badge shows "Verified"** — create agent, navigate to list, badge shows "Verified" (auto-pass)
2. **Detail page shows verification section** — navigate to detail, status card visible with "Verified", attempts, "Verify Again" button
3. **Toggle agent inactive from detail** — toggle switch off, badge shows "Inactive", reload, state persists
4. **Toggle agent inactive from list** — dropdown Deactivate, card shows "Inactive" badge
5. **Phone number displayed on agent card** — create with phone, verify icon and number on card
6. **Navigate between list, detail, and edit** — list -> card -> detail -> Edit -> edit page -> Back -> detail -> Back -> list

### agents-isolation.spec.ts (6 tests)

Setup: two organizations with agents. Cleanup deletes both orgs.

1. **Show only active org's agents when switching** — agent in org1, different in org2, switch, verify isolation
2. **Deleting agent in org1 doesn't affect org2** — same-named agents, delete from org1, org2 still has it
3. **API rejects cross-org update** — create in org1, update via org2's ID, expect 404
4. **API rejects cross-org delete** — create in org1, delete via org2's ID, expect 404
5. **Name uniqueness is per-org** — same name in both orgs succeeds, duplicate in same org fails
6. **Return 404 when getting agent from different org** — create in org1, get via org2's ID, 404

### test-suites-crud.spec.ts (8 tests)

Setup: creates verified agent via API in beforeAll. Cleanup deletes suites and agents.

1. **Show empty state on fresh org** — navigate to test suites page, see empty state and "New Suite" CTA
2. **Create test suite with full config and wait for generation** — open dialog, fill name/description, select agent, choose scopes/thoroughness/edge cases/strictness, submit, see "Generating...", poll until "Ready", verify scenarios in detail
3. **View suite detail with scenarios** — create via API + wait for generation, navigate to detail, verify name/description/badge/test count/scenarios table
4. **Edit suite name and description** — create via API, edit icon from list, change name/description, save, verify list updated
5. **Delete test suite** — create via API, delete icon, confirm, removed from list
6. **Form validation - required fields** — try submit, see errors for name and agent
7. **Cancel create** — fill dialog, cancel, no suite created
8. **Agent dropdown shows verified agents** — verified agent appears in dropdown (smoke test)

### test-suites-features.spec.ts (6 tests)

Setup: creates verified agent. Some tests create suites and wait for generation.

1. **Generation status polling: Generating to Ready** — create via UI, observe "Generating..." badge with spinner, wait, transitions to "Never Run" (ready)
2. **Status badge shows correct state** — create via API + wait, navigate to list, verify "Never Run" badge
3. **Generate more scenarios** — create + generate, detail page, note count, click "Generate More", wait, count increased
4. **Suite detail shows test count** — after generation, test count badge matches scenario table rows
5. **Run suite triggers execution** — create with scenarios, click Run, status badge changes
6. **Edit dialog shows config as read-only note** — edit dialog shows note that only name/description can be changed

### test-suites-isolation.spec.ts (6 tests)

Setup: two organizations, each with agent and suite. Cleanup deletes both orgs.

1. **Show only active org's suites when switching** — suite in org1, different in org2, switch, verify isolation
2. **Deleting suite in org1 doesn't affect org2** — same-named suites, delete from org1, org2 still has it
3. **API rejects cross-org update** — create in org1, update via org2's ID, expect 404
4. **API rejects cross-org delete** — create in org1, delete via org2's ID, expect 404
5. **Name uniqueness is per-org** — same name in both orgs succeeds, duplicate in same org fails
6. **Cannot create suite with agent from different org** — create agent in org1, create suite in org2 referencing org1's agent, expect error

## Patterns

All tests follow existing persona e2e conventions:

- **Auth fixture** — reuse `auth.fixture.ts` for authenticated page and token
- **API-driven setup** — create entities via API client for test preconditions
- **UI-driven verification** — assert through page objects, not API responses
- **Cleanup in afterEach** — delete created entities via API (idempotent, 404 = success)
- **Deterministic names** — timestamp-based unique names via test data helpers
- **Org isolation tests** — create two orgs, verify data doesn't leak
- **Page object model** — all selectors centralized in page objects
