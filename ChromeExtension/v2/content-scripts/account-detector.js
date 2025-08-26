/**
 * eBay Account Detection Module
 * Detects current eBay account from page content and URL
 */

window.EBayAccountDetector = (function() {
    'use strict';

    const { Logger, DOM, URL, StringUtil, EventUtil, Extension } = window.EBayCSVCommon;

    // Account mapping configuration
    const ACCOUNT_MAPPING = {
        'seller_pro_2025': {
            sheetId: '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM',
            accountName: 'eBay Seller Pro 2025',
            type: 'production',
            patterns: ['seller_pro_2025', 'sellerpro2025', 'seller-pro-2025']
        },
        'test_api_account': {
            sheetId: '1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c',
            accountName: 'Test API Account', 
            type: 'testing',
            patterns: ['test_api_account', 'testapi', 'test-api']
        },
        'test_workspace_account': {
            sheetId: '1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII',
            accountName: 'Test Workspace Account',
            type: 'testing',
            patterns: ['test_workspace_account', 'testworkspace', 'test-workspace']
        }
    };

    const FALLBACK_ACCOUNT = {
        id: 'default_account',
        sheetId: '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM', // Default to seller_pro_2025
        accountName: 'Default Account',
        type: 'fallback',
        patterns: []
    };

    class AccountDetector {
        constructor() {
            this.currentAccount = null;
            this.detectionMethods = [
                this.detectFromUserMenu.bind(this),
                this.detectFromURL.bind(this),
                this.detectFromPageContent.bind(this),
                this.detectFromLocalStorage.bind(this),
                this.detectFromCookies.bind(this)
            ];
            
            this.initialize();
        }

        async initialize() {
            Logger.log('Account detector initializing...');
            
            // Detect account on page load
            await this.detectAccount();
            
            // Set up mutation observer to detect account changes
            this.setupAccountMonitoring();
            
            // Listen for URL changes (SPA navigation)
            this.setupURLChangeListener();
            
            Logger.log('Account detector initialized');
        }

        setupAccountMonitoring() {
            // Monitor for changes in account-related elements
            const observer = new MutationObserver(EventUtil.debounce(async (mutations) => {
                let shouldRedetect = false;
                
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        // Check if any added nodes contain account information
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                if (this.containsAccountInfo(node)) {
                                    shouldRedetect = true;
                                }
                            }
                        });
                    }
                });

                if (shouldRedetect) {
                    Logger.log('Account-related DOM change detected, re-detecting account');
                    await this.detectAccount();
                }
            }, 1000));

            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: false
            });
        }

        containsAccountInfo(element) {
            const accountSelectors = [
                '[data-testid*="user"]',
                '[data-testid*="account"]',
                '.gh-ug',
                '.user-info',
                '.account-info'
            ];

            return accountSelectors.some(selector => 
                element.matches && element.matches(selector) ||
                element.querySelector && element.querySelector(selector)
            );
        }

        setupURLChangeListener() {
            let lastUrl = location.href;
            
            new MutationObserver(() => {
                const currentUrl = location.href;
                if (currentUrl !== lastUrl) {
                    lastUrl = currentUrl;
                    Logger.log('URL changed, re-detecting account');
                    setTimeout(() => this.detectAccount(), 1000);
                }
            }).observe(document.body, { childList: true, subtree: true });
        }

        async detectAccount() {
            Logger.log('Starting account detection...');

            for (const method of this.detectionMethods) {
                try {
                    const account = await method();
                    if (account) {
                        Logger.log(`Account detected via ${method.name}:`, account);
                        await this.setCurrentAccount(account);
                        return account;
                    }
                } catch (error) {
                    Logger.error(`Error in ${method.name}:`, error);
                }
            }

            // No account detected, use fallback
            Logger.warn('No account detected, using fallback');
            await this.setCurrentAccount(FALLBACK_ACCOUNT);
            return FALLBACK_ACCOUNT;
        }

        async detectFromUserMenu() {
            Logger.log('Attempting to detect account from user menu...');

            const userMenuSelectors = [
                '#gh-ug b',                    // Classic eBay header
                '.gh-ug b',                    // Alternative class
                '[data-testid="user-menu"] span',  // New eBay design
                '.user-info .username',        // Seller Hub
                '.gh-eb-u-id',                // eBay user ID
                '.notif-user-id',             // Notification area
                '.user-id',                   // Generic user ID
                '.seller-info .seller-name'    // Seller info section
            ];

            for (const selector of userMenuSelectors) {
                try {
                    const element = document.querySelector(selector);
                    if (element && element.textContent.trim()) {
                        const username = StringUtil.normalizeWhitespace(element.textContent.trim());
                        const account = this.mapUsernameToAccount(username);
                        if (account) {
                            return account;
                        }
                    }
                } catch (error) {
                    Logger.error(`Error checking selector ${selector}:`, error);
                }
            }

            return null;
        }

        async detectFromURL() {
            Logger.log('Attempting to detect account from URL...');

            const url = window.location.href;
            const patterns = [
                /[?&]seller[_-]?id[=:]([^&\?#]+)/i,
                /[?&]account[=:]([^&\?#]+)/i, 
                /[?&]user[=:]([^&\?#]+)/i,
                /[?&]_ssn[=:]([^&\?#]+)/i,
                /\/seller\/([^\/\?#]+)/i,
                /\/usr\/([^\/\?#]+)/i
            ];

            for (const pattern of patterns) {
                const match = url.match(pattern);
                if (match && match[1]) {
                    const username = decodeURIComponent(match[1]);
                    const account = this.mapUsernameToAccount(username);
                    if (account) {
                        return account;
                    }
                }
            }

            return null;
        }

        async detectFromPageContent() {
            Logger.log('Attempting to detect account from page content...');

            // Wait a bit for page content to load
            await new Promise(resolve => setTimeout(resolve, 1000));

            const contentSelectors = [
                '[data-testid*="seller"]',
                '.seller-info',
                '.account-name', 
                '.user-account',
                '.breadcrumb',
                '.page-title',
                'h1',
                '.seller-details'
            ];

            for (const selector of contentSelectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    for (const element of elements) {
                        const text = StringUtil.normalizeWhitespace(element.textContent);
                        const account = this.extractAccountFromText(text);
                        if (account) {
                            return account;
                        }
                    }
                } catch (error) {
                    Logger.error(`Error checking content selector ${selector}:`, error);
                }
            }

            return null;
        }

        async detectFromLocalStorage() {
            Logger.log('Attempting to detect account from localStorage...');

            try {
                const keys = [
                    'ebay_user', 'user_info', 'account_info', 
                    'seller_info', 'logged_in_user'
                ];

                for (const key of keys) {
                    const value = localStorage.getItem(key);
                    if (value) {
                        try {
                            const data = JSON.parse(value);
                            if (data.username || data.sellerId || data.userId) {
                                const username = data.username || data.sellerId || data.userId;
                                const account = this.mapUsernameToAccount(username);
                                if (account) {
                                    return account;
                                }
                            }
                        } catch (e) {
                            // If not JSON, treat as string
                            const account = this.mapUsernameToAccount(value);
                            if (account) {
                                return account;
                            }
                        }
                    }
                }
            } catch (error) {
                Logger.error('Error reading localStorage:', error);
            }

            return null;
        }

        async detectFromCookies() {
            Logger.log('Attempting to detect account from cookies...');

            try {
                const cookies = document.cookie.split(';');
                const accountCookies = ['ebay_user', 'userid', 'u1f', 'nonsession'];
                
                for (const cookie of cookies) {
                    const [name, value] = cookie.split('=').map(s => s.trim());
                    if (accountCookies.some(ac => name.toLowerCase().includes(ac))) {
                        if (value) {
                            const decodedValue = decodeURIComponent(value);
                            const account = this.extractAccountFromText(decodedValue);
                            if (account) {
                                return account;
                            }
                        }
                    }
                }
            } catch (error) {
                Logger.error('Error reading cookies:', error);
            }

            return null;
        }

        mapUsernameToAccount(username) {
            if (!username) return null;
            
            const normalizedUsername = username.toLowerCase().replace(/[^a-z0-9_-]/g, '');
            
            for (const [accountId, config] of Object.entries(ACCOUNT_MAPPING)) {
                // Direct match
                if (normalizedUsername === accountId.toLowerCase()) {
                    return this.createAccountObject(accountId, config, username);
                }
                
                // Pattern match
                if (config.patterns.some(pattern => 
                    normalizedUsername.includes(pattern.toLowerCase()) ||
                    pattern.toLowerCase().includes(normalizedUsername)
                )) {
                    return this.createAccountObject(accountId, config, username);
                }
            }

            return null;
        }

        extractAccountFromText(text) {
            if (!text) return null;

            const normalizedText = text.toLowerCase();
            
            for (const [accountId, config] of Object.entries(ACCOUNT_MAPPING)) {
                if (config.patterns.some(pattern => 
                    normalizedText.includes(pattern.toLowerCase())
                )) {
                    return this.createAccountObject(accountId, config, text);
                }
            }

            // Check for any meaningful account patterns in text
            const accountPatterns = [
                /seller[:\s]*([a-zA-Z0-9_-]+)/i,
                /account[:\s]*([a-zA-Z0-9_-]+)/i,
                /user[:\s]*([a-zA-Z0-9_-]+)/i
            ];

            for (const pattern of accountPatterns) {
                const match = text.match(pattern);
                if (match && match[1]) {
                    const extractedName = match[1];
                    const account = this.mapUsernameToAccount(extractedName);
                    if (account) {
                        return account;
                    }
                }
            }

            return null;
        }

        createAccountObject(accountId, config, detectedUsername) {
            return {
                id: accountId,
                sheetId: config.sheetId,
                accountName: config.accountName,
                type: config.type,
                detectedUsername: detectedUsername,
                detectedAt: new Date().toISOString(),
                detectionMethod: 'content_analysis'
            };
        }

        async setCurrentAccount(account) {
            this.currentAccount = account;
            
            Logger.log('Account set:', account);
            
            // Store in extension storage
            try {
                await Extension.setStorageData({ 
                    currentAccount: account,
                    accountDetectedAt: new Date().toISOString()
                });
            } catch (error) {
                Logger.error('Failed to store account in extension storage:', error);
            }

            // Notify background script
            try {
                await Extension.sendMessage({
                    action: 'ACCOUNT_DETECTED',
                    account: account
                });
            } catch (error) {
                Logger.error('Failed to notify background script of account detection:', error);
            }

            // Emit event for other scripts
            EventUtil.emit('accountDetected', account);
        }

        getCurrentAccount() {
            return this.currentAccount;
        }

        async forceRedetection() {
            Logger.log('Forcing account re-detection...');
            return await this.detectAccount();
        }
    }

    // Initialize account detector
    let accountDetector = null;

    function initialize() {
        if (!accountDetector) {
            accountDetector = new AccountDetector();
        }
        return accountDetector;
    }

    // Public API
    return {
        initialize,
        getCurrentAccount: () => accountDetector?.getCurrentAccount(),
        forceRedetection: () => accountDetector?.forceRedetection(),
        ACCOUNT_MAPPING
    };

})();

// Auto-initialize if we're on an eBay page
if (window.EBayCSVCommon.URL.isEBay()) {
    window.EBayAccountDetector.initialize();
}

window.EBayCSVCommon.Logger.log('Account detector script loaded');