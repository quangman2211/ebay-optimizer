import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Box,
  IconButton,
  TextField,
  InputAdornment,
  Badge,
  Menu,
  MenuItem,
  Typography,
  Divider,
  Avatar,
  Button,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Search as SearchIcon,
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
} from '@mui/icons-material';
import { useAuth } from '../../context/AuthContext';

const TopBar = ({ onSidebarToggle, sidebarOpen }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  const { user, logout } = useAuth();
  
  const [notificationAnchor, setNotificationAnchor] = useState(null);
  const [messageAnchor, setMessageAnchor] = useState(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState(null);
  const [searchValue, setSearchValue] = useState('');

  const notifications = [
    { id: 1, title: '15 listings đã được tối ưu', time: '2 giờ trước', type: 'success' },
    { id: 2, title: '5 đơn hàng mới cần xử lý', time: '5 giờ trước', type: 'warning' },
    { id: 3, title: 'Đồng bộ thành công với Google Sheets', time: '3 giờ trước', type: 'info' },
  ];

  const messages = [
    { id: 1, from: 'John Doe', message: 'Cần hỗ trợ về đơn hàng #ORD-2451', time: '1 giờ trước' },
    { id: 2, from: 'Jane Smith', message: 'Cảm ơn về dịch vụ tuyệt vời!', time: '3 giờ trước' },
  ];

  const handleNotificationClick = (event) => {
    setNotificationAnchor(event.currentTarget);
  };

  const handleMessageClick = (event) => {
    setMessageAnchor(event.currentTarget);
  };

  const handleUserMenuClick = (event) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleClose = (setter) => {
    setter(null);
  };

  const handleLogout = () => {
    logout();
    handleClose(setUserMenuAnchor);
  };

  return (
    <AppBar
      position="fixed"
      elevation={0}
      sx={{
        backgroundColor: 'white',
        borderBottom: '1px solid #e3e6f0',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        zIndex: theme.zIndex.drawer + 1,
        ml: !isMobile ? (sidebarOpen ? '280px' : '80px') : 0,
        width: !isMobile ? `calc(100% - ${sidebarOpen ? '280px' : '80px'})` : '100%',
        transition: 'all 0.3s ease',
      }}
    >
      <Toolbar sx={{ minHeight: '70px !important', px: 3 }}>
        {/* Mobile Menu Button */}
        {isMobile && (
          <IconButton
            edge="start"
            color="primary"
            aria-label="menu"
            onClick={onSidebarToggle}
            sx={{ mr: 2 }}
            className="mobile-toggle"
          >
            <i className="bi bi-list" style={{ fontSize: '1.2rem' }} />
          </IconButton>
        )}

        {/* Search Bar */}
        <Box sx={{ flexGrow: 1, display: { xs: 'none', sm: 'flex' }, justifyContent: 'center', mr: 3 }}>
          <TextField
            size="small"
            placeholder="Tìm kiếm..."
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon sx={{ color: 'text.secondary' }} />
                </InputAdornment>
              ),
              sx: {
                width: { sm: 300, md: 400 },
                borderRadius: 20,
                backgroundColor: '#f8f9fa',
                '& .MuiOutlinedInput-notchedOutline': {
                  border: 'none',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  border: 'none',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  border: '2px solid #0064D2',
                },
              },
            }}
          />
        </Box>

        {/* Right Side Icons */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {/* Sync Button */}
          <Button
            variant="outlined"
            size="small"
            startIcon={<i className="bi bi-cloud-arrow-down" />}
            onClick={() => window.dispatchEvent(new CustomEvent('openSyncModal'))}
            sx={{
              borderRadius: 20,
              textTransform: 'none',
              borderColor: '#667eea',
              color: '#667eea',
              mr: 1,
              '&:hover': {
                borderColor: '#5a6fd8',
                backgroundColor: 'rgba(102, 126, 234, 0.04)',
              },
            }}
          >
            Import Sheets
          </Button>
          
          {/* Notifications */}
          <IconButton
            color="primary"
            onClick={handleNotificationClick}
            sx={{
              '&:hover': {
                backgroundColor: 'rgba(0, 100, 210, 0.04)',
              },
            }}
          >
            <Badge badgeContent={3} color="error">
              <NotificationsIcon />
            </Badge>
          </IconButton>

          {/* Messages */}
          <IconButton
            color="primary"
            onClick={handleMessageClick}
            sx={{
              mr: 1,
              '&:hover': {
                backgroundColor: 'rgba(0, 100, 210, 0.04)',
              },
            }}
          >
            <Badge badgeContent={2} color="warning">
              <EmailIcon />
            </Badge>
          </IconButton>

          {/* Divider */}
          <Divider
            orientation="vertical"
            flexItem
            sx={{
              height: 'calc(4.375rem - 2rem)',
              my: 'auto',
              mx: 1,
              display: { xs: 'none', sm: 'block' },
            }}
          />

          {/* User Menu */}
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
                backgroundColor: 'rgba(0, 100, 210, 0.04)',
              },
            }}
          >
            <Typography
              variant="body2"
              sx={{
                mr: 2,
                fontWeight: 500,
                color: 'text.secondary',
                display: { xs: 'none', lg: 'block' },
              }}
            >
              {user?.full_name || 'Administrator'}
            </Typography>
            <Avatar
              sx={{
                width: 40,
                height: 40,
                bgcolor: 'primary.main',
              }}
            >
              <PersonIcon />
            </Avatar>
          </Box>
        </Box>

        {/* Notification Menu */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={() => handleClose(setNotificationAnchor)}
          PaperProps={{
            sx: {
              width: 350,
              maxHeight: 400,
              mt: 1,
            },
          }}
        >
          <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Thông báo ({notifications.length})
            </Typography>
          </Box>
          {notifications.map((notification) => (
            <MenuItem key={notification.id} sx={{ py: 1.5, px: 2, alignItems: 'flex-start' }}>
              <Box>
                <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                  {notification.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {notification.time}
                </Typography>
              </Box>
            </MenuItem>
          ))}
          <Divider />
          <MenuItem sx={{ justifyContent: 'center', py: 1 }}>
            <Typography variant="body2" color="primary">
              Xem tất cả thông báo
            </Typography>
          </MenuItem>
        </Menu>

        {/* Message Menu */}
        <Menu
          anchorEl={messageAnchor}
          open={Boolean(messageAnchor)}
          onClose={() => handleClose(setMessageAnchor)}
          PaperProps={{
            sx: {
              width: 350,
              maxHeight: 400,
              mt: 1,
            },
          }}
        >
          <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Tin nhắn ({messages.length})
            </Typography>
          </Box>
          {messages.map((message) => (
            <MenuItem key={message.id} sx={{ py: 1.5, px: 2, alignItems: 'flex-start' }}>
              <Avatar sx={{ mr: 2, width: 32, height: 32, bgcolor: 'grey.400' }}>
                {message.from.charAt(0)}
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {message.from}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>
                  {message.message}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {message.time}
                </Typography>
              </Box>
            </MenuItem>
          ))}
          <Divider />
          <MenuItem sx={{ justifyContent: 'center', py: 1 }}>
            <Typography variant="body2" color="primary">
              Xem tất cả tin nhắn
            </Typography>
          </MenuItem>
        </Menu>

        {/* User Menu */}
        <Menu
          anchorEl={userMenuAnchor}
          open={Boolean(userMenuAnchor)}
          onClose={() => handleClose(setUserMenuAnchor)}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
          transformOrigin={{ vertical: 'top', horizontal: 'right' }}
          PaperProps={{
            sx: {
              mt: 1,
              minWidth: 200,
            },
          }}
        >
          <Box sx={{ px: 2, py: 1.5, borderBottom: '1px solid #e0e0e0' }}>
            <Typography variant="subtitle2" color="text.secondary">
              👋 Xin chào
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {user?.full_name || user?.email}
            </Typography>
          </Box>
          <MenuItem onClick={() => handleClose(setUserMenuAnchor)}>
            <SettingsIcon sx={{ mr: 2, fontSize: '1.1rem' }} />
            Cài đặt
          </MenuItem>
          <MenuItem onClick={() => handleClose(setUserMenuAnchor)}>
            <PersonIcon sx={{ mr: 2, fontSize: '1.1rem' }} />
            Hồ sơ
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
            <LogoutIcon sx={{ mr: 2, fontSize: '1.1rem' }} />
            Đăng xuất
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default TopBar;