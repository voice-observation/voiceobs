import { test, expect } from '../fixtures/auth.fixture';
import { LoginPage } from '../pages/login.page';
import { SidebarPage } from '../pages/sidebar.page';
import { DashboardPage } from '../pages/dashboard.page';
import { ApiClient } from '../helpers/api-client';
import { generateOrgName } from '../helpers/test-data';

test.describe('Organization Management', () => {
  let createdOrgIds: string[] = [];
  let apiClient: ApiClient;

  test.beforeEach(async ({ authenticatedPage }) => {
    apiClient = new ApiClient();
    createdOrgIds = [];

    // Start on dashboard
    const dashboardPage = new DashboardPage(authenticatedPage);
    await dashboardPage.goto();
  });

  test.afterEach(async ({ authenticatedPage }) => {
    if (createdOrgIds.length === 0) {
      return;
    }

    // Extract token from cookies for cleanup
    const cookies = await authenticatedPage.context().cookies();
    const authCookie = cookies.find(
      (c) => c.name.startsWith('sb-') && c.name.endsWith('-auth-token')
    );

    if (authCookie) {
      const raw = authCookie.value.replace(/^base64-/, '');
      const parsed = JSON.parse(Buffer.from(raw, 'base64').toString('utf-8'));
      const token = parsed.access_token;

      if (token) {
        for (const orgId of createdOrgIds) {
          try {
            await apiClient.deleteOrganization(orgId, token);
          } catch (error) {
            console.warn(`Failed to cleanup org ${orgId}:`, error);
          }
        }
      }
    }
    createdOrgIds = [];
  });

  test('should show default organization after login', async ({ authenticatedPage }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    // Should have at least one org (the default auto-created one)
    // getOrgList() opens the switcher itself
    const orgs = await sidebarPage.getOrgList();
    expect(orgs.length).toBeGreaterThan(0);
  });

  test('should create new organization', async ({ authenticatedPage, authToken }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    // Generate unique org name
    const newOrgName = generateOrgName();

    // Create org
    await sidebarPage.createOrg(newOrgName);

    // Wait a moment for creation
    await authenticatedPage.waitForTimeout(1000);

    // New org should appear in switcher
    const orgs = await sidebarPage.getOrgList();
    expect(orgs.some(org => org.includes(newOrgName.substring(0, 20)))).toBe(true);

    // New org should be active
    const activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(newOrgName.substring(0, 20));

    // Track for cleanup (get org ID from API)
    const userOrgs = await apiClient.getUserOrgs(authToken);
    const createdOrg = userOrgs.find(o => o.name === newOrgName);
    if (createdOrg) {
      createdOrgIds.push(createdOrg.id);
    }
  });

  test('should switch between organizations', async ({ authenticatedPage, authToken }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    // Create two orgs
    const org1Name = generateOrgName();
    const org2Name = generateOrgName();

    await sidebarPage.createOrg(org1Name);
    await authenticatedPage.waitForTimeout(1000);

    await sidebarPage.createOrg(org2Name);
    await authenticatedPage.waitForTimeout(1000);

    // org2 should be active now
    let activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(org2Name);

    // Switch back to org1
    await sidebarPage.switchOrg(org1Name);
    await authenticatedPage.waitForTimeout(500);

    // org1 should now be active
    activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(org1Name);

    // Track for cleanup
    const userOrgs = await apiClient.getUserOrgs(authToken);
    const createdOrg1 = userOrgs.find(o => o.name === org1Name);
    const createdOrg2 = userOrgs.find(o => o.name === org2Name);
    if (createdOrg1) createdOrgIds.push(createdOrg1.id);
    if (createdOrg2) createdOrgIds.push(createdOrg2.id);
  });

  test('should disable create button for empty org name', async ({ authenticatedPage }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    // Open the create org dialog
    await sidebarPage.openCreateOrgDialog();

    // With empty input, the create button should be disabled
    await expect(sidebarPage.createOrgSubmit).toBeDisabled();

    // Dialog should still be open
    await expect(sidebarPage.createOrgDialog).toBeVisible();
  });

  test('should persist active org across page reload', async ({ authenticatedPage, authToken }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);

    // Create a new org
    const orgName = generateOrgName();
    await sidebarPage.createOrg(orgName);
    await authenticatedPage.waitForTimeout(1000);

    // Verify it's active
    let activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(orgName.substring(0, 20));

    // Reload the page
    await authenticatedPage.reload();
    await authenticatedPage.waitForLoadState('networkidle');

    // Active org should still be the same
    activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(orgName.substring(0, 20));

    // Track for cleanup
    const userOrgs = await apiClient.getUserOrgs(authToken);
    const createdOrg = userOrgs.find(o => o.name === orgName);
    if (createdOrg) {
      createdOrgIds.push(createdOrg.id);
    }
  });

  test('should persist active org after logout and login', async ({ page, authToken }) => {
    const sidebarPage = new SidebarPage(page);
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    // Login first
    await loginPage.goto();
    const testEmail = process.env.TEST_USER_EMAIL!;
    const testPassword = process.env.TEST_USER_PASSWORD!;
    await loginPage.login(testEmail, testPassword);
    await page.waitForURL(/^(?!.*\/login).*$/);

    // Create a new org
    const orgName = generateOrgName();
    await sidebarPage.createOrg(orgName);
    await page.waitForTimeout(1000);

    // Verify it's active
    let activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(orgName.substring(0, 20));

    // Logout
    await sidebarPage.logout();
    await page.waitForURL(/\/login/);

    // Login again
    await loginPage.login(testEmail, testPassword);
    await page.waitForURL(/^(?!.*\/login).*$/);
    await page.waitForLoadState('networkidle');

    // Active org should still be the same
    activeOrg = await sidebarPage.getActiveOrgName();
    expect(activeOrg).toContain(orgName.substring(0, 20));

    // Track for cleanup
    const userOrgs = await apiClient.getUserOrgs(authToken);
    const createdOrg = userOrgs.find(o => o.name === orgName);
    if (createdOrg) {
      createdOrgIds.push(createdOrg.id);
    }
  });
});
