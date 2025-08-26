/**
 * Data Service Interface (Liskov Substitution Principle)
 * All data services must implement this interface to ensure consistent behavior
 */

/**
 * Base Data Service Interface
 * Defines the contract that all data services must follow
 */
class IDataService {
  /**
   * Fetch data with parameters
   * @param {Object} params - Query parameters
   * @returns {Promise<Object>} Normalized response
   */
  async fetchData(params = {}) {
    throw new Error('Must implement fetchData method');
  }

  /**
   * Save data
   * @param {Object} data - Data to save
   * @returns {Promise<Object>} Save result
   */
  async saveData(data) {
    throw new Error('Must implement saveData method');
  }

  /**
   * Update existing data
   * @param {string|number} id - Data ID
   * @param {Object} data - Updated data
   * @returns {Promise<Object>} Update result
   */
  async updateData(id, data) {
    throw new Error('Must implement updateData method');
  }

  /**
   * Delete data
   * @param {string|number} id - Data ID
   * @returns {Promise<Object>} Delete result
   */
  async deleteData(id) {
    throw new Error('Must implement deleteData method');
  }

  /**
   * Get data by ID
   * @param {string|number} id - Data ID
   * @returns {Promise<Object>} Data item
   */
  async getById(id) {
    throw new Error('Must implement getById method');
  }

  /**
   * Search data
   * @param {string} query - Search query
   * @param {Object} params - Additional parameters
   * @returns {Promise<Object>} Search results
   */
  async search(query, params = {}) {
    throw new Error('Must implement search method');
  }

  /**
   * Get service name
   * @returns {string} Service name
   */
  getServiceName() {
    throw new Error('Must implement getServiceName method');
  }

  /**
   * Validate data before operations
   * @param {Object} data - Data to validate
   * @returns {Object} Validation result
   */
  validateData(data) {
    return { valid: true, errors: [] };
  }

  /**
   * Transform data for consistent format
   * @param {Object} rawData - Raw data from source
   * @returns {Object} Transformed data
   */
  transformData(rawData) {
    return rawData;
  }
}

export default IDataService;