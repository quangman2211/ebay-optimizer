/**
 * Listings Service following Single Responsibility Principle
 * Responsible ONLY for listings-related operations
 */

import BaseAPIService from '../base/BaseAPIService.js';
import api from '../api.js';

class ListingsService extends BaseAPIService {
  constructor() {
    super(api, '/listings');
  }

  /**
   * Transform API data to consistent listing format
   * Single Responsibility: Only handles listing data transformation
   * @param {Object} apiListing - Raw listing from API
   * @returns {Object} Normalized listing object
   */
  transformListing(apiListing) {
    return {
      id: apiListing.id,
      title: apiListing.title || 'Unknown Product',
      image: apiListing.images && apiListing.images.length > 0 
        ? apiListing.images[0] 
        : 'https://via.placeholder.com/80x80?text=No+Image',
      category: apiListing.category || 'Uncategorized',
      currentPrice: parseFloat(apiListing.price_ebay || 0),
      originalPrice: parseFloat(apiListing.price_cost || apiListing.price_ebay || 0),
      status: apiListing.status || 'active',
      watchers: parseInt(apiListing.watchers || 0),
      views: parseInt(apiListing.page_views || 0),
      sold: parseInt(apiListing.sold_quantity || 0),
      performanceScore: parseFloat(apiListing.performance_score || 0),
      seoScore: parseFloat(apiListing.seo_score || 0),
      createdAt: apiListing.created_at ? new Date(apiListing.created_at) : new Date(),
      updatedAt: apiListing.updated_at ? new Date(apiListing.updated_at) : new Date(),
      ebayItemId: apiListing.ebay_item_id || null,
      sku: apiListing.sku || null,
      quantity: parseInt(apiListing.quantity || 0),
      condition: apiListing.condition || 'new',
      description: apiListing.description || '',
      keywords: apiListing.keywords || [],
      accountId: apiListing.account_id || null
    };
  }

  /**
   * Override normalizeResponse to transform listings data
   * @param {Object} response - Raw API response
   * @returns {NormalizedResponse}
   */
  normalizeResponse(response) {
    const normalized = super.normalizeResponse(response);
    
    if (normalized.success && normalized.data) {
      // Transform single listing or array of listings
      if (Array.isArray(normalized.data)) {
        normalized.data = normalized.data.map(listing => this.transformListing(listing));
      } else {
        normalized.data = this.transformListing(normalized.data);
      }
    }
    
    return normalized;
  }

  /**
   * Get listings by status
   * Single Responsibility: Only handles status-based filtering
   * @param {string} status - Listing status
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getByStatus(status, params = {}) {
    return this.getAll({ ...params, status });
  }

  /**
   * Get listings by category
   * Single Responsibility: Only handles category-based filtering
   * @param {string} category - Listing category
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getByCategory(category, params = {}) {
    return this.getAll({ ...params, category });
  }

  /**
   * Get draft listings
   * Single Responsibility: Only handles draft listings
   * @param {Object} params - Query parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getDrafts(params = {}) {
    return this.getByStatus('draft', params);
  }

  /**
   * Get active listings
   * Single Responsibility: Only handles active listings
   * @param {Object} params - Query parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getActive(params = {}) {
    return this.getByStatus('active', params);
  }

  /**
   * Get listings needing optimization
   * Single Responsibility: Only handles optimization filtering
   * @param {number} threshold - Performance score threshold (default: 70)
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getNeedingOptimization(threshold = 70, params = {}) {
    try {
      const response = await this.getAll(params);
      
      if (response.success && Array.isArray(response.data)) {
        response.data = response.data.filter(listing => 
          listing.performanceScore < threshold
        );
        response.total = response.data.length;
      }
      
      return response;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get listings missing images
   * Single Responsibility: Only handles image validation
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getMissingImages(params = {}) {
    try {
      const response = await this.getAll(params);
      
      if (response.success && Array.isArray(response.data)) {
        response.data = response.data.filter(listing => 
          !listing.image || listing.image.includes('placeholder') || !listing.images || listing.images.length === 0
        );
        response.total = response.data.length;
      }
      
      return response;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Optimize listing
   * Single Responsibility: Only handles optimization requests
   * @param {string|number} id - Listing ID
   * @returns {Promise<NormalizedResponse>}
   */
  async optimize(id) {
    try {
      const response = await this.api.post(`${this.endpoint}/${id}/optimize`);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Bulk optimize listings
   * Single Responsibility: Only handles bulk optimization
   * @param {Array<string|number>} ids - Listing IDs
   * @returns {Promise<NormalizedResponse>}
   */
  async bulkOptimize(ids) {
    try {
      const response = await this.api.post(`${this.endpoint}/bulk-optimize`, { 
        listing_ids: ids 
      });
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get categories
   * Single Responsibility: Only handles category data
   * @returns {Promise<NormalizedResponse>}
   */
  async getCategories() {
    try {
      const response = await this.api.get(`${this.endpoint}/categories`);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Bulk update listings
   * Single Responsibility: Only handles bulk updates
   * @param {Array<string|number>} ids - Listing IDs
   * @param {Object} data - Update data
   * @returns {Promise<NormalizedResponse>}
   */
  async bulkUpdate(ids, data) {
    try {
      const response = await this.api.put(`${this.endpoint}/bulk`, { 
        listing_ids: ids, 
        ...data 
      });
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get listing performance statistics
   * Single Responsibility: Only handles performance stats
   * @returns {Promise<NormalizedResponse>}
   */
  async getPerformanceStats() {
    try {
      const response = await this.api.get(`${this.endpoint}/performance-stats`);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }
}

// Export singleton instance
export default new ListingsService();