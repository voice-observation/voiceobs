import { test, expect } from '../../fixtures/auth.fixture';
import { PersonaListPage } from '../../pages/persona-list.page';
import { PersonaDetailPage } from '../../pages/persona-detail.page';
import { PersonaCreatePage } from '../../pages/persona-create.page';
import { PersonaEditPage } from '../../pages/persona-edit.page';
import { ApiClient } from '../../helpers/api-client';
import { getOrgIdFromPage } from '../../helpers/org';
import {
  generatePersonaData,
  E2E_TRAITS,
  E2E_ELEVENLABS_MODEL_DISPLAY,
} from '../../helpers/test-data';

/** Personas to delete in afterEach - store orgId so cleanup works even when test fails */
type CreatedPersona = { orgId: string; personaId: string };

test.describe('Personas CRUD', () => {
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

  test('should list personas on fresh org', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);

    await listPage.goto();
    expect(await listPage.isLoaded()).toBe(true);

    const personas = await listPage.getPersonaCards();
    expect(personas.length).toBeGreaterThan(0);

    const systemPersonas = personas.filter((p) => p.type.toLowerCase().includes('system'));
    expect(systemPersonas.length).toBeGreaterThan(0);
  });

  test('should create custom persona with all fields', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const createPage = new PersonaCreatePage(authenticatedPage);

    await listPage.goto();
    await listPage.clickCreate();
    expect(await createPage.isLoaded()).toBe(true);

    const personaData = generatePersonaData();
    await createPage.fillForm({
      name: personaData.name,
      description: personaData.description || 'E2E test',
      traits: personaData.traits || [...E2E_TRAITS],
      voiceProvider: personaData.tts_provider || 'elevenlabs',
      voiceModel: E2E_ELEVENLABS_MODEL_DISPLAY,
    });

    await createPage.clickSubmit();

    await authenticatedPage.waitForURL(/\/personas(\?|$)/, { timeout: 10000 });

    // Wait for list to load and the new persona card to appear (list fetches on mount)
    await expect(
      authenticatedPage.locator(
        `[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaData.name}"))`
      )
    ).toBeVisible({ timeout: 15000 });

    const personas = await listPage.getPersonaCards();
    const created = personas.find((p) => p.name === personaData.name);
    expect(created).toBeDefined();

    await listPage.clickPersonaCard(personaData.name);
    const detailPage = new PersonaDetailPage(authenticatedPage);
    expect(await detailPage.isLoaded()).toBe(true);

    const expectedTraits = personaData.traits || [...E2E_TRAITS];
    // Wait for detail page to load and traits to render (fetches on mount)
    const firstTrait = expectedTraits[0];
    await expect(
      authenticatedPage.locator(`[data-testid="trait-${firstTrait}"]`)
    ).toBeVisible({ timeout: 10000 });

    const displayedTraits = await detailPage.getTraits();
    for (const trait of expectedTraits) {
      expect(displayedTraits).toContain(trait);
    }

    // Extract persona ID from URL (/personas/[id]) for cleanup - avoids listPersonas API call
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const url = new URL(authenticatedPage.url());
    const pathParts = url.pathname.split('/').filter(Boolean);
    const personaId = pathParts[pathParts.length - 1];
    if (personaId && orgId) {
      createdPersonas.push({ orgId, personaId });
    }
  });

  test('should view persona detail', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await listPage.goto();
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await detailPage.goto(created.id);
    expect(await detailPage.isLoaded()).toBe(true);

    expect(await detailPage.getPersonaName()).toBe(personaData.name);
    if (personaData.description) {
      expect(await detailPage.getPersonaDescription()).toContain(personaData.description);
    }
  });

  test('should edit custom persona', async ({ authenticatedPage, authToken }) => {
    const detailPage = new PersonaDetailPage(authenticatedPage);
    const editPage = new PersonaEditPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await detailPage.goto(created.id);
    await detailPage.clickEdit();
    expect(await editPage.isLoaded()).toBe(true);

    const newName = generatePersonaData().name;
    const newDescription = 'Updated description for E2E testing';
    await editPage.fillName(newName);
    await editPage.fillDescription(newDescription);
    await editPage.clickSave();

    await authenticatedPage.waitForURL(new RegExp(`/personas/${created.id}$`), { timeout: 10000 });

    expect(await detailPage.getPersonaName()).toBe(newName);
    expect(await detailPage.getPersonaDescription()).toContain(newDescription);
  });

  test('should delete custom persona', async ({ authenticatedPage, authToken }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);

    await detailPage.goto(created.id);
    await detailPage.clickDelete();

    const confirmButton = authenticatedPage.locator('[role="alertdialog"] button:has-text("Delete")');
    await confirmButton.waitFor({ state: 'visible', timeout: 3000 });
    await confirmButton.click();

    await authenticatedPage.waitForURL(/\/personas(\?|$)/, { timeout: 10000 });

    const personas = await listPage.getPersonaCards();
    const deleted = personas.find((p) => p.name === personaData.name);
    expect(deleted).toBeUndefined();
  });

  test('should disable submit when name or description is empty', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const createPage = new PersonaCreatePage(authenticatedPage);

    await listPage.goto();
    await listPage.clickCreate();
    expect(await createPage.isLoaded()).toBe(true);

    // Empty name, valid description - submit should be disabled
    await createPage.fillName('');
    await createPage.fillDescription('Some description');
    expect(await createPage.isSubmitDisabled()).toBe(true);

    // Valid name, empty description - submit should be disabled
    await createPage.fillName('Test Persona');
    await createPage.fillDescription('');
    expect(await createPage.isSubmitDisabled()).toBe(true);
  });

  test('should cancel create operation', async ({ authenticatedPage }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const createPage = new PersonaCreatePage(authenticatedPage);

    await listPage.goto();
    const initialCount = (await listPage.getPersonaCards()).length;

    await listPage.clickCreate();
    expect(await createPage.isLoaded()).toBe(true);

    const personaData = generatePersonaData();
    await createPage.fillName(personaData.name);
    await createPage.fillDescription(personaData.description || 'test');

    await createPage.clickCancel();

    await authenticatedPage.waitForURL(/\/personas(\?|$)/, { timeout: 10000 });

    // Wait for list to load (tabs visible = past loading state)
    await authenticatedPage
      .getByRole('tab', { name: 'Active Personas', exact: true })
      .waitFor({ state: 'visible', timeout: 10000 });
    await authenticatedPage.waitForLoadState('networkidle');

    const finalCount = (await listPage.getPersonaCards()).length;
    expect(finalCount).toBe(initialCount);
  });

  test('should soft delete custom persona (toggle to inactive)', async ({
    authenticatedPage,
    authToken,
  }) => {
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
  });

  test('should navigate between list, create, detail, and edit pages', async ({
    authenticatedPage,
    authToken,
  }) => {
    const listPage = new PersonaListPage(authenticatedPage);
    const createPage = new PersonaCreatePage(authenticatedPage);
    const detailPage = new PersonaDetailPage(authenticatedPage);
    const editPage = new PersonaEditPage(authenticatedPage);

    await listPage.goto();
    expect(await listPage.isLoaded()).toBe(true);

    await listPage.clickCreate();
    expect(await createPage.isLoaded()).toBe(true);

    await createPage.clickCancel();
    expect(await listPage.isLoaded()).toBe(true);

    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personas = await apiClient.listPersonas(orgId, authToken!);
    const systemPersona = personas.find((p: { persona_type?: string }) => p.persona_type === 'system');
    expect(systemPersona).toBeDefined();

    await listPage.clickPersonaCard(systemPersona!.name);
    expect(await detailPage.isLoaded()).toBe(true);

    await detailPage.clickEdit();
    expect(await editPage.isLoaded()).toBe(true);

    await editPage.clickCancel();
    expect(await detailPage.isLoaded()).toBe(true);

    await detailPage.clickBack();
    expect(await listPage.isLoaded()).toBe(true);
  });

  test('should cancel edit operation', async ({ authenticatedPage, authToken }) => {
    const detailPage = new PersonaDetailPage(authenticatedPage);
    const editPage = new PersonaEditPage(authenticatedPage);

    await authenticatedPage.goto('/personas');
    const orgId = await getOrgIdFromPage(authenticatedPage);
    const personaData = generatePersonaData();
    const created = await apiClient.createPersona(orgId, personaData, authToken!);
    createdPersonas.push({ orgId, personaId: created.id });

    await detailPage.goto(created.id);
    const originalName = await detailPage.getPersonaName();

    await detailPage.clickEdit();
    expect(await editPage.isLoaded()).toBe(true);

    await editPage.fillName('Should Not Be Saved');
    await editPage.clickCancel();

    await authenticatedPage.waitForURL(new RegExp(`/personas/${created.id}$`), { timeout: 10000 });

    expect(await detailPage.getPersonaName()).toBe(originalName);
  });
});
