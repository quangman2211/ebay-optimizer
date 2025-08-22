import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available (use correct token key)
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log('API: Adding auth token to request:', config.url);
    } else {
      console.log('API: No token found for request:', config.url);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('API: Success response for:', response.config.url);
    return response;
  },
  (error) => {
    console.log('API: Error response:', error.response?.status, 'for:', error.config?.url);
    if (error.response?.status === 401) {
      // Handle unauthorized - use correct token keys
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
      localStorage.removeItem('token_type');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Note: Comprehensive API definitions below - duplicates removed

// Orders APIs
export const ordersAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/orders?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/orders/${id}`),
  create: (data) => api.post('/orders', data),
  update: (id, data) => api.put(`/orders/${id}`, data),
  delete: (id) => api.delete(`/orders/${id}`),
  updateStatus: (id, status) => api.put(`/orders/${id}/status`, { status }),
  addTracking: (id, trackingData) => api.put(`/orders/${id}/tracking`, trackingData),
  bulkUpdate: (orderIds, data) => api.put('/orders/bulk', { order_ids: orderIds, ...data }),
  getStatistics: () => api.get('/orders/statistics'),
};

// Listings APIs  
export const listingsAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/listings?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/listings/${id}`),
  create: (data) => api.post('/listings', data),
  update: (id, data) => api.put(`/listings/${id}`, data),
  delete: (id) => api.delete(`/listings/${id}`),
  bulkUpdate: (listingIds, data) => api.put('/listings/bulk', { listing_ids: listingIds, ...data }),
  optimize: (id) => api.post(`/listings/${id}/optimize`),
  getCategories: () => api.get('/listings/categories'),
  getStatistics: () => api.get('/listings/statistics'),
};

// Sources APIs
export const sourcesAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/sources?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/sources/${id}`),
  create: (data) => api.post('/sources', data),
  update: (id, data) => api.put(`/sources/${id}`, data),
  delete: (id) => api.delete(`/sources/${id}`),
  sync: (id) => api.post(`/sources/${id}/sync`),
  testConnection: (id) => api.post(`/sources/${id}/test`),
  getProducts: (id, params = {}) => {
    const queryParams = new URLSearchParams(params);
    return api.get(`/sources/${id}/products?${queryParams.toString()}`);
  },
  getStatistics: () => api.get('/sources/statistics'),
};

// Accounts APIs
export const accountsAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/accounts?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/accounts/${id}`),
  create: (data) => api.post('/accounts', data),
  update: (id, data) => api.put(`/accounts/${id}`, data),
  delete: (id) => api.delete(`/accounts/${id}`),
  sync: (id) => api.post(`/accounts/${id}/sync`),
  getStatistics: () => api.get('/accounts/statistics'),
};

// Settings APIs
export const settingsAPI = {
  getAll: () => api.get('/settings'),
  update: (data) => api.put('/settings', data),
  getApiConfig: () => api.get('/settings/api-config'),
  updateApiConfig: (data) => api.put('/settings/api-config', data),
  getNotificationSettings: () => api.get('/settings/notifications'),
  updateNotificationSettings: (data) => api.put('/settings/notifications', data),
  
  // Google Sheets specific APIs
  getGoogleSheetsConfig: () => api.get('/settings'),
  updateGoogleSheetsConfig: (data) => api.put('/settings/google-sheets', data),
  testGoogleSheetsConnection: (data) => api.post('/settings/google-sheets/test-connection', data),
  getGoogleSheetsStatus: () => api.get('/settings/google-sheets/status'),
};

// Dashboard APIs
export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getRecentOrders: (limit = 10) => api.get(`/dashboard/recent-orders?limit=${limit}`),
  getTopProducts: (limit = 5) => api.get(`/dashboard/top-products?limit=${limit}`),
  getRevenueChart: (period = '30d') => api.get(`/dashboard/revenue-chart?period=${period}`),
  getCategoryChart: () => api.get('/dashboard/category-chart'),
  getActivityTimeline: (limit = 10) => api.get(`/dashboard/activity-timeline?limit=${limit}`),
  getAlerts: () => api.get('/dashboard/alerts'),
  getSummary: () => api.get('/dashboard/summary'),
};

// Optimization APIs
export const optimizationAPI = {
  optimizeTitle: (data) => api.post('/optimize/title', data),
  optimizeDescription: (data) => api.post('/optimize/description', data),
  generateKeywords: (data) => api.post('/optimize/keywords', data),
  bulkOptimize: (data) => api.post('/optimize/bulk', data),
  analyzeListing: (id) => api.post(`/optimize/analyze/${id}`),
};

