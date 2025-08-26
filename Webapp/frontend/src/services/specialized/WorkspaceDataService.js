/**
 * Workspace Data Service following Single Responsibility Principle
 * Responsible ONLY for workspace-related data operations and calculations
 */

import ListingsService from './ListingsService.js';
import OrdersService from './OrdersService.js';
import { dashboardAPI, accountsAPI } from '../api.js';

class WorkspaceDataService {
  /**
   * Get today's performance statistics
   * Single Responsibility: Only calculates today's workspace metrics
   * @returns {Promise<Object>}
   */
  async getTodayStats() {
    try {
      const [dashboardResponse, listingsResponse] = await Promise.all([
        dashboardAPI.getStats(),
        ListingsService.getAll({ page: 1, size: 1 }) // Just for total count
      ]);

      const stats = dashboardResponse.data?.data || {};
      
      return {
        success: true,
        data: {
          listingsToday: stats.daily_listings || 0,
          targetListings: 50, // This could be configurable
          avgTimePerListing: 3.2, // This would come from employee metrics API
          successRate: this.calculateSuccessRate(stats),
          weeklyListings: stats.weekly_listings || 0,
          monthlyListings: stats.monthly_listings || 0,
          totalListings: listingsResponse.total || 0
        }
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        data: this.getDefaultTodayStats()
      };
    }
  }

  /**
   * Calculate success rate from statistics
   * Single Responsibility: Only handles success rate calculation
   * @param {Object} stats - Dashboard statistics
   * @returns {number} Success rate percentage
   */
  calculateSuccessRate(stats) {
    const active = stats.active_listings || 0;
    const total = Math.max(stats.total_listings || 1, 1);
    return Math.round((active / total) * 100);
  }

  /**
   * Get work queue metrics
   * Single Responsibility: Only calculates work queue from various data sources
   * @returns {Promise<Object>}
   */
  async getWorkQueue() {
    try {
      const [
        draftsResponse,
        allListingsResponse,
        pendingOrdersResponse
      ] = await Promise.all([
        ListingsService.getDrafts({ page: 1, size: 1 }),
        ListingsService.getAll({ page: 1, size: 100 }), // Get sample for analysis
        OrdersService.getByStatus('shipped', { page: 1, size: 100 })
      ]);

      const allListings = allListingsResponse.data || [];
      const shippedOrders = pendingOrdersResponse.data || [];

      const workQueue = {
        drafts: draftsResponse.total || 0,
        pendingOptimization: this.countListingsNeedingOptimization(allListings),
        failedSyncs: this.countFailedSyncs(shippedOrders),
        missingImages: this.countMissingImages(allListings)
      };

      return {
        success: true,
        data: workQueue
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        data: this.getDefaultWorkQueue()
      };
    }
  }

  /**
   * Count listings needing optimization
   * Single Responsibility: Only handles optimization count logic
   * @param {Array} listings - Array of listings
   * @returns {number}
   */
  countListingsNeedingOptimization(listings) {
    if (!Array.isArray(listings)) return 0;
    
    return listings.filter(listing => 
      (listing.performanceScore || 0) < 70
    ).length;
  }

  /**
   * Count failed syncs from orders
   * Single Responsibility: Only handles sync failure count logic
   * @param {Array} orders - Array of orders
   * @returns {number}
   */
  countFailedSyncs(orders) {
    if (!Array.isArray(orders)) return 0;
    
    return orders.filter(order => 
      order.status === 'shipped' && 
      (!order.tracking_number || order.tracking_number === '')
    ).length;
  }

  /**
   * Count listings with missing images
   * Single Responsibility: Only handles missing image count logic
   * @param {Array} listings - Array of listings
   * @returns {number}
   */
  countMissingImages(listings) {
    if (!Array.isArray(listings)) return 0;
    
    return listings.filter(listing => 
      !listing.image || 
      listing.image.includes('placeholder') || 
      !listing.images || 
      listing.images.length === 0
    ).length;
  }

  /**
   * Get available accounts
   * Single Responsibility: Only handles account data transformation for workspace
   * @returns {Promise<Object>}
   */
  async getAccounts() {
    try {
      const response = await accountsAPI.getAll({
        page: 1,
        size: 100,
        sort_by: 'last_activity',
        sort_order: 'desc'
      });

      if (response.data?.items) {
        const transformedAccounts = response.data.items.map(account => ({
          email: account.username || account.email || `account_${account.id}`,
          status: account.status || 'active',
          syncTime: account.last_activity 
            ? new Date(account.last_activity).toLocaleString('vi-VN')
            : 'Chưa có hoạt động',
          listings: account.total_listings || 0,
          revenue: account.monthly_revenue || 0
        }));

        return {
          success: true,
          data: transformedAccounts
        };
      }

      return {
        success: true,
        data: this.getDefaultAccounts()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        data: this.getDefaultAccounts()
      };
    }
  }

  /**
   * Calculate progress percentage
   * Single Responsibility: Only handles progress calculation
   * @param {number} current - Current value
   * @param {number} target - Target value
   * @returns {number} Progress percentage
   */
  calculateProgress(current, target) {
    if (!target || target === 0) return 0;
    return Math.min((current / target) * 100, 100);
  }

  /**
   * Get total work queue items
   * Single Responsibility: Only handles queue total calculation
   * @param {Object} workQueue - Work queue object
   * @returns {number}
   */
  getTotalWorkQueueItems(workQueue) {
    return Object.values(workQueue || {}).reduce((total, count) => total + count, 0);
  }

  /**
   * Check if account is active
   * Single Responsibility: Only handles account status validation
   * @param {Object} account - Account object
   * @returns {boolean}
   */
  isAccountActive(account) {
    return account && account.status === 'active';
  }

  /**
   * Get default today stats for fallback
   * @returns {Object}
   */
  getDefaultTodayStats() {
    return {
      listingsToday: 0,
      targetListings: 50,
      avgTimePerListing: 0,
      successRate: 0,
      weeklyListings: 0,
      monthlyListings: 0,
      totalListings: 0
    };
  }

  /**
   * Get default work queue for fallback
   * @returns {Object}
   */
  getDefaultWorkQueue() {
    return {
      drafts: 0,
      pendingOptimization: 0,
      failedSyncs: 0,
      missingImages: 0
    };
  }

  /**
   * Get default accounts for fallback
   * @returns {Array}
   */
  getDefaultAccounts() {
    return [
      {
        email: 'demo_seller@ebay.com',
        status: 'active',
        syncTime: new Date().toLocaleString('vi-VN'),
        listings: 0,
        revenue: 0
      }
    ];
  }

  /**
   * Refresh workspace data
   * Single Responsibility: Only handles complete workspace data refresh
   * @returns {Promise<Object>}
   */
  async refreshWorkspaceData() {
    try {
      const [todayStats, workQueue, accounts] = await Promise.all([
        this.getTodayStats(),
        this.getWorkQueue(),
        this.getAccounts()
      ]);

      return {
        success: true,
        data: {
          todayStats: todayStats.data,
          workQueue: workQueue.data,
          accounts: accounts.data
        },
        errors: [
          ...(todayStats.success ? [] : [todayStats.error]),
          ...(workQueue.success ? [] : [workQueue.error]),
          ...(accounts.success ? [] : [accounts.error])
        ].filter(Boolean)
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        data: {
          todayStats: this.getDefaultTodayStats(),
          workQueue: this.getDefaultWorkQueue(),
          accounts: this.getDefaultAccounts()
        }
      };
    }
  }
}

// Export singleton instance
export default new WorkspaceDataService();