import React from 'react';
import { Box, Typography } from '@mui/material';
import MainLayout from '../components/Layout/MainLayout';

const SuppliersPage = () => {
  return (
    <MainLayout>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600, mb: 2 }}>
          Nhà cung cấp
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Trang này đang được phát triển...
        </Typography>
      </Box>
    </MainLayout>
  );
};

export default SuppliersPage;