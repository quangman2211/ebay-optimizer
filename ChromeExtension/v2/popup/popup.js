/**
 * eBay CSV Processor Extension Popup
 * Main UI controller for the extension popup
 */

class PopupController {
    constructor() {
        this.currentAccount = null;
        this.extensionStatus = 'initializing';
        this.logs = [];
        this.settings = {
            debugMode: true,
            autoProcess: true,
            notifications: true
        };
        
        this.initialize();
    }

    async initialize() {
        console.log('🚀 Popup initializing...');
        
        // Load settings
        await this.loadSettings();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Initialize UI
        this.initializeUI();
        
        // Check extension status
        await this.checkExtensionStatus();
        
        // Load current account
        await this.loadCurrentAccount();
        
        // Load recent activity
        await this.loadRecentActivity();
        
        console.log('✅ Popup initialized');
    }

    setupEventListeners() {
        // Account refresh button
        document.getElementById('refreshAccountBtn').addEventListener('click', () => {
            this.refreshAccount();
        });

        // Test buttons
        document.getElementById('testCSVBtn').addEventListener('click', () => {
            this.testCSVProcessing();
        });

        document.getElementById('testSheetsBtn').addEventListener('click', () => {
            this.testSheetsConnection();
        });

        document.getElementById('simulateDownloadBtn').addEventListener('click', () => {
            this.simulateDownload();
        });

        // Clear logs button
        document.getElementById('clearLogsBtn').addEventListener('click', () => {
            this.clearLogs();
        });

        // Quick action buttons
        document.getElementById('openSimulatorBtn').addEventListener('click', () => {
            this.openSimulator();
        });

        document.getElementById('viewSheetsBtn').addEventListener('click', () => {
            this.viewGoogleSheets();
        });

        document.getElementById('exportLogsBtn').addEventListener('click', () => {
            this.exportLogs();
        });

        // Settings toggle
        document.getElementById('settingsToggle').addEventListener('click', () => {
            this.toggleSettings();
        });

        // Settings checkboxes
        document.getElementById('debugMode').addEventListener('change', (e) => {
            this.updateSetting('debugMode', e.target.checked);
        });

        document.getElementById('autoProcess').addEventListener('change', (e) => {
            this.updateSetting('autoProcess', e.target.checked);
        });

        document.getElementById('notifications').addEventListener('change', (e) => {
            this.updateSetting('notifications', e.target.checked);
        });

        // Footer links
        document.getElementById('helpBtn').addEventListener('click', () => {
            this.showHelp();
        });

        document.getElementById('aboutBtn').addEventListener('click', () => {
            this.showAbout();
        });

        document.getElementById('feedbackBtn').addEventListener('click', () => {
            this.showFeedback();
        });
    }

    initializeUI() {
        // Set initial status
        this.updateExtensionStatus('Ready');
        
        // Load settings into UI
        document.getElementById('debugMode').checked = this.settings.debugMode;
        document.getElementById('autoProcess').checked = this.settings.autoProcess;
        document.getElementById('notifications').checked = this.settings.notifications;
        
        // Add initial log
        this.addLog('Extension popup opened', 'info');
    }

    async checkExtensionStatus() {
        try {
            this.updateConnectionStatus('checking');
            
            const response = await this.sendMessage({ action: 'GET_STATUS' });
            
            if (response && response.status) {
                this.updateConnectionStatus('connected');
                this.extensionStatus = response.status;
            } else {
                this.updateConnectionStatus('error');
                this.addLog('Background script not responding', 'error');
            }
        } catch (error) {
            this.updateConnectionStatus('error');
            this.addLog(`Connection error: ${error.message}`, 'error');
        }
    }

