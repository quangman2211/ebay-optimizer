/**
 * eBay CSV Download Processor
 * Detects CSV downloads and sends to backend API
 * No Google Sheets direct integration - backend handles everything
 */

class EBayCSVProcessor {
    constructor() {
        this.isProcessing = false;
        this.downloadQueue = [];
        this.csvMapping = null;
        
        // Initialize backend API client (loaded from backend-api-client.js)
        this.apiClient = typeof backendAPI !== 'undefined' ? backendAPI : new BackendAPIClient();
        
        this.init();
    }

    async init() {
        console.log('🚀 eBay CSV Processor initialized (Backend API Mode)');
        
        // Test backend connection
        const connectionTest = await this.apiClient.testConnection();
        if (connectionTest.success) {
            console.log('✅ Backend connected:', connectionTest.backend);
            console.log('   Latency:', connectionTest.latency);
        } else {
            console.error('❌ Backend connection failed:', connectionTest.message);
            this.showNotification('Backend connection failed', 'error');
        }
        
        // Load CSV mapping configuration
        await this.loadCSVMapping();
        
        // Listen for CSV download events from simulator
        this.setupEventListeners();
        
        // Monitor for actual file downloads (if possible)
        this.setupDownloadMonitor();
        
        // Detect current account
        this.currentAccount = await this.detectCurrentAccount();
        console.log('📊 Current account detected:', this.currentAccount);
    }

    async loadCSVMapping() {
        try {
            // In real extension, this would be loaded from storage or config
            this.csvMapping = {
                orders: {
                    filename_pattern: /eBay-awaiting-shipment-report-.*\.csv/,
                    type: 'orders',
                    fields: [
                        'Sales Record Number',
                        'Order Number',
                        'Buyer Username', 
                        'Buyer Name',
                        'Buyer Email',
                        'Item Number',
                        'Item Title',
                        'Custom Label',
                        'Quantity',
                        'Sold For',
                        'Total Price',
                        'Sale Date',
                        'Paid On Date',
                        'Ship By Date',
                        'Tracking Number'
                    ]
                },
                listings: {
                    filename_pattern: /eBay-all-active-listings-report-.*\.csv/,
                    type: 'listings',
                    fields: [
                        'Item number',
                        'Title',
                        'Custom label (SKU)',
                        'Available quantity',
                        'Current price',
                        'Sold quantity',
                        'Watchers',
                        'Start date',
                        'End date',
                        'Condition'
                    ]
                }
            };
            console.log('✅ CSV mapping loaded');
        } catch (error) {
            console.error('❌ Failed to load CSV mapping:', error);
        }
    }

    setupEventListeners() {
        // Listen for custom download events from simulator
        window.addEventListener('ebayCSVDownload', (event) => {
            console.log('📥 CSV download detected:', event.detail);
            this.handleCSVDownload(event.detail);
        });

        // Listen for page ready events
        window.addEventListener('ebayPageReady', (event) => {
            console.log('📄 eBay page ready:', event.detail);
            this.handlePageReady(event.detail);
        });

        // Listen for order clicks (for additional context)
        window.addEventListener('ebayOrderClick', (event) => {
            console.log('🖱️ Order clicked:', event.detail);
        });
    }

