/**
 * Account Strategy Pattern (Open/Closed Principle)
 * Open for extension: Can add new account types
 * Closed for modification: Existing account handlers don't need changes
 */

/**
 * Base Account Handler Interface
 * All account handlers must implement this interface
 */
class AccountHandler {
  /**
   * Handle account-specific operations
   * @param {Object} account - Account data
   * @returns {Object} Account configuration
   */
  handle(account) {
    throw new Error('Must implement handle method');
  }

  /**
   * Get account type name
   * @returns {string} Account type name
   */
  getType() {
    throw new Error('Must implement getType method');
  }

  /**
   * Get account limits
   * @param {Object} account - Account data
   * @returns {Object} Account limits
   */
  getLimits(account) {
    throw new Error('Must implement getLimits method');
  }

  /**
   * Get available features
   * @param {Object} account - Account data
   * @returns {Array<string>} Available features
   */
  getFeatures(account) {
    throw new Error('Must implement getFeatures method');
  }

  /**
   * Calculate health score
   * @param {Object} account - Account data
   * @returns {number} Health score (0-100)
   */
  calculateHealthScore(account) {
    throw new Error('Must implement calculateHealthScore method');
  }

  /**
   * Check if account can perform action
   * @param {Object} account - Account data
   * @param {string} action - Action to check
   * @returns {boolean} Whether action is allowed
   */
  canPerformAction(account, action) {
    return true; // Default: allow all actions
  }
}

/**
 * Personal Account Handler
 * Handles individual/personal eBay accounts
 */
class PersonalAccountHandler extends AccountHandler {
  getType() {
    return 'personal';
  }

  handle(account) {
    return {
      type: this.getType(),
      limits: this.getLimits(account),
      features: this.getFeatures(account),
      healthScore: this.calculateHealthScore(account),
      restrictions: this.getRestrictions(account),
      supportLevel: 'basic'
    };
  }

  getLimits(account) {
    return {
      monthlyListings: 100,
      monthlyRevenue: 5000,
      dailyListings: 10,
      maxImageSize: 5, // MB
      maxItemValue: 2000,
      categories: ['Electronics', 'Fashion', 'Home & Garden', 'Sports'],
      internationalSelling: false
    };
  }

  getFeatures(account) {
    return [
      'basic_listing',
      'basic_analytics',
      'standard_support',
      'mobile_app',
      'basic_templates',
      'standard_shipping'
    ];
  }

  calculateHealthScore(account) {
    let score = 50; // Base score for personal accounts

    // Feedback score impact
    if (account.feedbackScore >= 99) score += 25;
    else if (account.feedbackScore >= 95) score += 15;
    else if (account.feedbackScore >= 90) score += 5;

    // Activity level
    if (account.totalListings > 50) score += 10;
    if (account.totalSales > 100) score += 10;

    // Account age (simulate based on join date)
    const accountAge = this.getAccountAgeMonths(account.joinDate);
    if (accountAge > 12) score += 5;

    return Math.min(score, 100);
  }

  getRestrictions(account) {
    return [
      'No bulk operations',
      'Limited listing templates',
      'Standard customer support only',
      'No advanced analytics'
    ];
  }

  canPerformAction(account, action) {
    const restrictedActions = ['bulk_operations', 'advanced_analytics', 'priority_support'];
    return !restrictedActions.includes(action);
  }

  getAccountAgeMonths(joinDate) {
    if (!joinDate) return 0;
    const join = new Date(joinDate);
    const now = new Date();
    return Math.floor((now - join) / (1000 * 60 * 60 * 24 * 30));
  }
}

/**
 * Business Account Handler
 * Handles business eBay accounts
 */
class BusinessAccountHandler extends AccountHandler {
  getType() {
    return 'business';
  }

  handle(account) {
    return {
      type: this.getType(),
      limits: this.getLimits(account),
      features: this.getFeatures(account),
      healthScore: this.calculateHealthScore(account),
      restrictions: this.getRestrictions(account),
      supportLevel: 'premium'
    };
  }

  getLimits(account) {
    return {
      monthlyListings: 1000,
      monthlyRevenue: 50000,
      dailyListings: 50,
      maxImageSize: 10, // MB
      maxItemValue: 10000,
      categories: 'all', // All categories available
      internationalSelling: true
    };
  }

  getFeatures(account) {
    return [
      'advanced_listing',
      'bulk_operations',
      'advanced_analytics',
      'priority_support',
      'mobile_app',
      'custom_templates',
      'expedited_shipping',
      'inventory_management',
      'automated_pricing',
      'competitor_analysis'
    ];
  }

  calculateHealthScore(account) {
    let score = 70; // Higher base score for business accounts

    // Feedback score impact (more important for business)
    if (account.feedbackScore >= 99) score += 20;
    else if (account.feedbackScore >= 95) score += 10;
    else if (account.feedbackScore >= 90) score += 5;

    // Revenue performance
    if (account.monthlyRevenue > 10000) score += 10;
    if (account.monthlyRevenue > 25000) score += 5;

    // Listing performance
    if (account.totalListings > 500) score += 5;

    return Math.min(score, 100);
  }

