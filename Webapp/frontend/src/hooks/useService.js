/**
 * React Hook for Service Injection (Dependency Inversion Principle)
 * Provides easy access to services from React components
 */

import { useState, useEffect, useRef } from 'react';
import ServiceContainer from '../container/ServiceContainer.js';

/**
 * Hook to inject a service into React component
 * @param {string} serviceName - Name of service to inject
 * @returns {Object} Service instance
 */
export function useService(serviceName) {
  const [service, setService] = useState(null);
  const [error, setError] = useState(null);
  const mounted = useRef(true);

  useEffect(() => {
    try {
      const serviceInstance = ServiceContainer.resolve(serviceName);
      if (mounted.current) {
        setService(serviceInstance);
        setError(null);
      }
    } catch (err) {
      if (mounted.current) {
        setError(err.message);
        setService(null);
      }
    }

    return () => {
      mounted.current = false;
    };
  }, [serviceName]);

  return { service, error, loading: !service && !error };
}

/**
 * Hook to inject multiple services
 * @param {Array<string>} serviceNames - Array of service names
 * @returns {Object} Object with service instances
 */
export function useServices(serviceNames) {
  const [services, setServices] = useState({});
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);
  const mounted = useRef(true);

  useEffect(() => {
    const resolvedServices = {};
    const serviceErrors = {};

    serviceNames.forEach(serviceName => {
      try {
        resolvedServices[serviceName] = ServiceContainer.resolve(serviceName);
      } catch (err) {
        serviceErrors[serviceName] = err.message;
      }
    });

    if (mounted.current) {
      setServices(resolvedServices);
      setErrors(serviceErrors);
      setLoading(false);
    }

    return () => {
      mounted.current = false;
    };
  }, [serviceNames]);

  return { services, errors, loading };
}

/**
 * Hook for dashboard data with automatic refresh
 * @param {number} refreshInterval - Refresh interval in milliseconds
 * @returns {Object} Dashboard data and methods
 */
