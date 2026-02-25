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

type CreatedSuite = { orgId: string; suiteId: string };
type CreatedAgent = { orgId: string; agentId: string };

test.describe('Test Suites CRUD', () => {
  let apiClient: ApiClient;
  let createdSuites: CreatedSuite[] = [];
  let createdAgents: CreatedAgent[] = [];
  let createdOrgIds: string[] = [];

  // Shared state for tests that reuse one suite (created in beforeAll)
  let sharedOrgId: string;
  let sharedAgent: { id: string; name: string };
  let sharedSuite: { id: string; name: string };
  let sharedSuiteName: string;

  test.beforeAll(async ({ authenticatedPage, authToken }) => {
    const api = new ApiClient();
    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    sharedOrgId = await getOrgIdFromPage(authenticatedPage);

    const agentData = generateAgentData();
    sharedAgent = await api.createAgent(sharedOrgId, agentData, authToken, {
      bypassVerification: 'verified',
    });

    const suiteData = generateTestSuiteData(sharedAgent.id);
    sharedSuite = await api.createTestSuite(sharedOrgId, suiteData, authToken);
    await api.waitForGeneration(sharedOrgId, sharedSuite.id, authToken, 120000, 2000);

    sharedSuiteName = sharedSuite.name;
  });

  test.afterAll(async ({ authToken }) => {
    const api = new ApiClient();
    if (sharedAgent) {
      try {
        await api.deleteAgent(sharedOrgId, sharedAgent.id, authToken);
      } catch {
        /* ignore */
      }
    }
  });

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdSuites = [];
    createdAgents = [];
    createdOrgIds = [];
  });

  test.afterEach(async ({ authToken }) => {
    for (const { orgId, suiteId } of createdSuites) {
      try {
        await apiClient.deleteTestSuite(orgId, suiteId, authToken);
      } catch {
        /* ignore */
      }
    }
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

  test.describe.serial('with shared suite', () => {
    test('should view suite detail with scenarios', async ({ authenticatedPage }) => {
      const detailPage = new TestSuiteDetailPage(authenticatedPage);

      await detailPage.goto(sharedOrgId, sharedSuite.id);
      expect(await detailPage.isLoaded()).toBe(true);

      const name = await detailPage.getName();
      expect(name).toContain(sharedSuite.name);

      const badge = await detailPage.getStatusBadge();
      expect(badge).toBeDefined();

      const rowCount = await detailPage.getScenarioRowCount();
      expect(rowCount).toBeGreaterThan(0);
    });

    test('should edit suite name and description', async ({
      authenticatedPage,
    }) => {
      const listPage = new TestSuiteListPage(authenticatedPage);
      const dialog = new TestSuiteCreateDialogPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      await listPage.goto(sharedOrgId);
      await expect(listPage.getSuiteRowByName(sharedSuiteName)).toBeVisible({
        timeout: 10000,
      });

      await listPage.clickEdit(sharedSuiteName);
      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

      const newName = generateTestSuiteData(sharedAgent.id).name;
      sharedSuiteName = newName;
      await dialog.fillName(newName);
      await dialog.fillDescription('Updated description');
      await dialog.clickSave();

      await authenticatedPage.getByRole('dialog').waitFor({
        state: 'hidden',
        timeout: 10000,
      });
      await authenticatedPage.waitForTimeout(1000);

      const rows = await listPage.getSuiteRows();
      expect(rows.find((r) => r.name === newName)).toBeDefined();
    });

    test('should delete test suite', async ({ authenticatedPage }) => {
      const listPage = new TestSuiteListPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      await listPage.goto(sharedOrgId);
      await expect(listPage.getSuiteRowByName(sharedSuiteName)).toBeVisible({
        timeout: 10000,
      });

      await listPage.clickDelete(sharedSuiteName);

      const confirmButton = authenticatedPage
        .locator('[role="alertdialog"]')
        .getByRole('button', { name: 'Delete Suite' });
      await confirmButton.waitFor({ state: 'visible', timeout: 3000 });
      await confirmButton.click();

      await authenticatedPage.waitForTimeout(2000);
      const rows = await listPage.getSuiteRows();
      expect(rows.find((r) => r.name === sharedSuiteName)).toBeUndefined();
    });
  });

  test.describe('without shared suite', () => {
    test('should show empty state on fresh org', async ({
      authenticatedPage,
      authToken,
    }) => {
      const sidebar = new SidebarPage(authenticatedPage);
      const listPage = new TestSuiteListPage(authenticatedPage);

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

    test('should create suite with full config and wait for generation', async ({
      authenticatedPage,
      authToken,
    }) => {
      test.setTimeout(300000);
      const listPage = new TestSuiteListPage(authenticatedPage);
      const detailPage = new TestSuiteDetailPage(authenticatedPage);
      const dialog = new TestSuiteCreateDialogPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      const suiteData = generateTestSuiteData(sharedAgent.id);
      await listPage.goto(sharedOrgId);
      await listPage.clickNewSuite();

      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

      await dialog.fillCreateForm({
        name: suiteData.name,
        description: suiteData.description || '',
        agentName: sharedAgent.name,
        testScopes: ['core_flows'],
        thoroughness: 'Light',
        strictness: 'Balanced (recommended)',
      });

      await dialog.clickGenerate();

      await authenticatedPage.getByRole('dialog').waitFor({
        state: 'hidden',
        timeout: 10000,
      });
      await authenticatedPage.waitForTimeout(2000);

      const suites = await apiClient.listTestSuites(sharedOrgId, authToken);
      const created = suites.find((s: { name: string }) => s.name === suiteData.name);
      expect(created).toBeDefined();
      if (created) createdSuites.push({ orgId: sharedOrgId, suiteId: created.id });

      const result = await apiClient.waitForGeneration(
        sharedOrgId,
        created.id,
        authToken,
        120000,
        2000
      );

      await detailPage.goto(sharedOrgId, created.id);
      const rowCount = await detailPage.getScenarioRowCount();
      if (result.status === 'ready') {
        expect(rowCount).toBeGreaterThan(0);
      }
    });

    test('should show form validation for required fields', async ({
      authenticatedPage,
    }) => {
      const listPage = new TestSuiteListPage(authenticatedPage);
      const dialog = new TestSuiteCreateDialogPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      await listPage.goto(sharedOrgId);
      await listPage.clickNewSuite();
      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

      expect(await dialog.isGenerateDisabled()).toBe(true);
    });

    test('should cancel create', async ({ authenticatedPage }) => {
      const listPage = new TestSuiteListPage(authenticatedPage);
      const dialog = new TestSuiteCreateDialogPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      await listPage.goto(sharedOrgId);
      const initialRows = await listPage.getSuiteRows();
      const initialCount = initialRows.length;

      await listPage.clickNewSuite();
      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

      await dialog.fillName('Should Not Be Created');
      await dialog.clickCancel();

      await authenticatedPage.getByRole('dialog').waitFor({
        state: 'hidden',
        timeout: 5000,
      });
      await authenticatedPage.waitForTimeout(500);

      const finalRows = await listPage.getSuiteRows();
      expect(finalRows.length).toBe(initialCount);
    });

    test('should show verified agents in dropdown', async ({
      authenticatedPage,
    }) => {
      test.setTimeout(180000);
      const listPage = new TestSuiteListPage(authenticatedPage);
      const dialog = new TestSuiteCreateDialogPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      await listPage.goto(sharedOrgId);
      await listPage.clickNewSuite();
      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });

      await dialog.dialog.getByRole('combobox').click();
      await expect(
        authenticatedPage.getByRole('option', {
          name: new RegExp(sharedAgent.name, 'i'),
        })
      ).toBeVisible({ timeout: 5000 });
    });
  });
});