  getRestrictions(account) {
    const restrictions = [];
    
    // Add restrictions based on performance
    if (account.feedbackScore < 95) {
      restrictions.push('Limited high-value item listings');
    }
    
    if (account.monthlyRevenue < 1000) {
      restrictions.push('Reduced international shipping options');
    }

    return restrictions;
  }

  canPerformAction(account, action) {
    // Business accounts can perform most actions
    const restrictedActions = [];
    
    // Restrict based on performance
    if (account.feedbackScore < 90) {
      restrictedActions.push('high_value_listings');
    }

    return !restrictedActions.includes(action);
  }
}

/**
 * Enterprise Account Handler
 * Handles large-scale enterprise eBay accounts
 */
class EnterpriseAccountHandler extends AccountHandler {
  getType() {
    return 'enterprise';
  }

  handle(account) {
    return {
      type: this.getType(),
      limits: this.getLimits(account),
      features: this.getFeatures(account),
      healthScore: this.calculateHealthScore(account),
      restrictions: this.getRestrictions(account),
      supportLevel: 'enterprise'
    };
  }

  getLimits(account) {
    return {
      monthlyListings: -1, // Unlimited
      monthlyRevenue: -1, // Unlimited
      dailyListings: -1, // Unlimited
      maxImageSize: 50, // MB
      maxItemValue: -1, // Unlimited
      categories: 'all',
      internationalSelling: true
    };
  }

  getFeatures(account) {
    return [
      'all_features',
      'custom_integrations',
      'dedicated_support',
      'api_access',
      'white_label_solutions',
      'multi_channel_selling',
      'advanced_reporting',
      'custom_workflows',
      'bulk_operations',
      'automated_repricing',
      'inventory_sync',
      'order_management_system'
    ];
  }

  calculateHealthScore(account) {
    let score = 80; // High base score for enterprise

    // Enterprise accounts should maintain high standards
    if (account.feedbackScore >= 99.5) score += 15;
    else if (account.feedbackScore >= 98) score += 10;
    else if (account.feedbackScore < 95) score -= 20; // Penalty for low feedback

    // Volume metrics
    if (account.monthlyRevenue > 100000) score += 5;
    if (account.totalListings > 5000) score += 5;

    return Math.min(Math.max(score, 0), 100);
  }

  getRestrictions(account) {
    const restrictions = [];
    
    // Enterprise accounts have higher standards
    if (account.feedbackScore < 98) {
      restrictions.push('Account review required for full features');
    }

    if (account.monthlyRevenue < 10000) {
      restrictions.push('Enterprise features under evaluation');
    }

    return restrictions;
  }

  canPerformAction(account, action) {
    // Enterprise accounts can perform all actions unless there are serious issues
    if (account.feedbackScore < 95) {
      return !['high_risk_operations', 'bulk_international_shipping'].includes(action);
    }
    
    return true; // Can perform all actions
  }
}

/**
 * Store Account Handler
 * Handles eBay Store accounts with subscriptions
 */
class StoreAccountHandler extends AccountHandler {
  getType() {
    return 'store';
  }

  handle(account) {
    const storeLevel = this.getStoreLevel(account);
    
    return {
      type: this.getType(),
      storeLevel: storeLevel,
      limits: this.getLimits(account, storeLevel),
      features: this.getFeatures(account, storeLevel),
      healthScore: this.calculateHealthScore(account),
      restrictions: this.getRestrictions(account, storeLevel),
      supportLevel: this.getSupportLevel(storeLevel),
      subscriptionFee: this.getSubscriptionFee(storeLevel)
    };
  }

  getStoreLevel(account) {
    // Determine store level based on metrics
    if (account.monthlyRevenue > 10000) return 'anchor';
    if (account.monthlyRevenue > 5000) return 'premium';
    if (account.monthlyRevenue > 1000) return 'basic';
    return 'starter';
  }

  getLimits(account, storeLevel = 'basic') {
    const limits = {
      starter: {
        monthlyListings: 250,
        monthlyRevenue: 25000,
        dailyListings: 25,
        freeListings: 250
      },
      basic: {
        monthlyListings: 500,
        monthlyRevenue: 50000,
        dailyListings: 50,
        freeListings: 250
      },
      premium: {
        monthlyListings: 2500,
        monthlyRevenue: 100000,
        dailyListings: 100,
        freeListings: 1000
      },
      anchor: {
        monthlyListings: 25000,
        monthlyRevenue: 500000,
        dailyListings: 500,
        freeListings: 25000
      }
    };

    return {
      ...limits[storeLevel],
      maxImageSize: 15,
      maxItemValue: 25000,
      categories: 'all',
      internationalSelling: true
    };
  }

