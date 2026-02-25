import { Page, Locator } from '@playwright/test';

export class SidebarPage {
  readonly page: Page;
  readonly sidebar: Locator;
  readonly logoutButton: Locator;
  readonly orgSwitcher: Locator;
  readonly createOrgButton: Locator;
  readonly createOrgDialog: Locator;
  readonly orgNameInput: Locator;
  readonly createOrgSubmit: Locator;
  readonly orgValidationError: Locator;

  constructor(page: Page) {
    this.page = page;
    this.sidebar = page.locator('aside');
    this.logoutButton = page.locator('aside button:has-text("Log out")');
    this.orgSwitcher = page.getByTestId('org-switcher-trigger');
    this.createOrgButton = page.getByTestId('org-switcher-create-org');
    this.createOrgDialog = page.locator('[role="dialog"]');
    this.orgNameInput = page.getByTestId('create-org-name-input');
    this.createOrgSubmit = page.getByTestId('create-org-submit');
    this.orgValidationError = page.locator('[role="dialog"] .text-destructive');
  }

  async getUserEmail(): Promise<string | null> {
    // Email renders in sidebar bottom as: <div className="truncate ... text-muted-foreground">{user.email}</div>
    const emailEl = this.sidebar.locator('.mt-auto .truncate');
    await emailEl.waitFor({ state: 'visible', timeout: 5000 });
    return await emailEl.textContent();
  }

  async logout() {
    await this.logoutButton.click();
  }

  async openOrgSwitcher() {
    await this.orgSwitcher.click();
  }

  async getActiveOrgName(): Promise<string | null> {
    const orgName = this.orgSwitcher.locator('span.truncate');
    return await orgName.textContent();
  }

  async getOrgList(): Promise<string[]> {
    await this.orgSwitcher.waitFor({ state: 'visible', timeout: 10000 });
    await this.orgSwitcher.click();
    await this.page.getByTestId('org-switcher-menu').waitFor({ state: 'visible', timeout: 5000 });
    const orgItems = this.page.getByTestId('org-switcher-org-item');
    const count = await orgItems.count();
    const orgs: string[] = [];

    for (let i = 0; i < count; i++) {
      const text = await orgItems.nth(i).textContent();
      if (text && !text.includes('Create')) {
        orgs.push(text.trim());
      }
    }

    await this.page.keyboard.press('Escape');
    return orgs;
  }

  async switchOrg(name: string) {
    await this.orgSwitcher.waitFor({ state: 'visible', timeout: 10000 });
    await this.orgSwitcher.click();
    await this.page.getByTestId('org-switcher-menu').waitFor({ state: 'visible', timeout: 5000 });
    await this.page.getByTestId('org-switcher-org-item').filter({ hasText: name }).click();
  }

  async openCreateOrgDialog() {
    await this.orgSwitcher.waitFor({ state: 'visible', timeout: 10000 });
    await this.orgSwitcher.click();
    await this.page.getByTestId('org-switcher-menu').waitFor({ state: 'visible', timeout: 5000 });
    await this.page.getByTestId('org-switcher-create-org').click();
  }

  async createOrg(name: string): Promise<void> {
    await this.openCreateOrgDialog();
    await this.orgNameInput.fill(name);
    await this.createOrgSubmit.click();
    // Wait for dialog to close
    await this.createOrgDialog.waitFor({ state: 'hidden', timeout: 5000 });
  }

  async createOrgExpectError(name: string): Promise<string | null> {
    await this.openCreateOrgDialog();
    await this.orgNameInput.fill(name);
    await this.createOrgSubmit.click();
    // Wait for error text to appear
    await this.orgValidationError.waitFor({ state: 'visible', timeout: 3000 });
    return await this.orgValidationError.textContent();
  }
}
