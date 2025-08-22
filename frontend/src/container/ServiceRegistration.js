/**
 * Service Registration (Dependency Inversion Principle)
 * Configures all services in the dependency injection container
 */

import ServiceContainer from './ServiceContainer.js';

// Import service implementations
import BaseAPIService from '../services/base/BaseAPIService.js';
import ListingsService from '../services/specialized/ListingsService.js';
import OrdersService from '../services/specialized/OrdersService.js';
import WorkspaceDataService from '../services/specialized/WorkspaceDataService.js';

// Import strategy implementations
import OptimizationStrategyFactory from '../strategies/optimization/OptimizationStrategy.js';
import AccountStrategyFactory from '../strategies/accounts/AccountStrategy.js';

// Import API
import api from '../services/api.js';

/**
 * Register all services in the container
 * Following Dependency Inversion Principle
 */
export function registerServices(container = ServiceContainer) {
  // Bootstrap basic services
  container.bootstrap();

  // Register API service
  container.registerSingleton('api', api);

  // Register base services
  container.registerSingleton('baseAPIService', BaseAPIService, {
    dependencies: ['api']
  });

  // Register specialized services with dependencies
  container.registerSingleton('listingsService', () => {
    return new ListingsService();
  }, {
    factory: true
  });

  container.registerSingleton('ordersService', () => {
    return new OrdersService();
  }, {
    factory: true
  });

  container.registerSingleton('workspaceDataService', () => {
    return new WorkspaceDataService();
  }, {
    factory: true,
    dependencies: ['listingsService', 'ordersService']
  });

  // Register strategy factories
  container.registerSingleton('optimizationStrategyFactory', OptimizationStrategyFactory);
  container.registerSingleton('accountStrategyFactory', AccountStrategyFactory);

  // Register dashboard service
  container.registerSingleton('dashboardService', () => {
    return createDashboardService(container);
  }, {
    factory: true,
    dependencies: ['listingsService', 'ordersService', 'workspaceDataService']
  });

  // Register notification service
  container.registerSingleton('notificationService', () => {
    return createNotificationService(container);
  }, {
    factory: true,
    dependencies: ['eventBus', 'logger']
  });

  // Register analytics service
  container.registerSingleton('analyticsService', () => {
    return createAnalyticsService(container);
  }, {
    factory: true,
    dependencies: ['listingsService', 'ordersService', 'logger']
  });

  // Register account service
  container.registerSingleton('accountService', () => {
    return createAccountService(container);
  }, {
    factory: true,
    dependencies: ['accountStrategyFactory', 'logger']
  });

  return container;
}

/**
 * Create dashboard service with injected dependencies
 */