    async loadCurrentAccount() {
        try {
            this.updateAccountStatus('detecting');
            
            const response = await this.sendMessage({ action: 'GET_ACCOUNT_INFO' });
            
            if (response && response.success && response.account) {
                this.currentAccount = response.account;
                this.updateAccountDisplay(response.account);
                this.updateAccountStatus('detected');
                
                // Update sheet status
                if (response.sheetConfig) {
                    this.updateSheetStatus('configured');
                } else {
                    this.updateSheetStatus('not_configured');
                }
                
                this.addLog(`Account detected: ${response.account.accountName || response.account.id}`, 'success');
            } else {
                this.updateAccountStatus('not_found');
                this.updateSheetStatus('pending');
                this.addLog('No account detected', 'warning');
            }
        } catch (error) {
            this.updateAccountStatus('error');
            this.addLog(`Account detection failed: ${error.message}`, 'error');
        }
    }

    async loadRecentActivity() {
        try {
            const storage = await this.getStorageData(['csvProcessingLog', 'csvErrorLog']);
            
            if (storage.csvProcessingLog && storage.csvProcessingLog.length > 0) {
                const recent = storage.csvProcessingLog.slice(-5);
                recent.forEach(entry => {
                    const message = `Processed ${entry.recordCount} ${entry.type} records`;
                    this.addLog(message, 'success', entry.timestamp);
                });
            }
            
            if (storage.csvErrorLog && storage.csvErrorLog.length > 0) {
                const recentErrors = storage.csvErrorLog.slice(-3);
                recentErrors.forEach(entry => {
                    this.addLog(`Error: ${entry.error}`, 'error', entry.timestamp);
                });
            }
            
            this.updateProcessingStats(storage.csvProcessingLog || []);
        } catch (error) {
            this.addLog(`Failed to load activity: ${error.message}`, 'error');
        }
    }

    updateProcessingStats(logs) {
        const totalRecords = logs.reduce((sum, entry) => sum + (entry.recordCount || 0), 0);
        const successCount = logs.filter(entry => entry.status === 'success').length;
        const successRate = logs.length > 0 ? Math.round((successCount / logs.length) * 100) : 0;
        const lastProcessed = logs.length > 0 ? new Date(logs[logs.length - 1].timestamp).toLocaleString() : 'None';
        
        document.getElementById('recordsProcessed').textContent = totalRecords.toString();
        document.getElementById('successRate').textContent = `${successRate}%`;
        document.getElementById('lastProcessed').textContent = lastProcessed;
    }

    // Status update methods
    updateConnectionStatus(status) {
        const element = document.getElementById('connectionStatus');
        const value = document.getElementById('connectionValue');
        
        element.classList.remove('connected', 'error', 'warning');
        
        switch (status) {
            case 'connected':
                element.classList.add('connected');
                value.textContent = 'Connected';
                value.className = 'status-value success';
                break;
            case 'error':
                element.classList.add('error');
                value.textContent = 'Error';
                value.className = 'status-value error';
                break;
            case 'checking':
            default:
                value.textContent = 'Checking...';
                value.className = 'status-value';
                break;
        }
    }

    updateAccountStatus(status) {
        const element = document.getElementById('accountStatus');
        const value = document.getElementById('accountValue');
        
        element.classList.remove('connected', 'error', 'warning');
        
        switch (status) {
            case 'detected':
                element.classList.add('connected');
                value.textContent = 'Detected';
                value.className = 'status-value success';
                break;
            case 'not_found':
                element.classList.add('warning');
                value.textContent = 'Not Found';
                value.className = 'status-value warning';
                break;
            case 'error':
                element.classList.add('error');
                value.textContent = 'Error';
                value.className = 'status-value error';
                break;
            case 'detecting':
            default:
                value.textContent = 'Detecting...';
                value.className = 'status-value';
                break;
        }
    }

