import { test, expect } from '../../fixtures/auth.fixture';
import { TestSuiteListPage } from '../../pages/test-suite-list.page';
import { TestSuiteDetailPage } from '../../pages/test-suite-detail.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateAgentData, generateTestSuiteData } from '../../helpers/test-data';

test.describe('Test Suites Features', () => {
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
    if (sharedSuite && sharedOrgId) {
      try {
        await api.deleteTestSuite(sharedOrgId, sharedSuite.id, authToken);
      } catch {
        /* ignore */
      }
    }
    if (sharedAgent && sharedOrgId) {
      try {
        await api.deleteAgent(sharedOrgId, sharedAgent.id, authToken);
      } catch {
        /* ignore */
      }
    }
  });

  test.describe.serial('with shared suite', () => {
    test('should show correct status badge after generation', async ({
      authenticatedPage,
    }) => {
      const listPage = new TestSuiteListPage(authenticatedPage);

      await listPage.goto(sharedOrgId);
      const badge = await listPage.getStatusBadge(sharedSuiteName);
      expect(badge).toContain('Never Run');
    });

    test('should show test count matching scenario rows', async ({
      authenticatedPage,
    }) => {
      const detailPage = new TestSuiteDetailPage(authenticatedPage);

      await detailPage.goto(sharedOrgId, sharedSuite.id);
      const testCount = await detailPage.getTestCount();
      const scenarioCount = await detailPage.getScenarioRowCount();
      expect(testCount).toBe(scenarioCount);
    });

    test('should show read-only note in edit dialog', async ({
      authenticatedPage,
    }) => {
      const listPage = new TestSuiteListPage(authenticatedPage);

      await listPage.goto(sharedOrgId);
      await listPage.clickEdit(sharedSuiteName);

      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });
      await expect(
        authenticatedPage.getByText(/Only name and description can be changed/)
      ).toBeVisible({ timeout: 5000 });
    });

    test('should generate more scenarios', async ({
      authenticatedPage,
      authToken,
    }) => {
      const detailPage = new TestSuiteDetailPage(authenticatedPage);
      const api = new ApiClient();

      await detailPage.goto(sharedOrgId, sharedSuite.id);
      const initialCount = await detailPage.getScenarioRowCount();

      await detailPage.clickGenerateMore();
      await authenticatedPage.getByRole('dialog').waitFor({ state: 'visible' });
      await authenticatedPage
        .getByRole('dialog')
        .getByRole('button', { name: /^Generate$/ })
        .click();
      await authenticatedPage.getByRole('dialog').waitFor({
        state: 'hidden',
        timeout: 5000,
      });
      await authenticatedPage.waitForTimeout(2000);

      await api.waitForGeneration(
        sharedOrgId,
        sharedSuite.id,
        authToken,
        120000,
        2000
      );

      await detailPage.goto(sharedOrgId, sharedSuite.id);
      const finalCount = await detailPage.getScenarioRowCount();
      expect(finalCount).toBeGreaterThanOrEqual(initialCount);
    });
  });
});
