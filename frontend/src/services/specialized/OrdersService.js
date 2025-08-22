/**
 * Orders Service following Single Responsibility Principle
 * Responsible ONLY for orders-related operations
 */

import BaseAPIService from '../base/BaseAPIService.js';
import api from '../api.js';

class OrdersService extends BaseAPIService {
  constructor() {
    super(api, '/orders');
  }

  /**
   * Transform API data to consistent order format
   * Single Responsibility: Only handles order data transformation
   * @param {Object} apiOrder - Raw order from API
   * @returns {Object} Normalized order object
   */
  transformOrder(apiOrder) {
    return {
      id: apiOrder.id,
      orderNumber: apiOrder.order_number || `ORD-${apiOrder.id}`,
      itemId: apiOrder.item_id || 'N/A',
      machine: apiOrder.machine || 'N/A',
      productName: apiOrder.product_name || 'Unknown Product',
      productLink: apiOrder.product_link || '#',
      productOption: apiOrder.product_option || 'Standard',
      trackingNumber: apiOrder.tracking_number || '',
      customerName: apiOrder.customer_name || 'Unknown Customer',
      usernameEbay: apiOrder.username_ebay || 'N/A',
      shippingAddress: apiOrder.shipping_address || 'N/A',
      customerPhone: apiOrder.customer_phone || 'N/A',
      customerEmail: apiOrder.customer_email || 'N/A',
      netEB: parseFloat(apiOrder.price_ebay || 0),
      priceCost: parseFloat(apiOrder.price_cost || 0),
      profit: parseFloat(apiOrder.price_ebay || 0) - parseFloat(apiOrder.price_cost || 0),
      orderDate: apiOrder.order_date 
        ? new Date(apiOrder.order_date).toISOString().split('T')[0] 
        : new Date().toISOString().split('T')[0],
      expectedShipDate: apiOrder.expected_ship_date 
        ? new Date(apiOrder.expected_ship_date).toISOString().split('T')[0]
        : null,
      actualShipDate: apiOrder.actual_ship_date 
        ? new Date(apiOrder.actual_ship_date).toISOString().split('T')[0]
        : null,
      status: apiOrder.status || 'pending',
      shipper: apiOrder.shipper || '',
      shippingCost: parseFloat(apiOrder.shipping_cost || 0),
      tax: parseFloat(apiOrder.tax || 0),
      totalAmount: parseFloat(apiOrder.total_amount || apiOrder.price_ebay || 0),
      currency: apiOrder.currency || 'USD',
      paymentMethod: apiOrder.payment_method || 'Unknown',
      notes: apiOrder.notes || '',
      priority: apiOrder.priority || 'normal',
      source: apiOrder.source || 'ebay',
      isAlert: this.hasAlert(apiOrder),
      alerts: this.generateAlerts(apiOrder),
      accountId: apiOrder.account_id || null,
      createdAt: apiOrder.created_at ? new Date(apiOrder.created_at) : new Date(),
      updatedAt: apiOrder.updated_at ? new Date(apiOrder.updated_at) : new Date()
    };
  }

  /**
   * Check if order has alerts
   * Single Responsibility: Only handles alert detection logic
   * @param {Object} apiOrder - Raw order from API
   * @returns {boolean}
   */
  hasAlert(apiOrder) {
    const orderDate = new Date(apiOrder.order_date || Date.now());
    const expectedShipDate = new Date(apiOrder.expected_ship_date || Date.now());
    const now = new Date();

    // Check for overdue shipping
    if (apiOrder.status === 'pending' && expectedShipDate < now) {
      return true;
    }

    // Check for missing tracking
    if (apiOrder.status === 'shipped' && !apiOrder.tracking_number) {
      return true;
    }

    // Check for high-value orders
    if (parseFloat(apiOrder.price_ebay || 0) > 1000) {
      return true;
    }

    return false;
  }

  /**
   * Generate alert messages for order
   * Single Responsibility: Only handles alert message generation
   * @param {Object} apiOrder - Raw order from API
   * @returns {Array<string>}
   */
  generateAlerts(apiOrder) {
    const alerts = [];
    const orderDate = new Date(apiOrder.order_date || Date.now());
    const expectedShipDate = new Date(apiOrder.expected_ship_date || Date.now());
    const now = new Date();

    // Overdue shipping alert
    if (apiOrder.status === 'pending' && expectedShipDate < now) {
      const daysPast = Math.floor((now - expectedShipDate) / (1000 * 60 * 60 * 24));
      alerts.push(`Overdue shipping by ${daysPast} day(s)`);
    }

    // Missing tracking alert
    if (apiOrder.status === 'shipped' && !apiOrder.tracking_number) {
      alerts.push('Missing tracking number');
    }

    // High-value order alert
    if (parseFloat(apiOrder.price_ebay || 0) > 1000) {
      alerts.push('High-value order - requires special handling');
    }

    // Customer communication needed
    if (apiOrder.status === 'pending' && !apiOrder.customer_email) {
      alerts.push('Missing customer contact information');
    }

    return alerts;
  }