    updateSheetStatus(status) {
        const element = document.getElementById('sheetStatus');
        const value = document.getElementById('sheetValue');
        
        element.classList.remove('connected', 'error', 'warning');
        
        switch (status) {
            case 'configured':
                element.classList.add('connected');
                value.textContent = 'Ready';
                value.className = 'status-value success';
                break;
            case 'not_configured':
                element.classList.add('warning');
                value.textContent = 'Not Configured';
                value.className = 'status-value warning';
                break;
            case 'error':
                element.classList.add('error');
                value.textContent = 'Error';
                value.className = 'status-value error';
                break;
            case 'pending':
            default:
                value.textContent = 'Pending';
                value.className = 'status-value';
                break;
        }
    }

    updateAccountDisplay(account) {
        document.getElementById('currentAccount').textContent = account.accountName || account.id || 'Unknown';
        document.getElementById('currentSheetId').textContent = account.sheetId || 'Not configured';
        document.getElementById('accountType').textContent = account.type || 'Unknown';
    }

    updateExtensionStatus(status) {
        const element = document.getElementById('extensionStatus');
        element.textContent = status;
        
        // Update class based on status
        element.className = status.toLowerCase().includes('error') ? 'status-error' :
                          status.toLowerCase().includes('warning') ? 'status-warning' :
                          'status-ok';
    }

