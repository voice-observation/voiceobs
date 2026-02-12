import { test, expect } from '../../fixtures/auth.fixture';
import { PersonaListPage } from '../../pages/persona-list.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateOrgName, generatePersonaData } from '../../helpers/test-data';

test.describe('Personas Organization Isolation', () => {
  let apiClient: ApiClient;
  let createdOrgIds: string[] = [];

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdOrgIds = [];
  });

  test.afterEach(async ({ authToken }) => {
    if (createdOrgIds.length === 0 || !authToken) return;

    for (const orgId of createdOrgIds) {
      try {
        await apiClient.deleteOrganization(orgId, authToken);
      } catch {
        // Ignore cleanup failures
      }
    }
  });

  test('should show only active org personas when switching orgs', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await authenticatedPage.goto('/personas');
    await authenticatedPage.waitForLoadState('networkidle');
    const org1Id = await getOrgIdFromPage(authenticatedPage);

    const personaData = generatePersonaData();
    await apiClient.createPersona(org1Id, personaData, authToken!);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    await listPage.goto();
    const personasInOrg2 = await listPage.getPersonaCards();

    const createdInOrg1 = personasInOrg2.find((p) => p.name === personaData.name);
    expect(createdInOrg1).toBeUndefined();
  });

  test('deleting persona in org1 does not affect org2', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await authenticatedPage.goto('/personas');
    const org1Id = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData({ name: 'Customer Service' });
    const created1 = await apiClient.createPersona(org1Id, personaData, authToken!);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    await authenticatedPage.goto('/personas');
    const org2Id = await getOrgIdFromPage(authenticatedPage);
    const created2 = await apiClient.createPersona(org2Id, personaData, authToken!);

    await apiClient.deletePersona(org1Id, created1.id, authToken!);

    const personas2 = await apiClient.listPersonas(org2Id, authToken!);
    const stillExists = personas2.find((p: { id: string }) => p.id === created2.id);
    expect(stillExists).toBeDefined();
  });

  test('API UPDATE rejects cross-org operations', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(org1.id, personaData, authToken!);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    await expect(
      apiClient.updatePersona(org2.id, created.id, { name: 'Hacked' }, authToken!)
    ).rejects.toThrow();
  });

  test('API DELETE rejects cross-org operations', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(org1.id, personaData, authToken!);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    // Cross-org delete: backend returns 404 (persona not in org2); API client treats 404 as no-op.
    // Verify isolation: persona must still exist in org1.
    await apiClient.deletePersona(org2.id, created.id, authToken!);
    const personasInOrg1 = await apiClient.listPersonas(org1.id, authToken!);
    const stillExists = personasInOrg1.find((p: { id: string }) => p.id === created.id);
    expect(stillExists).toBeDefined();
  });

  test('default persona is per-org (independent)', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await authenticatedPage.goto('/personas');
    const org1Id = await getOrgIdFromPage(authenticatedPage);
    const personas1 = await apiClient.listPersonas(org1Id, authToken!);
    const org1Default = personas1.find((p: { is_default?: boolean }) => p.is_default);
    expect(org1Default).toBeDefined();

    const customPersona = generatePersonaData();
    const created1 = await apiClient.createPersona(org1Id, customPersona, authToken!);
    await apiClient.setPersonaDefault(org1Id, created1.id, authToken!);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    await authenticatedPage.goto('/personas');
    const org2Id = await getOrgIdFromPage(authenticatedPage);
    const personas2 = await apiClient.listPersonas(org2Id, authToken!);
    const org2Default = personas2.find((p: { is_default?: boolean }) => p.is_default);
    expect(org2Default).toBeDefined();
    expect(org2Default!.id).not.toBe(created1.id);
  });

  test('name uniqueness is per-org (two orgs can have same name)', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    const sharedName = 'Customer Service Rep';
    const personaData = generatePersonaData({ name: sharedName });
    const created1 = await apiClient.createPersona(org1!.id, personaData, authToken!);
    expect(created1.name).toBe(sharedName);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);
    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    const created2 = await apiClient.createPersona(org2!.id, personaData, authToken!);
    expect(created2.name).toBe(sharedName);
    expect(created2.id).not.toBe(created1.id);
  });

  test('should return 404 when getting persona from different org', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(org1.id, personaData, authToken!);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    await expect(
      apiClient.getPersona(org2.id, created.id, authToken!)
    ).rejects.toThrow();
  });
});
