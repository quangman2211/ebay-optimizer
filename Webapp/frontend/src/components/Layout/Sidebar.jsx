import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Typography,
  IconButton,
  Divider,
  Avatar,
  Menu,
  MenuItem,
  Badge,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';
import { ordersAPI, listingsAPI, sourcesAPI, draftsAPI } from '../../services/api';

const Sidebar = ({ open, onClose, onToggle }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  const { user, logout, userRole, canAccess, getUserRoleDisplay } = useAuth();
  
  // Debug RBAC
  console.log('Sidebar: Current user role:', userRole);
  console.log('Sidebar: User object:', user);
  console.log('Sidebar: canAccess function available:', typeof canAccess);
  const [userMenuAnchor, setUserMenuAnchor] = useState(null);
  const [badges, setBadges] = useState({
    orders: 0,
    listings: 0,
    sources: 0,
    drafts: 0
  });

  const location = useLocation();
  
  // Fetch badge counts from API
  useEffect(() => {
    const fetchBadgeCounts = async () => {
      try {
        // Fetch pending orders count
        const ordersResponse = await ordersAPI.getAll({
          status: 'pending',
          page: 1,
          size: 1
        });
        
        // Fetch draft listings count
        const listingsResponse = await listingsAPI.getAll({
          status: 'draft', 
          page: 1,
          size: 1
        });
        
        // Fetch disconnected sources count
        const sourcesResponse = await sourcesAPI.getAll({
          status: 'disconnected',
          page: 1,
          size: 1
        });
        
        // Fetch draft listings count
        const draftsResponse = await draftsAPI.getAll({
          status: 'pending',
          page: 1,
          size: 1
        });
        
        setBadges({
          orders: ordersResponse.data?.total || 0,
          listings: listingsResponse.data?.total || 0,
          sources: sourcesResponse.data?.total || 0,
          drafts: draftsResponse.data?.total || 0
        });
        
      } catch (error) {
        console.warn('Sidebar: Error fetching badge counts:', error);
        // Keep badges at 0 on error
      }
    };
    
    fetchBadgeCounts();
    
    // Refresh badges every 30 seconds
    const interval = setInterval(fetchBadgeCounts, 30000);
    return () => clearInterval(interval);
  }, []);
  
  // Role-based menu items
  const getMenuItems = () => {
    const baseItems = [
      { text: 'Workspace', icon: 'bi-lightning', path: '/workspace', roles: ['ADMIN', 'EBAY_MANAGER', 'FULFILLMENT_STAFF'] },
      { text: 'Analytics', icon: 'bi-speedometer2', path: '/dashboard', roles: ['ADMIN', 'EBAY_MANAGER', 'FULFILLMENT_STAFF'] },
    ];

    const managerItems = [
      { text: 'Quick Listing', icon: 'bi-plus-circle', path: '/quick-listing', roles: ['ADMIN', 'EBAY_MANAGER'] },
      { 
        text: 'Draft Listings', 
        icon: 'bi-file-earmark-text', 
        path: '/drafts',
        roles: ['ADMIN', 'EBAY_MANAGER'],
        badge: badges.drafts > 0 ? badges.drafts : null,
        badgeColor: 'warning'
      },
      { 
        text: 'Quản lý Listings', 
        icon: 'bi-list-ul', 
        path: '/listings',
        roles: ['ADMIN', 'EBAY_MANAGER'],
        badge: badges.listings > 0 ? badges.listings : null,
        badgeColor: 'info'
      },
    ];

    const orderItems = [
      { 
        text: 'Quản lý Đơn hàng', 
        icon: 'bi-cart-check', 
        path: '/orders', 
        roles: ['ADMIN', 'EBAY_MANAGER', 'FULFILLMENT_STAFF'],
        badge: badges.orders > 0 ? badges.orders : null, 
        badgeColor: 'error' 
      },
      { 
        text: 'Nguồn hàng', 
        icon: 'bi-cart3', 
        path: '/sources',
        roles: ['ADMIN', 'EBAY_MANAGER', 'FULFILLMENT_STAFF'],
        badge: badges.sources > 0 ? badges.sources : null,
        badgeColor: 'warning',
        readOnly: userRole === 'FULFILLMENT_STAFF' // Read-only for staff
      },
    ];

    const adminItems = [
      { 
        text: 'Quản lý Sản phẩm', 
        icon: 'bi-box-seam', 
        path: '/products',
        roles: ['ADMIN', 'EBAY_MANAGER']
      },
      { text: 'Tài khoản eBay', icon: 'bi-person-badge', path: '/accounts', roles: ['ADMIN', 'EBAY_MANAGER'] },
      { text: 'CSV Import', icon: 'bi-file-spreadsheet', path: '/csv-import', roles: ['ADMIN', 'EBAY_MANAGER'] },
      { text: 'Cài đặt', icon: 'bi-gear', path: '/settings', roles: ['ADMIN'] },
    ];

    const allItems = [...baseItems, ...managerItems, ...orderItems, ...adminItems];
    
    // Filter items based on user role
    return allItems.filter(item => {
      if (!item.roles) return true; // No role restriction
      const hasAccess = canAccess(item.roles);
      console.log(`Sidebar: ${item.text} - Required roles: [${item.roles?.join(',')}] - User role: ${userRole} - Access: ${hasAccess}`);
      return hasAccess;
    });
  };

  let menuItems = getMenuItems();
  
  // Fallback: If no menu items (role issue), show basic items
  if (menuItems.length === 0 && user) {
    console.warn('Sidebar: No menu items found, using fallback menu');
    menuItems = [
      { text: 'Workspace', icon: 'bi-lightning', path: '/workspace' },
      { text: 'Analytics', icon: 'bi-speedometer2', path: '/dashboard' },
      { text: 'Quản lý Đơn hàng', icon: 'bi-cart-check', path: '/orders' },
    ];
  }
  
  console.log('Sidebar: Final menu items:', menuItems.length);

  const handleUserMenuClick = (event) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  const handleLogout = () => {
    logout();
    handleUserMenuClose();
  };

  const sidebarContent = (
    <Box
      sx={{
        width: open ? 280 : 80,
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        display: 'flex',
        flexDirection: 'column',
        transition: 'all 0.3s ease',
        overflow: 'hidden',
      }}
    >
      {/* Sidebar Header */}
      <Box
        sx={{
          p: 2.5,
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: 1,
              background: 'rgba(255, 255, 255, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mr: open ? 1.5 : 0,
            }}
          >
            <i className="bi bi-shop-window" style={{ color: 'white', fontSize: '1.2rem' }} />
          </Box>
          {open && (
            <Box>
              <Typography
                variant="h6"
                sx={{
                  fontWeight: 600,
                  fontSize: '1.2rem',
                  whiteSpace: 'nowrap',
                  lineHeight: 1.2,
                }}
              >
                eBay Optimizer
              </Typography>
              <Typography
                variant="caption"
                sx={{
                  opacity: 0.8,
                  fontSize: '0.75rem',
                  display: 'block',
                  whiteSpace: 'nowrap',
                }}
              >
                {getUserRoleDisplay() || 'Loading...'}
              </Typography>
            </Box>
          )}
        </Box>
        <IconButton
          onClick={onToggle}
          sx={{
            color: 'white',
            background: 'rgba(255, 255, 255, 0.1)',
            '&:hover': {
              background: 'rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          <MenuIcon />
        </IconButton>
      </Box>

      {/* Navigation Items */}
      <List sx={{ px: 0, py: 0, flex: 1 }}>
        {menuItems.map((item, index) => {
          const isActive = location.pathname === item.path || 
                          (location.pathname === '/' && item.path === '/dashboard');
          
          return (
            <ListItem key={index} disablePadding>
              <ListItemButton
                component={Link}
                to={item.path}
                sx={{
                  px: 2.5,
                  py: 1.5,
                  borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                  color: isActive ? 'white' : 'rgba(255, 255, 255, 0.8)',
                  backgroundColor: isActive ? 'rgba(255, 255, 255, 0.15)' : 'transparent',
                  borderRight: isActive ? '3px solid #ffc107' : 'none',
                  '&:hover': {
                    color: 'white',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  },
                  justifyContent: open ? 'flex-start' : 'center',
                  textDecoration: 'none',
                }}
              >
                <ListItemIcon
                  sx={{
                    color: 'inherit',
                    minWidth: open ? 40 : 0,
                    mr: open ? 1.5 : 0,
                  }}
                >
                  {item.badge ? (
                    <Badge
                      badgeContent={item.badge}
                      color={item.badgeColor}
                      sx={{
                        '& .MuiBadge-badge': {
                          fontSize: '0.65rem',
                          minWidth: 16,
                          height: 16,
                          right: -6,
                          top: -6,
                        },
                      }}
                    >
                      <i className={`bi ${item.icon}`} style={{ fontSize: '1.1rem' }} />
                    </Badge>
                  ) : (
                    <i className={`bi ${item.icon}`} style={{ fontSize: '1.1rem' }} />
                  )}
                </ListItemIcon>
                {open && (
                  <ListItemText
                    primary={item.text}
                    sx={{
                      '& .MuiListItemText-primary': {
                        fontSize: '0.9rem',
                        fontWeight: 500,
                      },
                    }}
                  />
                )}
                {open && item.badge && !item.badgeColor && (
                  <Badge
                    badgeContent={item.badge}
                    color="error"
                    sx={{
                      ml: 'auto',
                      '& .MuiBadge-badge': {
                        position: 'static',
                        transform: 'none',
                      },
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      {/* User Menu Footer */}
      <Box
        sx={{
          p: 2.5,
          borderTop: '1px solid rgba(255, 255, 255, 0.1)',
          mt: 'auto',
        }}
      >
        <Box
          onClick={handleUserMenuClick}
          sx={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            p: 1,
            borderRadius: 2,
            transition: 'all 0.2s ease',
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: 'rgba(255, 255, 255, 0.2)',
              mr: open ? 1.5 : 0,
            }}
          >
            <PersonIcon sx={{ fontSize: '1.2rem' }} />
          </Avatar>
          {open && (
            <Box sx={{ flex: 1 }}>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {user?.full_name || user?.name || user?.email?.split('@')[0] || 'User'}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                {getUserRoleDisplay()}
              </Typography>
            </Box>
          )}
        </Box>

        <Menu
          anchorEl={userMenuAnchor}
          open={Boolean(userMenuAnchor)}
          onClose={handleUserMenuClose}
          PaperProps={{
            sx: {
              mt: -1,
              ml: 2,
              minWidth: 180,
              backgroundColor: 'rgba(52, 58, 64, 0.95)',
              backdropFilter: 'blur(10px)',
              color: 'white',
              '& .MuiMenuItem-root': {
                color: 'white',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                },
              },
            },
          }}
        >
          <MenuItem onClick={handleUserMenuClose}>
            <SettingsIcon sx={{ mr: 2, fontSize: '1.1rem' }} />
            Cài đặt
          </MenuItem>
          <MenuItem onClick={handleUserMenuClose}>
            <PersonIcon sx={{ mr: 2, fontSize: '1.1rem' }} />
            Hồ sơ
          </MenuItem>
          <Divider sx={{ my: 1, borderColor: 'rgba(255, 255, 255, 0.2)' }} />
          <MenuItem onClick={handleLogout}>
            <LogoutIcon sx={{ mr: 2, fontSize: '1.1rem' }} />
            Đăng xuất
          </MenuItem>
        </Menu>
      </Box>
    </Box>
  );

  if (isMobile) {
    return (
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile
        }}
        PaperProps={{
          sx: {
            border: 'none',
            boxShadow: '2px 0 10px rgba(0, 0, 0, 0.1)',
          },
        }}
      >
        {sidebarContent}
      </Drawer>
    );
  }

  return (
    <Drawer
      variant="permanent"
      PaperProps={{
        sx: {
          border: 'none',
          boxShadow: '2px 0 10px rgba(0, 0, 0, 0.1)',
        },
      }}
    >
      {sidebarContent}
    </Drawer>
  );
};

export default Sidebar;