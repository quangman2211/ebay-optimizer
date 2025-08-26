/**
 * API Tests - Authentication Endpoints
 */

const { test, expect } = require('@playwright/test');
const { ApiHelpers } = require('../../utils/api-helpers');

test.describe('Authentication API', () => {
  let apiHelper;
  const API_BASE_URL = 'http://localhost:8000/api/v1';

  test.beforeEach(async () => {
    apiHelper = new ApiHelpers();
  });

  test.afterEach(async () => {
    await apiHelper.cleanup();
  });

  test('POST /auth/register - should create new user', async ({ request }) => {
    const testData = apiHelper.generateTestData();
    const userData = testData.user;

    const response = await request.post(`${API_BASE_URL}/auth/register`, {
      data: userData
    });

    expect(response.status()).toBe(200);
    
    const responseData = await response.json();
    expect(responseData).toHaveProperty('email', userData.email);
    expect(responseData).toHaveProperty('username', userData.username);
    expect(responseData).toHaveProperty('id');
    expect(responseData).not.toHaveProperty('password');
    expect(responseData).not.toHaveProperty('hashed_password');
  });

  test('POST /auth/register - should reject duplicate email', async ({ request }) => {
    const testData = apiHelper.generateTestData();
    const userData = testData.user;

    // Register user first time
    await request.post(`${API_BASE_URL}/auth/register`, {
      data: userData
    });

    // Try to register same email again
    const response = await request.post(`${API_BASE_URL}/auth/register`, {
      data: userData
    });

    expect(response.status()).toBe(400); // Validation error for duplicate email
    
    const responseData = await response.json();
    expect(responseData.detail).toBeDefined();
  });

  test('POST /auth/register - should validate required fields', async ({ request }) => {
    const invalidData = { email: 'invalid-email' }; // Missing required fields

    const response = await request.post(`${API_BASE_URL}/auth/register`, {
      data: invalidData
    });

    expect(response.status()).toBe(422); // Validation error
    
    const responseData = await response.json();
    expect(responseData).toHaveProperty('detail');
  });

  test('POST /auth/login-json - should login with valid credentials', async ({ request }) => {
    // Create test user first
    const userData = await apiHelper.registerUser();

    const loginData = {
      email: userData.user.email,
      password: userData.user.password
    };

    const response = await request.post(`${API_BASE_URL}/auth/login-json`, {
      data: loginData
    });

    expect(response.status()).toBe(200);
    
    const responseData = await response.json();
    expect(responseData).toHaveProperty('access_token');
    expect(responseData).toHaveProperty('token_type', 'bearer');
    expect(typeof responseData.access_token).toBe('string');
    expect(responseData.access_token.length).toBeGreaterThan(0);
  });

  test('POST /auth/login-json - should reject invalid credentials', async ({ request }) => {
    const loginData = {
      email: 'nonexistent@example.com',
      password: 'wrongpassword'
    };

    const response = await request.post(`${API_BASE_URL}/auth/login-json`, {
      data: loginData
    });

    expect(response.status()).toBe(401);
    
    const responseData = await response.json();
    expect(responseData).toHaveProperty('detail');
  });

  test('POST /auth/login-json - should validate email format', async ({ request }) => {
    const loginData = {
      email: 'invalid-email-format',
      password: 'somepassword'
    };

    const response = await request.post(`${API_BASE_URL}/auth/login-json`, {
      data: loginData
    });

    expect(response.status()).toBe(422); // Validation error
    
    const responseData = await response.json();
    expect(responseData).toHaveProperty('detail');
  });

  test('GET /auth/me - should return current user with valid token', async ({ request }) => {
    // Create and login user
    const userData = await apiHelper.registerUser();
    await apiHelper.loginUser(userData.user.email, userData.user.password);

    const response = await request.get(`${API_BASE_URL}/auth/me`, {
      headers: apiHelper.getAuthHeaders()
    });

    expect(response.status()).toBe(200);
    
    const responseData = await response.json();
    expect(responseData).toHaveProperty('email', userData.user.email);
    expect(responseData).toHaveProperty('username', userData.user.username);
    expect(responseData).toHaveProperty('id');
    expect(responseData).not.toHaveProperty('password');
    expect(responseData).not.toHaveProperty('hashed_password');
  });

  test('GET /auth/me - should reject invalid token', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/auth/me`, {
      headers: {
        'Authorization': 'Bearer invalid.jwt.token'
      }
    });

    expect(response.status()).toBe(401);
  });

  test('GET /auth/me - should reject missing token', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/auth/me`);

    expect(response.status()).toBe(401);
  });

  test('should handle concurrent registration requests', async ({ request }) => {
    const testData = apiHelper.generateTestData();
    
    // Create multiple users concurrently
    const registrationPromises = [];
    for (let i = 0; i < 5; i++) {
      const userData = {
        ...testData.user,
        email: `concurrent_${i}_${Date.now()}@example.com`,
        username: `concurrent_${i}_${Date.now()}`
      };
      
      registrationPromises.push(
        request.post(`${API_BASE_URL}/auth/register`, { data: userData })
      );
    }

    const responses = await Promise.all(registrationPromises);
    
    // All should succeed
    responses.forEach(response => {
      expect(response.status()).toBe(200);
    });
  });

  test('should handle API rate limiting gracefully', async ({ request }) => {
    // This test would check if the API handles rate limiting properly
    // Making many requests in quick succession
    const requests = [];
    for (let i = 0; i < 20; i++) {
      requests.push(
        request.get(`${API_BASE_URL}/health`)
      );
    }

    const responses = await Promise.all(requests);
    
    // Should either succeed or return 429 (Too Many Requests)
    responses.forEach(response => {
      expect([200, 429]).toContain(response.status());
    });
  });
});