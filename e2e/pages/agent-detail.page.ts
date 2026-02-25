import { Page, Locator } from '@playwright/test';

export class AgentDetailPage {
  readonly page: Page;
  readonly editButton: Locator;
  readonly deleteButton: Locator;
  readonly verifyButton: Locator;
  readonly activeToggle: Locator;
  readonly backButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.editButton = page.getByRole('button', { name: 'Edit', exact: true });
    this.deleteButton = page.getByRole('button', { name: 'Delete', exact: true });
    this.verifyButton = page.getByRole('button', { name: /Verify Again/ });
    this.activeToggle = page.locator('#active-toggle');
    this.backButton = page.getByRole('button', { name: /Back to Agents/ }).or(
      page.locator('h1').locator('../..').locator('button').first()
    );
  }

  async goto(orgId: string, agentId: string) {
    await this.page.goto(`/orgs/${orgId}/agents/${agentId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/agents\/[^/]+$/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async getName(): Promise<string> {
    const heading = this.page.getByTestId('agent-name');
    return (await heading.textContent())?.trim() || '';
  }

  async getDescription(): Promise<string> {
    const descEl = this.page.locator('p').filter({ hasText: /\w{10,}/ }).first();
    return (await descEl.textContent())?.trim() || '';
  }

  async getPhoneNumber(): Promise<string | null> {
    const phoneEl = this.page.locator('text=/\\+\\d{5,}/').first();
    if (await phoneEl.isVisible().catch(() => false)) {
      return (await phoneEl.textContent())?.trim() || null;
    }
    return null;
  }

  async getConnectionStatusBadge(): Promise<string> {
    const badge = this.page.locator('[class*="badge"]').first();
    return (await badge.textContent())?.trim() || '';
  }

  async getActiveToggleState(): Promise<boolean> {
    const checked = await this.activeToggle.getAttribute('data-state');
    return checked === 'checked';
  }

  async toggleActive() {
    await this.activeToggle.click();
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickDelete() {
    await this.deleteButton.click();
  }

  async clickVerify() {
    await this.verifyButton.click();
  }

  async clickBack() {
    const link = this.page.getByRole('link', { name: /Back to Agents/ });
    if (await link.isVisible().catch(() => false)) {
      await link.click();
    } else {
      await this.backButton.click();
    }
  }

  /** Get intent badge texts. */
  async getIntents(): Promise<string[]> {
    const section = this.page.locator('text=Supported Intents').locator('..');
    const badges = section.locator('[class*="badge"]');
    const count = await badges.count();
    const intents: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await badges.nth(i).textContent();
      if (text) intents.push(text.trim());
    }
    return intents;
  }

  /** Check if verification section is visible. */
  async isVerificationSectionVisible(): Promise<boolean> {
    return this.page.getByText('Verification Status').isVisible().catch(() => false);
  }
}
