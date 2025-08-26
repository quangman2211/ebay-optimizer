/**
 * Google Sheets Writer Module
 * Writes eBay data directly to Google Sheets
 */

import { SHEET_STRUCTURE } from './sheets-config.js';

/**
 * CSV to Google Sheets Processor
 * Handles CSV data transformation and writing to sheets
 */
class CSVToSheetsProcessor {
  constructor() {
    this.fieldMapping = {
      orders: {
        'Sales Record Number': 'A',
        'Order Number': 'B', 
        'Buyer Username': 'C',
        'Buyer Name': 'D',
        'Buyer Email': 'E',
        'Item Number': 'F',
        'Item Title': 'G',
        'Custom Label': 'H',
        'Quantity': 'I',
        'Sold For': 'J',
        'Total Price': 'K',
        'Sale Date': 'L',
        'Paid On Date': 'M',
        'Ship By Date': 'N',
        'Tracking Number': 'O',
        'Status': 'P',
        'Account': 'Q',
        'Last Updated': 'R'
      },
      listings: {
        'Item number': 'A',
        'Title': 'B',
        'Custom label (SKU)': 'C',
        'Available quantity': 'D',
        'Current price': 'E',
        'Sold quantity': 'F',
        'Watchers': 'G',
        'Start date': 'H',
        'End date': 'I',
        'Condition': 'J',
        'Status': 'K',
        'Account': 'L',
        'Last Updated': 'M'
      }
    };
  }

  /**
   * Process CSV data and prepare for Google Sheets
   */
  processCSVData(data, type, account) {
    const processedData = data.map(record => {
      const row = {};
      
      // Add metadata
      row.account = account.name || 'Unknown Account';
      row.last_updated = new Date().toISOString();
      row.status = type === 'orders' ? 'awaiting_shipment' : 'active';
      
      // Map fields based on type
      if (type === 'orders') {
        row.sales_record_number = record['Sales Record Number'] || '';
        row.order_number = record['Order Number'] || '';
        row.buyer_username = record['Buyer Username'] || '';
        row.buyer_name = record['Buyer Name'] || '';
        row.buyer_email = record['Buyer Email'] || '';
        row.item_number = record['Item Number'] || '';
        row.item_title = record['Item Title'] || '';
        row.custom_label = record['Custom Label'] || '';
        row.quantity = this.parseNumber(record['Quantity']);
        row.sold_for = this.parseCurrency(record['Sold For']);
        row.total_price = this.parseCurrency(record['Total Price']);
        row.sale_date = this.formatDate(record['Sale Date']);
        row.paid_date = this.formatDate(record['Paid On Date']);
        row.ship_by_date = this.formatDate(record['Ship By Date']);
        row.tracking_number = record['Tracking Number'] || '';
      } else if (type === 'listings') {
        row.item_number = record['Item number'] || '';
        row.title = record['Title'] || '';
        row.custom_label = record['Custom label (SKU)'] || '';
        row.available_quantity = this.parseNumber(record['Available quantity']);
        row.current_price = this.parseCurrency(record['Current price']);
        row.sold_quantity = this.parseNumber(record['Sold quantity']);
        row.watchers = this.parseNumber(record['Watchers']);
        row.start_date = this.formatDate(record['Start date']);
        row.end_date = this.formatDate(record['End date']);
        row.condition = record['Condition'] || '';
      }
      
      return row;
    });

    return this.formatForSheetsAPI(processedData, type);
  }

  /**
   * Format data for Google Sheets API (2D array)
   */
  formatForSheetsAPI(data, type) {
    if (type === 'orders') {
      return data.map(row => [
        row.sales_record_number,
        row.order_number,
        row.buyer_username,
        row.buyer_name,
        row.buyer_email,
        row.item_number,
        row.item_title,
        row.custom_label,
        row.quantity,
        row.sold_for,
        row.total_price,
        row.sale_date,
        row.paid_date,
        row.ship_by_date,
        row.tracking_number,
        row.status,
        row.account,
        row.last_updated
      ]);
    } else if (type === 'listings') {
      return data.map(row => [
        row.item_number,
        row.title,
        row.custom_label,
        row.available_quantity,
        row.current_price,
        row.sold_quantity,
        row.watchers,
        row.start_date,
        row.end_date,
        row.condition,
        row.status,
        row.account,
        row.last_updated
      ]);
    }
    return [];
  }

  parseCurrency(value) {
    if (!value) return 0;
    const cleaned = value.replace(/[$,]/g, '');
    return parseFloat(cleaned) || 0;
  }

