/**
 * Account Service Interface (Interface Segregation Principle)
 * Focused interface ONLY for account operations
 */

/**
 * Account-specific operations interface
 * Separated from generic IDataService to follow ISP
 */
class IAccountService {
  /**
   * Update account health score
   * @param {string|number} accountId - Account ID
   * @returns {Promise<Object>} Updated health score
   */
  async updateHealthScore(accountId) {
    throw new Error('Must implement updateHealthScore method');
  }

  /**
   * Get account limits
   * @param {string|number} accountId - Account ID
   * @returns {Promise<Object>} Account limits
   */
  async getAccountLimits(accountId) {
    throw new Error('Must implement getAccountLimits method');
  }

  /**
   * Update account settings
   * @param {string|number} accountId - Account ID
   * @param {Object} settings - Account settings
   * @returns {Promise<Object>} Update result
   */
  async updateSettings(accountId, settings) {
    throw new Error('Must implement updateSettings method');
  }

  /**
   * Get account performance
   * @param {string|number} accountId - Account ID
   * @param {string} period - Time period (day, week, month, year)
   * @returns {Promise<Object>} Performance data
   */
  async getPerformance(accountId, period = 'month') {
    throw new Error('Must implement getPerformance method');
  }

  /**
   * Check account status
   * @param {string|number} accountId - Account ID
   * @returns {Promise<Object>} Account status
   */
  async checkStatus(accountId) {
    throw new Error('Must implement checkStatus method');
  }

  /**
   * Calculate health score
   * @param {Object} account - Account data
   * @returns {number} Health score (0-100)
   */
  calculateHealthScore(account) {
    let score = 50; // Base score
    
    // Feedback score impact
    if (account.feedbackScore >= 99) score += 25;
    else if (account.feedbackScore >= 95) score += 15;
    else if (account.feedbackScore >= 90) score += 5;
    else if (account.feedbackScore < 80) score -= 20;
    
    // Activity level
    if (account.totalListings > 100) score += 10;
    if (account.totalSales > 500) score += 10;
    
    // Account age bonus
    const accountAge = this.getAccountAgeMonths(account.joinDate);
    if (accountAge > 12) score += 5;
    if (accountAge > 24) score += 5;
    
    // Penalty for violations
    if (account.violations > 0) score -= (account.violations * 10);
    
    // Performance bonus
    if (account.monthlyRevenue > 10000) score += 10;
    
    return Math.min(Math.max(score, 0), 100);
  }

  /**
   * Check account restrictions
   * @param {Object} account - Account data
   * @returns {Array<string>} List of restrictions
   */
  getAccountRestrictions(account) {
    const restrictions = [];
    
    if (account.feedbackScore < 80) {
      restrictions.push('Low feedback score - selling restrictions may apply');
    }
    
    if (account.violations > 0) {
      restrictions.push('Policy violations detected');
    }
    
    if (account.monthlyRevenue > account.monthlyLimit * 0.9) {
      restrictions.push('Approaching monthly revenue limit');
    }
    
    if (account.totalListings > account.listingLimit * 0.9) {
      restrictions.push('Approaching listing limit');
    }
    
    if (!account.paymentMethodVerified) {
      restrictions.push('Payment method verification required');
    }
    
    return restrictions;
  }

  /**
   * Get available features for account
   * @param {Object} account - Account data
   * @returns {Array<string>} Available features
   */
  getAvailableFeatures(account) {
    const features = ['basic_listing', 'basic_support'];
    
    if (account.accountType === 'business') {
      features.push('bulk_operations', 'advanced_analytics', 'priority_support');
    }
    
    if (account.accountType === 'enterprise') {
      features.push('api_access', 'dedicated_support', 'custom_integrations');
    }
    
    if (account.storeSubscription) {
      features.push('store_customization', 'listing_designer', 'traffic_reports');
    }
    
    if (account.feedbackScore >= 95) {
      features.push('trusted_seller_badge');
    }
    
    return features;
  }

  /**
   * Check if account can perform action
   * @param {Object} account - Account data
   * @param {string} action - Action to check
   * @returns {boolean} Whether action is allowed
   */
  canPerformAction(account, action) {
    const restrictions = this.getAccountRestrictions(account);
    const features = this.getAvailableFeatures(account);
    
    // High-risk actions require clean account
    if (['bulk_operations', 'high_value_listings'].includes(action)) {
      return restrictions.length === 0 && account.feedbackScore >= 90;
    }
    
    // Feature-based actions
    if (features.includes(action)) {
      return true;
    }
    
    // Default allowed actions
    const defaultAllowed = ['create_listing', 'view_orders', 'basic_support'];
    return defaultAllowed.includes(action);
  }

  /**
   * Get account age in months
   * @param {string} joinDate - Account join date
   * @returns {number} Age in months
   */
  getAccountAgeMonths(joinDate) {
    if (!joinDate) return 0;
    
    const join = new Date(joinDate);
    const now = new Date();
    return Math.floor((now - join) / (1000 * 60 * 60 * 24 * 30));
  }

  /**
   * Validate account data
   * @param {Object} account - Account data
   * @returns {Object} Validation result
   */
  validateAccount(account) {
    const errors = [];
    
    if (!account.usernameEbay) {
      errors.push('eBay username is required');
    }
    
    if (!account.accountType) {
      errors.push('Account type is required');
    }
    
    if (!account.email || !this.isValidEmail(account.email)) {
      errors.push('Valid email is required');
    }
    
    if (account.feedbackScore < 0 || account.feedbackScore > 100) {
      errors.push('Feedback score must be between 0 and 100');
    }
    
    if (!account.joinDate) {
      errors.push('Join date is required');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Validate email format
   * @param {string} email - Email to validate
   * @returns {boolean} Whether email is valid
   */
  isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }
}

export default IAccountService;