    setupDownloadMonitor() {
        // Monitor for actual downloads in browser
        // This would typically use chrome.downloads API in background script
        console.log('📡 Download monitor ready');
        
        // Listen for messages from background script about downloads
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            if (request.type === 'csvDownloadDetected') {
                this.handleCSVDownload({
                    filename: request.filename,
                    content: request.content,
                    url: request.url
                });
                sendResponse({ success: true });
            }
        });
    }

    async detectCurrentAccount() {
        // Try to detect account from page
        const accountFromPage = this.detectAccountFromPage();
        if (accountFromPage) {
            return accountFromPage;
        }

        // Try to get from storage
        const stored = await this.getFromStorage('current_account');
        if (stored) {
            return stored;
        }

        // Default account
        return 'default_account';
    }

    detectAccountFromPage() {
        // Try multiple methods to detect account
        
        // Method 1: Check user info in header
        const userElement = document.querySelector('[data-test-id="user-info"], .gh-ua, #gh-ug');
        if (userElement) {
            const username = userElement.textContent.trim();
            if (username) {
                console.log('Account detected from header:', username);
                return username;
            }
        }

        // Method 2: Check account dropdown
        const accountDropdown = document.querySelector('[aria-label*="Account"], .gh-dd-u');
        if (accountDropdown) {
            const accountText = accountDropdown.textContent.trim();
            const match = accountText.match(/Hi\s+([^!]+)/);
            if (match) {
                console.log('Account detected from dropdown:', match[1]);
                return match[1];
            }
        }

        // Method 3: Check URL for seller name
        const urlMatch = window.location.href.match(/seller\.ebay\.com.*[?&]seller=([^&]+)/);
        if (urlMatch) {
            console.log('Account detected from URL:', urlMatch[1]);
            return urlMatch[1];
        }

        return null;
    }

    async handleCSVDownload(downloadData) {
        if (this.isProcessing) {
            this.downloadQueue.push(downloadData);
            console.log('📋 Added to queue. Queue size:', this.downloadQueue.length);
            return;
        }

        this.isProcessing = true;
        
        try {
            const { filename, content, url } = downloadData;
            
            // Determine CSV type
            const csvType = this.determineCSVType(filename);
            if (!csvType) {
                console.warn('⚠️ Unknown CSV type for file:', filename);
                this.showNotification('Unknown CSV type', 'warning');
                return;
            }

            console.log(`🔍 Processing ${csvType} CSV...`);
            
            // Validate CSV format first
            const validationResult = await this.apiClient.validateCSV(
                this.currentAccount,
                csvType,
                content
            );

            if (!validationResult.success || !validationResult.data?.valid) {
                console.error('❌ CSV validation failed:', validationResult.message);
                this.showNotification('Invalid CSV format', 'error');
                return;
            }

            console.log('✅ CSV validated:', validationResult.data);

            // Upload to backend
            const uploadResult = await this.apiClient.uploadCSV(
                this.currentAccount,
                csvType,
                content,
                {
                    filename: filename,
                    url: url,
                    timestamp: new Date().toISOString(),
                    extension_version: chrome.runtime.getManifest().version
                }
            );

            if (uploadResult.success) {
                console.log('✅ CSV uploaded successfully:', uploadResult.data);
                
                const message = `Processed ${uploadResult.data.rows_processed || 0} ${csvType}`;
                this.showNotification(message, 'success');
                
                // Store processing history
                await this.saveProcessingHistory({
                    filename: filename,
                    type: csvType,
                    account: this.currentAccount,
                    processed: uploadResult.data.rows_processed || 0,
                    skipped: uploadResult.data.rows_skipped || 0,
                    timestamp: new Date().toISOString()
                });
            } else {
                console.error('❌ CSV upload failed:', uploadResult.message);
                this.showNotification('Upload failed: ' + uploadResult.message, 'error');
            }

        } catch (error) {
            console.error('❌ Error processing CSV:', error);
            this.showNotification('Processing error: ' + error.message, 'error');
        } finally {
            this.isProcessing = false;
            
            // Process next in queue
            if (this.downloadQueue.length > 0) {
                const next = this.downloadQueue.shift();
                console.log('📋 Processing next from queue...');
                this.handleCSVDownload(next);
            }
        }
    }

    determineCSVType(filename) {
        if (!filename) return null;
        
        // Check against known patterns
        for (const [type, config] of Object.entries(this.csvMapping)) {
            if (config.filename_pattern.test(filename)) {
                return type;
            }
        }
        
        // Fallback: check for keywords
        const lowerFilename = filename.toLowerCase();
        if (lowerFilename.includes('order') || lowerFilename.includes('shipment')) {
            return 'orders';
        }
        if (lowerFilename.includes('listing') || lowerFilename.includes('active')) {
            return 'listings';
        }
        
        return null;
    }

    async handlePageReady(pageData) {
        console.log('📄 Page ready for processing:', pageData);
        
        // Update current account if detected
        if (pageData.account) {
            this.currentAccount = pageData.account;
            await this.saveToStorage('current_account', pageData.account);
        }
        
        // Check for download buttons and enhance them
        this.enhanceDownloadButtons();
    }

    enhanceDownloadButtons() {
        // Find download report buttons
        const downloadButtons = document.querySelectorAll(
            'button[aria-label*="Download"], a[href*="download"], .download-report-btn'
        );
        
        downloadButtons.forEach(button => {
            if (!button.dataset.enhanced) {
                button.dataset.enhanced = 'true';
                
                // Add click listener to track downloads
                button.addEventListener('click', (e) => {
                    console.log('📥 Download button clicked');
                    this.trackDownloadClick(button);
                });
                
                // Add visual indicator
                button.style.position = 'relative';
                const badge = document.createElement('span');
                badge.textContent = '✓';
                badge.style.cssText = `
                    position: absolute;
                    top: -5px;
                    right: -5px;
                    background: #28a745;
                    color: white;
                    border-radius: 50%;
                    width: 16px;
                    height: 16px;
                    font-size: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                `;
                button.appendChild(badge);
            }
        });
        
        if (downloadButtons.length > 0) {
            console.log(`✅ Enhanced ${downloadButtons.length} download buttons`);
        }
    }

    trackDownloadClick(button) {
        // Store information about the download attempt
        chrome.runtime.sendMessage({
            type: 'downloadInitiated',
            data: {
                buttonText: button.textContent,
                href: button.href || button.getAttribute('href'),
                timestamp: new Date().toISOString()
            }
        });
    }

    showNotification(message, type = 'info') {
        // Send notification to background script
        chrome.runtime.sendMessage({
            type: 'showNotification',
            data: {
                message: message,
                type: type,
                timestamp: new Date().toISOString()
            }
        });

        // Also show in console with appropriate styling
        const styles = {
            success: 'color: #28a745; font-weight: bold;',
            error: 'color: #dc3545; font-weight: bold;',
            warning: 'color: #ffc107; font-weight: bold;',
            info: 'color: #17a2b8; font-weight: bold;'
        };
        
        console.log(`%c${type.toUpperCase()}: ${message}`, styles[type] || styles.info);
    }

    async saveProcessingHistory(historyEntry) {
        try {
            const history = await this.getFromStorage('processing_history') || [];
            history.unshift(historyEntry); // Add to beginning
            
            // Keep only last 100 entries
            if (history.length > 100) {
                history.length = 100;
            }
            
            await this.saveToStorage('processing_history', history);
            console.log('📝 Processing history saved');
        } catch (error) {
            console.error('Failed to save history:', error);
        }
    }

    async getFromStorage(key) {
        return new Promise((resolve) => {
            chrome.storage.local.get(key, (result) => {
                resolve(result[key]);
            });
        });
    }

    async saveToStorage(key, value) {
        return new Promise((resolve) => {
            chrome.storage.local.set({ [key]: value }, resolve);
        });
    }
}

// Initialize processor when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.ebayCSVProcessor = new EBayCSVProcessor();
    });
} else {
    window.ebayCSVProcessor = new EBayCSVProcessor();
}