/**
 * Listing Service Interface (Interface Segregation Principle)
 * Focused interface ONLY for listing operations
 */

/**
 * Listing-specific operations interface
 * Separated from generic IDataService to follow ISP
 */
class IListingService {
  /**
   * Optimize listing title
   * @param {string} title - Original title
   * @param {Object} options - Optimization options
   * @returns {Promise<Object>} Optimized title result
   */
  async optimizeTitle(title, options = {}) {
    throw new Error('Must implement optimizeTitle method');
  }

  /**
   * Generate description
   * @param {Object} listing - Listing data
   * @param {string} template - Description template
   * @returns {Promise<Object>} Generated description
   */
  async generateDescription(listing, template = 'default') {
    throw new Error('Must implement generateDescription method');
  }

  /**
   * Extract keywords
   * @param {Object} listing - Listing data
   * @returns {Promise<Array<string>>} Extracted keywords
   */
  async extractKeywords(listing) {
    throw new Error('Must implement extractKeywords method');
  }

  /**
   * Calculate SEO score
   * @param {Object} listing - Listing data
   * @returns {Promise<number>} SEO score (0-100)
   */
  async calculateSEOScore(listing) {
    throw new Error('Must implement calculateSEOScore method');
  }

  /**
   * Get category suggestions
   * @param {Object} listing - Listing data
   * @returns {Promise<Array<string>>} Category suggestions
   */
  async getCategorySuggestions(listing) {
    throw new Error('Must implement getCategorySuggestions method');
  }

  /**
   * Validate listing data
   * @param {Object} listing - Listing data
   * @returns {Object} Validation result
   */
  validateListing(listing) {
    const errors = [];
    
    if (!listing.title || listing.title.length === 0) {
      errors.push('Title is required');
    }
    
    if (!listing.description || listing.description.length === 0) {
      errors.push('Description is required');
    }
    
    if (!listing.currentPrice || listing.currentPrice <= 0) {
      errors.push('Price must be greater than 0');
    }
    
    if (!listing.category) {
      errors.push('Category is required');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
}

export default IListingService;