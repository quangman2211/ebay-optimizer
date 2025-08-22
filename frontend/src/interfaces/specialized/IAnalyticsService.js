/**
 * Analytics Service Interface (Interface Segregation Principle)
 * Focused interface ONLY for analytics operations
 */

/**
 * Analytics-specific operations interface
 * Separated from generic IDataService to follow ISP
 */
class IAnalyticsService {
  /**
   * Get dashboard metrics
   * @param {string} period - Time period (day, week, month, year)
   * @returns {Promise<Object>} Dashboard metrics
   */
  async getDashboardMetrics(period = 'month') {
    throw new Error('Must implement getDashboardMetrics method');
  }

  /**
   * Get revenue analytics
   * @param {string} period - Time period
   * @param {Object} filters - Analytics filters
   * @returns {Promise<Object>} Revenue analytics data
   */
  async getRevenueAnalytics(period = 'month', filters = {}) {
    throw new Error('Must implement getRevenueAnalytics method');
  }

  /**
   * Get performance trends
   * @param {string} metric - Metric to analyze
   * @param {string} period - Time period
   * @returns {Promise<Object>} Trend data
   */
  async getPerformanceTrends(metric, period = 'month') {
    throw new Error('Must implement getPerformanceTrends method');
  }

  /**
   * Get category analytics
   * @param {Object} params - Analytics parameters
   * @returns {Promise<Object>} Category analytics
   */
  async getCategoryAnalytics(params = {}) {
    throw new Error('Must implement getCategoryAnalytics method');
  }

  /**
   * Generate analytics report
   * @param {string} reportType - Type of report
   * @param {Object} options - Report options
   * @returns {Promise<Object>} Generated report
   */
  async generateReport(reportType, options = {}) {
    throw new Error('Must implement generateReport method');
  }

  /**
   * Calculate growth rate
   * @param {number} currentValue - Current period value
   * @param {number} previousValue - Previous period value
   * @returns {number} Growth rate percentage
   */
  calculateGrowthRate(currentValue, previousValue) {
    if (previousValue === 0) return currentValue > 0 ? 100 : 0;
    return ((currentValue - previousValue) / previousValue) * 100;
  }

  /**
   * Calculate conversion rate
   * @param {number} conversions - Number of conversions
   * @param {number} total - Total opportunities
   * @returns {number} Conversion rate percentage
   */
  calculateConversionRate(conversions, total) {
    if (total === 0) return 0;
    return (conversions / total) * 100;
  }

  /**
   * Calculate average order value
   * @param {number} totalRevenue - Total revenue
   * @param {number} totalOrders - Total number of orders
   * @returns {number} Average order value
   */
  calculateAverageOrderValue(totalRevenue, totalOrders) {
    if (totalOrders === 0) return 0;
    return totalRevenue / totalOrders;
  }

  /**
   * Calculate profit margin
   * @param {number} revenue - Total revenue
   * @param {number} costs - Total costs
   * @returns {number} Profit margin percentage
   */
  calculateProfitMargin(revenue, costs) {
    if (revenue === 0) return 0;
    return ((revenue - costs) / revenue) * 100;
  }

  /**
   * Get top performing items
   * @param {Array} items - Items to analyze
   * @param {string} metric - Metric to sort by
   * @param {number} limit - Number of items to return
   * @returns {Array} Top performing items
   */
  getTopPerformingItems(items, metric = 'revenue', limit = 10) {
    if (!Array.isArray(items)) return [];
    
    return items
      .sort((a, b) => (b[metric] || 0) - (a[metric] || 0))
      .slice(0, limit);
  }