  /**
   * Override normalizeResponse to transform orders data
   * @param {Object} response - Raw API response
   * @returns {NormalizedResponse}
   */
  normalizeResponse(response) {
    const normalized = super.normalizeResponse(response);
    
    if (normalized.success && normalized.data) {
      // Transform single order or array of orders
      if (Array.isArray(normalized.data)) {
        normalized.data = normalized.data.map(order => this.transformOrder(order));
      } else {
        normalized.data = this.transformOrder(normalized.data);
      }
    }
    
    return normalized;
  }

  /**
   * Get orders by status
   * Single Responsibility: Only handles status-based filtering
   * @param {string} status - Order status
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getByStatus(status, params = {}) {
    return this.getAll({ ...params, status });
  }

  /**
   * Get pending orders
   * Single Responsibility: Only handles pending orders
   * @param {Object} params - Query parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getPending(params = {}) {
    return this.getByStatus('pending', params);
  }

  /**
   * Get shipped orders
   * Single Responsibility: Only handles shipped orders
   * @param {Object} params - Query parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getShipped(params = {}) {
    return this.getByStatus('shipped', params);
  }

  /**
   * Get delivered orders
   * Single Responsibility: Only handles delivered orders
   * @param {Object} params - Query parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getDelivered(params = {}) {
    return this.getByStatus('delivered', params);
  }

  /**
   * Get overdue orders
   * Single Responsibility: Only handles overdue order filtering
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getOverdue(params = {}) {
    try {
      const response = await this.getAll(params);
      
      if (response.success && Array.isArray(response.data)) {
        const now = new Date();
        response.data = response.data.filter(order => {
          const expectedShipDate = new Date(order.expectedShipDate || Date.now());
          return order.status === 'pending' && expectedShipDate < now;
        });
        response.total = response.data.length;
      }
      
      return response;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get orders missing tracking
   * Single Responsibility: Only handles tracking validation
   * @param {Object} params - Additional parameters
   * @returns {Promise<NormalizedResponse>}
   */
  async getMissingTracking(params = {}) {
    try {
      const response = await this.getAll(params);
      
      if (response.success && Array.isArray(response.data)) {
        response.data = response.data.filter(order => 
          order.status === 'shipped' && !order.trackingNumber
        );
        response.total = response.data.length;
      }
      
      return response;
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Update order status
   * Single Responsibility: Only handles status updates
   * @param {string|number} id - Order ID
   * @param {string} status - New status
   * @returns {Promise<NormalizedResponse>}
   */
  async updateStatus(id, status) {
    try {
      const response = await this.api.put(`${this.endpoint}/${id}/status`, { status });
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Add tracking number to order
   * Single Responsibility: Only handles tracking number updates
   * @param {string|number} id - Order ID
   * @param {string} trackingNumber - Tracking number
   * @param {string} shipper - Shipping company
   * @returns {Promise<NormalizedResponse>}
   */
  async addTracking(id, trackingNumber, shipper = '') {
    try {
      const response = await this.api.put(`${this.endpoint}/${id}/tracking`, { 
        tracking_number: trackingNumber,
        shipper: shipper
      });
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Bulk update order status
   * Single Responsibility: Only handles bulk status updates
   * @param {Array<string|number>} ids - Order IDs
   * @param {string} status - New status
   * @returns {Promise<NormalizedResponse>}
   */
  async bulkUpdateStatus(ids, status) {
    try {
      const response = await this.api.put(`${this.endpoint}/bulk-status`, { 
        order_ids: ids,
        status: status
      });
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get order statistics
   * Single Responsibility: Only handles order statistics
   * @returns {Promise<NormalizedResponse>}
   */
  async getOrderStats() {
    try {
      const response = await this.api.get(`${this.endpoint}/statistics`);
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  /**
   * Get revenue statistics
   * Single Responsibility: Only handles revenue calculations
   * @param {string} period - Time period (day, week, month, year)
   * @returns {Promise<NormalizedResponse>}
   */
  async getRevenueStats(period = 'month') {
    try {
      const response = await this.api.get(`${this.endpoint}/revenue-stats`, {
        params: { period }
      });
      return this.normalizeResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }
}

// Export singleton instance
export default new OrdersService();