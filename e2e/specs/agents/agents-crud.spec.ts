import { test, expect } from '../../fixtures/auth.fixture';
import { AgentListPage } from '../../pages/agent-list.page';
import { AgentDetailPage } from '../../pages/agent-detail.page';
import { AgentFormPage } from '../../pages/agent-form.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateAgentData, generateAgentName, generateOrgName } from '../../helpers/test-data';

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
      try {
        await apiClient.deleteAgent(orgId, agentId, authToken);
      } catch {
        /* ignore */
      }
    }
    for (const orgId of createdOrgIds) {
      try {
        await apiClient.deleteOrganization(orgId, authToken);
      } catch {
        /* ignore */
      }
    }
  });

  test('should show empty state on fresh org', async ({ authenticatedPage, authToken }) => {
    const sidebar = new SidebarPage(authenticatedPage);
    const listPage = new AgentListPage(authenticatedPage);

    const orgName = generateOrgName();
    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    await sidebar.createOrg(orgName);
    await authenticatedPage.waitForTimeout(1000);

    const orgs = await apiClient.getUserOrgs(authToken);
    const org = orgs.find((o: { name: string }) => o.name === orgName);
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

    await authenticatedPage.getByRole('dialog').waitFor({ state: 'hidden', timeout: 15000 });
    await authenticatedPage.waitForTimeout(2000);

    const cards = await listPage.getAgentCards();
    const created = cards.find((c) => c.name === agentData.name);
    expect(created).toBeDefined();

    const agents = await apiClient.listAgents(orgId, authToken);
    const apiAgent = agents.find((a: { name: string }) => a.name === agentData.name);
    if (apiAgent) createdAgents.push({ orgId, agentId: apiAgent.id });
  });

  test('should view agent detail', async ({ authenticatedPage, authToken }) => {
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
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await listPage.goto(orgId);
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

  test('should edit agent via detail page modal', async ({ authenticatedPage, authToken }) => {
    const detailPage = new AgentDetailPage(authenticatedPage);
    const form = new AgentFormPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
    createdAgents.push({ orgId, agentId: created.id });

    await detailPage.goto(orgId, created.id);
    await detailPage.clickEdit();

    await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

    const newName = generateAgentName();
    await form.fillName(newName);
    await form.clickSave();

    await authenticatedPage.getByRole('dialog').waitFor({ state: 'hidden', timeout: 10000 });
    await authenticatedPage.waitForTimeout(1000);

    const name = await detailPage.getName();
    expect(name).toBe(newName);
  });

  test('should delete agent', async ({ authenticatedPage, authToken }) => {
    const listPage = new AgentListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    const orgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });

    await listPage.goto(orgId);
    await expect(listPage.getAgentCardByName(agentData.name)).toBeVisible({ timeout: 10000 });

    await listPage.clickDelete(agentData.name);

    const confirmButton = authenticatedPage
      .locator('[role="alertdialog"]')
      .getByRole('button', { name: 'Delete' });
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

    await form.clickCreate();

    const errors = await form.getValidationErrors();
    expect(errors.length).toBeGreaterThan(0);
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
    const created = await apiClient.createAgent(orgId, agentData, authToken, {
      bypassVerification: 'verified',
    });
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
