import { Page, Locator } from '@playwright/test';

export class TestSuiteListPage {
  readonly page: Page;
  readonly newSuiteButton: Locator;
  readonly emptyState: Locator;
  readonly suiteTable: Locator;

  constructor(page: Page) {
    this.page = page;
    this.newSuiteButton = page.getByTestId('test-suite-new-button');
    this.emptyState = page.getByTestId('test-suite-empty-state');
    this.suiteTable = page.getByTestId('test-suite-list-table');
  }

  async goto(orgId: string) {
    await this.page.goto(`/orgs/${orgId}/test-suites`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/orgs\/[^/]+\/test-suites(\?|$)/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async clickNewSuite() {
    await this.newSuiteButton.click();
  }

  /** Get all suite rows from the table. */
  async getSuiteRows(): Promise<{ name: string; element: Locator }[]> {
    await this.page.waitForTimeout(1000);
    const rows = this.suiteTable.locator('[data-testid="test-suite-row"]');
    const count = await rows.count();
    const result: { name: string; element: Locator }[] = [];

    for (let i = 0; i < count; i++) {
      const row = rows.nth(i);
      const name = await row.getAttribute('data-suite-name');
      if (name) {
        result.push({ name, element: row });
      }
    }

    return result;
  }

  /** Find a suite row by name. */
  getSuiteRowByName(name: string): Locator {
    return this.page.getByTestId('test-suite-row').filter({ hasText: name });
  }

  /** Get the status badge text for a suite row. */
  async getStatusBadge(suiteName: string): Promise<string> {
    const row = this.getSuiteRowByName(suiteName);
    const badge = row.getByTestId('test-suite-status-badge');
    return (await badge.textContent())?.trim() || '';
  }

  async clickView(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.getByTestId('test-suite-action-view').click();
  }

  async clickEdit(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.getByTestId('test-suite-action-edit').click();
  }

  async clickRun(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.getByTestId('test-suite-action-run').click();
  }

  async clickDelete(suiteName: string) {
    const row = this.getSuiteRowByName(suiteName);
    await row.getByTestId('test-suite-action-delete').click();
  }
}
