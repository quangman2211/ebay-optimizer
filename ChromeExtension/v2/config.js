/**
 * Extension Configuration
 * Manage backend URLs and API settings
 */

const ExtensionConfig = {
  // Environment selection: 'local', 'ngrok', 'production'
  currentEnvironment: 'local',
  
  // Backend API endpoints
  environments: {
    local: {
      name: 'Local Development',
      baseURL: 'http://localhost:8000/api/v1',
      apiKey: 'dev-api-key-12345',
      timeout: 30000
    },
    ngrok: {
      name: 'Ngrok Tunnel',
      baseURL: 'https://YOUR-NGROK-ID.ngrok-free.app/api/v1',  // UPDATE THIS
      apiKey: 'dev-api-key-12345',
      timeout: 45000
    },
    production: {
      name: 'Render Production',
      baseURL: 'https://ebay-optimizer-api.onrender.com/api/v1',  // UPDATE AFTER DEPLOYMENT
      apiKey: 'prod-api-key-CHANGE-ME',  // UPDATE THIS
      timeout: 60000
    }
  },
  
  // Get current environment configuration
  getCurrentConfig() {
    return this.environments[this.currentEnvironment] || this.environments.local;
  },
  
  // Switch environment
  setEnvironment(env) {
    if (this.environments[env]) {
      this.currentEnvironment = env;
      console.log(`Environment switched to: ${env}`);
      return true;
    }
    console.error(`Invalid environment: ${env}`);
    return false;
  },
  
  // Update specific environment URL
  updateEnvironmentURL(env, url) {
    if (this.environments[env]) {
      this.environments[env].baseURL = url;
      console.log(`Updated ${env} URL to: ${url}`);
      return true;
    }
    return false;
  },
  
  // Update API key
  updateAPIKey(env, apiKey) {
    if (this.environments[env]) {
      this.environments[env].apiKey = apiKey;
      console.log(`Updated ${env} API key`);
      return true;
    }
    return false;
  },
  
  // Load saved configuration from Chrome storage
  async loadFromStorage() {
    return new Promise((resolve) => {
      chrome.storage.local.get(['extension_config'], (result) => {
        if (result.extension_config) {
          // Merge saved config with defaults
          Object.assign(this, result.extension_config);
          console.log('Configuration loaded from storage');
        }
        resolve();
      });
    });
  },
  
  // Save current configuration to Chrome storage
  async saveToStorage() {
    return new Promise((resolve) => {
      chrome.storage.local.set({
        extension_config: {
          currentEnvironment: this.currentEnvironment,
          environments: this.environments
        }
      }, () => {
        console.log('Configuration saved to storage');
        resolve();
      });
    });
  }
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ExtensionConfig;
}