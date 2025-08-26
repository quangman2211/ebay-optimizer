# 🧪 eBay Optimizer - Playwright Testing Framework

## 📍 **Vị trí mới**
Playwright testing framework đã được di chuyển từ `frontend/` lên thư mục `Webapp/` để quản lý testing cho toàn bộ ứng dụng.

## 🚀 **Cách sử dụng**

### Cài đặt dependencies:
```bash
cd /home/quangman/EBAY/ebay-optimizer/Webapp
npm install
npm run playwright:install
```

### Chạy tests:
```bash
# API tests only (không cần start frontend)
npm run test:api-only

# Full E2E tests (cần cả frontend + backend)
npm run test:e2e

# UI mode để debug
npm run test:e2e:ui

# Xem kết quả test
npm run test:e2e:report
```

### Các lệnh test cụ thể:
```bash
npm run test:auth        # Authentication tests
npm run test:api         # API integration tests  
npm run test:journey     # User journey tests
npm run test:chrome      # Chrome browser only
npm run test:firefox     # Firefox browser only
npm run test:mobile      # Mobile testing
```

## 📁 **Cấu trúc thư mục**
```
/home/quangman/EBAY/ebay-optimizer/Webapp/
├── playwright.config.js           # Config chính cho E2E tests
├── playwright-api.config.js       # Config cho API-only tests
├── package.json                   # Dependencies và scripts
├── tests/                         # Toàn bộ test suites
│   ├── e2e/
│   │   ├── auth/                  # Authentication tests
│   │   ├── api/                   # API endpoint tests
│   │   ├── accounts/              # Account management
│   │   └── user-journey.spec.js   # Complete workflows
│   ├── utils/                     # Page objects & helpers
│   └── fixtures/                  # Test data
├── test-results/                  # Test output
├── test-data/                     # Sample data files
├── frontend/                      # React app
└── backend/                       # FastAPI server
```

## ✅ **Trạng thái hiện tại**
- ✅ 14/14 API tests passing
- ✅ Authentication flows tested
- ✅ Framework hoạt động hoàn hảo từ vị trí mới
- ✅ Multi-browser support ready
- ✅ CI/CD integration ready

## 🔧 **Configurations**
- **Frontend URL**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`  
- **Browsers**: Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari
- **Chrome Extension**: Automatically loaded for testing

Happy Testing! 🎉