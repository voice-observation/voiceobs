import { test, expect } from '../../fixtures/auth.fixture';
import { TestSuiteListPage } from '../../pages/test-suite-list.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateOrgName, generateAgentData, generateTestSuiteData } from '../../helpers/test-data';

test.describe('Test Suites Organization Isolation', () => {
  let sharedOrg1Name: string;
  let sharedOrg2Name: string;
  let sharedOrg1Id: string;
  let sharedOrg2Id: string;
  let sharedAgent1: { id: string; name: string };
  let sharedAgent2: { id: string; name: string };
  let sharedSuite1: { id: string; name: string };
  let sharedSuite2: { id: string; name: string };

  test.beforeAll(async ({ authenticatedPage, authToken }) => {
    const api = new ApiClient();
    const sidebar = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    sharedOrg1Name = generateOrgName();
    sharedOrg2Name = generateOrgName();

    await sidebar.createOrg(sharedOrg1Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs1 = await api.getUserOrgs(authToken);
    const org1 = orgs1.find((o: { name: string }) => o.name === sharedOrg1Name);
    sharedOrg1Id = org1!.id;

    await sidebar.createOrg(sharedOrg2Name);
    await authenticatedPage.waitForTimeout(1000);
    const orgs2 = await api.getUserOrgs(authToken);
    const org2 = orgs2.find((o: { name: string }) => o.name === sharedOrg2Name);
    sharedOrg2Id = org2!.id;

    sharedAgent1 = await api.createAgent(sharedOrg1Id, generateAgentData(), authToken, {
      bypassVerification: 'verified',
    });
    sharedAgent2 = await api.createAgent(sharedOrg2Id, generateAgentData(), authToken, {
      bypassVerification: 'verified',
    });
    await authenticatedPage.waitForTimeout(1000);

    const suiteData = generateTestSuiteData(sharedAgent1.id, { name: 'Shared Suite' });
    sharedSuite1 = await api.createTestSuite(sharedOrg1Id, suiteData, authToken);
    sharedSuite2 = await api.createTestSuite(sharedOrg2Id, {
      ...suiteData,
      agent_id: sharedAgent2.id,
    }, authToken);

    await api.waitForGeneration(sharedOrg1Id, sharedSuite1.id, authToken, 120000, 2000);
    await api.waitForGeneration(sharedOrg2Id, sharedSuite2.id, authToken, 120000, 2000);
  });

  test.afterAll(async ({ authToken }) => {
    const api = new ApiClient();
    for (const orgId of [sharedOrg1Id, sharedOrg2Id]) {
      try {
        await api.deleteOrganization(orgId, authToken);
      } catch {
        /* ignore */
      }
    }
  });

  test.describe('read-only isolation', () => {
    test('should show only active org suites when switching', async ({
      authenticatedPage,
    }) => {
      const sidebar = new SidebarPage(authenticatedPage);
      const listPage = new TestSuiteListPage(authenticatedPage);

      await authenticatedPage.goto('/');
      await authenticatedPage.waitForLoadState('networkidle');

      await sidebar.switchOrg(sharedOrg1Name);
      await authenticatedPage.waitForTimeout(500);
      const org1Id = await getOrgIdFromPage(authenticatedPage);
      await listPage.goto(org1Id);
      const rows1 = await listPage.getSuiteRows();
      expect(rows1.find((r) => r.name === 'Shared Suite')).toBeDefined();
      expect(rows1.length).toBe(1);

      await sidebar.switchOrg(sharedOrg2Name);
      await authenticatedPage.waitForTimeout(500);
      const org2Id = await getOrgIdFromPage(authenticatedPage);
      await listPage.goto(org2Id);
      const rows2 = await listPage.getSuiteRows();
      expect(rows2.find((r) => r.name === 'Shared Suite')).toBeDefined();
      expect(rows2.length).toBe(1);
    });

    test('should reject cross-org update via API', async ({ authToken }) => {
      const api = new ApiClient();

      await expect(
        api.updateTestSuite(sharedOrg2Id, sharedSuite1.id, { name: 'Hacked' }, authToken)
      ).rejects.toThrow();

      const suiteInOrg1 = await api.getTestSuite(sharedOrg1Id, sharedSuite1.id, authToken);
      expect(suiteInOrg1.name).toBe(sharedSuite1.name);
    });

    test('should reject cross-org delete via API', async ({ authToken }) => {
      const api = new ApiClient();

      await expect(
        api.deleteTestSuite(sharedOrg2Id, sharedSuite1.id, authToken)
      ).rejects.toThrow();

      const suites1 = await api.listTestSuites(sharedOrg1Id, authToken);
      expect(suites1.find((s: { id: string }) => s.id === sharedSuite1.id)).toBeDefined();
    });

    test('should allow same name in different orgs', async ({ authToken }) => {
      const api = new ApiClient();

      expect(sharedSuite1.id).not.toBe(sharedSuite2.id);

      const suiteData = generateTestSuiteData(sharedAgent1.id, { name: 'Shared Suite' });
      await expect(
        api.createTestSuite(sharedOrg1Id, suiteData, authToken)
      ).rejects.toThrow();
    });

    test('should reject creating suite with agent from different org', async ({
      authToken,
    }) => {
      const api = new ApiClient();
      const suiteData = generateTestSuiteData(sharedAgent1.id);

      await expect(
        api.createTestSuite(sharedOrg2Id, suiteData, authToken)
      ).rejects.toThrow();
    });
  });

  test.describe.serial('mutating isolation', () => {
    test('should not affect org2 when deleting suite in org1', async ({
      authToken,
    }) => {
      const api = new ApiClient();

      await api.deleteTestSuite(sharedOrg1Id, sharedSuite1.id, authToken);

      const suites2 = await api.listTestSuites(sharedOrg2Id, authToken);
      expect(suites2.find((s: { id: string }) => s.id === sharedSuite2.id)).toBeDefined();
    });
  });
});
