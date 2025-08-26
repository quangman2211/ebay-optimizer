/**
 * Backend API Client for Chrome Extension
 * Handles all communication with the backend server
 * No Google OAuth2 required - uses API key authentication
 */

class BackendAPIClient {
  constructor() {
    // Backend URL configuration - can be changed via popup settings
    this.baseURL = this.getBackendURL();
    this.apiKey = this.getAPIKey();
    this.timeout = 30000; // 30 seconds timeout
  }

  /**
   * Get backend URL from storage or use default
   */
  getBackendURL() {
    // Check Chrome storage for saved backend URL
    const savedURL = localStorage.getItem('backend_url');
    if (savedURL) {
      return savedURL;
    }

    // Default URLs based on environment
    const urls = {
      local: 'http://localhost:8000/api/v1',
      ngrok: 'https://your-app.ngrok-free.app/api/v1',  // Update with your ngrok URL
      production: 'https://ebay-optimizer-api.onrender.com/api/v1'  // Update after Render deployment
    };

    // Default to local for development
    return urls.local;
  }

  /**
   * Get API key from storage or use development key
   */
  getAPIKey() {
    // Check Chrome storage for saved API key
    const savedKey = localStorage.getItem('api_key');
    if (savedKey) {
      return savedKey;
    }

    // Default development API key
    return 'dev-api-key-12345';
  }

  /**
   * Update backend URL
   */
  setBackendURL(url) {
    this.baseURL = url;
    localStorage.setItem('backend_url', url);
    console.log(`Backend URL updated to: ${url}`);
  }

  /**
   * Update API key
   */
  setAPIKey(apiKey) {
    this.apiKey = apiKey;
    localStorage.setItem('api_key', apiKey);
    console.log('API key updated');
  }

  /**
   * Make HTTP request to backend
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions = {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      }
    };

    const requestOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...(options.headers || {})
      }
    };

    console.log(`[API] ${requestOptions.method} ${url}`);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...requestOptions,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`[API] Response:`, data);
      return data;

    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      console.error(`[API] Error:`, error);
      throw error;
    }
  }

  /**
   * Health check endpoint
   */
  async healthCheck() {
    try {
      const response = await this.request('/extension/csv/health');
      return {
        success: true,
        ...response
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Upload CSV data to backend
   */
  async uploadCSV(accountIdentifier, csvType, csvContent, metadata = {}) {
    try {
      const payload = {
        account_identifier: accountIdentifier,
        csv_type: csvType,  // 'orders' or 'listings'
        csv_content: csvContent,
        metadata: metadata
      };

      const response = await this.request('/extension/csv/upload', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      return {
        success: response.success || false,
        message: response.message || 'Upload completed',
        data: response.data || {}
      };

    } catch (error) {
      console.error('[API] CSV upload failed:', error);
      return {
        success: false,
        message: `Upload failed: ${error.message}`,
        error: error.message
      };
    }
  }

  /**
   * Validate CSV format before upload
   */
  async validateCSV(accountIdentifier, csvType, csvContent) {
    try {
      const payload = {
        account_identifier: accountIdentifier,
        csv_type: csvType,
        csv_content: csvContent
      };

      const response = await this.request('/extension/csv/validate', {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      return response;

    } catch (error) {
      console.error('[API] CSV validation failed:', error);
      return {
        success: false,
        message: `Validation failed: ${error.message}`,
        data: { valid: false }
      };
    }
  }

  /**
   * Send collected orders data
   */
  async sendOrders(accountId, ordersData) {
    try {
      const response = await this.request('/extension/collect/orders', {
        method: 'POST',
        body: JSON.stringify({
          account_id: accountId,
          orders_data: ordersData
        })
      });

      return response;

    } catch (error) {
      console.error('[API] Orders collection failed:', error);
      return {
        success: false,
        message: `Failed to send orders: ${error.message}`
      };
    }
  }

  /**
   * Send collected listings data
   */
  async sendListings(accountId, listingsData) {
    try {
      const response = await this.request('/extension/collect/listings', {
        method: 'POST',
        body: JSON.stringify({
          account_id: accountId,
          listings_data: listingsData
        })
      });

      return response;

    } catch (error) {
      console.error('[API] Listings collection failed:', error);
      return {
        success: false,
        message: `Failed to send listings: ${error.message}`
      };
    }
  }

  /**
   * Test connection to backend
   */
  async testConnection() {
    const startTime = Date.now();
    
    try {
      const health = await this.healthCheck();
      const latency = Date.now() - startTime;

      if (health.success) {
        return {
          success: true,
          message: 'Connected to backend successfully',
          latency: `${latency}ms`,
          backend: this.baseURL,
          features: health.data?.features || {}
        };
      } else {
        return {
          success: false,
          message: `Connection failed: ${health.error}`,
          backend: this.baseURL
        };
      }

    } catch (error) {
      return {
        success: false,
        message: `Connection error: ${error.message}`,
        backend: this.baseURL
      };
    }
  }

  /**
   * Retry failed request with exponential backoff
   */
  async retryRequest(fn, maxRetries = 3, delay = 1000) {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        if (i === maxRetries - 1) {
          throw error;
        }
        
        const waitTime = delay * Math.pow(2, i);
        console.log(`[API] Retry ${i + 1}/${maxRetries} after ${waitTime}ms`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }
}

// Create singleton instance
const backendAPI = new BackendAPIClient();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BackendAPIClient;
}