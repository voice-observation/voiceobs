import { Page, Locator } from '@playwright/test';

export class TestSuiteDetailPage {
  readonly page: Page;
  readonly editButton: Locator;
  readonly runButton: Locator;
  readonly generateMoreButton: Locator;
  readonly backButton: Locator;
  readonly moreMenu: Locator;

  constructor(page: Page) {
    this.page = page;
    this.editButton = page.getByRole('button', { name: 'Edit', exact: true });
    this.runButton = page.getByRole('button', { name: /Run Suite/ });
    this.generateMoreButton = page.getByRole('button', { name: /Generate More/ });
    this.backButton = page
      .getByRole('button', { name: /Back to Test Suites/ })
      .or(page.locator('h1').locator('../..').locator('button').first());
    this.moreMenu = page
      .getByRole('button', { name: /more/i })
      .or(page.locator('button[aria-haspopup="menu"]').last());
  }

  async goto(orgId: string, suiteId: string) {
    await this.page.goto(`/orgs/${orgId}/test-suites/${suiteId}`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/test-suites\/[^/]+$/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async getName(): Promise<string> {
    const heading = this.page.getByTestId('test-suite-name');
    return (await heading.textContent())?.trim() || '';
  }

  async getDescription(): Promise<string | null> {
    const desc = this.page.locator('h1 + p, h2 + p').first();
    if (await desc.isVisible().catch(() => false)) {
      return (await desc.textContent())?.trim() || null;
    }
    return null;
  }

  async getStatusBadge(): Promise<string> {
    const badge = this.page.getByTestId('test-suite-status-badge');
    await badge.waitFor({ state: 'visible', timeout: 10000 });
    return (await badge.textContent())?.trim() || '';
  }

  /** Get the test count from the "Tests: N" badge. */
  async getTestCount(): Promise<number> {
    const testsEl = this.page.getByText(/Tests:\s*\d+/);
    const text = await testsEl.textContent();
    const match = text?.match(/Tests:\s*(\d+)/);
    return match ? parseInt(match[1], 10) : 0;
  }

  /** Get scenario count from the scenarios table rows. */
  async getScenarioRowCount(): Promise<number> {
    const table = this.page.locator('table');
    if (!(await table.isVisible().catch(() => false))) return 0;
    const rows = table.locator('tbody tr');
    return await rows.count();
  }

  /** Check if the "Generating..." indicator is visible. */
  async isGenerating(): Promise<boolean> {
    return this.page.getByText('Generating Test Scenarios').isVisible().catch(() => false);
  }

  async clickEdit() {
    await this.editButton.click();
  }

  async clickRun() {
    await this.runButton.click();
  }

  async clickGenerateMore() {
    await this.generateMoreButton.click();
  }

  async clickDelete() {
    await this.moreMenu.click();
    await this.page.locator('[role="menu"]').waitFor({ state: 'visible' });
    await this.page.locator('[role="menuitem"]:has-text("Delete")').click();
  }

  async clickBack() {
    const link = this.page.getByRole('link', { name: /Back to Test Suites/ });
    if (await link.isVisible().catch(() => false)) {
      await link.click();
    } else {
      await this.backButton.click();
    }
  }
}
