import { Page } from '@playwright/test';

/** LocalStorage key used by auth context for active org */
const ORG_STORAGE_KEY = 'voiceobs_active_org_id';

/**
 * Get the active org ID from the page.
 * Must be called after navigating to a page that has loaded the auth context
 * (e.g. /personas or /).
 * Polls until the org ID appears (auth context loads async) or timeout.
 */
export async function getOrgIdFromPage(
  page: Page,
  options?: { timeout?: number }
): Promise<string> {
  const timeout = options?.timeout ?? 10000;
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const orgId = await page.evaluate(
      (key) => localStorage.getItem(key) || '',
      ORG_STORAGE_KEY
    );
    if (orgId) return orgId;
    await page.waitForTimeout(300);
  }
  return '';
}