    // Action methods
    async refreshAccount() {
        const btn = document.getElementById('refreshAccountBtn');
        btn.classList.add('loading');
        btn.disabled = true;
        
        try {
            const response = await this.sendMessage({ action: 'ACCOUNT_DETECTED', forceRedetect: true });
            await this.loadCurrentAccount();
            this.addLog('Account refreshed', 'success');
        } catch (error) {
            this.addLog(`Account refresh failed: ${error.message}`, 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    async testCSVProcessing() {
        const btn = document.getElementById('testCSVBtn');
        btn.classList.add('loading');
        btn.disabled = true;
        
        try {
            this.addLog('Testing CSV processing...', 'info');
            
            // Get mock CSV data
            const mockData = document.getElementById('mockCSVData').value;
            
            // Simulate CSV download event
            const testEvent = {
                type: 'orders',
                filename: `eBay-awaiting-shipment-report-test-${Date.now()}.csv`,
                data: mockData,
                recordCount: 2,
                totalValue: '$142.43'
            };

            // Send to content script for processing
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tabs[0]) {
                await chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'TEST_CSV_PROCESSING',
                    csvData: testEvent
                });
                
                this.addLog('CSV test processing initiated', 'success');
            } else {
                throw new Error('No active tab found');
            }
        } catch (error) {
            this.addLog(`CSV test failed: ${error.message}`, 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    async testSheetsConnection() {
        const btn = document.getElementById('testSheetsBtn');
        btn.classList.add('loading');
        btn.disabled = true;
        
        try {
            this.addLog('Testing Google Sheets connection...', 'info');
            
            const response = await this.sendMessage({
                action: 'WRITE_CSV_TO_SHEETS',
                sheetId: this.currentAccount?.sheetId || '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM',
                csvData: [{
                    sales_record_number: 'TEST',
                    order_number: 'TEST-ORDER-' + Date.now(),
                    buyer_name: 'Test User',
                    item_title: 'Test Item',
                    total_price: 1.00,
                    status: 'test',
                    account: 'test',
                    last_updated: new Date().toISOString()
                }],
                type: 'orders',
                account: this.currentAccount || { name: 'test' }
            });
            
            if (response && response.success) {
                this.addLog('Google Sheets connection test successful', 'success');
            } else {
                throw new Error(response?.error || 'Unknown error');
            }
        } catch (error) {
            this.addLog(`Sheets test failed: ${error.message}`, 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    async simulateDownload() {
        const btn = document.getElementById('simulateDownloadBtn');
        btn.classList.add('loading');
        btn.disabled = true;
        
        try {
            this.addLog('Simulating CSV download...', 'info');
            
            // Dispatch custom event to simulate download
            const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
            if (tabs[0]) {
                await chrome.tabs.sendMessage(tabs[0].id, {
                    action: 'SIMULATE_CSV_DOWNLOAD'
                });
                
                this.addLog('Download simulation triggered', 'success');
            } else {
                throw new Error('No active tab found');
            }
        } catch (error) {
            this.addLog(`Simulation failed: ${error.message}`, 'error');
        } finally {
            btn.classList.remove('loading');
            btn.disabled = false;
        }
    }

    openSimulator() {
        const simulatorURL = chrome.runtime.getURL('../temp/ebay-orders-simulator.html');
        chrome.tabs.create({ url: simulatorURL });
        this.addLog('Simulator opened', 'info');
    }

    viewGoogleSheets() {
        if (this.currentAccount && this.currentAccount.sheetId) {
            const sheetsURL = `https://docs.google.com/spreadsheets/d/${this.currentAccount.sheetId}/edit`;
            chrome.tabs.create({ url: sheetsURL });
            this.addLog('Google Sheets opened', 'info');
        } else {
            this.addLog('No sheet configured for current account', 'warning');
        }
    }

    exportLogs() {
        const logsText = this.logs.map(log => `[${log.time}] ${log.message}`).join('\n');
        const blob = new Blob([logsText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `ebay-csv-processor-logs-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        
        URL.revokeObjectURL(url);
        this.addLog('Logs exported', 'info');
    }

    clearLogs() {
        this.logs = [];
        document.getElementById('recentLogs').innerHTML = '<div class="log-item"><span class="log-time">--:--</span><span class="log-message">Logs cleared</span></div>';
        this.addLog('Logs cleared', 'info');
    }

    toggleSettings() {
        const section = document.querySelector('.section.collapsed, .section:not(.collapsed)');
        section.classList.toggle('collapsed');
    }

    showHelp() {
        const helpURL = chrome.runtime.getURL('../temp/E2E_TESTING_GUIDE.md');
        chrome.tabs.create({ url: helpURL });
        this.addLog('Help opened', 'info');
    }

    showAbout() {
        alert('eBay CSV Processor v2.2.0\n\nAutomatically processes eBay CSV downloads and syncs to Google Sheets.\n\nDeveloped for efficient eBay data management.');
    }

    showFeedback() {
        chrome.tabs.create({ url: 'https://github.com/your-repo/issues' });
    }

    // Utility methods
    addLog(message, type = 'info', timestamp = null) {
        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        const log = { time, message, type };
        
        this.logs.push(log);
        
        const logsContainer = document.getElementById('recentLogs');
        const logItem = document.createElement('div');
        logItem.className = `log-item ${type}`;
        logItem.innerHTML = `<span class="log-time">${time}</span><span class="log-message">${message}</span>`;
        
        logsContainer.appendChild(logItem);
        logsContainer.scrollTop = logsContainer.scrollHeight;
        
        // Keep only last 50 logs
        if (this.logs.length > 50) {
            this.logs = this.logs.slice(-50);
            const items = logsContainer.querySelectorAll('.log-item');
            if (items.length > 50) {
                items[0].remove();
            }
        }
    }

    async sendMessage(message) {
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(message, (response) => {
                if (chrome.runtime.lastError) {
                    reject(new Error(chrome.runtime.lastError.message));
                } else {
                    resolve(response);
                }
            });
        });
    }

    async getStorageData(keys) {
        return new Promise((resolve) => {
            chrome.storage.local.get(keys, resolve);
        });
    }

    async setStorageData(data) {
        return new Promise((resolve) => {
            chrome.storage.local.set(data, resolve);
        });
    }

    async loadSettings() {
        const data = await this.getStorageData(['extensionSettings']);
        if (data.extensionSettings) {
            this.settings = { ...this.settings, ...data.extensionSettings };
        }
    }

    async updateSetting(key, value) {
        this.settings[key] = value;
        await this.setStorageData({ extensionSettings: this.settings });
        this.addLog(`Setting updated: ${key} = ${value}`, 'info');
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PopupController();
});