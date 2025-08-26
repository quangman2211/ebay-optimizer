/**
 * Google Sheets Configuration for eBay CSV Processor Extension
 * Maps account IDs to actual Google Sheet configurations
 */

export const SHEETS_CONFIG = {
  // Production eBay Account
  'seller_pro_2025': {
    accountId: 'seller_pro_2025',
    ebayUsername: 'seller_pro_2025',
    sheetId: '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM',
    sheetName: 'eBay_Sync_seller_pro_2025',
    type: 'production',
    description: 'Production eBay seller account',
    active: true
  },

  // Test API Account
  'test_api_account': {
    accountId: 'test_api_account',
    ebayUsername: 'test_api_account',
    sheetId: '1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c',
    sheetName: 'eBay_Sync_test_api_account',
    type: 'testing',
    description: 'eBay API testing account',
    active: true
  },

  // Test Workspace Account  
  'test_workspace_account': {
    accountId: 'test_workspace_account',
    ebayUsername: 'test_workspace_account',
    sheetId: '1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII',
    sheetName: 'eBay_Sync_test_workspace_account',
    type: 'testing',
    description: 'eBay workspace testing account',
    active: true
  },

  // Legacy account mappings for backward compatibility
  'pathabesek0': {
    accountId: 'pathabesek0',
    ebayUsername: 'pathabesek0',
    sheetId: '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM',
    sheetName: 'eBay_Sync_seller_pro_2025',
    type: 'production',
    description: 'Legacy mapping to seller_pro_2025',
    active: true
  },

  'tanbooks': {
    accountId: 'tanbooks',
    ebayUsername: 'tanbooks',
    sheetId: '1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c',
    sheetName: 'eBay_Sync_test_api_account',
    type: 'testing',
    description: 'Legacy mapping to test_api_account',
    active: true
  },

  'scholastic': {
    accountId: 'scholastic',
    ebayUsername: 'scholastic',
    sheetId: '1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII',
    sheetName: 'eBay_Sync_test_workspace_account',
    type: 'testing',
    description: 'Legacy mapping to test_workspace_account',
    active: true
  }
};

// Default fallback configuration
export const DEFAULT_SHEET_CONFIG = {
  accountId: 'default',
  ebayUsername: 'default',
  sheetId: '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM', // Default to seller_pro_2025
  sheetName: 'eBay_Sync_seller_pro_2025',
  type: 'fallback',
  description: 'Default fallback configuration',
  active: true
};

/**
 * Get sheet configuration for a specific eBay username
 */
export function getSheetConfigByUsername(username) {
  if (!username) return DEFAULT_SHEET_CONFIG;
  
  // Direct match
  const config = SHEETS_CONFIG[username];
  if (config && config.active) {
    return config;
  }
  
  // Search by ebayUsername field
  for (const [accountId, config] of Object.entries(SHEETS_CONFIG)) {
    if (config.ebayUsername === username && config.active) {
      return config;
    }
  }
  
  // Partial match (case insensitive)
  const lowerUsername = username.toLowerCase();
  for (const [accountId, config] of Object.entries(SHEETS_CONFIG)) {
    if (config.ebayUsername.toLowerCase().includes(lowerUsername) && config.active) {
      return config;
    }
  }
  
  return DEFAULT_SHEET_CONFIG;
}

/**
 * Get sheet configuration by account ID
 */
export function getSheetConfigById(accountId) {
  const config = SHEETS_CONFIG[accountId];
  return (config && config.active) ? config : DEFAULT_SHEET_CONFIG;
}

/**
 * Get all active sheet configurations
 */
export function getAllActiveSheetConfigs() {
  return Object.values(SHEETS_CONFIG).filter(config => config.active);
}

/**
 * Get production sheet configurations only
 */
export function getProductionSheetConfigs() {
  return Object.values(SHEETS_CONFIG).filter(config => 
    config.active && config.type === 'production'
  );
}

/**
 * Get testing sheet configurations only
 */
export function getTestingSheetConfigs() {
  return Object.values(SHEETS_CONFIG).filter(config => 
    config.active && config.type === 'testing'
  );
}

/**
 * Sheet structure definition for each Google Sheet
 */
export const SHEET_STRUCTURE = {
  orders: {
    sheetName: "Orders",
    headers: [
      "Timestamp",
      "Order ID",
      "Buyer",
      "Total",
      "Status",
      "Items",
      "Ship Address",
      "Tracking",
      "Ship Date",
      "Order Date",
      "Payment Status"
    ]
  },
  listings: {
    sheetName: "Listings",
    headers: [
      "Timestamp",
      "Item ID",
      "Title",
      "Price",
      "Quantity",
      "Quantity Sold",
      "Views",
      "Watchers",
      "Status",
      "Category",
      "Condition",
      "Start Date",
      "End Date"
    ]
  },
  messages: {
    sheetName: "Messages",
    headers: [
      "Timestamp",
      "Sender",
      "Subject",
      "Content",
      "Message Date",
      "Read Status",
      "Message Type",
      "Related Item ID",
      "Related Order ID",
      "Priority"
    ]
  }
};