// Export APIs
export const exportAPI = {
  getReports: () => api.get('/export/reports'),
  exportListings: (params) => api.post('/export/listings', null, { params }),
  exportOrders: (params) => api.post('/export/orders', null, { params }),
  exportFinancial: (params) => api.post('/export/financial', null, { params }),
  exportPerformance: (params) => api.post('/export/performance', null, { params }),
  getTemplates: () => api.get('/export/templates'),
  exportFromTemplate: (templateId, params) => api.post(`/export/template/${templateId}`, null, { params }),
  previewReport: (type, params) => api.get(`/export/preview/${type}`, { params }),
};

// Sync APIs
export const syncAPI = {
  syncListingsToSheets: () => api.post('/sync/listings/to-sheets'),
  syncListingsFromSheets: () => api.post('/sync/listings/from-sheets'),
  syncOrdersToSheets: () => api.post('/sync/orders/to-sheets'),
  fullSync: (direction = 'bidirectional') => api.post('/sync/full-sync', null, { params: { direction } }),
  getStatus: () => api.get('/sync/status'),
  getConfig: () => api.get('/sync/config'),
  updateConfig: (data) => api.put('/sync/config', data),
  updateSyncConfig: (config) => api.put('/sync/config', null, { params: config }),
  testConnection: () => api.post('/sync/test-connection'),
  getHistory: (limit = 20) => api.get(`/sync/history?limit=${limit}`),
};

// Multi-Account APIs for Employee Productivity

// Draft Listings APIs - Employee workflow focused
export const draftsAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/drafts?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/drafts/${id}`),
  create: (data) => api.post('/drafts', data),
  update: (id, data) => api.put(`/drafts/${id}`, data),
  delete: (id) => api.delete(`/drafts/${id}`),
  
  // Employee workflow APIs
  updateImageStatus: (id, data) => api.patch(`/drafts/${id}/image-status`, data),
  bulkUpdateStatus: (data) => api.patch('/drafts/bulk-status', data),
  getReadyToList: (accountId) => api.get(`/drafts/ready/to-list?account_id=${accountId || ''}`),
  getAnalytics: (accountId) => api.get(`/drafts/analytics?account_id=${accountId || ''}`),
  getByEmployee: (employeeName) => api.get(`/drafts/by-employee/${employeeName}`),
  
  // Productivity features
  getBatchCreateOptions: (sourceProductId) => api.get(`/drafts/batch-create-options/${sourceProductId}`),
  batchCreate: (sourceProductId, accounts, customizations) => 
    api.post('/drafts/batch-create', { source_product_id: sourceProductId, accounts, customizations }),
  getTaskQueue: (employeeName) => api.get(`/drafts/task-queue?employee=${employeeName}`),
  updateTaskStatus: (taskId, status) => api.patch(`/drafts/tasks/${taskId}`, { status }),
};

// Messages APIs - Customer service focused
export const messagesAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/messages?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/messages/${id}`),
  create: (data) => api.post('/messages', data),
  update: (id, data) => api.put(`/messages/${id}`, data),
  delete: (id) => api.delete(`/messages/${id}`),
  
  // Customer service workflow
  markRead: (id) => api.patch(`/messages/${id}/read`),
  markReplied: (id) => api.patch(`/messages/${id}/replied`),
  bulkMarkRead: (messageIds) => api.patch('/messages/bulk-read', { message_ids: messageIds }),
  bulkUpdatePriority: (messageIds, priority) => 
    api.patch('/messages/bulk-priority', { message_ids: messageIds, priority }),
  
  // Employee productivity features
  getUnreadCount: (accountId) => api.get(`/messages/unread/count?account_id=${accountId || ''}`),
  getUnreplied: (accountId) => api.get(`/messages/unreplied/list?account_id=${accountId || ''}`),
  getOverdue: (accountId) => api.get(`/messages/overdue/list?account_id=${accountId || ''}`),
  getAnalytics: (accountId) => api.get(`/messages/analytics?account_id=${accountId || ''}`),
  
  // Quick reply features
  getTemplates: () => api.get('/messages/templates'),
  createTemplate: (template) => api.post('/messages/templates', template),
  replyWithTemplate: (messageId, templateId, customText) => 
    api.post(`/messages/${messageId}/reply-template`, { template_id: templateId, custom_text: customText }),
};

