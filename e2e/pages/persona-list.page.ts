import { Page, Locator } from '@playwright/test';

export class PersonaListPage {
  readonly page: Page;
  readonly createButton: Locator;
  readonly activeTab: Locator;
  readonly inactiveTab: Locator;
  readonly personaCards: Locator;

  constructor(page: Page) {
    this.page = page;
    this.createButton = page.locator('a[href="/personas/new"]');
    this.activeTab = page.getByRole('tab', { name: 'Active Personas', exact: true });
    this.inactiveTab = page.getByRole('tab', { name: 'Inactive Personas', exact: true });
    this.personaCards = page.locator('[data-testid="persona-card"]');
  }

  async goto() {
    await this.page.goto('/personas');
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/personas(\?|$)/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickCreate() {
    await this.createButton.first().click();
  }

  async getPersonaCards(): Promise<{ element: Locator; name: string; type: string; isDefault: boolean }[]> {
    const count = await this.personaCards.count();
    const cards = [];

    for (let i = 0; i < count; i++) {
      const card = this.personaCards.nth(i);
      const nameEl = card.locator('[data-testid="persona-name"]');
      const typeEl = card.locator('[data-testid="persona-type"]');
      const defaultBadge = card.locator('[data-testid="default-badge"]');

      const name = (await nameEl.textContent())?.trim() || '';
      const type = (await typeEl.textContent())?.trim().toLowerCase() || '';
      const isDefault = await defaultBadge.isVisible().catch(() => false);

      cards.push({
        element: card,
        name,
        type,
        isDefault,
      });
    }

    return cards;
  }

  async clickPersonaCard(name: string) {
    await this.page.locator(`[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${name}"))`).first().click();
  }

  async switchToInactiveTab() {
    await this.inactiveTab.click();
  }

  async switchToActiveTab() {
    await this.activeTab.click();
  }

  async toggleActiveFromList(personaName: string) {
    const card = this.page.locator(`[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaName}"))`);
    const toggleButton = card.locator('[data-testid="toggle-active-button"]');
    await toggleButton.click();
  }

  async clickPreviewAudio(personaName: string) {
    const card = this.page.locator(`[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaName}"))`).first();
    const previewButton = card.locator('[data-testid="preview-audio-button"]');
    await previewButton.scrollIntoViewIfNeeded();
    await previewButton.click({ force: true });
  }

  async clickSetDefaultFromList(personaName: string) {
    const card = this.page
      .locator(`[data-testid="persona-card"]:has([data-testid="persona-name"]:has-text("${personaName}"))`)
      .first();
    await card.scrollIntoViewIfNeeded();
    await card.locator('[data-testid="persona-card-menu"]').click();
    await this.page.locator('[data-testid="set-default-menu-item"]').first().click();
  }
}
