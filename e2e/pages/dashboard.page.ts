import { Page } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  async goto() {
    await this.page.goto('/');
  }

  async isLoaded(): Promise<boolean> {
    // Wait for sidebar to appear (indicates app loaded, not on login page)
    // Do NOT use 'networkidle' — Next.js + Supabase keep persistent connections
    try {
      await this.page.locator('aside').waitFor({ state: 'visible', timeout: 10000 });
      return !this.page.url().includes('/login');
    } catch {
      return false;
    }
  }

  getUrl(): string {
    return this.page.url();
  }
}