  parseNumber(value) {
    if (!value) return 0;
    const cleaned = value.replace(/[^0-9]/g, '');
    return parseInt(cleaned) || 0;
  }

  formatDate(dateString) {
    if (!dateString) return '';
    try {
      // Handle eBay format: Aug-21-25
      const parts = dateString.split('-');
      if (parts.length === 3) {
        const month = this.monthNameToNumber(parts[0]);
        const day = parseInt(parts[1]);
        const year = 2000 + parseInt(parts[2]);
        return new Date(year, month - 1, day).toLocaleDateString();
      }
      return new Date(dateString).toLocaleDateString();
    } catch (error) {
      console.warn('Date format error:', dateString, error);
      return dateString;
    }
  }

  monthNameToNumber(monthName) {
    const months = {
      'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
      'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
      'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    };
    return months[monthName] || 1;
  }
}

export class GoogleSheetsWriter {
  constructor() {
    this.authToken = null;
    this.isAuthenticated = false;
    this.csvProcessor = new CSVToSheetsProcessor();
  }

  /**
   * Initialize Google authentication
   */
  async authenticate() {
    try {
      // Check if Chrome identity API is available
      if (typeof chrome === 'undefined' || !chrome.identity) {
        console.warn('Chrome identity API not available, using mock authentication');
        this.authToken = 'mock_token_for_testing';
        this.isAuthenticated = true;
        return this.authToken;
      }

      // Use Chrome identity API to get OAuth2 token
      return new Promise((resolve, reject) => {
        chrome.identity.getAuthToken({ 
          interactive: true 
        }, (token) => {
          if (chrome.runtime.lastError) {
            console.error('Auth error:', chrome.runtime.lastError);
            reject(new Error(chrome.runtime.lastError.message));
          } else if (!token) {
            reject(new Error('No authentication token received'));
          } else {
            this.authToken = token;
            this.isAuthenticated = true;
            console.log('✅ Google Sheets authentication successful');
            resolve(token);
          }
        });
      });
    } catch (error) {
      console.error('❌ Authentication failed:', error);
      throw error;
    }
  }

  /**
   * Clear cached auth token and re-authenticate
   */
  async refreshAuthentication() {
    if (this.authToken && typeof chrome !== 'undefined' && chrome.identity) {
      return new Promise((resolve) => {
        chrome.identity.removeCachedAuthToken({ token: this.authToken }, () => {
          this.isAuthenticated = false;
          this.authToken = null;
          console.log('🔄 Authentication token cleared');
          resolve();
        });
      });
    } else {
      this.isAuthenticated = false;
      this.authToken = null;
    }
  }

  /**
   * Check if current token is valid
   */
  async validateToken() {
    if (!this.authToken || !this.isAuthenticated) {
      return false;
    }

    try {
      // Test token with a simple API call
      const response = await fetch('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=' + this.authToken);
      const result = await response.json();
      
      if (response.ok && result.scope && result.scope.includes('spreadsheets')) {
        console.log('✅ Token validation successful');
        return true;
      } else {
        console.log('⚠️ Token validation failed, needs refresh');
        return false;
      }
    } catch (error) {
      console.error('❌ Token validation error:', error);
      return false;
    }
  }

