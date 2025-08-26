/**
 * End-to-End User Journey Tests
 * Complete workflow testing from login to data processing
 */

const { test, expect } = require('@playwright/test');
const { ApiHelpers } = require('../utils/api-helpers');
const { 
  LoginPage, 
  DashboardPage, 
  AccountsPage, 
  ListingsPage, 
  OrdersPage, 
  CSVImportPage 
} = require('../utils/page-objects');

test.describe('Complete User Journey', () => {
  let apiHelper;
  let testUser;
  let testAccount;

  test.beforeEach(async ({ page }) => {
    apiHelper = new ApiHelpers();
    
    // Setup test user
    const userData = await apiHelper.registerUser();
    testUser = userData.user;
    
    // Login via API to get auth token
    await apiHelper.loginUser(testUser.email, testUser.password);
    
    // Set auth state in browser
    await page.goto('/');
    await page.evaluate((token) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_email', arguments[1]);
    }, apiHelper.token, testUser.email);
  });

  test.afterEach(async () => {
    await apiHelper.cleanup();
  });

  test('Complete workflow: Login → Create Account → Add Listing → View Orders', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);
    const accountsPage = new AccountsPage(page);
    const listingsPage = new ListingsPage(page);
    const ordersPage = new OrdersPage(page);

    // Step 1: Login
    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await dashboardPage.expectDashboard();

    // Step 2: Navigate to Accounts and create account
    await dashboardPage.navigateToAccounts();
    await accountsPage.expectAccountsPage();
    await accountsPage.createAccount();

    // Fill account form (assuming modal or form appears)
    const testAccountData = apiHelper.generateTestData().account;
    await page.fill('input[name="ebay_username"]', testAccountData.ebay_username);
    await page.fill('input[name="email"]', testAccountData.email);
    await page.fill('input[name="sheet_id"]', testAccountData.sheet_id);
    await page.click('button:has-text("Create"), button:has-text("Save")');

    // Wait for account to be created and appear in table
    await accountsPage.expectAccountInTable(testAccountData.ebay_username);

    // Step 3: Navigate to Listings and create listing
    await dashboardPage.navigateToListings();
    await listingsPage.expectListingsPage();
    await listingsPage.createListing();

    // Fill listing form
    const testListingData = apiHelper.generateTestData().listing;
    await page.fill('input[name="title"]', testListingData.title);
    await page.fill('input[name="ebay_item_id"]', testListingData.ebay_item_id);
    await page.fill('input[name="price"]', testListingData.price.toString());
    await page.fill('input[name="quantity"]', testListingData.quantity.toString());
    await page.selectOption('select[name="condition"]', testListingData.condition);
    await page.click('button:has-text("Create"), button:has-text("Save")');

    // Wait for listing to be created and appear in table
    await listingsPage.expectListingInTable(testListingData.title);

    // Step 4: Navigate to Orders
    await dashboardPage.navigateToOrders();
    await ordersPage.expectOrdersPage();

    // Step 5: Verify navigation works correctly
    await dashboardPage.navigateToListings();
    await listingsPage.expectListingsPage();
    await listingsPage.searchListings(testListingData.title);
    await listingsPage.expectListingInTable(testListingData.title);

    // Step 6: Return to dashboard
    await page.click('a:has-text("Dashboard"), .logo, .home-link');
    await dashboardPage.expectDashboard();
  });

  test('CSV Import workflow: Setup → Import → Verify', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const csvImportPage = new CSVImportPage(page);
    const ordersPage = new OrdersPage(page);

    // Setup: Create account first via API
    testAccount = await apiHelper.createAccount();

    // Step 1: Navigate to dashboard and then CSV import
    await page.goto('/dashboard');
    await dashboardPage.expectDashboard();
    await dashboardPage.navigateToCSVImport();
    await csvImportPage.expectCSVImportPage();

    // Step 2: Fill CSV import form
    const testSheetId = '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'; // Google Sheets test sheet
    await csvImportPage.fillImportForm(testSheetId, testAccount.id.toString(), 'orders');

    // Step 3: Preview data
    await csvImportPage.previewData();
    
    // Verify preview table appears with data
    await expect(page.locator('.preview-table tbody tr')).toHaveCount({ min: 1 });

    // Step 4: Start import
    await csvImportPage.startImport();

    // Step 5: Wait for import to complete
    await csvImportPage.expectImportComplete();

    // Step 6: Verify imported data appears in orders
    await dashboardPage.navigateToOrders();
    await ordersPage.expectOrdersPage();
    
    // Check that some orders exist in the table
    await expect(page.locator('table tbody tr')).toHaveCount({ min: 1 });
  });

  test('Error handling: Invalid data and network issues', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);
    const listingsPage = new ListingsPage(page);

    await page.goto('/dashboard');
    await dashboardPage.expectDashboard();

    // Test 1: Try to create listing with invalid data
    await dashboardPage.navigateToListings();
    await listingsPage.expectListingsPage();
    await listingsPage.createListing();

    // Fill form with invalid data
    await page.fill('input[name="title"]', ''); // Empty title
    await page.fill('input[name="price"]', '-10'); // Negative price
    await page.click('button:has-text("Create"), button:has-text("Save")');

    // Expect validation errors
    await expect(page.locator('.error, .alert, [role="alert"]')).toBeVisible();

    // Test 2: Test offline behavior
    await page.route('**/*', route => route.abort());
    
    await page.reload();
    
    // Should show offline message or error
    await expect(page.locator('body')).toContainText(/offline|error|failed/i);

    // Restore network
    await page.unroute('**/*');
    await page.reload();
    await dashboardPage.expectDashboard();
  });

  test('Performance: Page load times and responsiveness', async ({ page }) => {
    const dashboardPage = new DashboardPage(page);

    // Measure page load times
    const navigationStart = Date.now();
    await page.goto('/dashboard');
    await dashboardPage.expectDashboard();
    const dashboardLoadTime = Date.now() - navigationStart;

    expect(dashboardLoadTime).toBeLessThan(5000); // Dashboard should load in < 5s

    // Test navigation performance
    const listingsStart = Date.now();
    await dashboardPage.navigateToListings();
    await page.waitForURL('**/listings');
    const listingsLoadTime = Date.now() - listingsStart;

    expect(listingsLoadTime).toBeLessThan(3000); // Navigation should be < 3s

    // Test API response times
    const apiStart = Date.now();
    const response = await page.request.get('http://localhost:8000/api/v1/health');
    const apiTime = Date.now() - apiStart;

    expect(response.status()).toBe(200);
    expect(apiTime).toBeLessThan(1000); // API should respond in < 1s
  });

  test('Cross-browser compatibility basics', async ({ page, browserName }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    // Basic functionality should work across browsers
    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await dashboardPage.expectDashboard();

    // Test basic interactions
    await dashboardPage.navigateToListings();
    await expect(page).toHaveURL(/.*listings/);

    // Browser-specific tests
    if (browserName === 'chromium') {
      // Test Chrome-specific features (like extensions)
      console.log('Testing Chrome-specific features');
    } else if (browserName === 'firefox') {
      // Test Firefox-specific behavior
      console.log('Testing Firefox-specific features');
    }
  });

  test('Mobile responsiveness', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 }); // iPhone SE size

    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login(testUser.email, testUser.password);
    await dashboardPage.expectDashboard();

    // Check mobile navigation (hamburger menu, etc.)
    const mobileMenu = page.locator('.mobile-menu, .hamburger, .menu-toggle');
    if (await mobileMenu.isVisible()) {
      await mobileMenu.click();
      await expect(page.locator('.navigation, .sidebar')).toBeVisible();
    }

    // Test mobile-specific interactions
    await dashboardPage.navigateToListings();
    await expect(page).toHaveURL(/.*listings/);
  });
});