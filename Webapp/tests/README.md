# 🧪 eBay Optimizer Testing Suite

Comprehensive Playwright-based testing framework for eBay Optimizer application.

## 📋 **Test Overview**

### Test Types
- **E2E UI Tests**: User interface and interaction testing
- **API Integration Tests**: Backend endpoint testing
- **User Journey Tests**: Complete workflow testing
- **Cross-browser Tests**: Chrome, Firefox, Safari compatibility
- **Mobile Responsive Tests**: Mobile device testing
- **Performance Tests**: Load time and responsiveness

### Test Structure
```
tests/
├── e2e/
│   ├── auth/           # Authentication tests
│   ├── listings/       # Listings management tests
│   ├── orders/         # Orders processing tests
│   ├── accounts/       # Account management tests
│   ├── csv-import/     # CSV import workflow tests
│   └── api/           # API endpoint tests
├── fixtures/          # Test data and fixtures
├── utils/            # Helper functions and page objects
└── config/           # Test configuration
```

## 🚀 **Getting Started**

### Prerequisites
```bash
# Install dependencies
npm install

# Install Playwright browsers
npm run playwright:install
```

### Required Services
Before running tests, ensure these services are running:
- **Frontend**: `http://localhost:3000` (React app)
- **Backend**: `http://localhost:8000` (FastAPI server)

Start services:
```bash
# Terminal 1: Start backend
cd ../backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start frontend  
cd Webapp/frontend
npm start
```

## 🎯 **Running Tests**

### Basic Commands
```bash
# Run all tests
npm run test:e2e

# Run with UI mode (visual test runner)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Debug mode (step through tests)
npm run test:e2e:debug

# Show test report
npm run test:e2e:report
```

### Specific Test Suites
```bash
# Authentication tests
npm run test:auth

# API tests
npm run test:api

# User journey tests
npm run test:journey
```

### Browser-specific Tests
```bash
# Chrome only
npm run test:chrome

# Firefox only
npm run test:firefox

# Safari only
npm run test:webkit

# Mobile Chrome
npm run test:mobile
```

### Advanced Options
```bash
# Run specific test file
npx playwright test tests/e2e/auth/login.spec.js

# Run tests matching pattern
npx playwright test --grep "should login"

# Run failed tests only
npx playwright test --last-failed

# Parallel execution
npx playwright test --workers=4
```

## 📁 **Test Files**

### Authentication Tests (`tests/e2e/auth/`)
- `login.spec.js` - Login/logout functionality
- `registration.spec.js` - User registration
- `token-management.spec.js` - JWT token handling

### API Tests (`tests/e2e/api/`)
- `auth-api.spec.js` - Authentication endpoints
- `listings-api.spec.js` - Listings CRUD operations
- `accounts-api.spec.js` - Account management endpoints

### User Journey Tests
- `user-journey.spec.js` - Complete workflow testing
- `csv-import-journey.spec.js` - CSV import process
- `performance-tests.spec.js` - Performance benchmarks

## 🛠️ **Test Utilities**

### Page Objects (`tests/utils/page-objects.js`)
Abstraction layer for UI interactions:
```javascript
const { LoginPage } = require('../utils/page-objects');

const loginPage = new LoginPage(page);
await loginPage.goto();
await loginPage.login('user@example.com', 'password');
```

### API Helpers (`tests/utils/api-helpers.js`)
Backend API interaction utilities:
```javascript
const { ApiHelpers } = require('../utils/api-helpers');

const apiHelper = new ApiHelpers();
await apiHelper.registerUser();
await apiHelper.loginUser('user@example.com', 'password');
```

### Test Data (`test-data/`)
- `sample-orders.csv` - Test order data
- `sample-listings.csv` - Test listing data
- `test-accounts.json` - Test account configurations

## 📊 **Test Reports**

### HTML Report
After running tests, view results:
```bash
npm run test:e2e:report
```

### Report Locations
- **HTML Report**: `test-results/html-report/index.html`
- **JSON Results**: `test-results/results.json`
- **JUnit XML**: `test-results/results.xml`
- **Screenshots**: `test-results/screenshots/`
- **Videos**: `test-results/videos/`

## 🐛 **Debugging**

### Debug Mode
```bash
# Run in debug mode
npm run test:e2e:debug

# Debug specific test
npx playwright test --debug tests/e2e/auth/login.spec.js
```

### Screenshots & Videos
- Screenshots taken automatically on test failure
- Videos recorded for failed tests
- Traces captured for analysis

### Common Issues

#### Test Timeout
```bash
# Increase timeout
npx playwright test --timeout=60000
```

#### Browser Not Found
```bash
# Reinstall browsers
npm run playwright:install
```

#### Services Not Running
```bash
# Check if services are up
curl http://localhost:3000  # Frontend
curl http://localhost:8000/health  # Backend
```

## ⚡ **Performance Benchmarks**

### Expected Performance
- **Page Load Time**: < 3 seconds
- **API Response**: < 500ms
- **Navigation**: < 2 seconds
- **Form Submission**: < 1 second

### Performance Tests
```bash
# Run performance tests
npx playwright test --grep "Performance"
```

## 🔧 **Configuration**

### Playwright Config (`playwright.config.js`)
- Browser settings
- Test timeouts
- Retry configuration
- Report settings
- Web server setup

### Environment Variables
```bash
# Test environment
PLAYWRIGHT_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000

# Chrome extension testing
EXTENSION_PATH=/path/to/extension
```

## 🔄 **CI/CD Integration**

### GitHub Actions Example
```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run tests
        run: npm run test:e2e
```

## 📝 **Writing New Tests**

### Test Template
```javascript
const { test, expect } = require('@playwright/test');

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
  });

  test('should do something', async ({ page }) => {
    // Test implementation
    await page.goto('/page');
    await expect(page).toHaveTitle('Expected Title');
  });
});
```

### Best Practices
1. **Use Page Objects** for UI interactions
2. **Use API Helpers** for backend operations
3. **Clean up test data** after each test
4. **Use meaningful test names** and descriptions
5. **Add assertions** to verify expected behavior
6. **Handle async operations** properly
7. **Use test hooks** for setup/teardown

## 📚 **Resources**

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Test Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Guide](https://playwright.dev/docs/debug)
- [API Testing](https://playwright.dev/docs/api-testing)

---

## 🏃‍♂️ **Quick Start Guide**

1. **Install & Setup**:
   ```bash
   npm install
   npm run playwright:install
   ```

2. **Start Services**:
   ```bash
   # Backend: cd ../backend && python3 -m uvicorn app.main:app --reload
   # Frontend: npm start
   ```

3. **Run Tests**:
   ```bash
   npm run test:e2e
   ```

4. **View Results**:
   ```bash
   npm run test:e2e:report
   ```

Happy Testing! 🎉