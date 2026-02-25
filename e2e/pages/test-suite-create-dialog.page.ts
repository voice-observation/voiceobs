import { Page, Locator } from '@playwright/test';

/**
 * Wraps the CreateTestSuiteDialog component.
 *
 * Form input IDs: suiteName, description, agent (Select)
 * Checkboxes: test scopes, edge cases
 * Slider: thoroughness
 * Radio: evaluation strictness
 */
export class TestSuiteCreateDialogPage {
  readonly page: Page;
  readonly dialog: Locator;
  readonly nameInput: Locator;
  readonly descriptionInput: Locator;
  readonly agentSelect: Locator;
  readonly generateButton: Locator;
  readonly saveButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.dialog = page.getByRole('dialog');
    this.nameInput = page.locator('#suiteName');
    this.descriptionInput = page.locator('#description');
    this.agentSelect = page.locator('[role="combobox"]').or(
      this.dialog.locator('button').filter({ hasText: /Select an agent/ })
    );
    this.generateButton = page.getByTestId('test-suite-generate-button');
    this.saveButton = page.getByTestId('test-suite-save-button');
    this.cancelButton = this.dialog.getByTestId('test-suite-cancel-button');
  }

  async fillName(name: string) {
    await this.nameInput.fill(name);
  }

  async fillDescription(description: string) {
    await this.descriptionInput.fill(description);
  }

  /** Select an agent from the dropdown by agent name text. */
  async selectAgent(agentName: string) {
    await this.dialog.getByRole('combobox').click();
    const option = this.page.getByRole('option', { name: new RegExp(agentName, 'i') }).first();
    await option.waitFor({ state: 'visible', timeout: 15000 });
    await option.click({ force: true });
  }

  /** Select test scope checkbox by scope id (e.g. "core_flows", "common_mistakes"). */
  async selectTestScope(scopeId: string) {
    await this.dialog.getByTestId(`test-scope-${scopeId}`).click();
  }

  /** Set thoroughness by clicking the label (Light, Standard, Exhaustive). */
  async setThoroughness(label: string) {
    await this.dialog.getByText(label, { exact: true }).click();
  }

  /** Select edge case checkbox by edge case id (e.g. "hesitations", "interrupts"). */
  async selectEdgeCase(edgeCaseId: string) {
    await this.dialog.getByTestId(`edge-case-${edgeCaseId}`).click();
  }

  /** Select evaluation strictness radio by label. */
  async setStrictness(label: string) {
    await this.dialog.getByLabel(new RegExp(label.split(' ')[0], 'i')).click();
  }

  /** Fill the complete create form. */
  async fillCreateForm(data: {
    name: string;
    description?: string;
    agentName: string;
    testScopes?: string[];
    thoroughness?: string;
    edgeCases?: string[];
    strictness?: string;
  }) {
    await this.fillName(data.name);
    if (data.description) {
      await this.fillDescription(data.description);
    }
    await this.selectAgent(data.agentName);
    for (const scope of data.testScopes || ['core_flows']) {
      await this.selectTestScope(scope);
    }
    if (data.thoroughness) {
      await this.setThoroughness(data.thoroughness);
    }
    for (const ec of data.edgeCases || []) {
      await this.selectEdgeCase(ec);
    }
    if (data.strictness) {
      await this.setStrictness(data.strictness);
    }
  }

  async clickGenerate() {
    await this.generateButton.click();
  }

  async clickSave() {
    await this.saveButton.click();
  }

  async clickCancel() {
    await this.cancelButton.click();
  }

  async isGenerateDisabled(): Promise<boolean> {
    return await this.generateButton.isDisabled();
  }
}
