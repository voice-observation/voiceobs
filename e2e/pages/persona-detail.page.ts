import { Page, Locator } from '@playwright/test';

export class PersonaDetailPage {
  readonly page: Page;
  readonly personaName: Locator;
  readonly personaDescription: Locator;
  readonly editButton: Locator;
  readonly deleteButton: Locator;
  readonly toggleActiveButton: Locator;
  readonly previewAudioButton: Locator;
  readonly backButton: Locator;
  readonly defaultBadge: Locator;
  readonly personaType: Locator;
  readonly setDefaultButton: Locator;
  readonly traitsContainer: Locator;

  constructor(page: Page) {
    this.page = page;
    this.personaName = page.locator('[data-testid="persona-name"]');
    this.personaDescription = page.locator('[data-testid="persona-description"]');
    this.editButton = page.locator('[data-testid="edit-persona-link"]');
    this.deleteButton = page.locator('[data-testid="delete-persona-button"]');
    // Scope to detail page (has active-indicator); list cards don't, so this avoids matching list
    this.toggleActiveButton = page.locator('[data-testid="active-indicator"] ~ [data-testid="toggle-active-button"]');
    this.previewAudioButton = page.locator('[data-testid="preview-audio-button"]');
    this.backButton = page.locator('a[href="/personas"]');
    this.defaultBadge = page.locator('[data-testid="default-badge"]');
    // Scope to detail page header (h1) - list page uses h3, so this avoids matching list cards
    this.personaType = page.locator('h1[data-testid="persona-name"] ~ [data-testid="persona-type"]');
    this.setDefaultButton = page.locator('[data-testid="set-default-button"]');
    this.traitsContainer = page.locator('[data-testid="persona-traits"]');
  }

  async goto(personaId: string) {
    await this.page.goto(`/personas/${personaId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/personas\/[^/]+$/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async getPersonaName(): Promise<string> {
    return (await this.personaName.textContent())?.trim() || '';
  }

  async getPersonaDescription(): Promise<string> {
    return (await this.personaDescription.textContent())?.trim() || '';
  }

  async isDefault(): Promise<boolean> {
    return await this.defaultBadge.isVisible().catch(() => false);
  }

  async getPersonaType(): Promise<string> {
    return (await this.personaType.textContent())?.trim().toLowerCase() || '';
  }

  async getTraits(): Promise<string[]> {
    const badges = this.traitsContainer.locator('[data-testid^="trait-"]');
    const count = await badges.count();
    const traits: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await badges.nth(i).textContent();
      if (text) traits.push(text.trim());
    }
    return traits;
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickDelete() {
    await this.deleteButton.click();
  }

  async clickSetDefault() {
    await this.setDefaultButton.click();
  }

  async isDeleteButtonDisabled(): Promise<boolean> {
    return await this.deleteButton.isDisabled();
  }

  async toggleActive() {
    await this.toggleActiveButton.click();
  }

  async clickPreviewAudio() {
    await this.previewAudioButton.first().click();
  }

  async clickBack() {
    await this.backButton.first().click();
  }
}
