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
  const { user, logout } = useAuth();
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
  
  const menuItems = [
    { text: 'Workspace', icon: 'bi-lightning', path: '/workspace' },
    { text: 'Quick Listing', icon: 'bi-plus-circle', path: '/quick-listing' },
    { text: 'Analytics', icon: 'bi-speedometer2', path: '/dashboard' },
    { 
      text: 'Draft Listings', 
      icon: 'bi-file-earmark-text', 
      path: '/drafts',
      badge: badges.drafts > 0 ? badges.drafts : null,
      badgeColor: 'warning'
    },
    { 
      text: 'Quản lý Listings', 
      icon: 'bi-list-ul', 
      path: '/listings',
      badge: badges.listings > 0 ? badges.listings : null,
      badgeColor: 'info'
    },
    { 
      text: 'Quản lý Đơn hàng', 
      icon: 'bi-cart-check', 
      path: '/orders', 
      badge: badges.orders > 0 ? badges.orders : null, 
      badgeColor: 'error' 
    },
    { 
      text: 'Nguồn hàng', 
      icon: 'bi-cart3', 
      path: '/sources',
      badge: badges.sources > 0 ? badges.sources : null,
      badgeColor: 'warning'
    },
    { 
      text: 'Quản lý Sản phẩm', 
      icon: 'bi-box-seam', 
      path: '/products'
    },
    { text: 'Tài khoản eBay', icon: 'bi-person-badge', path: '/accounts' },
    { text: 'Cài đặt', icon: 'bi-gear', path: '/settings' },
  ];

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
                eBay Manager
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
                Quản lý listings đơn giản và hiệu quả
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
                {user?.full_name || 'Admin'}
              </Typography>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                Administrator
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