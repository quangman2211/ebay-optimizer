/**
 * Background Service Worker for eBay CSV Processor Extension
 * Manages CSV download detection, processing, and Google Sheets integration
 */

import { sheetsWriter } from './google-sheets-writer.js';
import { getSheetConfigByUsername, getSheetConfigById, SHEETS_CONFIG } from './sheets-config.js';

class EbayToSheetsExtension {
  constructor() {
    this.currentAccount = null;
    this.currentSheetConfig = null;
    this.collectionStatus = 'idle';
    this.isCollecting = false;
    this.downloadMonitor = null;
    
    this.setupMessageListeners();
    this.setupDownloadMonitoring();
    this.initializeExtension();
  }

  async initializeExtension() {
    console.log('🚀 eBay CSV Processor Extension initializing...');
    
    try {
      // Initialize extension storage
      await this.initializeStorage();
      
      // Try to authenticate on startup (non-blocking)
      this.authenticateAsync();
      
      // Initialize download monitoring
      this.initializeDownloadMonitoring();
      
      // Set extension status
      await this.updateExtensionStatus('ready');
      
      console.log('✅ eBay CSV Processor Extension initialized successfully');
    } catch (error) {
      console.error('❌ Extension initialization failed:', error);
      await this.updateExtensionStatus('error', error.message);
    }
  }

  async initializeStorage() {
    const defaultStorage = {
      csvProcessingLog: [],
      csvErrorLog: [],
      extensionSettings: {
        debugMode: true,
        autoProcess: true,
        notifications: true
      },
      extensionStatus: {
        status: 'initializing',
        lastUpdated: new Date().toISOString()
      }
    };

    const existing = await this.getStorageData(Object.keys(defaultStorage));
    const toSet = {};
    
    for (const [key, defaultValue] of Object.entries(defaultStorage)) {
      if (!existing[key]) {
        toSet[key] = defaultValue;
      }
    }

    if (Object.keys(toSet).length > 0) {
      await this.setStorageData(toSet);
      console.log('📦 Extension storage initialized');
    }
  }

  async authenticateAsync() {
    try {
      await sheetsWriter.authenticate();
      console.log('✅ Google Sheets authentication successful');
      await this.updateExtensionStatus('authenticated');
    } catch (error) {
      console.log('⚠️ Initial authentication skipped, will authenticate on first use');
      console.log('Auth error:', error.message);
    }
  }

  initializeDownloadMonitoring() {
    // Set up more comprehensive download monitoring
    if (chrome.downloads && chrome.downloads.onCreated) {
      chrome.downloads.onCreated.addListener((downloadItem) => {
        this.handleDownloadCreated(downloadItem);
      });
    }

    if (chrome.downloads && chrome.downloads.onChanged) {
      chrome.downloads.onChanged.addListener((downloadDelta) => {
        this.handleDownloadChanged(downloadDelta);
      });
    }

    console.log('📥 Download monitoring initialized');
  }

  async updateExtensionStatus(status, details = null) {
    const statusData = {
      status: status,
      details: details,
      lastUpdated: new Date().toISOString()
    };

    await this.setStorageData({ extensionStatus: statusData });
    
    // Emit status change event
    this.broadcastMessage({
      action: 'STATUS_CHANGED',
      status: statusData
    });
  }

