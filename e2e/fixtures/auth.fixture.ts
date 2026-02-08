import { test as base, Page } from '@playwright/test';
import * as dotenv from 'dotenv';
import * as path from 'path';
import * as fs from 'fs';

dotenv.config({ path: '.env.test' });

const STORAGE_STATE_PATH = path.join(__dirname, '../.auth/user.json');

type AuthFixtures = {
  authenticatedPage: Page;
  authToken: string;
};

/**
 * Custom fixture that provides an authenticated page
 * Logs in once and reuses the session via storageState
 */
export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ browser }, use) => {
    const testUserEmail = process.env.TEST_USER_EMAIL;
    const testUserPassword = process.env.TEST_USER_PASSWORD;
    const baseUrl = process.env.BASE_URL || 'http://localhost:3000';

    if (!testUserEmail || !testUserPassword) {
      throw new Error('TEST_USER_EMAIL and TEST_USER_PASSWORD must be set in .env.test');
    }

    // Try cached session, fall back to fresh login
    let context;
    let needsLogin = true;

    if (fs.existsSync(STORAGE_STATE_PATH)) {
      context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
      const page = await context.newPage();

      // Validate the cached session is still active
      await page.goto(`${baseUrl}/`);
      await page.waitForURL(/./, { timeout: 10000 });
      needsLogin = page.url().includes('/login');

      await page.close();

      if (needsLogin) {
        await context.close();
      }
    }

    if (needsLogin) {
      // Login and save session
      context = await browser.newContext();
      const page = await context.newPage();

      await page.goto(`${baseUrl}/login`);
      await page.fill('input[type="email"]', testUserEmail);
      await page.fill('input[type="password"]', testUserPassword);
      await page.click('button[type="submit"]');
      await page.waitForURL((url) => url.pathname !== '/login', { timeout: 10000 });

      // Save storage state
      const authDir = path.dirname(STORAGE_STATE_PATH);
      if (!fs.existsSync(authDir)) {
        fs.mkdirSync(authDir, { recursive: true });
      }
      await context.storageState({ path: STORAGE_STATE_PATH });

      await page.close();
    }

    // Create new page with authenticated context
    const page = await context.newPage();

    await use(page);

    await page.close();
    await context.close();
  },

  authToken: async ({ authenticatedPage }, use) => {
    // Supabase SSR stores auth in cookies, not localStorage.
    // Cookie value is "base64-<json>" with access_token inside.
    const cookies = await authenticatedPage.context().cookies();
    const authCookie = cookies.find(
      (c) => c.name.startsWith('sb-') && c.name.endsWith('-auth-token')
    );

    if (!authCookie) {
      throw new Error('Failed to extract auth token from authenticated session');
    }

    const raw = authCookie.value.replace(/^base64-/, '');
    const parsed = JSON.parse(Buffer.from(raw, 'base64').toString('utf-8'));
    const token = parsed.access_token;

    if (!token) {
      throw new Error('Failed to extract access_token from auth cookie');
    }

    await use(token);
  },
});

export { expect } from '@playwright/test';