// Account Sheets APIs - Google Sheets sync focused
export const accountSheetsAPI = {
  getAll: (params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return api.get(`/account-sheets?${queryParams.toString()}`);
  },
  getById: (id) => api.get(`/account-sheets/${id}`),
  create: (data) => api.post('/account-sheets', data),
  update: (id, data) => api.put(`/account-sheets/${id}`, data),
  delete: (id) => api.delete(`/account-sheets/${id}`),
  
  // Sheet management
  createDefaults: (accountId) => api.post(`/account-sheets/account/${accountId}/create-defaults`),
  getSheetsNeedingSync: () => api.get('/account-sheets/sync/needed'),
  triggerSync: (sheetId) => api.post('/account-sheets/sync/trigger', { sheet_id: sheetId }),
  bulkUpdateSync: (sheetIds, autoSync) => 
    api.patch('/account-sheets/bulk-sync', { sheet_ids: sheetIds, auto_sync: autoSync }),
  bulkUpdateFrequency: (sheetIds, frequency) => 
    api.patch('/account-sheets/bulk-frequency', { sheet_ids: sheetIds, frequency_minutes: frequency }),
  
  // Monitoring and analytics
  getAnalytics: (accountId) => api.get(`/account-sheets/analytics?account_id=${accountId || ''}`),
  getSheetsWithErrors: () => api.get('/account-sheets/errors/list'),
  getSyncHistory: (sheetId) => api.get(`/account-sheets/${sheetId}/sync-history`),
  validateData: (sheetId) => api.post(`/account-sheets/${sheetId}/validate`),
};

// Employee Productivity APIs - New for employee management
export const productivityAPI = {
  // Daily stats
  getDailyStats: (employeeName, date) => 
    api.get(`/productivity/daily-stats?employee=${employeeName}&date=${date || ''}`),
  getWeeklyStats: (employeeName) => 
    api.get(`/productivity/weekly-stats?employee=${employeeName}`),
  
  // Task management
  getTaskQueue: (employeeName) => api.get(`/productivity/tasks?employee=${employeeName}`),
  updateTask: (taskId, data) => api.put(`/productivity/tasks/${taskId}`, data),
  completeTask: (taskId) => api.patch(`/productivity/tasks/${taskId}/complete`),
  
  // Performance tracking
  getPerformanceMetrics: (employeeName, period) => 
    api.get(`/productivity/performance?employee=${employeeName}&period=${period}`),
  getLeaderboard: (period) => api.get(`/productivity/leaderboard?period=${period}`),
  
  // Goal setting
  getGoals: (employeeName) => api.get(`/productivity/goals?employee=${employeeName}`),
  setGoal: (employeeName, goalData) => api.post('/productivity/goals', { employee: employeeName, ...goalData }),
  updateGoalProgress: (goalId, progress) => api.patch(`/productivity/goals/${goalId}`, { progress }),
};

// Workflow APIs - Process automation
export const workflowAPI = {
  // Batch operations
  batchCreateDrafts: (sourceProductId, targetAccounts, customizations) =>
    api.post('/workflow/batch-create-drafts', { 
      source_product_id: sourceProductId, 
      target_accounts: targetAccounts,
      customizations 
    }),
  
  batchApproveImages: (draftIds, employeeName) =>
    api.post('/workflow/batch-approve-images', { draft_ids: draftIds, employee: employeeName }),
  
  batchPublishToEbay: (draftIds) =>
    api.post('/workflow/batch-publish', { draft_ids: draftIds }),
  
  // Process templates
  getWorkflowTemplates: () => api.get('/workflow/templates'),
  createWorkflowTemplate: (template) => api.post('/workflow/templates', template),
  executeWorkflow: (templateId, parameters) => 
    api.post(`/workflow/templates/${templateId}/execute`, parameters),
  
  // Automation rules
  getAutomationRules: () => api.get('/workflow/automation-rules'),
  createAutomationRule: (rule) => api.post('/workflow/automation-rules', rule),
  updateAutomationRule: (ruleId, updates) => api.put(`/workflow/automation-rules/${ruleId}`, updates),
};

