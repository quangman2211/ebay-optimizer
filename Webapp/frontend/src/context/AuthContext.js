import React, { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/auth';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [userPermissions, setUserPermissions] = useState([]);

  useEffect(() => {
    const initializeAuth = async () => {
      console.log('AuthContext: Starting initialization...');
      try {
        if (authService.isAuthenticated()) {
          console.log('AuthContext: Token found, checking user data...');
          const userData = authService.getUser();
          if (userData) {
            console.log('AuthContext: User data found in localStorage:', userData.email);
            console.log('AuthContext: Role from userData:', userData.role);
            console.log('AuthContext: Permissions from userData:', userData.permissions);
            setUser(userData);
            setUserRole(userData.role);
            setUserPermissions(userData.permissions || []);
            setIsAuthenticated(true);
          } else {
            console.log('AuthContext: No user data, fetching from API...');
            // Token exists but no user data, fetch it
            const freshUserData = await authService.getCurrentUser();
            console.log('AuthContext: Fresh user data received:', freshUserData.email);
            console.log('AuthContext: Role from API:', freshUserData.role);
            console.log('AuthContext: Permissions from API:', freshUserData.permissions);
            setUser(freshUserData);
            setUserRole(freshUserData.role);
            setUserPermissions(freshUserData.permissions || []);
            setIsAuthenticated(true);
            localStorage.setItem('user_data', JSON.stringify(freshUserData));
          }
        } else {
          console.log('AuthContext: No token found, user not authenticated');
        }
      } catch (error) {
        console.error('AuthContext: Initialization error:', error);
        authService.logout();
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        console.log('AuthContext: Initialization complete, setting loading=false');
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    console.log('AuthContext: Login attempt for:', credentials.email);
    setLoading(true);
    try {
      const result = await authService.login(credentials);
      
      if (result.success) {
        const userData = authService.getUser();
        console.log('AuthContext: Login successful, user data:', userData?.email);
        console.log('AuthContext: Login role:', userData?.role);
        console.log('AuthContext: Login permissions:', userData?.permissions);
        setUser(userData);
        setUserRole(userData?.role);
        setUserPermissions(userData?.permissions || []);
        setIsAuthenticated(true);
        return { success: true };
      } else {
        console.log('AuthContext: Login failed:', result.error);
        return { success: false, error: result.error };
      }
    } catch (error) {
      console.error('AuthContext: Login error:', error);
      return { 
        success: false, 
        error: 'Đã có lỗi xảy ra. Vui lòng thử lại.' 
      };
    } finally {
      console.log('AuthContext: Login process complete, setting loading=false');
      setLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    setUserRole(null);
    setUserPermissions([]);
    setIsAuthenticated(false);
  };

  const register = async (userData) => {
    setLoading(true);
    try {
      const result = await authService.register(userData);
      return result;
    } finally {
      setLoading(false);
    }
  };

  // Permission and role helper functions
  const hasPermission = (permission) => {
    if (!isAuthenticated || !userPermissions) return false;
    return userPermissions.includes(permission);
  };

  const hasRole = (role) => {
    if (!isAuthenticated || !userRole) return false;
    return userRole === role;
  };

  const isAdmin = () => hasRole('ADMIN');
  const isManager = () => hasRole('EBAY_MANAGER');
  const isStaff = () => hasRole('FULFILLMENT_STAFF');

  const canAccess = (requiredRoles = []) => {
    if (!isAuthenticated || !userRole) return false;
    if (requiredRoles.length === 0) return true; // No restrictions
    return requiredRoles.includes(userRole);
  };

  const getUserRoleDisplay = () => {
    if (!userRole) return 'User';
    switch (userRole) {
      case 'ADMIN': return 'Administrator';
      case 'EBAY_MANAGER': return 'eBay Manager';
      case 'FULFILLMENT_STAFF': return 'Fulfillment Staff';
      default: return 'User';
    }
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    userRole,
    userPermissions,
    login,
    logout,
    register,
    // Permission helpers
    hasPermission,
    hasRole,
    isAdmin,
    isManager,
    isStaff,
    canAccess,
    getUserRoleDisplay,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};