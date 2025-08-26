/**
 * Common utilities and helper functions for eBay CSV Processor Extension
 * Provides shared functionality across all content scripts
 */

window.EBayCSVCommon = (function() {
    'use strict';

    // Extension configuration
    const CONFIG = {
        DEBUG: true,
        CSV_PATTERNS: {
            orders: /eBay-awaiting-shipment-report-.*\.csv$/i,
            listings: /eBay-all-active-listings-report-.*\.csv$/i,
            soldListings: /eBay-sold-listings-report-.*\.csv$/i
        },
        EBAY_DOMAINS: ['ebay.com', 'ebay.co.uk', 'ebay.de', 'ebay.fr'],
        TIMEOUT: {
            API_REQUEST: 30000,
            AUTH_TIMEOUT: 60000,
            RETRY_DELAY: 2000
        }
    };

    // Logging utility
    const Logger = {
        log: function(message, data = null) {
            if (CONFIG.DEBUG) {
                const timestamp = new Date().toISOString();
                const prefix = '[eBay CSV Processor]';
                if (data) {
                    console.log(`${prefix} ${timestamp}: ${message}`, data);
                } else {
                    console.log(`${prefix} ${timestamp}: ${message}`);
                }
            }
        },
        error: function(message, error = null) {
            const timestamp = new Date().toISOString();
            const prefix = '[eBay CSV ERROR]';
            if (error) {
                console.error(`${prefix} ${timestamp}: ${message}`, error);
            } else {
                console.error(`${prefix} ${timestamp}: ${message}`);
            }
        },
        warn: function(message, data = null) {
            if (CONFIG.DEBUG) {
                const timestamp = new Date().toISOString();
                const prefix = '[eBay CSV WARN]';
                if (data) {
                    console.warn(`${prefix} ${timestamp}: ${message}`, data);
                } else {
                    console.warn(`${prefix} ${timestamp}: ${message}`);
                }
            }
        }
    };

    // DOM utilities
    const DOM = {
        waitForElement: function(selector, timeout = 5000) {
            return new Promise((resolve, reject) => {
                const element = document.querySelector(selector);
                if (element) {
                    resolve(element);
                    return;
                }

                const observer = new MutationObserver((mutations) => {
                    const element = document.querySelector(selector);
                    if (element) {
                        observer.disconnect();
                        resolve(element);
                    }
                });

                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });

                setTimeout(() => {
                    observer.disconnect();
                    reject(new Error(`Element ${selector} not found within ${timeout}ms`));
                }, timeout);
            });
        },

        isVisible: function(element) {
            if (!element) return false;
            const style = window.getComputedStyle(element);
            return style.display !== 'none' && 
                   style.visibility !== 'hidden' && 
                   style.opacity !== '0' &&
                   element.offsetHeight > 0;
        },

        getTextContent: function(element) {
            if (!element) return '';
            return element.textContent.trim();
        },

        getAllTextContents: function(elements) {
            return Array.from(elements).map(el => this.getTextContent(el));
        }
    };

    // URL utilities
    const URL = {
        isEBay: function(url = window.location.href) {
            return CONFIG.EBAY_DOMAINS.some(domain => url.includes(domain));
        },

        getEBayDomain: function(url = window.location.href) {
            for (const domain of CONFIG.EBAY_DOMAINS) {
                if (url.includes(domain)) {
                    return domain;
                }
            }
            return null;
        },

        isOrdersPage: function(url = window.location.href) {
            const patterns = [
                /\/sh\/ord/i,
                /\/mys\/orders/i,
                /\/orderdetails/i,
                /orders/i
            ];
            return patterns.some(pattern => pattern.test(url));
        },

        isListingsPage: function(url = window.location.href) {
            const patterns = [
                /\/sh\/lst/i,
                /\/mys\/listings/i,
                /\/sellinghub\/listings/i,
                /listings/i
            ];
            return patterns.some(pattern => pattern.test(url));
        },

        isSellerHub: function(url = window.location.href) {
            return url.includes('/sh/') || url.includes('/sellinghub/');
        }
    };

    // Data validation utilities
    const Validator = {
        isValidEmail: function(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },

        isValidCurrency: function(value) {
            if (!value) return false;
            const currencyRegex = /^\$?[0-9,]+(\.[0-9]{2})?$/;
            return currencyRegex.test(value.toString());
        },

        isValidDate: function(dateStr) {
            if (!dateStr) return false;
            const date = new Date(dateStr);
            return !isNaN(date.getTime());
        },

        isValidItemNumber: function(itemNum) {
            if (!itemNum) return false;
            // eBay item numbers are typically 12-digit numbers
            const itemRegex = /^[0-9]{10,15}$/;
            return itemRegex.test(itemNum.toString());
        }
    };

    // String utilities
    const StringUtil = {
        stripHtml: function(html) {
            const div = document.createElement('div');
            div.innerHTML = html;
            return div.textContent || div.innerText || '';
        },

        extractNumbers: function(str) {
            if (!str) return '';
            return str.replace(/[^0-9]/g, '');
        },

        extractCurrency: function(str) {
            if (!str) return 0;
            const cleaned = str.replace(/[$,]/g, '');
            return parseFloat(cleaned) || 0;
        },

        normalizeWhitespace: function(str) {
            if (!str) return '';
            return str.replace(/\s+/g, ' ').trim();
        },

        truncate: function(str, length = 50) {
            if (!str) return '';
            return str.length > length ? str.substring(0, length) + '...' : str;
        }
    };

    // Event utilities
    const EventUtil = {
        debounce: function(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        },

        throttle: function(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        emit: function(eventName, data = null) {
            const event = new CustomEvent(eventName, {
                detail: data,
                bubbles: true,
                cancelable: true
            });
            document.dispatchEvent(event);
            Logger.log(`Event emitted: ${eventName}`, data);
        },

        listen: function(eventName, callback) {
            document.addEventListener(eventName, callback);
            Logger.log(`Event listener added: ${eventName}`);
        }
    };

    // Chrome Extension utilities
    const Extension = {
        sendMessage: function(message) {
            return new Promise((resolve, reject) => {
                if (typeof chrome !== 'undefined' && chrome.runtime) {
                    chrome.runtime.sendMessage(message, (response) => {
                        if (chrome.runtime.lastError) {
                            Logger.error('Extension message error:', chrome.runtime.lastError);
                            reject(new Error(chrome.runtime.lastError.message));
                        } else {
                            Logger.log('Extension message sent:', message.action);
                            resolve(response);
                        }
                    });
                } else {
                    Logger.warn('Chrome runtime not available, using mock response');
                    // Mock response for testing
                    setTimeout(() => resolve({ success: true, mock: true }), 100);
                }
            });
        },

        getStorageData: function(keys) {
            return new Promise((resolve, reject) => {
                if (typeof chrome !== 'undefined' && chrome.storage) {
                    chrome.storage.local.get(keys, (result) => {
                        if (chrome.runtime.lastError) {
                            reject(new Error(chrome.runtime.lastError.message));
                        } else {
                            resolve(result);
                        }
                    });
                } else {
                    // Mock storage for testing
                    resolve({});
                }
            });
        },

        setStorageData: function(data) {
            return new Promise((resolve, reject) => {
                if (typeof chrome !== 'undefined' && chrome.storage) {
                    chrome.storage.local.set(data, () => {
                        if (chrome.runtime.lastError) {
                            reject(new Error(chrome.runtime.lastError.message));
                        } else {
                            resolve();
                        }
                    });
                } else {
                    // Mock storage for testing
                    resolve();
                }
            });
        }
    };

    // CSV utilities
    const CSV = {
        isEBayCSV: function(filename) {
            return Object.values(CONFIG.CSV_PATTERNS).some(pattern => 
                pattern.test(filename)
            );
        },

        getCSVType: function(filename) {
            for (const [type, pattern] of Object.entries(CONFIG.CSV_PATTERNS)) {
                if (pattern.test(filename)) {
                    return type;
                }
            }
            return null;
        },

        parseCSVLine: function(line) {
            const result = [];
            let current = '';
            let inQuotes = false;
            
            for (let i = 0; i < line.length; i++) {
                const char = line[i];
                const nextChar = line[i + 1];
                
                if (char === '"') {
                    if (inQuotes && nextChar === '"') {
                        current += '"';
                        i++; // Skip next quote
                    } else {
                        inQuotes = !inQuotes;
                    }
                } else if (char === ',' && !inQuotes) {
                    result.push(current.trim());
                    current = '';
                } else {
                    current += char;
                }
            }
            
            result.push(current.trim());
            return result;
        }
    };

    // Initialize common functionality
    function initialize() {
        Logger.log('Common utilities initialized');
        
        // Set up global error handler for extension
        window.addEventListener('error', (event) => {
            Logger.error('Global error in extension:', {
                message: event.message,
                filename: event.filename,
                line: event.lineno,
                column: event.colno,
                error: event.error
            });
        });

        // Set up unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (event) => {
            Logger.error('Unhandled promise rejection:', event.reason);
        });
    }

    // Initialize when script loads
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // Public API
    return {
        CONFIG,
        Logger,
        DOM,
        URL,
        Validator,
        StringUtil,
        EventUtil,
        Extension,
        CSV,
        initialize
    };

})();

// Log that common utilities are loaded
window.EBayCSVCommon.Logger.log('Common utilities script loaded');