export function useDashboardData(refreshInterval = 30000) {
  const { service: dashboardService, error: serviceError } = useService('dashboardService');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const fetchData = async () => {
    if (!dashboardService) return;

    try {
      setLoading(true);
      const result = await dashboardService.getDashboardData();
      
      if (result.success) {
        setData(result.data);
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dashboardService) {
      fetchData();

      if (refreshInterval > 0) {
        intervalRef.current = setInterval(fetchData, refreshInterval);
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [dashboardService, refreshInterval]);

  return {
    data,
    loading,
    error: error || serviceError,
    refresh: fetchData
  };
}

/**
 * Hook for listings data with CRUD operations
 * @returns {Object} Listings data and CRUD methods
 */
export function useListings() {
  const { service: listingsService, error: serviceError } = useService('listingsService');
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchListings = async () => {
    if (!listingsService) return;

    try {
      setLoading(true);
      const result = await listingsService.getAll();
      
      if (result.success) {
        setListings(result.data || []);
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const createListing = async (listingData) => {
    if (!listingsService) return { success: false, error: 'Service not available' };

    try {
      const result = await listingsService.saveData(listingData);
      if (result.success) {
        await fetchListings(); // Refresh list
      }
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const updateListing = async (id, listingData) => {
    if (!listingsService) return { success: false, error: 'Service not available' };

    try {
      const result = await listingsService.updateData(id, listingData);
      if (result.success) {
        await fetchListings(); // Refresh list
      }
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const deleteListing = async (id) => {
    if (!listingsService) return { success: false, error: 'Service not available' };

    try {
      const result = await listingsService.deleteData(id);
      if (result.success) {
        await fetchListings(); // Refresh list
      }
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  useEffect(() => {
    if (listingsService) {
      fetchListings();
    }
  }, [listingsService]);

  return {
    listings,
    loading,
    error: error || serviceError,
    refresh: fetchListings,
    create: createListing,
    update: updateListing,
    delete: deleteListing
  };
}

/**
 * Hook for orders data with CRUD operations
 * @returns {Object} Orders data and CRUD methods
 */
export function useOrders() {
  const { service: ordersService, error: serviceError } = useService('ordersService');
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchOrders = async () => {
    if (!ordersService) return;

    try {
      setLoading(true);
      const result = await ordersService.getAll();
      
      if (result.success) {
        setOrders(result.data || []);
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, status) => {
    if (!ordersService) return { success: false, error: 'Service not available' };

    try {
      const result = await ordersService.updateStatus(orderId, status);
      if (result.success) {
        await fetchOrders(); // Refresh list
      }
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const addTracking = async (orderId, trackingNumber, shipper) => {
    if (!ordersService) return { success: false, error: 'Service not available' };

    try {
      const result = await ordersService.addTracking(orderId, trackingNumber, shipper);
      if (result.success) {
        await fetchOrders(); // Refresh list
      }
      return result;
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  const getOverdueOrders = async () => {
    if (!ordersService) return { success: false, error: 'Service not available' };

    try {
      return await ordersService.getOverdue();
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  useEffect(() => {
    if (ordersService) {
      fetchOrders();
    }
  }, [ordersService]);

  return {
    orders,
    loading,
    error: error || serviceError,
    refresh: fetchOrders,
    updateStatus: updateOrderStatus,
    addTracking,
    getOverdue: getOverdueOrders
  };
}

/**
 * Hook for optimization strategies
 * @returns {Object} Optimization methods
 */
export function useOptimization() {
  const { service: optimizationFactory, error: serviceError } = useService('optimizationStrategyFactory');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const optimizeListing = async (listing, strategyName = null) => {
    if (!optimizationFactory) return { success: false, error: 'Service not available' };

    try {
      setLoading(true);
      
      const strategy = strategyName 
        ? optimizationFactory.getStrategy(strategyName)
        : optimizationFactory.getBestStrategy(listing);

      if (!strategy) {
        return { success: false, error: 'No suitable optimization strategy found' };
      }

      const optimized = await strategy.optimize(listing);
      
      setError(null);
      return { success: true, data: optimized, strategy: strategy.getName() };
    } catch (err) {
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setLoading(false);
    }
  };

  const getAvailableStrategies = () => {
    if (!optimizationFactory) return [];
    
    return optimizationFactory.getAllStrategies().map(strategy => ({
      name: strategy.getName(),
      description: strategy.getDescription()
    }));
  };

  return {
    loading,
    error: error || serviceError,
    optimize: optimizeListing,
    getStrategies: getAvailableStrategies
  };
}

/**
 * Hook for notifications
 * @returns {Object} Notification methods
 */
export function useNotifications() {
  const { service: notificationService, error: serviceError } = useService('notificationService');
  const { service: eventBus } = useService('eventBus');
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    if (eventBus) {
      const handleNotification = (notification) => {
        setNotifications(prev => [notification, ...prev.slice(0, 9)]); // Keep last 10
      };

      eventBus.on('notification:sent', handleNotification);
      
      return () => {
        eventBus.off('notification:sent', handleNotification);
      };
    }
  }, [eventBus]);

  const sendNotification = async (message, recipient, options = {}) => {
    if (!notificationService) return { success: false, error: 'Service not available' };

    try {
      return await notificationService.send(message, recipient, options);
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  return {
    notifications,
    send: sendNotification,
    error: serviceError
  };
}

/**
 * Hook for analytics data
 * @param {string} period - Time period for analytics
 * @returns {Object} Analytics data and methods
 */
export function useAnalytics(period = 'month') {
  const { service: analyticsService, error: serviceError } = useService('analyticsService');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    if (!analyticsService) return;

    try {
      setLoading(true);
      const result = await analyticsService.getDashboardMetrics(period);
      
      if (result.success) {
        setMetrics(result.data);
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (analyticsService) {
      fetchMetrics();
    }
  }, [analyticsService, period]);

  return {
    metrics,
    loading,
    error: error || serviceError,
    refresh: fetchMetrics
  };
}