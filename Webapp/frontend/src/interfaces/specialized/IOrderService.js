/**
 * Order Service Interface (Interface Segregation Principle)
 * Focused interface ONLY for order operations
 */

/**
 * Order-specific operations interface
 * Separated from generic IDataService to follow ISP
 */
class IOrderService {
  /**
   * Update order status
   * @param {string|number} orderId - Order ID
   * @param {string} status - New status
   * @returns {Promise<Object>} Update result
   */
  async updateStatus(orderId, status) {
    throw new Error('Must implement updateStatus method');
  }

  /**
   * Add tracking information
   * @param {string|number} orderId - Order ID
   * @param {string} trackingNumber - Tracking number
   * @param {string} shipper - Shipping company
   * @returns {Promise<Object>} Update result
   */
  async addTracking(orderId, trackingNumber, shipper) {
    throw new Error('Must implement addTracking method');
  }

  /**
   * Get orders by status
   * @param {string} status - Order status
   * @param {Object} params - Additional parameters
   * @returns {Promise<Object>} Orders list
   */
  async getByStatus(status, params = {}) {
    throw new Error('Must implement getByStatus method');
  }

  /**
   * Get overdue orders
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Overdue orders
   */
  async getOverdue(params = {}) {
    throw new Error('Must implement getOverdue method');
  }

  /**
   * Bulk update orders
   * @param {Array<string|number>} orderIds - Order IDs
   * @param {Object} updateData - Update data
   * @returns {Promise<Object>} Update result
   */
  async bulkUpdate(orderIds, updateData) {
    throw new Error('Must implement bulkUpdate method');
  }

  /**
   * Calculate order profit
   * @param {Object} order - Order data
   * @returns {number} Profit amount
   */
  calculateProfit(order) {
    const netEB = parseFloat(order.netEB || 0);
    const priceCost = parseFloat(order.priceCost || 0);
    const shippingCost = parseFloat(order.shippingCost || 0);
    const tax = parseFloat(order.tax || 0);
    
    return netEB - priceCost - shippingCost - tax;
  }

  /**
   * Check if order has alerts
   * @param {Object} order - Order data
   * @returns {boolean} Whether order has alerts
   */
  hasAlerts(order) {
    const now = new Date();
    const expectedShipDate = new Date(order.expectedShipDate || Date.now());
    
    // Overdue shipping
    if (order.status === 'pending' && expectedShipDate < now) {
      return true;
    }
    
    // Missing tracking
    if (order.status === 'shipped' && !order.trackingNumber) {
      return true;
    }
    
    // High value order
    if (parseFloat(order.netEB || 0) > 1000) {
      return true;
    }
    
    return false;
  }

  /**
   * Generate order alerts
   * @param {Object} order - Order data
   * @returns {Array<string>} Alert messages
   */
  generateAlerts(order) {
    const alerts = [];
    const now = new Date();
    const expectedShipDate = new Date(order.expectedShipDate || Date.now());
    
    if (order.status === 'pending' && expectedShipDate < now) {
      const daysPast = Math.floor((now - expectedShipDate) / (1000 * 60 * 60 * 24));
      alerts.push(`Overdue shipping by ${daysPast} day(s)`);
    }
    
    if (order.status === 'shipped' && !order.trackingNumber) {
      alerts.push('Missing tracking number');
    }
    
    if (parseFloat(order.netEB || 0) > 1000) {
      alerts.push('High-value order - requires special handling');
    }
    
    if (!order.customerEmail) {
      alerts.push('Missing customer contact information');
    }
    
    return alerts;
  }

  /**
   * Validate order data
   * @param {Object} order - Order data
   * @returns {Object} Validation result
   */
  validateOrder(order) {
    const errors = [];
    
    if (!order.productName) {
      errors.push('Product name is required');
    }
    
    if (!order.customerName) {
      errors.push('Customer name is required');
    }
    
    if (!order.netEB || order.netEB <= 0) {
      errors.push('Price must be greater than 0');
    }
    
    if (!order.status) {
      errors.push('Status is required');
    }
    
    if (!order.orderDate) {
      errors.push('Order date is required');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export default IOrderService;