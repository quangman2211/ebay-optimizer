/**
 * Service Container (Dependency Inversion Principle)
 * Manages service registration and dependency injection
 */

/**
 * Dependency Injection Container
 * Implements the Inversion of Control pattern
 */
class ServiceContainer {
  constructor() {
    this.services = new Map();
    this.singletons = new Map();
    this.instances = new Map();
  }

  /**
   * Register a service
   * @param {string} name - Service name
   * @param {Function|Object} implementation - Service implementation
   * @param {Object} options - Registration options
   */
  register(name, implementation, options = {}) {
    const config = {
      implementation,
      singleton: options.singleton || false,
      dependencies: options.dependencies || [],
      factory: options.factory || false
    };

    this.services.set(name, config);
    return this;
  }

  /**
   * Register a singleton service
   * @param {string} name - Service name
   * @param {Function|Object} implementation - Service implementation
   * @param {Object} options - Registration options
   */
  registerSingleton(name, implementation, options = {}) {
    return this.register(name, implementation, { 
      ...options, 
      singleton: true 
    });
  }

  /**
   * Register a factory function
   * @param {string} name - Service name
   * @param {Function} factory - Factory function
   * @param {Object} options - Registration options
   */
  registerFactory(name, factory, options = {}) {
    return this.register(name, factory, { 
      ...options, 
      factory: true 
    });
  }

  /**
   * Resolve a service by name
   * @param {string} name - Service name
   * @returns {Object} Service instance
   */
  resolve(name) {
    const config = this.services.get(name);
    
    if (!config) {
      throw new Error(`Service '${name}' not found in container`);
    }

    // Return existing singleton instance
    if (config.singleton && this.instances.has(name)) {
      return this.instances.get(name);
    }

    // Create new instance
    const instance = this.createInstance(config);

    // Store singleton instance
    if (config.singleton) {
      this.instances.set(name, instance);
    }

    return instance;
  }

  /**
   * Create service instance with dependency injection
   * @param {Object} config - Service configuration
   * @returns {Object} Service instance
   */
  createInstance(config) {
    const { implementation, dependencies, factory } = config;

    // Resolve dependencies
    const resolvedDependencies = dependencies.map(dep => {
      if (typeof dep === 'string') {
        return this.resolve(dep);
      }
      if (typeof dep === 'object' && dep.name) {
        return this.resolve(dep.name);
      }
      return dep;
    });

    // Factory function
    if (factory) {
      return implementation(...resolvedDependencies);
    }

    // Constructor function
    if (typeof implementation === 'function') {
      return new implementation(...resolvedDependencies);
    }

    // Direct object
    return implementation;
  }

  /**
   * Check if service is registered
   * @param {string} name - Service name
   * @returns {boolean} Whether service is registered
   */
  has(name) {
    return this.services.has(name);
  }

  /**
   * Get all registered service names
   * @returns {Array<string>} Service names
   */
  getServiceNames() {
    return Array.from(this.services.keys());
  }

  /**
   * Clear all services
   */
  clear() {
    this.services.clear();
    this.singletons.clear();
    this.instances.clear();
  }

  /**
   * Create a scoped container
   * Inherits services from parent but maintains separate instances
   * @returns {ServiceContainer} Scoped container
   */
  createScope() {
    const scope = new ServiceContainer();
    
    // Copy service registrations
    for (const [name, config] of this.services) {
      scope.services.set(name, { ...config });
    }
    
    return scope;
  }

  /**
   * Auto-wire dependencies for a class
   * @param {Function} TargetClass - Class to wire
   * @param {Array<string>} dependencies - Dependency names
   * @returns {Function} Wired class
   */
  autoWire(TargetClass, dependencies = []) {
    const container = this;
    
    return class extends TargetClass {
      constructor(...args) {
        const resolvedDeps = dependencies.map(dep => container.resolve(dep));
        super(...resolvedDeps, ...args);
      }
    };
  }

  /**
   * Create a service locator function
   * @returns {Function} Service locator function
   */
  createLocator() {
    const container = this;
    
    return function serviceLocator(name) {
      return container.resolve(name);
    };
  }

  /**
   * Validate container configuration
   * @returns {Object} Validation result
   */
  validate() {
    const errors = [];
    const warnings = [];

    for (const [name, config] of this.services) {
      // Check circular dependencies
      if (this.hasCircularDependency(name)) {
        errors.push(`Circular dependency detected for service '${name}'`);
      }

      // Check missing dependencies
      for (const dep of config.dependencies) {
        if (typeof dep === 'string' && !this.has(dep)) {
          errors.push(`Missing dependency '${dep}' for service '${name}'`);
        }
      }

      // Warnings for potential issues
      if (config.dependencies.length > 5) {
        warnings.push(`Service '${name}' has many dependencies (${config.dependencies.length})`);
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings
    };
  }

  /**
   * Check for circular dependencies
   * @param {string} name - Service name
   * @param {Set} visited - Visited services
   * @returns {boolean} Whether circular dependency exists
   */
  hasCircularDependency(name, visited = new Set()) {
    if (visited.has(name)) {
      return true;
    }

    const config = this.services.get(name);
    if (!config) {
      return false;
    }

    visited.add(name);

    for (const dep of config.dependencies) {
      if (typeof dep === 'string') {
        if (this.hasCircularDependency(dep, new Set(visited))) {
          return true;
        }
      }
    }

    return false;
  }

  /**
   * Get dependency graph
   * @returns {Object} Dependency graph
   */
  getDependencyGraph() {
    const graph = {};

    for (const [name, config] of this.services) {
      graph[name] = {
        dependencies: config.dependencies.filter(dep => typeof dep === 'string'),
        singleton: config.singleton,
        factory: config.factory
      };
    }

    return graph;
  }

  /**
   * Bootstrap container with common services
   */
  bootstrap() {
    // Register basic services
    this.registerSingleton('logger', this.createLogger());
    this.registerSingleton('config', this.createConfig());
    this.registerSingleton('eventBus', this.createEventBus());
    
    return this;
  }

  /**
   * Create logger service
   * @returns {Object} Logger service
   */
  createLogger() {
    return {
      info: (message, ...args) => console.log(`[INFO] ${message}`, ...args),
      warn: (message, ...args) => console.warn(`[WARN] ${message}`, ...args),
      error: (message, ...args) => console.error(`[ERROR] ${message}`, ...args),
      debug: (message, ...args) => console.debug(`[DEBUG] ${message}`, ...args)
    };
  }

  /**
   * Create config service
   * @returns {Object} Config service
   */
  createConfig() {
    return {
      get: (key, defaultValue = null) => {
        return process.env[key] || defaultValue;
      },
      apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8001/api/v1',
      appName: process.env.REACT_APP_NAME || 'eBay Optimizer'
    };
  }

  /**
   * Create event bus service
   * @returns {Object} Event bus service
   */
  createEventBus() {
    const listeners = new Map();
    
    return {
      on: (event, callback) => {
        if (!listeners.has(event)) {
          listeners.set(event, []);
        }
        listeners.get(event).push(callback);
      },
      
      emit: (event, data) => {
        if (listeners.has(event)) {
          listeners.get(event).forEach(callback => callback(data));
        }
      },
      
      off: (event, callback) => {
        if (listeners.has(event)) {
          const callbacks = listeners.get(event);
          const index = callbacks.indexOf(callback);
          if (index > -1) {
            callbacks.splice(index, 1);
          }
        }
      }
    };
  }
}

// Export singleton container instance
export default new ServiceContainer();