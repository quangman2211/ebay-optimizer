/**
 * Basic smoke test to verify Playwright framework works
 */

const { test, expect } = require('@playwright/test');

test.describe('Framework Verification', () => {
  test('should verify API endpoint is accessible', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');
    
    expect(response.status()).toBe(200);
    
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
    expect(data).toHaveProperty('service');
  });

  test('should verify backend auth endpoints exist', async ({ request }) => {
    // Test that endpoints return proper error codes when no auth
    const endpoints = [
      '/api/v1/auth/me',
      '/api/v1/accounts/',
      '/api/v1/listings/'
    ];

    for (const endpoint of endpoints) {
      const response = await request.get(`http://localhost:8000${endpoint}`);
      // Should return 401 (unauthorized) not 404 (not found)
      expect([401, 307]).toContain(response.status()); // 307 is redirect
    }
  });

  test('should be able to register and login via API', async ({ request }) => {
    const timestamp = Date.now();
    const testUser = {
      username: `test_${timestamp}`,
      email: `test_${timestamp}@example.com`,
      password: 'testpass123'
    };

    // Register user
    const registerResponse = await request.post('http://localhost:8000/api/v1/auth/register', {
      data: testUser
    });

    expect(registerResponse.status()).toBe(200);
    
    const userData = await registerResponse.json();
    expect(userData).toHaveProperty('email', testUser.email);

    // Login user
    const loginResponse = await request.post('http://localhost:8000/api/v1/auth/login-json', {
      data: {
        email: testUser.email,
        password: testUser.password
      }
    });

    expect(loginResponse.status()).toBe(200);
    
    const loginData = await loginResponse.json();
    expect(loginData).toHaveProperty('access_token');
    expect(loginData).toHaveProperty('token_type', 'bearer');
  });
});