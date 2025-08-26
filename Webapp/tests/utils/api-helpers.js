/**
 * API Helper functions for testing
 * Provides utilities for backend API interaction during tests
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiHelpers {
  constructor() {
    this.token = null;
  }

  /**
   * Register a test user
   */
  async registerUser(userData = {}) {
    const defaultUser = {
      username: `testuser_${Date.now()}`,
      email: `test_${Date.now()}@example.com`,
      password: 'testpass123'
    };

    const user = { ...defaultUser, ...userData };

    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Registration failed: ${error.detail || response.statusText}`);
    }

    return { user, response: await response.json() };
  }

  /**
   * Login and get auth token
   */
  async loginUser(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login-json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Login failed: ${error.detail || response.statusText}`);
    }

    const data = await response.json();
    this.token = data.access_token;
    return data;
  }

  /**
   * Get auth headers with token
   */
  getAuthHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.token}`
    };
  }

  /**
   * Create test account
   */
  async createAccount(accountData = {}) {
    const defaultAccount = {
      ebay_username: `testaccount_${Date.now()}`,
      email: `account_${Date.now()}@example.com`,
      sheet_id: `test_sheet_${Date.now()}`
    };

    const account = { ...defaultAccount, ...accountData };

    const response = await fetch(`${API_BASE_URL}/accounts/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(account)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Account creation failed: ${error.detail || response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Create test listing
   */
  async createListing(listingData = {}) {
    const defaultListing = {
      title: `Test Listing ${Date.now()}`,
      ebay_item_id: `item_${Date.now()}`,
      price: 29.99,
      quantity: 10,
      condition: 'New',
      category: 'Electronics'
    };

    const listing = { ...defaultListing, ...listingData };

    const response = await fetch(`${API_BASE_URL}/listings/`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(listing)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(`Listing creation failed: ${error.detail || response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get user profile
   */
  async getCurrentUser() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error(`Get user failed: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Cleanup test data (delete created resources)
   */
  async cleanup() {
    // This would delete any test data created during tests
    // Implementation depends on backend cleanup endpoints
    console.log('Cleaning up test data...');
    this.token = null;
  }

  /**
   * Wait for condition with timeout
   */
  async waitForCondition(conditionFn, timeout = 10000, interval = 500) {
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      if (await conditionFn()) {
        return true;
      }
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    
    throw new Error(`Condition not met within ${timeout}ms`);
  }

  /**
   * Generate test data
   */
  generateTestData() {
    const timestamp = Date.now();
    return {
      user: {
        username: `testuser_${timestamp}`,
        email: `test_${timestamp}@example.com`,
        password: 'testpass123'
      },
      account: {
        ebay_username: `testaccount_${timestamp}`,
        email: `account_${timestamp}@example.com`,
        sheet_id: `test_sheet_${timestamp}`
      },
      listing: {
        title: `Test Product ${timestamp}`,
        ebay_item_id: `${timestamp}`,
        price: Math.floor(Math.random() * 100) + 10,
        quantity: Math.floor(Math.random() * 50) + 1,
        condition: 'New'
      }
    };
  }
}

module.exports = { ApiHelpers };