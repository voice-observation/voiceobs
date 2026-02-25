import { Page, Locator } from '@playwright/test';

export class AgentListPage {
  readonly page: Page;
  readonly newAgentButton: Locator;
  readonly emptyState: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newAgentButton = page.getByRole('button', { name: 'New Agent' });
    this.emptyState = page.getByText('Create Your First Agent');
  }

  async goto(orgId: string) {
    await this.page.goto(`/orgs/${orgId}/agents`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/agents(\?|$)/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickNewAgent() {
    await this.newAgentButton.click();
  }

  /**
   * Get all agent cards on the page.
   * Agent cards are in a grid; each has h3 with agent name.
   */
  async getAgentCards(): Promise<{ name: string; element: Locator }[]> {
    await this.page.waitForTimeout(1000);
    const cards = this.page.locator('.grid > div').filter({ has: this.page.locator('h3') });
    const count = await cards.count();
    const result: { name: string; element: Locator }[] = [];

    for (let i = 0; i < count; i++) {
      const card = cards.nth(i);
      const name = await card.locator('h3').first().textContent();
      if (name) {
        result.push({ name: name.trim(), element: card });
      }
    }

    return result;
  }

  /** Find an agent card by name. */
  getAgentCardByName(name: string): Locator {
    return this.page.locator('.grid > div').filter({
      has: this.page.locator(`h3:has-text("${name}")`),
    });
  }

  /** Open dropdown and click an action (View, Edit, Verify, Deactivate, Activate, Delete). */
  async clickCardAction(agentName: string, action: string) {
    const card = this.getAgentCardByName(agentName);
    const menuTrigger = card.locator('button[aria-haspopup="menu"]');
    await menuTrigger.click();
    await this.page.locator('[role="menu"]').waitFor({ state: 'visible' });
    await this.page.locator(`[role="menuitem"]:has-text("${action}")`).click();
  }

  async clickView(agentName: string) {
    await this.clickCardAction(agentName, 'View');
  }

  async clickEdit(agentName: string) {
    await this.clickCardAction(agentName, 'Edit');
  }

  async clickDelete(agentName: string) {
    await this.clickCardAction(agentName, 'Delete');
  }

  async clickVerify(agentName: string) {
    await this.clickCardAction(agentName, 'Verify');
  }

  async clickDeactivate(agentName: string) {
    await this.clickCardAction(agentName, 'Deactivate');
  }

  async clickActivate(agentName: string) {
    await this.clickCardAction(agentName, 'Activate');
  }

  /** Get the status badge locator for an agent card (connection + active status). */
  getStatusBadge(agentName: string): Locator {
    return this.getAgentCardByName(agentName).locator('[data-testid="agent-status-badge"]');
  }

  /** Get the status badge text for an agent card. */
  async getStatusBadgeText(agentName: string): Promise<string> {
    const badge = this.getStatusBadge(agentName);
    return (await badge.textContent())?.trim() || '';
  }

  /** Check if phone number is displayed on an agent card. */
  async getPhoneNumber(agentName: string): Promise<string | null> {
    const card = this.getAgentCardByName(agentName);
    const phoneEl = card.locator('text=/\\+\\d/');
    if (await phoneEl.isVisible().catch(() => false)) {
      return (await phoneEl.textContent())?.trim() || null;
    }
    return null;
  }
}
