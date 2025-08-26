// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for API-only Testing
 * Runs without starting web servers (assumes they're already running)
 */
module.exports = defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  
  reporter: [
    ['list'],
    ['json', { outputFile: 'test-results/api-results.json' }]
  ],
  
  use: {
    // For API testing
    baseURL: 'http://localhost:8000',
    extraHTTPHeaders: {
      'Accept': 'application/json',
    },
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'api-tests',
      use: {
        baseURL: 'http://localhost:8000',
      },
      testMatch: ['**/basic-test.spec.js', '**/api/**/*.spec.js']
    }
  ],

  timeout: 30 * 1000,
  expect: {
    timeout: 5 * 1000
  }
});