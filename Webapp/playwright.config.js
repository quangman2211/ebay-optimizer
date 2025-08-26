// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright Configuration for eBay Optimizer E2E Testing
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['list']
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:3000',
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    /* Take screenshot on failure */
    screenshot: 'only-on-failure',
    /* Record video on failure */
    video: 'retain-on-failure',
    /* Default timeout for expect assertions */
    expect: {
      timeout: 10000
    },
    /* Action timeout */
    actionTimeout: 30000,
    /* Navigation timeout */
    navigationTimeout: 30000
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Chrome extension testing capabilities
        launchOptions: {
          args: [
            '--disable-extensions-except=/home/quangman/EBAY/ebay-optimizer/ChromeExtension/v2',
            '--load-extension=/home/quangman/EBAY/ebay-optimizer/ChromeExtension/v2'
          ]
        }
      },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* API Testing Project */
    {
      name: 'api',
      use: {
        baseURL: 'http://localhost:8000',
      },
      testMatch: '**/api/**/*.spec.js'
    }
  ],

  /* Run your local dev server before starting the tests */
  webServer: [
    {
      command: 'cd frontend && npm start',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 120 * 1000, // 2 minutes
    },
    {
      command: 'cd backend && python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      url: 'http://localhost:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 60 * 1000, // 1 minute
    }
  ],

  /* Global timeout for the whole test run */
  globalTimeout: 60 * 60 * 1000, // 1 hour

  /* Output directory for test results */
  outputDir: 'test-results',

  /* Test timeout */
  timeout: 30 * 1000, // 30 seconds per test

  /* Expect timeout */
  expect: {
    timeout: 10 * 1000 // 10 seconds for assertions
  }
});