import { test, expect } from '../../fixtures/auth.fixture';
import { AgentListPage } from '../../pages/agent-list.page';
import { AgentDetailPage } from '../../pages/agent-detail.page';
import { AgentFormPage } from '../../pages/agent-form.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateAgentData } from '../../helpers/test-data';

type CreatedAgent = { orgId: string; agentId: string };

test.describe('Agents Features', () => {
  let apiClient: ApiClient;
  let createdAgents: CreatedAgent[] = [];

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdAgents = [];
  });

  test.afterEach(async ({ authToken }) => {
    for (const { orgId, agentId } of createdAgents) {
      try {
        await apiClient.deleteAgent(orgId, agentId, authToken);
      } catch {
        /* ignore */
      }
    }
  });

  test('should show Verified connection status badge', async ({
    authenticatedPage,
    authToken,
  }) => {
    test.setTimeout(60000);
    const listPage = new AgentListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    // Agent is already verified via bypass - no need to poll
    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 15000 });

    // Use expect with locator for resilience (auto-retry, avoids "page closed" races)
    await expect(listPage.getStatusBadge(agentData.name)).toContainText('Verified', {
      timeout: 10000,
    });
  });

  test('should show verification section on detail page', async ({
    authenticatedPage,
    authToken,
  }) => {
    const detailPage = new AgentDetailPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await detailPage.goto(orgId, created.id);
    expect(await detailPage.isVerificationSectionVisible()).toBe(true);
    await expect(detailPage.verifyButton).toBeVisible();
  });

  test('should toggle agent inactive from detail page', async ({
    authenticatedPage,
    authToken,
  }) => {
    const detailPage = new AgentDetailPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await detailPage.goto(orgId, created.id);
    const initialActive = await detailPage.getActiveToggleState();

    await detailPage.toggleActive();
    await authenticatedPage.waitForTimeout(1000);

    const afterToggle = await detailPage.getActiveToggleState();
    expect(afterToggle).toBe(!initialActive);

    await authenticatedPage.reload();
    await authenticatedPage.waitForLoadState('networkidle');
    const afterReload = await detailPage.getActiveToggleState();
    expect(afterReload).toBe(!initialActive);
  });

  test('should toggle agent inactive from list dropdown', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new AgentListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 15000 });

    await listPage.clickDeactivate(agentData.name);
    await authenticatedPage.waitForTimeout(2000);

    await expect(listPage.getStatusBadge(agentData.name)).toContainText('Inactive', {
      timeout: 10000,
    });
  });

  test('should show phone number on agent card', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const phone = '+15551234567';
    const agentData = generateAgentData({
      contact_info: { phone_number: phone },
    });

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 15000 });

    const displayedPhone = await listPage.getPhoneNumber(agentData.name);
    expect(displayedPhone).toContain('555');
  });

  test('should navigate between list and detail, and open edit dialog', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new AgentListPage(authenticatedPage);
    const detailPage = new AgentDetailPage(authenticatedPage);
    const formPage = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 15000 });

    await listPage.clickView(agentData.name);
    await authenticatedPage.waitForURL(/\/agents\/[^/]+$/, { timeout: 10000 });

    await detailPage.clickEdit();
    await expect(formPage.saveButton).toBeVisible({ timeout: 10000 });

    await formPage.clickCancel();
    await expect(formPage.saveButton).not.toBeVisible({ timeout: 5000 });

    await detailPage.clickBack();
    await authenticatedPage.waitForURL(/\/orgs\/[^/]+\/agents/, { timeout: 10000 });
  });
});
