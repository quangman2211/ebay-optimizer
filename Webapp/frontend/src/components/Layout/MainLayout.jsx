import React, { useState } from 'react';
import { Box, useTheme, useMediaQuery } from '@mui/material';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

const MainLayout = ({ children }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);

  const handleSidebarToggle = () => {
    setSidebarOpen(!sidebarOpen);
  };

  const handleSidebarClose = () => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sidebar
        open={sidebarOpen}
        onClose={handleSidebarClose}
        onToggle={handleSidebarToggle}
      />

      {/* Main Content */}
      <Box
        sx={{
          flexGrow: 1,
          display: 'flex',
          flexDirection: 'column',
          ml: !isMobile ? (sidebarOpen ? '280px' : '80px') : 0,
          transition: 'all 0.3s ease',
          minHeight: '100vh',
        }}
      >
        {/* Top Bar */}
        <TopBar
          onSidebarToggle={handleSidebarToggle}
          sidebarOpen={sidebarOpen}
        />

        {/* Page Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            mt: '70px', // TopBar height
            backgroundColor: '#f5f5f5',
            minHeight: 'calc(100vh - 70px)',
          }}
        >
          {children}
        </Box>
      </Box>

      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <Box
          onClick={handleSidebarClose}
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: theme.zIndex.drawer - 1,
          }}
        />
      )}
    </Box>
  );
};

export default MainLayout;