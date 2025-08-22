/**
 * Notification Service Interface (Interface Segregation Principle)
 * Focused interface for notification operations only
 */

/**
 * Base Notification Service Interface
 */
class INotificationService {
  /**
   * Send notification
   * @param {string} message - Notification message
   * @param {string} recipient - Recipient identifier
   * @param {Object} options - Additional options
   * @returns {Promise<Object>} Send result
   */
  async send(message, recipient, options = {}) {
    throw new Error('Must implement send method');
  }

  /**
   * Send bulk notifications
   * @param {Array<Object>} notifications - Array of notification objects
   * @returns {Promise<Object>} Bulk send result
   */
  async sendBulk(notifications) {
    throw new Error('Must implement sendBulk method');
  }

  /**
   * Get notification status
   * @param {string} notificationId - Notification ID
   * @returns {Promise<Object>} Status information
   */
  async getStatus(notificationId) {
    throw new Error('Must implement getStatus method');
  }

  /**
   * Get service name
   * @returns {string} Service name
   */
  getServiceName() {
    throw new Error('Must implement getServiceName method');
  }

  /**
   * Validate notification data
   * @param {Object} notification - Notification data
   * @returns {Object} Validation result
   */
  validateNotification(notification) {
    const errors = [];
    
    if (!notification.message) {
      errors.push('Message is required');
    }
    
    if (!notification.recipient) {
      errors.push('Recipient is required');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export default INotificationService;