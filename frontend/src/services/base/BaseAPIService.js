/**
 * Base API Service following SOLID principles
 * Implements Liskov Substitution Principle - all API services can substitute this base class
 */

class BaseAPIService {
  constructor(apiClient, endpoint) {
    this.api = apiClient;
    this.endpoint = endpoint;
  }

  /**
   * Get all items with pagination and filtering
   * @param {Object} params - Query parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getAll(params = {}) {
    try {
      const response = await this.fetchData(params);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get single item by ID
   * @param {string|number} id - Item ID
   * @returns {Promise<NormalizedResponse>}
   */
  async getById(id) {
    try {
      const response = await this.fetchById(id);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Create new item
   * @param {Object} data - Item data
   * @returns {Promise<NormalizedResponse>}
   */
  async create(data) {
    try {
      const response = await this.createItem(data);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Update existing item
   * @param {string|number} id - Item ID
   * @param {Object} data - Updated data
   * @returns {Promise<NormalizedResponse>}
   */
  async update(id, data) {
    try {
      const response = await this.updateItem(id, data);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Delete item
   * @param {string|number} id - Item ID
   * @returns {Promise<NormalizedResponse>}
   */
  async delete(id) {
    try {
      const response = await this.deleteItem(id);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Template methods - subclasses must implement these
  async fetchData(params) {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        queryParams.append(key, value);
      }
    });
    return this.api.get(`${this.endpoint}?${queryParams.toString()}`);
  }

  async fetchById(id) {
    return this.api.get(`${this.endpoint}/${id}`);
  }

  async createItem(data) {
    return this.api.post(this.endpoint, data);
  }

  async updateItem(id, data) {
    return this.api.put(`${this.endpoint}/${id}`, data);
  }

  async deleteItem(id) {
    return this.api.delete(`${this.endpoint}/${id}`);
  }

  /**
   * Normalize API response to consistent format
   * Ensures Liskov Substitution Principle - all responses have same structure
   * @param {Object} response - Raw API response
   * @returns {NormalizedResponse}
   */
  normalizeResponse(response) {
    const isSuccess = response.status >= 200 && response.status < 300;
    
    return {
      success: isSuccess,
      data: response.data?.items || response.data,
      total: response.data?.total || (Array.isArray(response.data?.items) ? response.data.items.length : 0),
      page: response.data?.page || 1,
      size: response.data?.size || 20,
      totalPages: response.data?.total_pages || Math.ceil((response.data?.total || 0) / (response.data?.size || 20)),
      error: !isSuccess ? this.extractErrorMessage(response) : null,
      status: response.status,
      headers: response.headers
    };
  }

  /**
   * Handle API errors consistently
   * @param {Error} error - Error object
   * @returns {NormalizedResponse}
   */
  handleError(error) {
    const message = this.extractErrorMessage(error.response || error);
    
    return {
      success: false,
      data: null,
      total: 0,
      page: 1,
      size: 20,
      totalPages: 0,
      error: message,
      status: error.response?.status || 500,
      headers: error.response?.headers || {}
    };
  }

  /**
   * Extract error message from response
   * @param {Object} response - Error response
   * @returns {string}
   */
  extractErrorMessage(response) {
    if (response?.data?.message) return response.data.message;
    if (response?.data?.error) return response.data.error;
    if (response?.statusText) return response.statusText;
    if (response?.message) return response.message;
    return 'An unexpected error occurred';
  }

  /**
   * Search items by query
   * @param {string} query - Search query
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async search(query, params = {}) {
    return this.getAll({ ...params, search: query });
  }

  /**
   * Get statistics for the resource
   * @returns {Promise<NormalizedResponse>}
   */
  async getStatistics() {
    try {
      const response = await this.api.get(`${this.endpoint}/statistics`);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }
}

/**
 * @typedef {Object} NormalizedResponse
 * @property {boolean} success - Whether the request was successful
 * @property {*} data - Response data
 * @property {number} total - Total number of items
 * @property {number} page - Current page number
 * @property {number} size - Page size
 * @property {number} totalPages - Total number of pages
 * @property {string|null} error - Error message if any
 * @property {number} status - HTTP status code
 * @property {Object} headers - Response headers
 */

export default BaseAPIService;