  setupMessageListeners() {
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
      // Handle async responses with better error handling
      (async () => {
        try {
          console.log(`📨 Received message: ${request.action}`, request);
          
          let response;
          
          switch(request.action) {
            case 'GET_ACCOUNT_INFO':
              response = await this.handleGetAccountInfo(request);
              break;
              
            case 'GET_STATUS':
              response = await this.handleGetStatus();
              break;
              
            case 'ACCOUNT_DETECTED':
              response = await this.handleAccountDetected(request.account || request);
              break;
              
            case 'csv_processed':
              response = await this.handleCSVProcessed(request);
              break;
              
            case 'csv_error':
              response = await this.handleCSVError(request);
              break;

            case 'WRITE_CSV_TO_SHEETS':
              response = await this.handleWriteCSVToSheets(request);
              break;

            case 'TEST_CONNECTION':
              response = await this.handleTestConnection();
              break;

            case 'CLEAR_CACHE':
              response = await this.handleClearCache();
              break;

            case 'GET_STORAGE_DATA':
              response = await this.handleGetStorageData(request.keys);
              break;

            case 'UPDATE_SETTINGS':
              response = await this.handleUpdateSettings(request.settings);
              break;
              
            // Legacy support
            case 'START_COLLECTION':
              response = await this.handleStartCollection();
              break;
              
            case 'STOP_COLLECTION':
              response = this.handleStopCollection();
              break;
              
            case 'DATA_COLLECTED':
              response = await this.handleDataCollected(request.type, request.data);
              break;
              
            default:
              console.warn(`Unknown action: ${request.action}`);
              response = { 
                success: false, 
                error: `Unknown action: ${request.action}`,
                availableActions: [
                  'GET_ACCOUNT_INFO', 'GET_STATUS', 'ACCOUNT_DETECTED',
                  'csv_processed', 'csv_error', 'WRITE_CSV_TO_SHEETS',
                  'TEST_CONNECTION', 'CLEAR_CACHE', 'GET_STORAGE_DATA'
                ]
              };
          }
          
          console.log(`📤 Sending response for ${request.action}:`, response);
          sendResponse(response);
        } catch (error) {
          console.error(`❌ Message handler error for ${request.action}:`, error);
          const errorResponse = { 
            success: false, 
            error: error.message,
            stack: error.stack,
            action: request.action
          };
          sendResponse(errorResponse);
        }
      })();
      
      return true; // Keep message channel open for async response
    });
  }

  setupDownloadMonitoring() {
    // Monitor for CSV file downloads
    chrome.downloads.onCreated.addListener((downloadItem) => {
      if (this.isEBayCSV(downloadItem.filename)) {
        console.log('🔍 eBay CSV download detected:', downloadItem.filename);
        this.handleDownloadDetected(downloadItem);
      }
    });

    chrome.downloads.onChanged.addListener((downloadDelta) => {
      if (downloadDelta.state && downloadDelta.state.current === 'complete') {
        this.handleDownloadComplete(downloadDelta.id);
      }
    });
  }

  isEBayCSV(filename) {
    const patterns = [
      /eBay-.*-report.*\.csv$/i,
      /eBay-awaiting-shipment.*\.csv$/i,
      /eBay-all-active-listings.*\.csv$/i,
      /eBay-sold-listings.*\.csv$/i
    ];
    
    return patterns.some(pattern => pattern.test(filename));
  }

  async handleDownloadDetected(downloadItem) {
    console.log('📥 Handling eBay CSV download:', downloadItem);
    
    // Store download info for processing
    this.downloadMonitor = {
      id: downloadItem.id,
      filename: downloadItem.filename,
      url: downloadItem.url,
      detected_at: new Date().toISOString()
    };
  }

  async handleDownloadComplete(downloadId) {
    if (this.downloadMonitor && this.downloadMonitor.id === downloadId) {
      console.log('✅ eBay CSV download completed:', this.downloadMonitor.filename);
      
      try {
        // Get the downloaded file
        const [downloadItem] = await chrome.downloads.search({ id: downloadId });
        
        if (downloadItem && downloadItem.filename) {
          // Notify content script about completed download
          const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
          
          if (tab) {
            chrome.tabs.sendMessage(tab.id, {
              action: 'CSV_DOWNLOAD_COMPLETE',
              download: {
                id: downloadId,
                filename: downloadItem.filename,
                url: downloadItem.url
              }
            });
          }
        }
      } catch (error) {
        console.error('Error handling download complete:', error);
      }
    }
  }

  async handleCSVProcessed(request) {
    console.log('📊 CSV processed notification:', request);
    
    // Log successful processing
    const logEntry = {
      timestamp: new Date().toISOString(),
      type: request.type,
      recordCount: request.recordCount,
      account: request.account,
      status: 'success'
    };
    
    // Store in extension storage for tracking
    const { csvProcessingLog = [] } = await chrome.storage.local.get('csvProcessingLog');
    csvProcessingLog.push(logEntry);
    
    // Keep only last 100 entries
    if (csvProcessingLog.length > 100) {
      csvProcessingLog.splice(0, csvProcessingLog.length - 100);
    }
    
    await chrome.storage.local.set({ csvProcessingLog });
    
    return { success: true, logged: true };
  }

  handleCSVError(request) {
    console.error('❌ CSV processing error:', request);
    
    // Log error for debugging
    const errorLog = {
      timestamp: new Date().toISOString(),
      filename: request.filename,
      error: request.error,
      status: 'error'
    };
    
    // Could store in extension storage or send to analytics
    chrome.storage.local.get('csvErrorLog').then(({ csvErrorLog = [] }) => {
      csvErrorLog.push(errorLog);
      chrome.storage.local.set({ csvErrorLog });
    });
    
    return { success: true, error_logged: true };
  }

  async handleWriteCSVToSheets(request) {
    console.log('📊 Handling CSV to Sheets write request:', {
      type: request.type,
      recordCount: request.csvData?.length,
      sheetId: request.sheetId
    });

    try {
      // Use the Google Sheets writer to write CSV data
      const result = await sheetsWriter.writeCSVOrders(
        request.sheetId,
        request.csvData,
        request.type,
        request.account
      );

      return {
        success: true,
        result: result,
        rowsWritten: request.csvData.length,
        sheetId: request.sheetId,
        type: request.type
      };

    } catch (error) {
      console.error('❌ Error writing CSV to sheets:', error);
      return {
        success: false,
        error: error.message,
        sheetId: request.sheetId,
        type: request.type
      };
    }
  }

  async handleGetAccountInfo() {
    if (!this.currentAccount) {
      // Try to detect account
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (tab.url.includes('ebay.com')) {
        const results = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          function: this.detectEbayAccount
        });
        
        const accountInfo = results[0]?.result;
        if (accountInfo && accountInfo.username) {
          this.currentAccount = accountInfo;
          this.currentSheetConfig = getSheetConfigByUsername(accountInfo.username);
        }
      }
    }
    
    return {
      success: true,
      account: this.currentAccount,
      sheetConfig: this.currentSheetConfig
    };
  }

  async handleAccountDetected(accountInfo) {
    console.log('Account detected:', accountInfo);
    
    this.currentAccount = accountInfo;
    this.currentSheetConfig = getSheetConfigByUsername(accountInfo.username);
    
    if (!this.currentSheetConfig) {
      console.warn(`No sheet configuration found for account: ${accountInfo.username}`);
      return {
        success: false,
        error: `Account ${accountInfo.username} not configured`
      };
    }
    
    console.log(`Account mapped to sheet: ${this.currentSheetConfig.sheetId}`);
    
    return {
      success: true,
      account: accountInfo,
      sheetConfig: this.currentSheetConfig
    };
  }

  async handleStartCollection() {
    if (this.isCollecting) {
      return { success: false, error: 'Collection already in progress' };
    }
    
    if (!this.currentSheetConfig) {
      return { success: false, error: 'No account/sheet configuration found' };
    }
    
    this.isCollecting = true;
    this.collectionStatus = 'collecting';
    
    try {
      // Get active tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      
      if (!tab.url.includes('ebay.com')) {
        throw new Error('Please navigate to eBay website first');
      }
      
      // Collect data from current page
      const collectionResults = await this.collectAllData(tab.id);
      
      // Write directly to Google Sheets
      const writeResults = await this.writeToGoogleSheets(collectionResults);
      
      this.collectionStatus = 'completed';
      this.isCollecting = false;
      
      return {
        success: true,
        account: this.currentAccount,
        sheetId: this.currentSheetConfig.sheetId,
        ordersCollected: collectionResults.orders?.length || 0,
        listingsCollected: collectionResults.listings?.length || 0,
        messagesCollected: collectionResults.messages?.length || 0,
        writeResults: writeResults
      };
      
    } catch (error) {
      console.error('Collection error:', error);
      this.collectionStatus = 'error';
      this.isCollecting = false;
      
      return {
        success: false,
        error: error.message
      };
    }
  }

  handleStopCollection() {
    this.isCollecting = false;
    this.collectionStatus = 'stopped';
    
    return { success: true };
  }

  handleGetStatus() {
    return {
      status: this.collectionStatus,
      isCollecting: this.isCollecting,
      currentAccount: this.currentAccount,
      currentSheetConfig: this.currentSheetConfig
    };
  }

  async handleDataCollected(type, data) {
    console.log(`Data collected: ${type}, ${data.length} items`);
    
    if (!this.currentSheetConfig) {
      return { success: false, error: 'No sheet configuration' };
    }
    
    try {
      // Write specific data type to sheet
      let result;
      const sheetId = this.currentSheetConfig.sheetId;
      
      switch(type) {
        case 'orders':
          result = await sheetsWriter.writeOrders(sheetId, data);
          break;
        case 'listings':
          result = await sheetsWriter.writeListings(sheetId, data);
          break;
        case 'messages':
          result = await sheetsWriter.writeMessages(sheetId, data);
          break;
        default:
          throw new Error(`Unknown data type: ${type}`);
      }
      
      return { success: true, result };
      
    } catch (error) {
      console.error(`Error writing ${type} to sheet:`, error);
      return { success: false, error: error.message };
    }
  }

  async collectAllData(tabId) {
    const results = {
      orders: [],
      listings: [],
      messages: []
    };
    
    try {
      // Check current page type and collect appropriate data
      const [tab] = await chrome.tabs.query({ tabId: tabId });
      const url = tab.url;
      
      if (url.includes('/sh/ord') || url.includes('/mys/orders')) {
        // Orders page
        const orderResults = await chrome.scripting.executeScript({
          target: { tabId: tabId },
          function: this.collectOrdersFromPage
        });
        results.orders = orderResults[0]?.result || [];
        
      } else if (url.includes('/sh/lst') || url.includes('/mys/listings')) {
        // Listings page
        const listingResults = await chrome.scripting.executeScript({
          target: { tabId: tabId },
          function: this.collectListingsFromPage
        });
        results.listings = listingResults[0]?.result || [];
        
      } else if (url.includes('/msg/') || url.includes('/messages')) {
        // Messages page
        const messageResults = await chrome.scripting.executeScript({
          target: { tabId: tabId },
          function: this.collectMessagesFromPage
        });
        results.messages = messageResults[0]?.result || [];
        
      } else {
        // Try to collect all available data from current page
        console.log('Attempting to collect any available data from current page');
        
        // Try orders
        try {
          const orderResults = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            function: this.collectOrdersFromPage
          });
          results.orders = orderResults[0]?.result || [];
        } catch (e) {
          console.log('No orders data on this page');
        }
        
        // Try listings
        try {
          const listingResults = await chrome.scripting.executeScript({
            target: { tabId: tabId },
            function: this.collectListingsFromPage
          });
          results.listings = listingResults[0]?.result || [];
        } catch (e) {
          console.log('No listings data on this page');
        }
      }
      
      console.log('Collection results:', {
        orders: results.orders.length,
        listings: results.listings.length,
        messages: results.messages.length
      });
      
      return results;
      
    } catch (error) {
      console.error('Data collection error:', error);
      return results;
    }
  }

  async writeToGoogleSheets(data) {
    if (!this.currentSheetConfig) {
      throw new Error('No sheet configuration available');
    }
    
    const sheetId = this.currentSheetConfig.sheetId;
    console.log(`Writing to Google Sheet: ${sheetId}`);
    
    try {
      // Batch write all data types
      const writeResults = await sheetsWriter.batchWrite(sheetId, data);
      
      console.log('Write results:', writeResults);
      
      if (writeResults.errors.length > 0) {
        console.warn('Some write operations had errors:', writeResults.errors);
      }
      
      return writeResults;
      
    } catch (error) {
      console.error('Google Sheets write error:', error);
      throw error;
    }
  }

  // New handler methods
  async handleTestConnection() {
    try {
      console.log('🔗 Testing extension connection...');
      
      const status = await this.getStorageData(['extensionStatus']);
      const sheetsAuth = await sheetsWriter.validateToken();
      
      return {
        success: true,
        extensionStatus: status.extensionStatus || { status: 'unknown' },
        sheetsAuthenticated: sheetsAuth,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async handleClearCache() {
    try {
      console.log('🗑️ Clearing extension cache...');
      
      // Clear authentication cache
      if (sheetsWriter.authToken) {
        await sheetsWriter.refreshAuthentication();
      }
      
      // Clear storage cache
      await this.setStorageData({
        csvProcessingLog: [],
        csvErrorLog: []
      });
      
      return {
        success: true,
        message: 'Cache cleared successfully'
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async handleGetStorageData(keys) {
    try {
      const data = await this.getStorageData(keys || ['csvProcessingLog', 'csvErrorLog', 'extensionSettings']);
      return {
        success: true,
        data: data
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  async handleUpdateSettings(settings) {
    try {
      console.log('⚙️ Updating extension settings:', settings);
      
      const current = await this.getStorageData(['extensionSettings']);
      const updated = {
        ...current.extensionSettings,
        ...settings
      };
      
      await this.setStorageData({ extensionSettings: updated });
      
      return {
        success: true,
        settings: updated
      };
    } catch (error) {
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Utility methods
  async getStorageData(keys) {
    return new Promise((resolve) => {
      chrome.storage.local.get(keys, (result) => {
        resolve(result);
      });
    });
  }

  async setStorageData(data) {
    return new Promise((resolve) => {
      chrome.storage.local.set(data, () => {
        resolve();
      });
    });
  }

  broadcastMessage(message) {
    // Broadcast to all active tabs with content scripts
    chrome.tabs.query({}, (tabs) => {
      tabs.forEach(tab => {
        if (tab.url && (tab.url.includes('ebay.com') || tab.url.startsWith('file://'))) {
          chrome.tabs.sendMessage(tab.id, message).catch(() => {
            // Ignore errors for tabs without content scripts
          });
        }
      });
    });
  }

  // Enhanced download monitoring
  async handleDownloadCreated(downloadItem) {
    if (this.isEBayCSV(downloadItem.filename)) {
      console.log('📥 Enhanced CSV download detected:', downloadItem);
      
      const downloadInfo = {
        id: downloadItem.id,
        filename: downloadItem.filename,
        url: downloadItem.url,
        totalBytes: downloadItem.totalBytes,
        createdAt: new Date().toISOString()
      };

      // Store download info
      this.downloadMonitor = downloadInfo;
      
      // Notify content scripts
      this.broadcastMessage({
        action: 'CSV_DOWNLOAD_DETECTED',
        download: downloadInfo
      });
    }
  }

  async handleDownloadChanged(downloadDelta) {
    if (this.downloadMonitor && this.downloadMonitor.id === downloadDelta.id) {
      if (downloadDelta.state && downloadDelta.state.current === 'complete') {
        console.log('✅ Enhanced CSV download completed:', this.downloadMonitor.filename);
        
        // Get final download info
        try {
          const [downloadItem] = await chrome.downloads.search({ id: downloadDelta.id });
          
          if (downloadItem) {
            const completedDownload = {
              ...this.downloadMonitor,
              finalFilename: downloadItem.filename,
              completedAt: new Date().toISOString()
            };
            
            // Notify content scripts
            this.broadcastMessage({
              action: 'CSV_DOWNLOAD_COMPLETE',
              download: completedDownload
            });
            
            // Log the completed download
            const { csvProcessingLog = [] } = await this.getStorageData(['csvProcessingLog']);
            csvProcessingLog.push({
              timestamp: completedDownload.completedAt,
              type: 'download_detected',
              filename: completedDownload.filename,
              status: 'detected'
            });
            
            await this.setStorageData({ csvProcessingLog });
          }
        } catch (error) {
          console.error('Error handling download complete:', error);
        }
      }
    }
  }

  // Injected function to detect eBay account
  detectEbayAccount() {
    const accountInfo = {
      username: null,
      displayName: null
    };
    
    // Try multiple methods to extract username
    const selectors = [
      '#gh-ug b',
      '.gh-ug b',
      '[data-testid="user-menu"] span',
      '.user-info .username'
    ];
    
    for (const selector of selectors) {
      const element = document.querySelector(selector);
      if (element) {
        accountInfo.username = element.textContent.trim();
        break;
      }
    }
    
    // Try URL parameters
    if (!accountInfo.username) {
      const urlParams = new URLSearchParams(window.location.search);
      accountInfo.username = urlParams.get('seller') || urlParams.get('_ssn');
    }
    
    return accountInfo;
  }

  // Injected function to collect orders
  collectOrdersFromPage() {
    const orders = [];
    const orderElements = document.querySelectorAll('.order-row, [data-testid="order-row"], .grid-row');
    
    orderElements.forEach(orderElement => {
      try {
        const order = {
          order_id: orderElement.querySelector('.order-id, [data-testid="order-id"]')?.textContent?.trim(),
          buyer: orderElement.querySelector('.buyer-name, [data-testid="buyer-name"]')?.textContent?.trim(),
          total: orderElement.querySelector('.order-total, [data-testid="order-total"]')?.textContent?.trim(),
          status: orderElement.querySelector('.order-status, [data-testid="order-status"]')?.textContent?.trim(),
          items: [],
          ship_address: orderElement.querySelector('.shipping-address')?.textContent?.trim(),
          tracking: orderElement.querySelector('.tracking-number')?.textContent?.trim(),
          ship_date: orderElement.querySelector('.ship-date')?.textContent?.trim(),
          order_date: orderElement.querySelector('.order-date')?.textContent?.trim(),
          payment_status: orderElement.querySelector('.payment-status')?.textContent?.trim()
        };
        
        // Extract items
        const itemElements = orderElement.querySelectorAll('.order-item');
        itemElements.forEach(item => {
          order.items.push({
            title: item.querySelector('.item-title')?.textContent?.trim(),
            quantity: item.querySelector('.quantity')?.textContent?.trim()
          });
        });
        
        if (order.order_id && order.buyer) {
          orders.push(order);
        }
      } catch (error) {
        console.error('Error extracting order:', error);
      }
    });
    
    return orders;
  }

  // Injected function to collect listings
  collectListingsFromPage() {
    const listings = [];
    const listingElements = document.querySelectorAll('.listing-row, [data-testid="listing-row"], .grid-row');
    
    listingElements.forEach(listingElement => {
      try {
        const listing = {
          item_id: listingElement.querySelector('.item-id, [data-testid="item-id"]')?.textContent?.trim(),
          title: listingElement.querySelector('.item-title, [data-testid="item-title"]')?.textContent?.trim(),
          price: listingElement.querySelector('.price, [data-testid="price"]')?.textContent?.trim(),
          quantity: listingElement.querySelector('.quantity')?.textContent?.trim() || '0',
          quantity_sold: listingElement.querySelector('.quantity-sold')?.textContent?.trim() || '0',
          views: listingElement.querySelector('.views')?.textContent?.trim() || '0',
          watchers: listingElement.querySelector('.watchers')?.textContent?.trim() || '0',
          status: listingElement.querySelector('.listing-status')?.textContent?.trim(),
          category: listingElement.querySelector('.category')?.textContent?.trim(),
          condition: listingElement.querySelector('.condition')?.textContent?.trim(),
          start_date: listingElement.querySelector('.start-date')?.textContent?.trim(),
          end_date: listingElement.querySelector('.end-date')?.textContent?.trim()
        };
        
        if (listing.item_id && listing.title) {
          listings.push(listing);
        }
      } catch (error) {
        console.error('Error extracting listing:', error);
      }
    });
    
    return listings;
  }

  // Injected function to collect messages
  collectMessagesFromPage() {
    const messages = [];
    const messageElements = document.querySelectorAll('.message-row, [data-testid="message-row"], .msg-row');
    
    messageElements.forEach(messageElement => {
      try {
        const message = {
          sender: messageElement.querySelector('.sender-name')?.textContent?.trim(),
          subject: messageElement.querySelector('.subject')?.textContent?.trim(),
          content: messageElement.querySelector('.message-content')?.textContent?.trim(),
          message_date: messageElement.querySelector('.message-date')?.textContent?.trim(),
          read_status: messageElement.querySelector('.read-status')?.textContent?.trim() || 'unread',
          message_type: messageElement.querySelector('.message-type')?.textContent?.trim() || 'general',
          related_item_id: messageElement.querySelector('.related-item')?.textContent?.trim(),
          related_order_id: messageElement.querySelector('.related-order')?.textContent?.trim(),
          priority: messageElement.querySelector('.priority')?.textContent?.trim() || 'normal'
        };
        
        if (message.sender && message.subject) {
          messages.push(message);
        }
      } catch (error) {
        console.error('Error extracting message:', error);
      }
    });
    
    return messages;
  }
}

// Initialize extension
const ebayToSheetsExtension = new EbayToSheetsExtension();