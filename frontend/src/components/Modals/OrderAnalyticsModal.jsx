import React, { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Analytics as AnalyticsIcon,
} from '@mui/icons-material';
import BaseModal from './BaseModal';

const OrderAnalyticsModal = ({ open, onClose }) => {
  const [timeRange, setTimeRange] = useState('last30days');

  const analytics = {
    totalOrders: { value: 1247, change: 12.5, trend: 'up' },
    totalRevenue: { value: 2458900, change: 8.3, trend: 'up' },
    avgOrderValue: { value: 197000, change: -2.1, trend: 'down' },
    conversionRate: { value: 3.2, change: 0.8, trend: 'up' },
  };

  const topProducts = [
    { name: 'iPhone 15 Pro Max', orders: 89, revenue: 178000000 },
    { name: 'Samsung Galaxy S24', orders: 67, revenue: 134000000 },
    { name: 'MacBook Air M2', orders: 45, revenue: 135000000 },
  ];

  const timeRanges = [
    { value: 'last7days', label: '7 ngày gần đây' },
    { value: 'last30days', label: '30 ngày gần đây' },
    { value: 'last90days', label: '90 ngày gần đây' },
    { value: 'thisYear', label: 'Năm nay' },
  ];

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND',
    }).format(amount);
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('vi-VN').format(num);
  };

  const renderTrendIcon = (trend) => {
    return trend === 'up' ? (
      <TrendingUpIcon sx={{ color: 'success.main', fontSize: '1rem' }} />
    ) : (
      <TrendingDownIcon sx={{ color: 'error.main', fontSize: '1rem' }} />
    );
  };

  return (
    <BaseModal
      open={open}
      onClose={onClose}
      title="Báo cáo phân tích đơn hàng"
      maxWidth="lg"
    >
      <Box>
        {/* Time Range Selector */}
        <Box sx={{ mb: 4 }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Khoảng thời gian</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Khoảng thời gian"
            >
              {timeRanges.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>

        {/* Analytics Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <AnalyticsIcon sx={{ color: 'primary.main', mr: 1 }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    Tổng đơn hàng
                  </Typography>
                </Box>
                <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {formatNumber(analytics.totalOrders.value)}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {renderTrendIcon(analytics.totalOrders.trend)}
                  <Typography
                    variant="body2"
                    sx={{
                      color: analytics.totalOrders.trend === 'up' ? 'success.main' : 'error.main',
                      ml: 0.5,
                    }}
                  >
                    {analytics.totalOrders.change > 0 ? '+' : ''}{analytics.totalOrders.change}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  Tổng doanh thu
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {formatCurrency(analytics.totalRevenue.value)}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {renderTrendIcon(analytics.totalRevenue.trend)}
                  <Typography
                    variant="body2"
                    sx={{
                      color: analytics.totalRevenue.trend === 'up' ? 'success.main' : 'error.main',
                      ml: 0.5,
                    }}
                  >
                    {analytics.totalRevenue.change > 0 ? '+' : ''}{analytics.totalRevenue.change}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  Giá trị đơn TB
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {formatCurrency(analytics.avgOrderValue.value)}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {renderTrendIcon(analytics.avgOrderValue.trend)}
                  <Typography
                    variant="body2"
                    sx={{
                      color: analytics.avgOrderValue.trend === 'up' ? 'success.main' : 'error.main',
                      ml: 0.5,
                    }}
                  >
                    {analytics.avgOrderValue.change > 0 ? '+' : ''}{analytics.avgOrderValue.change}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
                  Tỷ lệ chuyển đổi
                </Typography>
                <Typography variant="h5" sx={{ fontWeight: 'bold', mb: 1 }}>
                  {analytics.conversionRate.value}%
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {renderTrendIcon(analytics.conversionRate.trend)}
                  <Typography
                    variant="body2"
                    sx={{
                      color: analytics.conversionRate.trend === 'up' ? 'success.main' : 'error.main',
                      ml: 0.5,
                    }}
                  >
                    {analytics.conversionRate.change > 0 ? '+' : ''}{analytics.conversionRate.change}%
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Top Products */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
              Sản phẩm bán chạy nhất
            </Typography>
            
            {topProducts.map((product, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  py: 2,
                  borderBottom: index < topProducts.length - 1 ? '1px solid #e0e0e0' : 'none',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Chip
                    label={index + 1}
                    size="small"
                    color="primary"
                    sx={{ mr: 2, minWidth: 24 }}
                  />
                  <Typography variant="body1" sx={{ fontWeight: 500 }}>
                    {product.name}
                  </Typography>
                </Box>
                
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="body2" color="text.secondary">
                    {formatNumber(product.orders)} đơn hàng
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
                    {formatCurrency(product.revenue)}
                  </Typography>
                </Box>
              </Box>
            ))}
          </CardContent>
        </Card>
      </Box>
    </BaseModal>
  );
};

export default OrderAnalyticsModal;