  /**
   * Calculate performance score
   * @param {Object} metrics - Performance metrics
   * @returns {number} Performance score (0-100)
   */
  calculatePerformanceScore(metrics) {
    let score = 0;
    let factors = 0;
    
    // Revenue performance (weight: 30)
    if (metrics.revenue !== undefined) {
      const revenueScore = Math.min(metrics.revenue / 10000 * 100, 100);
      score += revenueScore * 0.3;
      factors += 0.3;
    }
    
    // Order volume performance (weight: 25)
    if (metrics.orders !== undefined) {
      const orderScore = Math.min(metrics.orders / 100 * 100, 100);
      score += orderScore * 0.25;
      factors += 0.25;
    }
    
    // Conversion rate performance (weight: 20)
    if (metrics.conversionRate !== undefined) {
      const conversionScore = Math.min(metrics.conversionRate * 10, 100);
      score += conversionScore * 0.2;
      factors += 0.2;
    }
    
    // Customer satisfaction (weight: 15)
    if (metrics.feedbackScore !== undefined) {
      score += metrics.feedbackScore * 0.15;
      factors += 0.15;
    }
    
    // Growth rate (weight: 10)
    if (metrics.growthRate !== undefined) {
      const growthScore = Math.min(Math.max(metrics.growthRate + 50, 0), 100);
      score += growthScore * 0.1;
      factors += 0.1;
    }
    
    return factors > 0 ? Math.round(score / factors) : 0;
  }

  /**
   * Generate insights from data
   * @param {Object} data - Analytics data
   * @returns {Array<Object>} Generated insights
   */
  generateInsights(data) {
    const insights = [];
    
    // Revenue insights
    if (data.revenue && data.previousRevenue) {
      const growthRate = this.calculateGrowthRate(data.revenue, data.previousRevenue);
      if (growthRate > 20) {
        insights.push({
          type: 'positive',
          category: 'revenue',
          message: `Revenue grew by ${growthRate.toFixed(1)}% compared to previous period`,
          impact: 'high'
        });
      } else if (growthRate < -10) {
        insights.push({
          type: 'warning',
          category: 'revenue',
          message: `Revenue declined by ${Math.abs(growthRate).toFixed(1)}% compared to previous period`,
          impact: 'high'
        });
      }
    }
    
    // Conversion rate insights
    if (data.conversionRate) {
      if (data.conversionRate > 10) {
        insights.push({
          type: 'positive',
          category: 'conversion',
          message: `Excellent conversion rate of ${data.conversionRate.toFixed(1)}%`,
          impact: 'medium'
        });
      } else if (data.conversionRate < 2) {
        insights.push({
          type: 'warning',
          category: 'conversion',
          message: `Low conversion rate of ${data.conversionRate.toFixed(1)}% - consider optimizing listings`,
          impact: 'high'
        });
      }
    }
    
    // Order volume insights
    if (data.orders && data.previousOrders) {
      const orderGrowth = this.calculateGrowthRate(data.orders, data.previousOrders);
      if (orderGrowth > 30) {
        insights.push({
          type: 'positive',
          category: 'orders',
          message: `Order volume increased by ${orderGrowth.toFixed(1)}%`,
          impact: 'medium'
        });
      }
    }
    
    return insights;
  }

  /**
   * Format analytics data for visualization
   * @param {Object} rawData - Raw analytics data
   * @param {string} chartType - Type of chart (line, bar, pie, etc.)
   * @returns {Object} Formatted chart data
   */
  formatForChart(rawData, chartType = 'line') {
    if (!rawData) return null;
    
    switch (chartType) {
      case 'line':
        return {
          labels: rawData.labels || [],
          datasets: [{
            label: rawData.label || 'Data',
            data: rawData.values || [],
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4
          }]
        };
        
      case 'bar':
        return {
          labels: rawData.labels || [],
          datasets: [{
            label: rawData.label || 'Data',
            data: rawData.values || [],
            backgroundColor: 'rgba(102, 126, 234, 0.8)',
            borderColor: '#667eea',
            borderWidth: 1
          }]
        };
        
      case 'pie':
        return {
          labels: rawData.labels || [],
          datasets: [{
            data: rawData.values || [],
            backgroundColor: [
              '#667eea', '#764ba2', '#f093fb', '#f5576c',
              '#4facfe', '#00f2fe', '#43e97b', '#38f9d7'
            ]
          }]
        };
        
      default:
        return rawData;
    }
  }
}

export default IAnalyticsService;