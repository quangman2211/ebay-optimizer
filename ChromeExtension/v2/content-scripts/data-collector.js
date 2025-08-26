/**
 * eBay Data Collection Module  
 * Collects various types of data from eBay pages
 */

window.EBayDataCollector = (function() {
    'use strict';

    const { Logger, DOM, URL, StringUtil, Validator, EventUtil, Extension } = window.EBayCSVCommon;

    class DataCollector {
        constructor() {
            this.isCollecting = false;
            this.collectedData = {
                orders: [],
                listings: [],
                messages: [],
                pageInfo: {}
            };
            
            this.initialize();
        }

        initialize() {
            Logger.log('Data collector initializing...');
            
            // Set up page monitoring
            this.setupPageMonitoring();
            
            // Listen for collection requests
            EventUtil.listen('requestDataCollection', (event) => {
                this.collectData(event.detail?.type || 'all');
            });

            Logger.log('Data collector initialized');
        }

        setupPageMonitoring() {
            // Monitor page for data collection opportunities
            const observer = new MutationObserver(EventUtil.debounce(() => {
                this.detectDataOpportunities();
            }, 2000));

            observer.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: false
            });
        }

        async detectDataOpportunities() {
            const url = window.location.href;
            let pageType = null;
            let dataAvailable = false;

            if (URL.isOrdersPage(url)) {
                pageType = 'orders';
                dataAvailable = this.hasOrdersData();
            } else if (URL.isListingsPage(url)) {
                pageType = 'listings';
                dataAvailable = this.hasListingsData();
            }

            if (pageType && dataAvailable) {
                const pageInfo = {
                    type: pageType,
                    url: url,
                    dataAvailable: dataAvailable,
                    detectedAt: new Date().toISOString()
                };

                EventUtil.emit('ebayPageReady', pageInfo);
                Logger.log(`eBay ${pageType} page ready with data`);
            }
        }

        hasOrdersData() {
            const orderSelectors = [
                '[data-testid*="order"]',
                '.order-row',
                '.grid-row',
                '.selling-order',
                '.order-details'
            ];

            return orderSelectors.some(selector => {
                const elements = document.querySelectorAll(selector);
                return elements.length > 0;
            });
        }

        hasListingsData() {
            const listingSelectors = [
                '[data-testid*="listing"]',
                '.listing-row',
                '.item-row',
                '.selling-item',
                '.listing-details'
            ];

            return listingSelectors.some(selector => {
                const elements = document.querySelectorAll(selector);
                return elements.length > 0;
            });
        }

        async collectData(type = 'all') {
            if (this.isCollecting) {
                Logger.warn('Data collection already in progress');
                return null;
            }

            this.isCollecting = true;
            Logger.log(`Starting data collection: ${type}`);

            try {
                const result = { success: false, data: {} };

                if (type === 'all' || type === 'orders') {
                    result.data.orders = await this.collectOrders();
                }

                if (type === 'all' || type === 'listings') {
                    result.data.listings = await this.collectListings();
                }

                if (type === 'all' || type === 'messages') {
                    result.data.messages = await this.collectMessages();
                }

                result.data.pageInfo = this.collectPageInfo();
                result.success = true;

                Logger.log('Data collection completed:', {
                    orders: result.data.orders?.length || 0,
                    listings: result.data.listings?.length || 0,
                    messages: result.data.messages?.length || 0
                });

                return result;

            } catch (error) {
                Logger.error('Data collection failed:', error);
                return { success: false, error: error.message };
            } finally {
                this.isCollecting = false;
            }
        }

        async collectOrders() {
            Logger.log('Collecting orders data...');

            const orders = [];
            const orderSelectors = [
                '[data-testid*="order-row"]',
                '.order-row',
                '.grid-row',
                '.selling-order',
                '.order-item'
            ];

            for (const selector of orderSelectors) {
                const orderElements = document.querySelectorAll(selector);
                if (orderElements.length > 0) {
                    Logger.log(`Found ${orderElements.length} order elements with selector: ${selector}`);

                    for (const element of orderElements) {
                        try {
                            const order = await this.extractOrderData(element);
                            if (order && this.isValidOrder(order)) {
                                orders.push(order);
                            }
                        } catch (error) {
                            Logger.error('Error extracting order from element:', error);
                        }
                    }
                    break; // Use first successful selector
                }
            }

            Logger.log(`Collected ${orders.length} orders`);
            return this.deduplicateOrders(orders);
        }

        async extractOrderData(element) {
            const order = {
                // Order identification
                order_id: this.extractText(element, [
                    '[data-testid*="order-id"]',
                    '.order-id',
                    '.order-number',
                    '.transaction-id'
                ]),

                sales_record_number: this.extractText(element, [
                    '[data-testid*="sales-record"]',
                    '.sales-record',
                    '.record-number'
                ]),

                // Buyer information
                buyer_username: this.extractText(element, [
                    '[data-testid*="buyer-name"]',
                    '.buyer-name',
                    '.buyer-username',
                    '.customer-name'
                ]),

                buyer_name: this.extractText(element, [
                    '[data-testid*="buyer-full-name"]',
                    '.buyer-full-name',
                    '.customer-full-name'
                ]),

                buyer_email: this.extractText(element, [
                    '[data-testid*="buyer-email"]',
                    '.buyer-email',
                    '.customer-email'
                ]),

                // Item information
                item_number: this.extractText(element, [
                    '[data-testid*="item-number"]',
                    '.item-number',
                    '.item-id',
                    '.listing-id'
                ]),

                item_title: this.extractText(element, [
                    '[data-testid*="item-title"]',
                    '.item-title',
                    '.product-title',
                    '.listing-title'
                ]),

                custom_label: this.extractText(element, [
                    '[data-testid*="custom-label"]',
                    '.custom-label',
                    '.sku',
                    '.product-sku'
                ]),

                // Quantities and pricing
                quantity: this.extractNumber(element, [
                    '[data-testid*="quantity"]',
                    '.quantity',
                    '.qty',
                    '.item-qty'
                ]),

                sold_for: this.extractCurrency(element, [
                    '[data-testid*="sold-for"]',
                    '.sold-for',
                    '.item-price',
                    '.unit-price'
                ]),

                total_price: this.extractCurrency(element, [
                    '[data-testid*="total-price"]',
                    '.total-price',
                    '.order-total',
                    '.final-price'
                ]),

                // Dates
                sale_date: this.extractDate(element, [
                    '[data-testid*="sale-date"]',
                    '.sale-date',
                    '.order-date',
                    '.purchase-date'
                ]),

                paid_date: this.extractDate(element, [
                    '[data-testid*="paid-date"]',
                    '.paid-date',
                    '.payment-date'
                ]),

                ship_by_date: this.extractDate(element, [
                    '[data-testid*="ship-by"]',
                    '.ship-by-date',
                    '.shipping-deadline'
                ]),

                // Status and tracking
                status: this.extractText(element, [
                    '[data-testid*="order-status"]',
                    '.order-status',
                    '.status',
                    '.fulfillment-status'
                ]),

                tracking_number: this.extractText(element, [
                    '[data-testid*="tracking"]',
                    '.tracking-number',
                    '.shipping-tracking'
                ]),

                // Additional fields
                shipping_service: this.extractText(element, [
                    '[data-testid*="shipping-service"]',
                    '.shipping-service',
                    '.delivery-method'
                ]),

                payment_method: this.extractText(element, [
                    '[data-testid*="payment-method"]',
                    '.payment-method',
                    '.payment-type'
                ]),

                // Meta information
                extracted_at: new Date().toISOString(),
                source: 'page_scraping'
            };

            return order;
        }

        async collectListings() {
            Logger.log('Collecting listings data...');

            const listings = [];
            const listingSelectors = [
                '[data-testid*="listing-row"]',
                '.listing-row',
                '.item-row',
                '.selling-item',
                '.listing-item'
            ];

            for (const selector of listingSelectors) {
                const listingElements = document.querySelectorAll(selector);
                if (listingElements.length > 0) {
                    Logger.log(`Found ${listingElements.length} listing elements with selector: ${selector}`);

                    for (const element of listingElements) {
                        try {
                            const listing = await this.extractListingData(element);
                            if (listing && this.isValidListing(listing)) {
                                listings.push(listing);
                            }
                        } catch (error) {
                            Logger.error('Error extracting listing from element:', error);
                        }
                    }
                    break; // Use first successful selector
                }
            }

            Logger.log(`Collected ${listings.length} listings`);
            return this.deduplicateListings(listings);
        }

        async extractListingData(element) {
            const listing = {
                // Listing identification
                item_number: this.extractText(element, [
                    '[data-testid*="item-number"]',
                    '.item-number',
                    '.item-id',
                    '.listing-id'
                ]),

                title: this.extractText(element, [
                    '[data-testid*="item-title"]',
                    '.item-title',
                    '.listing-title',
                    '.product-title'
                ]),

                custom_label: this.extractText(element, [
                    '[data-testid*="custom-label"]',
                    '.custom-label',
                    '.sku',
                    '.product-sku'
                ]),

                // Quantities and pricing
                available_quantity: this.extractNumber(element, [
                    '[data-testid*="available-quantity"]',
                    '.available-quantity',
                    '.qty-available',
                    '.stock-level'
                ]),

                current_price: this.extractCurrency(element, [
                    '[data-testid*="current-price"]',
                    '.current-price',
                    '.price',
                    '.listing-price'
                ]),

                sold_quantity: this.extractNumber(element, [
                    '[data-testid*="sold-quantity"]',
                    '.sold-quantity',
                    '.qty-sold',
                    '.sales-count'
                ]),

                // Engagement metrics
                watchers: this.extractNumber(element, [
                    '[data-testid*="watchers"]',
                    '.watchers',
                    '.watching-count',
                    '.watchers-count'
                ]),

                views: this.extractNumber(element, [
                    '[data-testid*="views"]',
                    '.views',
                    '.view-count',
                    '.page-views'
                ]),

                // Dates
                start_date: this.extractDate(element, [
                    '[data-testid*="start-date"]',
                    '.start-date',
                    '.listing-start',
                    '.created-date'
                ]),

                end_date: this.extractDate(element, [
                    '[data-testid*="end-date"]',
                    '.end-date',
                    '.listing-end',
                    '.expiry-date'
                ]),

                // Listing details
                status: this.extractText(element, [
                    '[data-testid*="listing-status"]',
                    '.listing-status',
                    '.status',
                    '.item-status'
                ]),

                format: this.extractText(element, [
                    '[data-testid*="format"]',
                    '.listing-format',
                    '.sale-format',
                    '.format-type'
                ]),

                condition: this.extractText(element, [
                    '[data-testid*="condition"]',
                    '.condition',
                    '.item-condition'
                ]),

                category: this.extractText(element, [
                    '[data-testid*="category"]',
                    '.category',
                    '.item-category'
                ]),

                // Meta information
                extracted_at: new Date().toISOString(),
                source: 'page_scraping'
            };

            return listing;
        }

        async collectMessages() {
            Logger.log('Collecting messages data...');
            // Messages collection implementation would go here
            // For now, return empty array as messages are less critical
            return [];
        }

        collectPageInfo() {
            return {
                url: window.location.href,
                title: document.title,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                domain: window.location.hostname,
                path: window.location.pathname
            };
        }

        // Helper methods for data extraction
        extractText(element, selectors) {
            for (const selector of selectors) {
                const found = element.querySelector(selector);
                if (found && found.textContent.trim()) {
                    return StringUtil.normalizeWhitespace(found.textContent.trim());
                }
            }
            return '';
        }

        extractNumber(element, selectors) {
            const text = this.extractText(element, selectors);
            if (!text) return 0;
            const numbers = StringUtil.extractNumbers(text);
            return parseInt(numbers) || 0;
        }

        extractCurrency(element, selectors) {
            const text = this.extractText(element, selectors);
            if (!text) return 0;
            return StringUtil.extractCurrency(text);
        }

        extractDate(element, selectors) {
            const text = this.extractText(element, selectors);
            if (!text) return null;
            
            try {
                const date = new Date(text);
                return !isNaN(date.getTime()) ? date.toISOString() : null;
            } catch (error) {
                return null;
            }
        }

        // Validation methods
        isValidOrder(order) {
            return order.order_id && order.buyer_username && order.item_number && order.total_price > 0;
        }

        isValidListing(listing) {
            return listing.item_number && listing.title && listing.current_price >= 0;
        }

        // Deduplication methods
        deduplicateOrders(orders) {
            const seen = new Set();
            return orders.filter(order => {
                const key = `${order.order_id}-${order.item_number}`;
                if (seen.has(key)) {
                    return false;
                }
                seen.add(key);
                return true;
            });
        }

        deduplicateListings(listings) {
            const seen = new Set();
            return listings.filter(listing => {
                const key = listing.item_number;
                if (seen.has(key)) {
                    return false;
                }
                seen.add(key);
                return true;
            });
        }
    }

    // Initialize data collector
    let dataCollector = null;

    function initialize() {
        if (!dataCollector) {
            dataCollector = new DataCollector();
        }
        return dataCollector;
    }

    // Public API
    return {
        initialize,
        collectData: (type) => dataCollector?.collectData(type),
        isCollecting: () => dataCollector?.isCollecting || false
    };

})();

// Auto-initialize if we're on an eBay page
if (window.EBayCSVCommon.URL.isEBay()) {
    window.EBayDataCollector.initialize();
}

window.EBayCSVCommon.Logger.log('Data collector script loaded');