  /**
   * Write data to a specific Google Sheet
   * @param {string} sheetId - Google Sheet ID
   * @param {string} range - Sheet range (e.g., "Orders!A2:K")
   * @param {Array} values - 2D array of values to write
   */
  async writeToSheet(sheetId, range, values) {
    // Validate inputs
    if (!sheetId || !range || !values || !Array.isArray(values)) {
      throw new Error('Invalid parameters for sheet write');
    }

    if (values.length === 0) {
      console.log('⚠️ No data to write to sheet');
      return { updates: { updatedRows: 0, updatedColumns: 0, updatedCells: 0 } };
    }

    // Ensure authentication
    if (!this.isAuthenticated || !(await this.validateToken())) {
      console.log('🔐 Authenticating for sheet write...');
      await this.authenticate();
    }

    // Handle mock mode for testing
    if (this.authToken === 'mock_token_for_testing') {
      console.log(`📊 Mock sheet write: ${values.length} rows to ${sheetId} range ${range}`);
      return {
        spreadsheetId: sheetId,
        tableRange: range,
        updates: {
          spreadsheetId: sheetId,
          updatedRange: range,
          updatedRows: values.length,
          updatedColumns: values[0]?.length || 0,
          updatedCells: values.length * (values[0]?.length || 0)
        }
      };
    }

    const url = `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}/values/${range}:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS`;

    let retryCount = 0;
    const maxRetries = 2;

    while (retryCount <= maxRetries) {
      try {
        console.log(`📊 Writing ${values.length} rows to sheet ${sheetId} (attempt ${retryCount + 1})`);
        
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.authToken}`,
            'Content-Type': 'application/json',
            'User-Agent': 'eBay CSV Processor Extension'
          },
          body: JSON.stringify({
            values: values,
            majorDimension: 'ROWS'
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          let errorDetails;
          
          try {
            errorDetails = JSON.parse(errorText);
          } catch {
            errorDetails = { message: errorText };
          }

          // Handle specific error codes
          if (response.status === 401) {
            throw new Error('AUTH_EXPIRED');
          } else if (response.status === 403) {
            throw new Error(`Permission denied: ${errorDetails.error?.message || 'Sheet access forbidden'}`);
          } else if (response.status === 404) {
            throw new Error(`Sheet not found: ${sheetId}`);
          } else {
            throw new Error(`Sheet API error (${response.status}): ${errorDetails.error?.message || response.statusText}`);
          }
        }

        const result = await response.json();
        console.log(`✅ Successfully wrote ${result.updates.updatedRows} rows to sheet`);
        
        return result;

      } catch (error) {
        console.error(`❌ Sheet write attempt ${retryCount + 1} failed:`, error.message);
        
        // Handle authentication errors
        if (error.message === 'AUTH_EXPIRED' || error.message.includes('401')) {
          if (retryCount < maxRetries) {
            console.log('🔄 Refreshing authentication and retrying...');
            await this.refreshAuthentication();
            await this.authenticate();
            retryCount++;
            continue;
          }
        }

        // Handle rate limiting
        if (error.message.includes('429') || error.message.includes('quota')) {
          if (retryCount < maxRetries) {
            const delay = Math.pow(2, retryCount) * 1000; // Exponential backoff
            console.log(`⏳ Rate limited, waiting ${delay}ms before retry...`);
            await new Promise(resolve => setTimeout(resolve, delay));
            retryCount++;
            continue;
          }
        }

        // If we've exhausted retries or it's an unrecoverable error
        if (retryCount >= maxRetries) {
          throw new Error(`Failed to write to sheet after ${maxRetries + 1} attempts: ${error.message}`);
        }

        throw error;
      }
    }
  }

  /**
   * Write CSV-processed orders data to Google Sheet
   */
  async writeCSVOrders(sheetId, csvData, type, account) {
    console.log(`📊 Writing ${csvData.length} ${type} records to sheet ${sheetId}`);
    
    // Process CSV data
    const processedValues = this.csvProcessor.processCSVData(csvData, type, account);
    
    // Determine sheet name and range
    const sheetName = type === 'orders' ? 'Orders' : 'Listings';
    const range = `${sheetName}!A:Z`; // Use full range for append
    
    try {
      const result = await this.writeToSheet(sheetId, range, processedValues);
      console.log(`✅ Successfully wrote ${processedValues.length} rows to ${sheetName} sheet`);
      return result;
    } catch (error) {
      console.error(`❌ Failed to write ${type} data to sheet:`, error);
      throw error;
    }
  }

  /**
   * Write orders data to Google Sheet (legacy method)
   */
  async writeOrders(sheetId, orders) {
    const timestamp = new Date().toISOString();
    const values = orders.map(order => [
      timestamp,
      order.order_id || '',
      order.buyer || '',
      order.total || '',
      order.status || '',
      JSON.stringify(order.items || []),
      order.ship_address || '',
      order.tracking || '',
      order.ship_date || '',
      order.order_date || '',
      order.payment_status || ''
    ]);

    return this.writeToSheet(sheetId, 'Orders!A:K', values);
  }

  /**
   * Write listings data to Google Sheet
   */
  async writeListings(sheetId, listings) {
    const timestamp = new Date().toISOString();
    const values = listings.map(listing => [
      timestamp,
      listing.item_id || '',
      listing.title || '',
      listing.price || '',
      listing.quantity || 0,
      listing.quantity_sold || 0,
      listing.views || 0,
      listing.watchers || 0,
      listing.status || '',
      listing.category || '',
      listing.condition || '',
      listing.start_date || '',
      listing.end_date || ''
    ]);

    return this.writeToSheet(sheetId, 'Listings!A:M', values);
  }

  /**
   * Write messages data to Google Sheet
   */
  async writeMessages(sheetId, messages) {
    const timestamp = new Date().toISOString();
    const values = messages.map(message => [
      timestamp,
      message.sender || '',
      message.subject || '',
      message.content || '',
      message.message_date || '',
      message.read_status || '',
      message.message_type || '',
      message.related_item_id || '',
      message.related_order_id || '',
      message.priority || 'normal'
    ]);

    return this.writeToSheet(sheetId, 'Messages!A:J', values);
  }

  /**
   * Check if sheet exists and has proper structure
   */
  async verifySheetStructure(sheetId) {
    if (!this.isAuthenticated) {
      await this.authenticate();
    }

    const url = `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}`;

    try {
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${this.authToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`Cannot access sheet: ${response.status}`);
      }

      const spreadsheet = await response.json();
      console.log(`Sheet verified: ${spreadsheet.properties.title}`);
      
      // Check if required sheets exist
      const sheetNames = spreadsheet.sheets.map(s => s.properties.title);
      const requiredSheets = ['Orders', 'Listings', 'Messages'];
      
      const missingSheets = requiredSheets.filter(name => !sheetNames.includes(name));
      
      if (missingSheets.length > 0) {
        console.warn(`Missing sheets: ${missingSheets.join(', ')}`);
        // Optionally create missing sheets
        await this.createMissingSheets(sheetId, missingSheets);
      }

      return true;

    } catch (error) {
      console.error('Error verifying sheet:', error);
      throw error;
    }
  }

  /**
   * Create missing sheets in the spreadsheet
   */
  async createMissingSheets(sheetId, sheetNames) {
    const requests = sheetNames.map(sheetName => ({
      addSheet: {
        properties: {
          title: sheetName
        }
      }
    }));

    const url = `https://sheets.googleapis.com/v4/spreadsheets/${sheetId}:batchUpdate`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.authToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ requests })
      });

