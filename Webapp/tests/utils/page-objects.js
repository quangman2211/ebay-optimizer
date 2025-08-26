/**
 * Page Object Models for eBay Optimizer
 * Provides abstraction layer for UI interactions
 */

class LoginPage {
  constructor(page) {
    this.page = page;
    this.emailInput = page.locator('input[name="email"], input[type="email"]');
    this.passwordInput = page.locator('input[name="password"], input[type="password"]');
    this.loginButton = page.locator('button[type="submit"], button:has-text("Login")');
    this.errorMessage = page.locator('.error, .alert-error, [role="alert"]');
  }

  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  async login(email, password) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
    
    // Wait for navigation after login
    await this.page.waitForURL('**/dashboard', { timeout: 10000 });
  }

  async expectLoginForm() {
    await this.emailInput.waitFor({ state: 'visible' });
    await this.passwordInput.waitFor({ state: 'visible' });
    await this.loginButton.waitFor({ state: 'visible' });
  }

  async expectError(errorText) {
    await this.errorMessage.waitFor({ state: 'visible' });
    if (errorText) {
      await expect(this.errorMessage).toContainText(errorText);
    }
  }
}

class DashboardPage {
  constructor(page) {
    this.page = page;
    this.navigationMenu = page.locator('nav, .sidebar, .navigation');
    this.userMenu = page.locator('.user-menu, .profile-menu');
    this.logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');
    this.welcomeMessage = page.locator('h1, .welcome, .dashboard-title');
  }

  async expectDashboard() {
    await this.page.waitForURL('**/dashboard', { timeout: 10000 });
    await this.navigationMenu.waitFor({ state: 'visible' });
  }

  async navigateToListings() {
    await this.page.click('a:has-text("Listings"), nav a[href*="listings"]');
    await this.page.waitForURL('**/listings');
  }

  async navigateToOrders() {
    await this.page.click('a:has-text("Orders"), nav a[href*="orders"]');
    await this.page.waitForURL('**/orders');
  }

  async navigateToAccounts() {
    await this.page.click('a:has-text("Accounts"), nav a[href*="accounts"]');
    await this.page.waitForURL('**/accounts');
  }

  async navigateToCSVImport() {
    await this.page.click('a:has-text("CSV Import"), nav a[href*="csv-import"]');
    await this.page.waitForURL('**/csv-import');
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
    await this.page.waitForURL('**/login');
  }
}

class ListingsPage {
  constructor(page) {
    this.page = page;
    this.createButton = page.locator('button:has-text("Create"), button:has-text("New Listing")');
    this.listingsTable = page.locator('table, .listings-grid, .data-grid');
    this.searchInput = page.locator('input[placeholder*="Search"], input[name="search"]');
    this.filterDropdown = page.locator('select[name="status"], .filter-dropdown');
    this.paginationNext = page.locator('button:has-text("Next"), .pagination-next');
    this.paginationPrev = page.locator('button:has-text("Previous"), .pagination-prev');
  }

  async expectListingsPage() {
    await this.page.waitForURL('**/listings');
    await this.listingsTable.waitFor({ state: 'visible' });
  }

  async createListing() {
    await this.createButton.click();
    await this.page.waitForURL('**/listings/create');
  }

  async searchListings(query) {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
    await this.page.waitForTimeout(1000); // Wait for search results
  }

  async filterByStatus(status) {
    await this.filterDropdown.selectOption(status);
    await this.page.waitForTimeout(1000); // Wait for filter results
  }

  async expectListingInTable(listingTitle) {
    const listingRow = this.page.locator(`tr:has-text("${listingTitle}")`);
    await listingRow.waitFor({ state: 'visible' });
  }
}

class OrdersPage {
  constructor(page) {
    this.page = page;
    this.ordersTable = page.locator('table, .orders-grid, .data-grid');
    this.statusFilter = page.locator('select[name="status"], .status-filter');
    this.dateFilter = page.locator('input[type="date"], .date-filter');
    this.exportButton = page.locator('button:has-text("Export")');
    this.refreshButton = page.locator('button:has-text("Refresh")');
  }

  async expectOrdersPage() {
    await this.page.waitForURL('**/orders');
    await this.ordersTable.waitFor({ state: 'visible' });
  }

  async filterByStatus(status) {
    await this.statusFilter.selectOption(status);
    await this.page.waitForTimeout(1000);
  }

  async expectOrderInTable(orderNumber) {
    const orderRow = this.page.locator(`tr:has-text("${orderNumber}")`);
    await orderRow.waitFor({ state: 'visible' });
  }

  async exportOrders() {
    await this.exportButton.click();
    // Wait for download or export modal
    await this.page.waitForTimeout(2000);
  }
}

class AccountsPage {
  constructor(page) {
    this.page = page;
    this.createButton = page.locator('button:has-text("Create"), button:has-text("Add Account")');
    this.accountsTable = page.locator('table, .accounts-grid');
    this.syncButton = page.locator('button:has-text("Sync")');
  }

  async expectAccountsPage() {
    await this.page.waitForURL('**/accounts');
    await this.accountsTable.waitFor({ state: 'visible' });
  }

  async createAccount() {
    await this.createButton.click();
    // Wait for create account modal or page
    await this.page.waitForTimeout(1000);
  }

  async expectAccountInTable(accountName) {
    const accountRow = this.page.locator(`tr:has-text("${accountName}")`);
    await accountRow.waitFor({ state: 'visible' });
  }
}

class CSVImportPage {
  constructor(page) {
    this.page = page;
    this.sheetIdInput = page.locator('input[name="sheetId"], input[placeholder*="Sheet ID"]');
    this.accountSelect = page.locator('select[name="account"], .account-select');
    this.dataTypeSelect = page.locator('select[name="dataType"], .data-type-select');
    this.previewButton = page.locator('button:has-text("Preview")');
    this.importButton = page.locator('button:has-text("Import"), button:has-text("Start Import")');
    this.statusIndicator = page.locator('.import-status, .progress-indicator');
    this.resultsTable = page.locator('.preview-table, .import-results');
  }

  async expectCSVImportPage() {
    await this.page.waitForURL('**/csv-import');
    await this.sheetIdInput.waitFor({ state: 'visible' });
  }

  async fillImportForm(sheetId, accountId, dataType) {
    await this.sheetIdInput.fill(sheetId);
    await this.accountSelect.selectOption(accountId);
    await this.dataTypeSelect.selectOption(dataType);
  }

  async previewData() {
    await this.previewButton.click();
    await this.resultsTable.waitFor({ state: 'visible', timeout: 15000 });
  }

  async startImport() {
    await this.importButton.click();
    await this.statusIndicator.waitFor({ state: 'visible' });
  }

  async expectImportComplete(timeout = 30000) {
    await this.page.waitForSelector('.import-success, .import-completed', { timeout });
  }
}

module.exports = {
  LoginPage,
  DashboardPage, 
  ListingsPage,
  OrdersPage,
  AccountsPage,
  CSVImportPage
};