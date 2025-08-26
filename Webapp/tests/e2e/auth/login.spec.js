/**
 * Authentication Tests - Login Flow
 */

const { test, expect } = require('@playwright/test');
const { ApiHelpers } = require('../../utils/api-helpers');
const { LoginPage, DashboardPage } = require('../../utils/page-objects');

test.describe('User Authentication', () => {
  let apiHelper;
  let testUser;

  test.beforeEach(async () => {
    apiHelper = new ApiHelpers();
  });

  test.afterEach(async () => {
    await apiHelper.cleanup();
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Setup test user via API
    const userData = await apiHelper.registerUser();
    testUser = userData.user;

    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    // Navigate to login page
    await loginPage.goto();
    await loginPage.expectLoginForm();

    // Perform login
    await loginPage.login(testUser.email, testUser.password);

    // Verify successful login
    await dashboardPage.expectDashboard();
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.expectLoginForm();

    // Try login with invalid credentials
    await loginPage.login('invalid@email.com', 'wrongpassword');

    // Verify error message
    await loginPage.expectError('Invalid credentials');
    await expect(page).toHaveURL(/.*login/); // Should stay on login page
  });

  test('should show error for empty fields', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await loginPage.goto();
    await loginPage.expectLoginForm();

    // Try login with empty fields
    await loginPage.loginButton.click();

    // Verify validation errors
    await expect(page.locator('input[name="email"]:invalid')).toBeVisible();
    await expect(page.locator('input[name="password"]:invalid')).toBeVisible();
  });

  test('should redirect to dashboard if already logged in', async ({ page }) => {
    // Setup test user and login via API
    const userData = await apiHelper.registerUser();
    await apiHelper.loginUser(userData.user.email, userData.user.password);
    
    // Set auth token in browser storage
    await page.goto('/');
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
    }, apiHelper.token);

    // Try to access login page
    await page.goto('/login');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('should logout successfully', async ({ page }) => {
    // Setup and login
    const userData = await apiHelper.registerUser();
    testUser = userData.user;

    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await dashboardPage.expectDashboard();

    // Perform logout
    await dashboardPage.logout();

    // Verify logout
    await expect(page).toHaveURL(/.*login/);
    
    // Try to access protected page
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/.*login/); // Should redirect to login
  });

  test('should handle token expiration', async ({ page }) => {
    // Setup user and expired token
    const userData = await apiHelper.registerUser();
    
    await page.goto('/');
    // Set expired token
    await page.evaluate(() => {
      localStorage.setItem('auth_token', 'expired.jwt.token');
    });

    // Try to access protected page
    await page.goto('/dashboard');

    // Should redirect to login due to expired token
    await expect(page).toHaveURL(/.*login/);
  });

  test('should remember login state across browser refresh', async ({ page }) => {
    // Setup and login
    const userData = await apiHelper.registerUser();
    testUser = userData.user;

    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await dashboardPage.expectDashboard();

    // Refresh the page
    await page.reload();

    // Should still be logged in
    await dashboardPage.expectDashboard();
    await expect(page).toHaveURL(/.*dashboard/);
  });
});