  getFeatures(account, storeLevel = 'basic') {
    const baseFeatures = [
      'store_customization',
      'listing_designer',
      'selling_manager',
      'traffic_reports'
    ];

    const levelFeatures = {
      starter: [...baseFeatures],
      basic: [
        ...baseFeatures,
        'markdown_manager',
        'promoted_listings',
        'vacation_settings'
      ],
      premium: [
        ...baseFeatures,
        'markdown_manager',
        'promoted_listings',
        'vacation_settings',
        'selling_manager_pro',
        'advanced_reports',
        'automated_feedback'
      ],
      anchor: [
        ...baseFeatures,
        'markdown_manager',
        'promoted_listings',
        'vacation_settings',
        'selling_manager_pro',
        'advanced_reports',
        'automated_feedback',
        'dedicated_support',
        'api_access',
        'bulk_tools'
      ]
    };

    return levelFeatures[storeLevel] || levelFeatures.basic;
  }

  calculateHealthScore(account) {
    let score = 60; // Base score for store accounts

    // Store performance metrics
    if (account.feedbackScore >= 99) score += 20;
    else if (account.feedbackScore >= 95) score += 10;

    // Revenue consistency
    if (account.monthlyRevenue > 5000) score += 15;
    if (account.monthlyRevenue > 15000) score += 10;

    // Store level bonus
    const storeLevel = this.getStoreLevel(account);
    const bonuses = { starter: 0, basic: 5, premium: 10, anchor: 15 };
    score += bonuses[storeLevel] || 0;

    return Math.min(score, 100);
  }

  getRestrictions(account, storeLevel = 'basic') {
    const restrictions = [];

    if (storeLevel === 'starter') {
      restrictions.push('Limited customization options');
      restrictions.push('Basic reporting only');
    }

    if (account.feedbackScore < 95) {
      restrictions.push('Store features under review');
    }

    return restrictions;
  }

  getSupportLevel(storeLevel) {
    const supportLevels = {
      starter: 'standard',
      basic: 'priority',
      premium: 'premium',
      anchor: 'dedicated'
    };

    return supportLevels[storeLevel] || 'standard';
  }

  getSubscriptionFee(storeLevel) {
    const fees = {
      starter: 4.95,
      basic: 21.95,
      premium: 59.95,
      anchor: 349.95
    };

    return fees[storeLevel] || 0;
  }
}

/**
 * Account Strategy Factory
 * Manages account handler creation and selection
 */
class AccountStrategyFactory {
  constructor() {
    this.handlers = new Map();
    
    // Register default handlers
    this.register(new PersonalAccountHandler());
    this.register(new BusinessAccountHandler());
    this.register(new EnterpriseAccountHandler());
    this.register(new StoreAccountHandler());
  }

  /**
   * Register new account handler
   * Open for extension: Can add new account types without modifying existing code
   * @param {AccountHandler} handler - Handler instance
   */
  register(handler) {
    if (!(handler instanceof AccountHandler)) {
      throw new Error('Handler must extend AccountHandler');
    }
    
    this.handlers.set(handler.getType(), handler);
  }

  /**
   * Get handler by type
   * @param {string} type - Account type
   * @returns {AccountHandler|null}
   */
  getHandler(type) {
    return this.handlers.get(type) || null;
  }

  /**
   * Get all available handlers
   * @returns {Array<AccountHandler>}
   */
  getAllHandlers() {
    return Array.from(this.handlers.values());
  }

  /**
   * Determine account type from account data
   * @param {Object} account - Account data
   * @returns {string} Account type
   */
  determineAccountType(account) {
    // Logic to determine account type based on account data
    if (account.storeSubscription) return 'store';
    if (account.monthlyRevenue > 100000 || account.totalListings > 5000) return 'enterprise';
    if (account.monthlyRevenue > 5000 || account.totalListings > 100) return 'business';
    return 'personal';
  }

  /**
   * Process account with appropriate handler
   * @param {Object} account - Account data
   * @returns {Object} Processed account configuration
   */
  processAccount(account) {
    const accountType = account.type || this.determineAccountType(account);
    const handler = this.getHandler(accountType);
    
    if (!handler) {
      throw new Error(`No handler found for account type: ${accountType}`);
    }
    
    return handler.handle(account);
  }

  /**
   * Get account capabilities
   * @param {Object} account - Account data
   * @returns {Object} Account capabilities
   */
  getAccountCapabilities(account) {
    const processed = this.processAccount(account);
    
    return {
      type: processed.type,
      limits: processed.limits,
      features: processed.features,
      healthScore: processed.healthScore,
      supportLevel: processed.supportLevel,
      canPerformActions: this.getActionCapabilities(account, processed.type)
    };
  }

  /**
   * Get action capabilities for account
   * @param {Object} account - Account data
   * @param {string} accountType - Account type
   * @returns {Object} Action capabilities
   */
  getActionCapabilities(account, accountType) {
    const handler = this.getHandler(accountType);
    if (!handler) return {};

    const actions = [
      'create_listing',
      'bulk_operations',
      'advanced_analytics',
      'api_access',
      'priority_support',
      'international_selling',
      'high_value_listings'
    ];

    const capabilities = {};
    actions.forEach(action => {
      capabilities[action] = handler.canPerformAction(account, action);
    });

    return capabilities;
  }
}

// Export classes and factory
export {
  AccountHandler,
  PersonalAccountHandler,
  BusinessAccountHandler,
  EnterpriseAccountHandler,
  StoreAccountHandler,
  AccountStrategyFactory
};

// Export default factory instance
export default new AccountStrategyFactory();