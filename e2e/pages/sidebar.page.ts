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
    // Logout button renders as: <Button>...Log out</Button>
    this.logoutButton = page.locator('aside button:has-text("Log out")');
    // OrgSwitcher trigger is a Radix DropdownMenuTrigger (button with aria-haspopup)
    this.orgSwitcher = page.locator('aside button[aria-haspopup="menu"]');
    this.createOrgButton = page.locator('[role="menuitem"]:has-text("Create organization")');
    this.createOrgDialog = page.locator('[role="dialog"]');
    // CreateOrgDialog input has id="org-name" and placeholder="Acme Corp"
    this.orgNameInput = page.locator('#org-name');
    this.createOrgSubmit = page.locator('[role="dialog"] button[type="submit"]');
    // Validation error renders as: <p className="text-sm text-destructive">{error}</p>
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
    // Read the active org name from the trigger button text (shows current org)
    const orgName = this.orgSwitcher.locator('span.truncate');
    return await orgName.textContent();
  }

  async getOrgList(): Promise<string[]> {
    await this.orgSwitcher.click();
    // Wait for dropdown to open
    await this.page.locator('[role="menu"]').waitFor({ state: 'visible' });
    const orgItems = this.page.locator('[role="menuitem"]');
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
    await this.orgSwitcher.click();
    await this.page.locator('[role="menu"]').waitFor({ state: 'visible' });
    await this.page.locator(`[role="menuitem"]:has-text("${name}")`).click();
  }

  async openCreateOrgDialog() {
    await this.orgSwitcher.click();
    const menu = this.page.locator('[role="menu"]');
    await menu.waitFor({ state: 'visible' });
    // Scope to menu to avoid matching other menuitems on the page
    await menu.getByRole('menuitem', { name: 'Create organization' }).click();
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
