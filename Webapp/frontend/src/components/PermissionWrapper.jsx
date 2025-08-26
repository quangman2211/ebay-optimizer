import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Box, Typography, Alert } from '@mui/material';

/**
 * PermissionWrapper - Component for role-based conditional rendering
 * 
 * Usage:
 * <PermissionWrapper roles={['ADMIN']}>
 *   <AdminOnlyComponent />
 * </PermissionWrapper>
 * 
 * <PermissionWrapper permissions={['manage_users']}>
 *   <UserManagementComponent />
 * </PermissionWrapper>
 */
const PermissionWrapper = ({ 
  children, 
  roles = [], 
  permissions = [], 
  fallback = null,
  showAccessDenied = false,
  requireAll = false // If true, user must have ALL permissions/roles. If false, ANY is sufficient.
}) => {
  const { canAccess, hasPermission, userRole, isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    if (showAccessDenied) {
      return (
        <Alert severity="warning" sx={{ m: 2 }}>
          Vui lòng đăng nhập để truy cập tính năng này.
        </Alert>
      );
    }
    return fallback;
  }

  // Check role access
  let hasRoleAccess = true;
  if (roles.length > 0) {
    hasRoleAccess = canAccess(roles);
  }

  // Check permission access  
  let hasPermissionAccess = true;
  if (permissions.length > 0) {
    if (requireAll) {
      // User must have ALL permissions
      hasPermissionAccess = permissions.every(permission => hasPermission(permission));
    } else {
      // User must have ANY permission
      hasPermissionAccess = permissions.some(permission => hasPermission(permission));
    }
  }

  const hasAccess = hasRoleAccess && hasPermissionAccess;

  if (!hasAccess) {
    if (showAccessDenied) {
      return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              Không Có Quyền Truy Cập
            </Typography>
            <Typography variant="body2">
              Bạn cần quyền <strong>{userRole || 'Unknown'}</strong> không đủ để truy cập tính năng này.
            </Typography>
            {roles.length > 0 && (
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Yêu cầu vai trò: {roles.join(', ')}
              </Typography>
            )}
            {permissions.length > 0 && (
              <Typography variant="caption" display="block">
                Yêu cầu quyền: {permissions.join(', ')}
              </Typography>
            )}
          </Alert>
        </Box>
      );
    }
    return fallback;
  }

  return children;
};

// Convenience wrapper components for common use cases
export const AdminOnly = ({ children, fallback = null, showAccessDenied = false }) => (
  <PermissionWrapper 
    roles={['ADMIN']} 
    fallback={fallback} 
    showAccessDenied={showAccessDenied}
  >
    {children}
  </PermissionWrapper>
);

export const ManagerOrAdmin = ({ children, fallback = null, showAccessDenied = false }) => (
  <PermissionWrapper 
    roles={['ADMIN', 'EBAY_MANAGER']} 
    fallback={fallback} 
    showAccessDenied={showAccessDenied}
  >
    {children}
  </PermissionWrapper>
);

export const StaffOrAbove = ({ children, fallback = null, showAccessDenied = false }) => (
  <PermissionWrapper 
    roles={['ADMIN', 'EBAY_MANAGER', 'FULFILLMENT_STAFF']} 
    fallback={fallback} 
    showAccessDenied={showAccessDenied}
  >
    {children}
  </PermissionWrapper>
);

export default PermissionWrapper;