      if (!response.ok) {
        throw new Error(`Failed to create sheets: ${response.status}`);
      }

      console.log(`Created sheets: ${sheetNames.join(', ')}`);
      
      // Add headers to new sheets
      for (const sheetName of sheetNames) {
        await this.addHeaders(sheetId, sheetName);
      }

    } catch (error) {
      console.error('Error creating sheets:', error);
      throw error;
    }
  }

  /**
   * Add headers to a sheet
   */
  async addHeaders(sheetId, sheetName) {
    const sheetType = sheetName.toLowerCase();
    const headers = SHEET_STRUCTURE[sheetType]?.headers;
    
    if (!headers) {
      console.warn(`No headers defined for sheet: ${sheetName}`);
      return;
    }

    const range = `${sheetName}!A1:${String.fromCharCode(64 + headers.length)}1`;
    
    try {
      await this.writeToSheet(sheetId, range, [headers]);
      console.log(`Headers added to ${sheetName}`);
    } catch (error) {
      console.error(`Error adding headers to ${sheetName}:`, error);
    }
  }

  /**
   * Batch write multiple data types
   */
  async batchWrite(sheetId, data) {
    const results = {
      orders: null,
      listings: null,
      messages: null,
      errors: []
    };

    try {
      // Verify sheet structure first
      await this.verifySheetStructure(sheetId);

      // Write orders
      if (data.orders && data.orders.length > 0) {
        try {
          results.orders = await this.writeOrders(sheetId, data.orders);
          console.log(`Wrote ${data.orders.length} orders`);
        } catch (error) {
          results.errors.push(`Orders: ${error.message}`);
        }
      }

      // Write listings
      if (data.listings && data.listings.length > 0) {
        try {
          results.listings = await this.writeListings(sheetId, data.listings);
          console.log(`Wrote ${data.listings.length} listings`);
        } catch (error) {
          results.errors.push(`Listings: ${error.message}`);
        }
      }

      // Write messages
      if (data.messages && data.messages.length > 0) {
        try {
          results.messages = await this.writeMessages(sheetId, data.messages);
          console.log(`Wrote ${data.messages.length} messages`);
        } catch (error) {
          results.errors.push(`Messages: ${error.message}`);
        }
      }

      return results;

    } catch (error) {
      console.error('Batch write failed:', error);
      results.errors.push(`General: ${error.message}`);
      return results;
    }
  }
}

// Export singleton instance
export const sheetsWriter = new GoogleSheetsWriter();