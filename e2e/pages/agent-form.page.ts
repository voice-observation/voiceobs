import { Page, Locator } from '@playwright/test';

/**
 * Wraps the AgentConfigForm component, used in both:
 * - Create dialog (from list page "New Agent" button)
 * - Edit page (/orgs/{orgId}/agents/{id}/edit)
 *
 * Form input IDs: name, description, context, phone
 * Intent checkboxes: Book, Reschedule, Cancel, Ask hours, Talk to human
 */
export class AgentFormPage {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly contextInput: Locator;
  readonly phoneInput: Locator;
  readonly createButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly validationErrors: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.locator('#name');
    this.descriptionInput = page.locator('#description');
    this.contextInput = page.locator('#context');
    this.phoneInput = page.locator('#phone');
    this.createButton = page.getByRole('button', { name: /Create Agent/ });
    this.saveButton = page.getByRole('button', { name: /Save Changes/ });
    this.cancelButton = page.getByRole('button', { name: 'Cancel' });
    this.validationErrors = page.locator('.text-destructive');
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async fillDescription(description: string) {
    await this.descriptionInput.fill(description);
  }

  async fillPhone(phone: string) {
    await this.phoneInput.fill(phone);
  }

  async fillContext(context: string) {
    await this.contextInput.fill(context);
  }

  /**
   * Select a predefined intent checkbox by label (Book, Reschedule, Cancel, Ask hours, Talk to human).
   * CheckboxCard is a custom div, not a native checkbox, so we find by text and click the card.
   */
  async selectIntent(label: string) {
    const card = this.page.locator('div.cursor-pointer').filter({ hasText: label });
    await card.click();
  }

  /** Add a custom intent via the text input + Add button (Plus icon). */
  async addCustomIntent(intent: string) {
    await this.page.getByPlaceholder('Add custom intent...').fill(intent);
    const addBtn = this.page
      .locator('div.flex.gap-2')
      .filter({ has: this.page.getByPlaceholder('Add custom intent...') })
      .locator('button');
    await addBtn.click();
  }

  /** Fill the complete agent form for creation. */
  async fillCreateForm(data: {
    name: string;
    description: string;
    phone: string;
    intents?: string[];
    customIntents?: string[];
    context?: string;
  }) {
    await this.fillName(data.name);
    await this.fillDescription(data.description);
    await this.fillPhone(data.phone);
    if (data.context) {
      await this.fillContext(data.context);
    }
    for (const intent of data.intents || ['Book']) {
      await this.selectIntent(intent);
    }
    for (const ci of data.customIntents || []) {
      await this.addCustomIntent(ci);
    }
  }

  async clickCreate() {
    await this.createButton.click();
  }

  async clickSave() {
    await this.saveButton.click();
  }

  async clickCancel() {
    await this.cancelButton.click();
  }

  async isCreateDisabled(): Promise<boolean> {
    return await this.createButton.isDisabled();
  }

  async isSaveDisabled(): Promise<boolean> {
    return await this.saveButton.isDisabled();
  }

  async getValidationErrors(): Promise<string[]> {
    const count = await this.validationErrors.count();
    const errors: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await this.validationErrors.nth(i).textContent();
      if (text) errors.push(text.trim());
    }
    return errors;
  }
}
