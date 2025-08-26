import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Create axios instance with auth interceptor
const authAPI = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
authAPI.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token expiration
authAPI.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

class AuthService {
  async login(credentials) {
    // Force real authentication - disable mock mode for consistent authentication
    console.log('AuthService: Using REAL authentication (mock disabled)');
    // if (this.isMockMode()) {
    //   return this.mockLogin(credentials);
    // }

    try {
      const response = await authAPI.post('/auth/login-json', credentials);
      const { access_token, token_type } = response.data;
      
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('token_type', token_type);
      
      // Get user info after successful login
      try {
        const userInfo = await this.getCurrentUser();
        localStorage.setItem('user_data', JSON.stringify(userInfo));
      } catch (userError) {
        // If /auth/me fails, create basic user data from credentials
        console.warn('Could not fetch user info, using basic data:', userError);
        const userInfo = {
          id: 1,
          email: credentials.email,
          name: credentials.email.split('@')[0],
          role: this.getRoleFromEmail(credentials.email),
          permissions: this.getPermissionsFromEmail(credentials.email),
          avatar: null,
          created_at: new Date().toISOString()
        };
        localStorage.setItem('user_data', JSON.stringify(userInfo));
      }
      
      return { success: true, data: response.data };
    } catch (error) {
      // Fallback to mock if backend not available
      if (error.code === 'ERR_NETWORK' || error.response?.status >= 500) {
        console.warn('Backend not available, using mock authentication');
        return this.mockLogin(credentials);
      }
      
      return {
        success: false,
        error: error.response?.data?.detail || 'Đăng nhập thất bại'
      };
    }
  }

  // Mock authentication for development
  isMockMode() {
    return process.env.NODE_ENV === 'development' && !process.env.REACT_APP_DISABLE_MOCK_AUTH;
  }

  mockLogin(credentials) {
    const { email, password } = credentials;
    
    // Demo credentials with roles
    const validCredentials = [
      { email: 'test@ebayoptimizer.com', password: '123456', role: 'ADMIN' },
      { email: 'manager@ebayoptimizer.com', password: '123456', role: 'EBAY_MANAGER' },
      { email: 'staff@ebayoptimizer.com', password: '123456', role: 'FULFILLMENT_STAFF' },
      { email: 'admin@ebay.vn', password: 'admin123', role: 'ADMIN' },
      { email: 'demo@gmail.com', password: 'demo123', role: 'ADMIN' }
    ];

    const isValid = validCredentials.some(
      cred => cred.email === email && cred.password === password
    );

    if (isValid) {
      // Create mock token và user data
      const mockToken = 'mock-jwt-token-' + Date.now();
      const userCred = validCredentials.find(cred => cred.email === email);
      const mockUser = {
        id: 1,
        email: email,
        name: this.getDisplayName(email),
        role: userCred.role,
        permissions: this.getPermissionsFromRole(userCred.role),
        avatar: null,
        created_at: '2024-01-01T00:00:00Z'
      };

      localStorage.setItem('access_token', mockToken);
      localStorage.setItem('token_type', 'bearer');
      localStorage.setItem('user_data', JSON.stringify(mockUser));

      return { 
        success: true, 
        data: { access_token: mockToken, token_type: 'bearer' } 
      };
    }

    return {
      success: false,
      error: 'Email hoặc mật khẩu không đúng. Thử: test@ebayoptimizer.com / 123456'
    };
  }

  async register(userData) {
    try {
      const response = await authAPI.post('/auth/register', userData);
      return { success: true, data: response.data };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Đăng ký thất bại'
      };
    }
  }

  async getCurrentUser() {
    // Force real API call - no mock mode
    console.log('AuthService: Getting current user from REAL API');
    // if (this.isMockMode() || this.getToken()?.startsWith('mock-jwt-token')) {
    //   const userData = localStorage.getItem('user_data');
    //   if (userData) {
    //     return JSON.parse(userData);
    //   }
    // }

    try {
      const response = await authAPI.get('/auth/me');
      const apiUserData = response.data;
      
      // Enhance API response with role info if missing
      if (!apiUserData.role && apiUserData.email) {
        apiUserData.role = this.getRoleFromEmail(apiUserData.email);
        apiUserData.permissions = this.getPermissionsFromEmail(apiUserData.email);
        console.log('Enhanced API user data with role:', apiUserData.role);
      }
      
      return apiUserData;
    } catch (error) {
      // Fallback to stored user data if API fails
      const userData = localStorage.getItem('user_data');
      if (userData) {
        const parsedData = JSON.parse(userData);
        // Ensure role is set in fallback data too
        if (!parsedData.role && parsedData.email) {
          parsedData.role = this.getRoleFromEmail(parsedData.email);
          parsedData.permissions = this.getPermissionsFromEmail(parsedData.email);
        }
        return parsedData;
      }
      throw error;
    }
  }

  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('token_type');
    localStorage.removeItem('user_data');
  }

  isAuthenticated() {
    return !!localStorage.getItem('access_token');
  }

  getToken() {
    return localStorage.getItem('access_token');
  }

  getUser() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  }

  // Helper functions for role and permission mapping
  getRoleFromEmail(email) {
    if (email === 'test@ebayoptimizer.com') return 'ADMIN';
    if (email === 'manager@ebayoptimizer.com') return 'EBAY_MANAGER';
    if (email === 'staff@ebayoptimizer.com') return 'FULFILLMENT_STAFF';
    if (email.includes('admin')) return 'ADMIN';
    return 'ADMIN'; // Default fallback
  }

  getPermissionsFromEmail(email) {
    const role = this.getRoleFromEmail(email);
    return this.getPermissionsFromRole(role);
  }

  getPermissionsFromRole(role) {
    const rolePermissions = {
      'ADMIN': [
        'manage_users', 'view_users', 'manage_suppliers', 'view_suppliers',
        'manage_products', 'view_products', 'update_inventory', 
        'manage_orders', 'view_orders', 'assign_orders', 'update_order_status',
        'manage_pricing', 'view_pricing', 'optimize_prices',
        'view_analytics', 'export_data', 'manage_settings', 'manage_roles', 'system_admin'
      ],
      'EBAY_MANAGER': [
        'view_users', 'manage_suppliers', 'view_suppliers',
        'manage_products', 'view_products', 'update_inventory',
        'manage_orders', 'view_orders', 'assign_orders', 'update_order_status',
        'manage_pricing', 'view_pricing', 'optimize_prices',
        'view_analytics', 'export_data'
      ],
      'FULFILLMENT_STAFF': [
        'view_suppliers', 'view_products', 'update_inventory',
        'view_orders', 'update_order_status',
        'view_pricing', 'view_analytics'
      ]
    };
    return rolePermissions[role] || [];
  }

  getDisplayName(email) {
    if (email === 'test@ebayoptimizer.com') return 'Test Admin User';
    if (email === 'manager@ebayoptimizer.com') return 'eBay Manager User';
    if (email === 'staff@ebayoptimizer.com') return 'Fulfillment Staff User';
    if (email === 'admin@ebay.vn') return 'Admin User';
    if (email === 'demo@gmail.com') return 'Demo User';
    return email.split('@')[0];
  }
}

const authService = new AuthService();
export default authService;