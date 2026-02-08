import { test, expect } from '../fixtures/auth.fixture';
import { LoginPage } from '../pages/login.page';
import { SidebarPage } from '../pages/sidebar.page';
import { DashboardPage } from '../pages/dashboard.page';

test.describe('Authentication', () => {
  test('should login with valid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const sidebarPage = new SidebarPage(page);
    const dashboardPage = new DashboardPage(page);

    // Navigate to login
    await loginPage.goto();

    // Login with test user
    const testEmail = process.env.TEST_USER_EMAIL!;
    const testPassword = process.env.TEST_USER_PASSWORD!;
    await loginPage.login(testEmail, testPassword);

    // Should redirect away from login to dashboard
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 });
    expect(await dashboardPage.isLoaded()).toBe(true);

    // User email should be visible in sidebar
    const displayedEmail = await sidebarPage.getUserEmail();
    expect(displayedEmail).toContain(testEmail);
  });

  test('should show error with invalid password', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();

    const testEmail = process.env.TEST_USER_EMAIL!;
    await loginPage.login(testEmail, 'wrong-password-123');

    // Should show error and stay on login page
    const errorText = await loginPage.getErrorText();
    expect(errorText).toBeTruthy();
    expect(await loginPage.isOnLoginPage()).toBe(true);
  });

  test('should show error with non-existent email', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();

    await loginPage.login('nonexistent@test.com', 'password123');

    // Should show error and stay on login page
    const errorText = await loginPage.getErrorText();
    expect(errorText).toBeTruthy();
    expect(await loginPage.isOnLoginPage()).toBe(true);
  });

  test('should redirect to protected route after login', async ({ page }) => {
    const loginPage = new LoginPage(page);

    // Try to access protected route while logged out
    await page.goto('/agents');

    // Should redirect to login with redirect parameter
    await expect(page).toHaveURL(/\/login.*redirect/);

    // Login
    const testEmail = process.env.TEST_USER_EMAIL!;
    const testPassword = process.env.TEST_USER_PASSWORD!;
    await loginPage.login(testEmail, testPassword);

    // Should redirect back to /agents
    await expect(page).toHaveURL(/\/agents/);
  });

  test('should protect dashboard route when not authenticated', async ({ page }) => {
    // Visit dashboard without authentication
    await page.goto('/');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should logout and clear session', async ({ authenticatedPage }) => {
    const sidebarPage = new SidebarPage(authenticatedPage);
    const dashboardPage = new DashboardPage(authenticatedPage);

    // Start on dashboard
    await dashboardPage.goto();
    expect(await dashboardPage.isLoaded()).toBe(true);

    // Logout
    await sidebarPage.logout();

    // Should redirect to login
    await expect(authenticatedPage).toHaveURL(/\/login/);

    // Try to access dashboard again
    await authenticatedPage.goto('/');

    // Should redirect to login (session cleared)
    await expect(authenticatedPage).toHaveURL(/\/login/);
  });
});
