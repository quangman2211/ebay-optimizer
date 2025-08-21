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