import React from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  console.log('ProtectedRoute: loading:', loading, 'isAuthenticated:', isAuthenticated);

  // Always show loading during auth initialization
  if (loading) {
    console.log('ProtectedRoute: Showing loading screen');
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight="100vh"
        bgcolor="#f8f9fa"
      >
        <CircularProgress size={60} color="primary" />
        <Typography variant="h6" sx={{ mt: 2, color: 'text.secondary' }}>
          Đang tải...
        </Typography>
      </Box>
    );
  }

  // Only redirect when loading is complete AND user is not authenticated
  if (!loading && !isAuthenticated) {
    console.log('ProtectedRoute: Redirecting to login - not authenticated');
    return <Navigate to="/login" replace />;
  }

  // User is authenticated and loading is complete
  console.log('ProtectedRoute: Rendering protected content');
  return children;
};

export default ProtectedRoute;