function createDashboardService(container) {
  const listingsService = container.resolve('listingsService');
  const ordersService = container.resolve('ordersService');
  const workspaceDataService = container.resolve('workspaceDataService');
  const logger = container.resolve('logger');

  return {
    async getDashboardData() {
      try {
        logger.info('Fetching dashboard data...');
        
        const [listings, orders, workspaceMetrics] = await Promise.all([
          listingsService.getAll(),
          ordersService.getAll(),
          workspaceDataService.getWorkspaceMetrics()
        ]);

        return {
          success: true,
          data: {
            listings: listings.data || [],
            orders: orders.data || [],
            metrics: workspaceMetrics.data || {},
            totalListings: listings.total || 0,
            totalOrders: orders.total || 0
          }
        };
      } catch (error) {
        logger.error('Failed to fetch dashboard data:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    async getQuickStats() {
      try {
        const [ordersResponse, listingsResponse] = await Promise.all([
          ordersService.getAll({ limit: 1000 }),
          listingsService.getAll({ limit: 1000 })
        ]);

        const orders = ordersResponse.data || [];
        const listings = listingsResponse.data || [];

        const totalRevenue = orders.reduce((sum, order) => sum + (order.netEB || 0), 0);
        const totalProfit = orders.reduce((sum, order) => sum + (order.profit || 0), 0);
        const pendingOrders = orders.filter(order => order.status === 'pending').length;
        const activeListings = listings.filter(listing => listing.status === 'active').length;

        return {
          success: true,
          data: {
            totalRevenue,
            totalProfit,
            pendingOrders,
            activeListings,
            totalOrders: orders.length,
            totalListings: listings.length
          }
        };
      } catch (error) {
        logger.error('Failed to fetch quick stats:', error);
        return {
          success: false,
          error: error.message,
          data: {
            totalRevenue: 0,
            totalProfit: 0,
            pendingOrders: 0,
            activeListings: 0,
            totalOrders: 0,
            totalListings: 0
          }
        };
      }
    }
  };
}

/**
 * Create notification service with injected dependencies
 */
function createNotificationService(container) {
  const eventBus = container.resolve('eventBus');
  const logger = container.resolve('logger');

  return {
    async send(message, recipient, options = {}) {
      try {
        logger.info(`Sending notification to ${recipient}: ${message}`);
        
        const notification = {
          id: Date.now().toString(),
          message,
          recipient,
          timestamp: new Date(),
          type: options.type || 'info',
          ...options
        };

        // Emit notification event
        eventBus.emit('notification:sent', notification);

        return {
          success: true,
          data: notification
        };
      } catch (error) {
        logger.error('Failed to send notification:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    async sendBulk(notifications) {
      try {
        const results = await Promise.all(
          notifications.map(notif => this.send(notif.message, notif.recipient, notif.options))
        );

        return {
          success: true,
          data: {
            sent: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length,
            results
          }
        };
      } catch (error) {
        logger.error('Failed to send bulk notifications:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    getServiceName() {
      return 'NotificationService';
    }
  };
}

/**
 * Create analytics service with injected dependencies
 */
function createAnalyticsService(container) {
  const listingsService = container.resolve('listingsService');
  const ordersService = container.resolve('ordersService');
  const logger = container.resolve('logger');

  return {
    async getDashboardMetrics(period = 'month') {
      try {
        logger.info(`Fetching dashboard metrics for period: ${period}`);
        
        const [ordersResponse, listingsResponse] = await Promise.all([
          ordersService.getAll(),
          listingsService.getAll()
        ]);

        const orders = ordersResponse.data || [];
        const listings = listingsResponse.data || [];

        // Calculate metrics
        const totalRevenue = orders.reduce((sum, order) => sum + (order.netEB || 0), 0);
        const totalOrders = orders.length;
        const averageOrderValue = totalOrders > 0 ? totalRevenue / totalOrders : 0;
        const conversionRate = listings.length > 0 ? (totalOrders / listings.length) * 100 : 0;

        return {
          success: true,
          data: {
            totalRevenue,
            totalOrders,
            averageOrderValue,
            conversionRate,
            totalListings: listings.length,
            period
          }
        };
      } catch (error) {
        logger.error('Failed to fetch dashboard metrics:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    async getRevenueAnalytics(period = 'month', filters = {}) {
      try {
        const ordersResponse = await ordersService.getAll(filters);
        const orders = ordersResponse.data || [];

        // Group by time period
        const revenueByDate = this.groupOrdersByDate(orders, period);

        return {
          success: true,
          data: {
            revenueByDate,
            totalRevenue: orders.reduce((sum, order) => sum + (order.netEB || 0), 0),
            period
          }
        };
      } catch (error) {
        logger.error('Failed to fetch revenue analytics:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    groupOrdersByDate(orders, period) {
      // Simple grouping implementation
      const grouped = {};
      
      orders.forEach(order => {
        const date = new Date(order.orderDate).toISOString().split('T')[0];
        if (!grouped[date]) {
          grouped[date] = 0;
        }
        grouped[date] += order.netEB || 0;
      });

      return grouped;
    }
  };
}

/**
 * Create account service with injected dependencies
 */
function createAccountService(container) {
  const accountStrategyFactory = container.resolve('accountStrategyFactory');
  const logger = container.resolve('logger');

  return {
    async processAccount(account) {
      try {
        logger.info(`Processing account: ${account.usernameEbay}`);
        
        const result = accountStrategyFactory.processAccount(account);
        
        return {
          success: true,
          data: result
        };
      } catch (error) {
        logger.error('Failed to process account:', error);
        return {
          success: false,
          error: error.message
        };
      }
    },

    async getAccountCapabilities(account) {
      try {
        const capabilities = accountStrategyFactory.getAccountCapabilities(account);
        
        return {
          success: true,
          data: capabilities
        };
      } catch (error) {
        logger.error('Failed to get account capabilities:', error);
        return {
          success: false,
          error: error.message
        };
      }
    }
  };
}

/**
 * Initialize and configure the service container
 */
export function initializeContainer() {
  const container = ServiceContainer.clear();
  registerServices(container);
  
  // Validate container configuration
  const validation = container.validate();
  
  if (!validation.valid) {
    console.error('Service container validation failed:', validation.errors);
    throw new Error('Invalid service container configuration');
  }
  
  if (validation.warnings.length > 0) {
    console.warn('Service container warnings:', validation.warnings);
  }
  
  console.log('Service container initialized successfully');
  console.log('Registered services:', container.getServiceNames());
  
  return container;
}

// Auto-initialize container
export default initializeContainer();