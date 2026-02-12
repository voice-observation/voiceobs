import { Page, Locator } from '@playwright/test';

export class PersonaEditPage {
  readonly page: Page;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly voiceProviderSelect: Locator;
  readonly voiceModelSelect: Locator;
  readonly traitSelectControl: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;
  readonly validationErrors: Locator;

  constructor(page: Page) {
    this.page = page;
    this.nameInput = page.locator('#name');
    this.descriptionInput = page.locator('#description');
    this.voiceProviderSelect = page.locator('#tts-provider');
    this.voiceModelSelect = page.locator('#tts-model');
    this.traitSelectControl = page.locator('[data-testid="trait-select"] .trait-select__control');
    this.saveButton = page.locator('button:has-text("Save Changes")');
    this.cancelButton = page.locator('a[href*="/personas/"]:has-text("Cancel")');
    this.validationErrors = page.locator('.text-destructive');
  }

  async goto(personaId: string) {
    await this.page.goto(`/personas/${personaId}/edit`);
    await this.page.waitForLoadState('networkidle');
  }

  async isLoaded(): Promise<boolean> {
    try {
      await this.page.waitForURL(/\/personas\/[^/]+\/edit/, { timeout: 10000 });
      return true;
    } catch {
      return false;
    }
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async fillDescription(description: string) {
    await this.descriptionInput.fill(description);
  }

  async selectVoiceProvider(provider: string) {
    await this.voiceProviderSelect.click();
    await this.page.getByRole('option', { name: new RegExp(provider, 'i') }).first().click();
  }

  async selectVoiceModel(model: string) {
    await this.voiceModelSelect.click();
    await this.page.getByRole('option').filter({ hasText: model }).first().click();
  }

  async selectTraits(traits: string[]) {
    if (traits.length === 0) return;
    await this.traitSelectControl.click();
    for (const trait of traits) {
      // Use word boundaries so "patient" matches only "patient", not "inpatient"
      await this.page.getByRole('option', { name: new RegExp(`\\b${trait}\\b`, 'i') }).first().click();
    }
    await this.page.keyboard.press('Escape');
  }

  async clickSave() {
    await this.saveButton.click();
  }

  async clickCancel() {
    await this.cancelButton.click();
  }

  async getValidationErrors(): Promise<string[]> {
    const count = await this.validationErrors.count();
    const errors = [];

    for (let i = 0; i < count; i++) {
      const text = await this.validationErrors.nth(i).textContent();
      if (text) {
        errors.push(text.trim());
      }
    }

    return errors;
  }
}
