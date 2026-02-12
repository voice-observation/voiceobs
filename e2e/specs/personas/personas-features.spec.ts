import { test, expect } from '../../fixtures/auth.fixture';
import { PersonaListPage } from '../../pages/persona-list.page';
import { PersonaDetailPage } from '../../pages/persona-detail.page';
import { PersonaEditPage } from '../../pages/persona-edit.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import { generatePersonaData } from '../../helpers/test-data';

/** Personas to delete in afterEach - store orgId so cleanup works even when test fails */
type CreatedPersona = { orgId: string; personaId: string };

test.describe('Personas Features', () => {
  let apiClient: ApiClient;
  let createdPersonas: CreatedPersona[] = [];

  test.beforeEach(async () => {
    apiClient = new ApiClient();
    createdPersonas = [];
  });

  test.afterEach(async ({ authToken }) => {
    if (createdPersonas.length === 0 || !authToken) return;

    for (const { orgId, personaId } of createdPersonas) {
      try {
        await apiClient.deletePersona(orgId, personaId, authToken);
      } catch {
        // Ignore cleanup failures
      }
    }
  });

  test('should set custom persona as default', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await apiClient.setPersonaDefault(orgId, created.id, authToken!);

    await listPage.goto();
    // Wait for list to load and default badge to appear
    await expect(
      authenticatedPage.locator(
        `[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaData.name}")) [data-testid="default-badge"]`
      )
    ).toBeVisible({ timeout: 10000 });
    const personas = await listPage.getPersonaCards();
    const ourPersona = personas.find((p) => p.name === personaData.name);
    expect(ourPersona?.isDefault).toBe(true);

    const allPersonas = await apiClient.listPersonas(orgId, authToken!);
    const systemPersona = allPersonas.find(
      (p: { persona_type?: string }) => p.persona_type === 'system'
    );
    if (systemPersona) {
      await apiClient.setPersonaDefault(orgId, systemPersona.id, authToken!);
    }
  });

  test('should toggle persona active status', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await apiClient.setPersonaActive(orgId, created.id, false, authToken!);

    await listPage.goto();
    await listPage.switchToInactiveTab();
    const inactivePersonas = await listPage.getPersonaCards();
    const ourPersona = inactivePersonas.find((p) => p.name === personaData.name);
    expect(ourPersona).toBeDefined();

    await listPage.toggleActiveFromList(personaData.name);
    await authenticatedPage.waitForTimeout(500);

    await listPage.switchToActiveTab();
    const activePersonas = await listPage.getPersonaCards();
    const ourPersonaActive = activePersonas.find((p) => p.name === personaData.name);
    expect(ourPersonaActive).toBeDefined();
  });

  test('should show default indicator in list', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const defaultPersonas = personas.filter((p) => p.isDefault);
    expect(defaultPersonas.length).toBeGreaterThanOrEqual(1);
  });

  test('only one default at a time (setting new clears old)', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    const allPersonas = await apiClient.listPersonas(orgId, authToken!);
    const systemPersona = allPersonas.find(
      (p: { persona_type?: string }) => p.persona_type === 'system'
    );
    expect(systemPersona).toBeDefined();

    await apiClient.setPersonaDefault(orgId, created.id, authToken!);
    const afterFirst = await apiClient.listPersonas(orgId, authToken!);
    const defaultCount1 = afterFirst.filter((p: { is_default?: boolean }) => p.is_default).length;
    expect(defaultCount1).toBe(1);

    await apiClient.setPersonaDefault(orgId, systemPersona!.id, authToken!);
    const afterSecond = await apiClient.listPersonas(orgId, authToken!);
    const defaultCount2 = afterSecond.filter((p: { is_default?: boolean }) => p.is_default).length;
    expect(defaultCount2).toBe(1);
    const newDefault = afterSecond.find((p: { is_default?: boolean }) => p.is_default);
    expect(newDefault!.id).toBe(systemPersona!.id);

    await apiClient.setPersonaDefault(orgId, systemPersona!.id, authToken!);
  });

  test('default persists across page reloads', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await apiClient.setPersonaDefault(orgId, created.id, authToken!);

    await listPage.goto();
    await expect(
      authenticatedPage.locator(
        `[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaData.name}")) [data-testid="default-badge"]`
      )
    ).toBeVisible({ timeout: 10000 });
    let personas = await listPage.getPersonaCards();
    let ourPersona = personas.find((p) => p.name === personaData.name);
    expect(ourPersona?.isDefault).toBe(true);

    await authenticatedPage.reload();
    await authenticatedPage.waitForLoadState('networkidle');
    await expect(
      authenticatedPage.locator(
        `[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaData.name}")) [data-testid="default-badge"]`
      )
    ).toBeVisible({ timeout: 10000 });
    personas = await listPage.getPersonaCards();
    ourPersona = personas.find((p) => p.name === personaData.name);
    expect(ourPersona?.isDefault).toBe(true);

    const systemPersona = (await apiClient.listPersonas(orgId, authToken!)).find(
      (p: { persona_type?: string }) => p.persona_type === 'system'
    );
    if (systemPersona) {
      await apiClient.setPersonaDefault(orgId, systemPersona.id, authToken!);
    }
  });

  test('toggle persists across page reloads', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await apiClient.setPersonaActive(orgId, created.id, false, authToken!);

    await listPage.goto();
    await listPage.switchToInactiveTab();
    let inactivePersonas = await listPage.getPersonaCards();
    expect(inactivePersonas.find((p) => p.name === personaData.name)).toBeDefined();

    await authenticatedPage.reload();
    await authenticatedPage.waitForLoadState('networkidle');
    await listPage.switchToInactiveTab();
    inactivePersonas = await listPage.getPersonaCards();
    expect(inactivePersonas.find((p) => p.name === personaData.name)).toBeDefined();
  });

  test('inactive personas can be edited', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);
    const editPage = new PersonaEditPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await apiClient.setPersonaActive(orgId, created.id, false, authToken!);

    await listPage.goto();
    await listPage.switchToInactiveTab();
    await listPage.clickPersonaCard(personaData.name);
    await detailPage.clickEdit();
    expect(await editPage.isLoaded()).toBe(true);

    const newName = generatePersonaData().name;
    await editPage.fillName(newName);
    await editPage.clickSave();

    await authenticatedPage.waitForURL(new RegExp(`/personas/${created.id}$`), { timeout: 10000 });
    expect(await detailPage.getPersonaName()).toBe(newName);
  });

  test('set default from detail page', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await detailPage.goto(created.id);
    await detailPage.clickSetDefault();

    await listPage.goto();
    // Wait for list to load and default badge to appear
    await expect(
      authenticatedPage.locator(
        `[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaData.name}")) [data-testid="default-badge"]`
      )
    ).toBeVisible({ timeout: 10000 });
    const personas = await listPage.getPersonaCards();
    const ourPersona = personas.find((p) => p.name === personaData.name);
    expect(ourPersona?.isDefault).toBe(true);

    const systemPersona = (await apiClient.listPersonas(orgId, authToken!)).find(
      (p: { persona_type?: string }) => p.persona_type === 'system'
    );
    if (systemPersona) {
      await apiClient.setPersonaDefault(orgId, systemPersona.id, authToken!);
    }
  });

  test('set default from list page action', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await listPage.goto();
    await listPage.clickSetDefaultFromList(personaData.name);

    // Wait for list to refresh and default badge to appear
    await expect(
      authenticatedPage.locator(
        `[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaData.name}")) [data-testid="default-badge"]`
      )
    ).toBeVisible({ timeout: 10000 });

    const personas = await listPage.getPersonaCards();
    const ourPersona = personas.find((p) => p.name === personaData.name);
    expect(ourPersona?.isDefault).toBe(true);

    const systemPersona = (await apiClient.listPersonas(orgId, authToken!)).find(
      (p: { persona_type?: string }) => p.persona_type === 'system'
    );
    if (systemPersona) {
      await apiClient.setPersonaDefault(orgId, systemPersona.id, authToken!);
    }
  });

  test('preview audio from detail page', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    await detailPage.clickPreviewAudio();
    await authenticatedPage.waitForTimeout(3000);
  });

  test('preview audio from list page', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await listPage.goto();
    const personas = await listPage.getPersonaCards();
    const systemPersona = personas.find((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersona).toBeDefined();

    await listPage.clickPreviewAudio(systemPersona!.name);
    // Verify click succeeded - button shows Playing or Try Voice (no navigation)
    await expect(
      authenticatedPage.locator(`[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${systemPersona!.name}")) [data-testid="preview-audio-button"]`)
    ).toBeVisible();
    });
});
