import { test, expect } from '../../fixtures/auth.fixture';
import { PersonaListPage } from '../../pages/persona-list.page';
import { PersonaDetailPage } from '../../pages/persona-detail.page';
import { PersonaEditPage } from '../../pages/persona-edit.page';
import { SidebarPage } from '../../pages/sidebar.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generateOrgName } from '../../helpers/test-data';

test.describe('Personas System Behavior', () => {
  let apiClient: ApiClient;
  let createdOrgIds: string[] = [];

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdOrgIds = [];
  });

  test.afterEach(async ({ authenticatedPage, authToken }) => {
    if (createdOrgIds.length === 0 || !authToken) return;

    for (const orgId of createdOrgIds) {
      try {
        await apiClient.deleteOrganization(orgId, authToken);
      } catch {
        // Ignore cleanup failures
      }
    }
  });

  test('should have system personas when org is created', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const orgName = generateOrgName();
    await sidebarPage.createOrg(orgName);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs = await apiClient.getUserOrgs(authToken!);
    const createdOrg = userOrgs.find((o: { name: string }) => o.name === orgName);
    if (createdOrg) {
      createdOrgIds.push(createdOrg.id);
    }

    await authenticatedPage.goto('/personas');
    await authenticatedPage.waitForLoadState('networkidle');

    const listPage = new PersonaListPage(authenticatedPage);
    const personas = await listPage.getPersonaCards();

    expect(personas.length).toBeGreaterThan(0);
    const systemPersonas = personas.filter((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersonas.length).toBeGreaterThan(0);
  });

  test('should have one default persona from seed catalog', async ({
    authenticatedPage,
    authToken,
  }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const orgName = generateOrgName();
    await sidebarPage.createOrg(orgName);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs = await apiClient.getUserOrgs(authToken!);
    const createdOrg = userOrgs.find((o: { name: string }) => o.name === orgName);
    if (createdOrg) {
      createdOrgIds.push(createdOrg.id);
    }

    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personas = await apiClient.listPersonas(orgId, authToken!);

    const defaultPersonas = personas.filter((p: { is_default?: boolean }) => p.is_default);
    expect(defaultPersonas.length).toBe(1);
  });

  test('should allow editing system persona', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);
    const editPage = new PersonaEditPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    await detailPage.clickEdit();
    expect(await editPage.isLoaded()).toBe(true);

    const newDescription = 'Edited system persona for E2E test';
    await editPage.fillDescription(newDescription);
    await editPage.clickSave();

    expect(await detailPage.getPersonaDescription()).toContain(newDescription);
  });

  test('edited system persona in org1 does not affect org2', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);
    const editPage = new PersonaEditPage(authenticatedPage);
    const sidebarPage = new SidebarPage(authenticatedPage);

    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');

    const org1Name = generateOrgName();
    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs1 = await apiClient.getUserOrgs(authToken!);
    const org1 = userOrgs1.find((o: { name: string }) => o.name === org1Name);
    if (org1) createdOrgIds.push(org1.id);

    await listPage.goto();
    const personas1 = await listPage.getPersonaCards();
    const systemPersona = personas1.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    await detailPage.clickEdit();
    const org1EditText = 'Org1 unique edit for E2E isolation check';
    await editPage.fillDescription(org1EditText);
    await editPage.clickSave();

    const org2Name = generateOrgName();
    await authenticatedPage.goto('/');
    await authenticatedPage.waitForLoadState('networkidle');
    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);

    const userOrgs2 = await apiClient.getUserOrgs(authToken!);
    const org2 = userOrgs2.find((o: { name: string }) => o.name === org2Name);
    if (org2) createdOrgIds.push(org2.id);

    await listPage.goto();
    const personas2 = await listPage.getPersonaCards();
    const org2SystemPersona = personas2.find(
      (p) => p.type.toLowerCase().includes('system') && p.name === systemPersona!.name
    );
    if (org2SystemPersona) {
      await listPage.clickPersonaCard(org2SystemPersona.name);
      const org2Description = await detailPage.getPersonaDescription();
      expect(org2Description).not.toContain(org1EditText);
    }
  });

  test('UI shows system persona badge', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();
    expect(systemPersona!.type.toLowerCase()).toContain('system');

    await listPage.clickPersonaCard(systemPersona!.name);
    const detailType = await detailPage.getPersonaType();
    expect(detailType).toContain('system');
  });

  test('UI disables delete button for system personas', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    const isDisabled = await detailPage.isDeleteButtonDisabled();
    expect(isDisabled).toBe(true);
  });

  test('soft delete (toggle) works for system personas', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    expect(await detailPage.isLoaded()).toBe(true);
    await detailPage.toggleActive();

    await listPage.goto();
    await listPage.switchToInactiveTab();
    const inactivePersonas = await listPage.getPersonaCards();
    const toggledPersona = inactivePersonas.find((p) => p.name === systemPersona!.name);
    expect(toggledPersona).toBeDefined();

    await listPage.toggleActiveFromList(systemPersona!.name);
    await authenticatedPage.waitForTimeout(500);
    await listPage.switchToActiveTab();
    const activePersonas = await listPage.getPersonaCards();
    const restoredPersona = activePersonas.find((p) => p.name === systemPersona!.name);
    expect(restoredPersona).toBeDefined();
  });

  test('persona_type field correctly shows system', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    expect(await detailPage.isLoaded()).toBe(true);
    const personaType = await detailPage.getPersonaType();
    expect(personaType).toBe('system');
  });

  test('should block hard delete of system persona', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await listPage.goto();
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const allPersonas = await apiClient.listPersonas(orgId, authToken!);
    const systemPersonaData = allPersonas.find(
      (p: { persona_type?: string }) => p.persona_type === 'system'
    );
    expect(systemPersonaData).toBeDefined();

    await expect(async () => {
      await apiClient.deletePersona(orgId, systemPersonaData!.id, authToken!);
    }).rejects.toThrow();
  });
});