// Products API Service
export const productsAPI = {
  // Get all products with filtering
  getAll: (params = {}) => api.get('/products', { params }),
  
  // Get single product
  getById: (id) => api.get(`/products/${id}`),
  
  // Create new product
  create: (productData) => api.post('/products', productData),
  
  // Update product
  update: (id, productData) => api.put(`/products/${id}`, productData),
  
  // Delete product
  delete: (id) => api.delete(`/products/${id}`),
  
  // Get product categories
  getCategories: () => api.get('/products/categories/list'),
  
  // Create draft from product
  createDraft: (productId, accountId) => 
    api.post(`/products/${productId}/create-draft?account_id=${accountId}`),
  
  // Get product statistics
  getStatistics: () => api.get('/products/statistics/summary'),
  
  // Bulk operations
  bulkApprove: (productIds) => 
    api.post('/products/bulk-approve', { product_ids: productIds }),
    
  bulkCreateDrafts: (productIds, accountIds) =>
    api.post('/products/bulk-create-drafts', { 
      product_ids: productIds, 
      account_ids: accountIds 
    }),
};

// Mock Data Service (temporary fallback)
export const mockDataService = {
  async getOrders() {
    // Return mock data từ DataService.js format
    return [
      { 
        orderNumber: "13-13428-98906",
        itemId: "365787369303",
        usernameEbay: "garden_master_2024",
        customerName: "John Doe",
        customerPhone: "(555) 123-4567",
        customerType: "New Buyer",
        nameProduct: "Chicken Wire Crop Coop Extension",
        linkProduct: "https://www.gardeners.com/buy/chicken-wire-crop-coop-extension/8611940.html",
        option: "Standard Size, Galvanized Wire",
        netEB: 89.95,
        address: "123 Farm Rd, Austin, TX 78701, USA",
        date: "2024-01-15",
        orderDate: "2024-01-15 11:30 AM",
        expectedShipDate: "2024-01-17",
        alerts: ["Don overdue"],
        machine: "Store_US_01",
        status: "pending",
        tracking: "",
        shipper: "",
      },
      { 
        orderNumber: "09-13393-44327",
        itemId: "167602829794",
        usernameEbay: "bbq_pitmaster",
        customerName: "Mike Johnson",
        customerPhone: "(512) 555-0123",
        customerType: "Repeat Buyer",
        nameProduct: "Billows® BBQ Temperature Control Fan Kit",
        linkProduct: "https://www.thermoworks.com/billows/",
        option: "Standard Kit with Controller",
        netEB: 299.00,
        address: "456 Smoke Ave, Dallas, TX 75201, USA",
        date: "2024-01-14",
        orderDate: "2024-01-14 9:45 AM",
        expectedShipDate: "2024-01-16",
        alerts: [],
        machine: "Store_US_01",
        status: "processing",
        tracking: "1Z999AA1012345678",
        shipper: "UPS",
      },
    ];
  },

  async getDashboardStats() {
    const orders = await this.getOrders();
    return {
      totalOrders: orders.length,
      pendingOrders: orders.filter(o => o.status === 'pending').length,
      processingOrders: orders.filter(o => o.status === 'processing').length,
      shippedOrders: orders.filter(o => o.status === 'shipped').length,
      totalRevenue: orders.reduce((sum, o) => sum + o.netEB, 0),
      trackingOrders: orders.filter(o => o.tracking && o.tracking.length > 0).length,
    };
  },

  async getListings() {
    return [
      { 
        id: "listing_001",
        itemId: "195432876543",
        title: "Apple iPhone 15 Pro Max 256GB Natural Titanium Unlocked",
        category: "Electronics",
        image: "/api/placeholder/80/80",
        priceEbay: 1205.37,
        profit: 185.83,
        quantity: 10,
        status: "active",
        views: 2847,
        watchers: 43,
        sold: 15,
        performance: 89,
      },
    ];
  },

  async getSources() {
    return [
      {
        id: "amazon-us",
        name: "Amazon US",
        icon: "🛒",
        products: 4,
        roi: 24.8,
        status: "connected",
        lastSync: "2025-08-20 14:30",
      },
    ];
  },

  async getAccounts() {
    return [
      {
        id: 1,
        username: "seller_pro_2025",
        email: "seller.pro@email.com",
        country: "US",
        flag: "🇺🇸",
        status: "active",
        healthScore: 92,
        totalListings: 147,
        activeListings: 132,
        totalSales: 1247,
        monthlyRevenue: 15420.50,
        feedbackScore: 99.2,
        feedbackCount: 2847,
        joinDate: "2018-03-15",
        lastActivity: "2025-08-20 14:30",
        limits: {
          monthlyListing: 500,
          monthlyRevenue: 25000,
          usedListing: 132,
          usedRevenue: 15420.50
        }
      },
    ];
  },
};

export default api;