import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Sync as SyncIcon,
  Visibility as ViewIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CloudUpload as UploadIcon,
  Analytics as AnalyticsIcon,
  ShoppingCart as CartIcon,
  AttachMoney as MoneyIcon,
  LocalOffer as TagsIcon,
  TrendingUp as TrendIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import StatsCards from '../components/Dashboard/StatsCards';
import RevenueChart from '../components/Dashboard/RevenueChart';
import CategoryChart from '../components/Dashboard/CategoryChart';
import {
  TrackingBulkModal,
  ExportOrdersModal,
  OrderAnalyticsModal,
  SyncModal,
} from '../components/Modals';
import { dashboardAPI } from '../services/api';

const EbayDashboard = () => {
  // Modal states
  const [trackingBulkOpen, setTrackingBulkOpen] = useState(false);
  const [exportOrdersOpen, setExportOrdersOpen] = useState(false);
  const [analyticsOpen, setAnalyticsOpen] = useState(false);
  const [syncModalOpen, setSyncModalOpen] = useState(false);

  // Data states
  const [dashboardStats, setDashboardStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [activities, setActivities] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch dashboard data
  useEffect(() => {
    let isMounted = true;
    let retryCount = 0;
    const MAX_RETRIES = 3;
    
    const fetchDashboardData = async () => {
      try {
        if (!isMounted) return;
        
        setLoading(true);
        setError(null);
        
        console.log('Dashboard: Fetching data, attempt:', retryCount + 1);
        
        // Fetch all dashboard data with timeout
        const fetchWithTimeout = (promise, timeout = 5000) => {
          return Promise.race([
            promise,
            new Promise((_, reject) => 
              setTimeout(() => reject(new Error('Request timeout')), timeout)
            )
          ]);
        };

        const [statsResponse, ordersResponse, productsResponse, activityResponse, alertsResponse] = await Promise.all([
          fetchWithTimeout(dashboardAPI.getStats()),
          fetchWithTimeout(dashboardAPI.getRecentOrders(5)),
          fetchWithTimeout(dashboardAPI.getTopProducts(5)),
          fetchWithTimeout(dashboardAPI.getActivityTimeline(8)),
          dashboardAPI.getAlerts ? fetchWithTimeout(dashboardAPI.getAlerts()) : Promise.resolve({ data: { data: [] } })
        ]);

        if (!isMounted) return;

        // Set dashboard stats
        setDashboardStats(statsResponse.data.data);
        
        // Set recent orders with formatted data
        setRecentOrders(ordersResponse.data.data.map(order => ({
          id: order.order_number || `#${order.id}`,
          customer: order.customer_name || 'N/A',
          value: order.price_ebay ? `$${order.price_ebay.toFixed(2)}` : '$0.00',
          status: order.status,
          statusColor: getStatusColor(order.status),
          originalData: order
        })));

        // Set top products with formatted data
        setTopProducts(productsResponse.data.data.map(product => ({
          name: product.title,
          category: product.category || 'N/A',
          sold: product.sold || 0,
          revenue: product.revenue ? `$${product.revenue.toFixed(2)}` : `$${((product.price || 0) * (product.sold || 0)).toFixed(2)}`,
          trend: product.performance_score > 75 ? 'up' : product.performance_score < 50 ? 'down' : 'flat',
          trendValue: `${product.performance_score || 0}%`,
        })));

        // Set activities with formatted data
        setActivities(activityResponse.data.data.map(activity => ({
          title: activity.description || activity.action,
          time: new Date(activity.timestamp).toLocaleString('vi-VN'),
          color: activity.color || getActivityColor(activity.action),
        })));

        // Set alerts (with fallback if not implemented)
        setAlerts(alertsResponse.data?.data || []);

      } catch (err) {
        if (!isMounted) return;
        
        console.error('Dashboard: Error fetching data:', err, 'Retry count:', retryCount);
        
        // Retry with exponential backoff if under max retries
        if (retryCount < MAX_RETRIES && (err.message.includes('timeout') || err.message.includes('401') || err.message.includes('500'))) {
          retryCount++;
          const delay = Math.min(1000 * Math.pow(2, retryCount - 1), 5000);
          console.log(`Dashboard: Retrying in ${delay}ms...`);
          setTimeout(() => {
            if (isMounted) fetchDashboardData();
          }, delay);
          return;
        }
        
        setError(`Không thể tải dữ liệu dashboard: ${err.message}`);
        
        // Set empty state instead of mock data
        console.log('Dashboard: API failed, showing empty state');
        setDashboardStats({
          total_orders: 0,
          monthly_revenue: 0,
          active_listings: 0,
          avg_performance_score: 0,
          profit_margin: 0,
        });
        
        setRecentOrders([]);
        setTopProducts([]);
        setActivities([]);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    // Only fetch data once when component mounts
    fetchDashboardData();
    
    // Cleanup function to prevent memory leaks
    return () => {
      console.log('Dashboard: Component unmounting, canceling requests');
      isMounted = false;
    };
  }, []); // Empty dependency array - only run once on mount

  // Helper functions
  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'processing': return 'info';
      case 'shipped': return 'primary';
      case 'delivered': return 'success';
      case 'cancelled': return 'error';
      default: return 'default';
    }
  };

  const getActivityColor = (action) => {
    switch (action) {
      case 'create': return '#28a745';
      case 'update': return '#17a2b8';
      case 'sync': return '#0064D2';
      case 'delete': return '#dc3545';
      default: return '#6c757d';
    }
  };

  // Create stats data for StatsCards component
  const createStatsData = () => {
    if (!dashboardStats) return [];
    
    return [
      {
        title: 'Tổng đơn hàng (Tháng)',
        value: dashboardStats.total_orders?.toLocaleString() || '0',
        change: '+12.5%',
        changeText: 'so với tháng trước',
        trend: 'up',
        icon: <CartIcon />,
        color: 'primary',
        borderColor: '#0064D2',
      },
      {
        title: 'Doanh thu (Tháng)',
        value: `$${(dashboardStats.monthly_revenue || dashboardStats.total_revenue || 0).toLocaleString()}`,
        change: `+${dashboardStats.profit_margin?.toFixed(1) || '8.3'}%`,
        changeText: 'so với tháng trước',
        trend: 'up',
        icon: <MoneyIcon />,
        color: 'success',
        borderColor: '#28a745',
      },
      {
        title: 'Active Listings',
        value: (dashboardStats.active_listings || dashboardStats.total_listings || 0).toLocaleString(),
        progress: Math.round(dashboardStats.avg_performance_score || 75),
        progressText: `${Math.round(dashboardStats.avg_performance_score || 75)}% đã tối ưu`,
        icon: <TagsIcon />,
        color: 'info',
        borderColor: '#17a2b8',
      },
      {
        title: 'Điểm hiệu suất TB',
        value: `${(dashboardStats.avg_performance_score || 0).toFixed(1)}`,
        change: '+2.1%',
        changeText: 'cải thiện tốt',
        trend: 'up',
        icon: <TrendIcon />,
        color: 'warning',
        borderColor: '#ffc107',
      },
    ];
  };

  const getStatusLabel = (status) => {
    const statusMap = {
      processing: 'Đang xử lý',
      delivered: 'Đã giao',
      shipping: 'Đang giao',
    };
    return statusMap[status] || status;
  };

  const handleExportReport = () => {
    setExportOrdersOpen(true);
  };

  const handleSyncData = () => {
    setSyncModalOpen(true);
  };

  return (
    <MainLayout>
      {/* Page Header */}
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: { xs: 'flex-start', sm: 'center' },
          flexDirection: { xs: 'column', sm: 'row' },
          mb: 4,
        }}
      >
        <Typography
          variant="h3"
          sx={{
            fontWeight: 600,
            color: 'text.primary',
            mb: { xs: 2, sm: 0 },
          }}
        >
          Dashboard Tổng quan
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExportReport}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 500,
            }}
          >
            Xuất báo cáo
          </Button>
          <Button
            variant="contained"
            startIcon={<SyncIcon />}
            onClick={handleSyncData}
            sx={{
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 500,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
              },
            }}
          >
            Đồng bộ dữ liệu
          </Button>
        </Box>
      </Box>

      {/* Loading Indicator */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Lỗi tải dữ liệu: {error}. Đang sử dụng dữ liệu dự phòng.
        </Alert>
      )}

      {/* Statistics Cards */}
      <StatsCards stats={createStatsData()} />

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <Card sx={{ mb: 4 }}>
          <CardHeader
            title={
              <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                <i className="bi bi-exclamation-triangle me-2" />
                Cảnh báo cần xử lý ({alerts.length})
              </Typography>
            }
          />
          <CardContent sx={{ pt: 0 }}>
            <Grid container spacing={2}>
              {alerts.map((alert) => (
                <Grid item xs={12} md={6} key={alert.id}>
                  <Alert 
                    severity={alert.type} 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      '& .MuiAlert-message': { 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between',
                        width: '100%'
                      }
                    }}
                  >
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        #{alert.orderNumber} - {alert.message}
                      </Typography>
                    </Box>
                    <Button 
                      size="small" 
                      color="inherit"
                      sx={{ ml: 2, textTransform: 'none' }}
                    >
                      Xem
                    </Button>
                  </Alert>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card sx={{ mb: 4 }}>
        <CardHeader
          title={
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              Hành động nhanh
            </Typography>
          }
        />
        <CardContent sx={{ pt: 0 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                onClick={() => window.location.href = '/orders'}
                sx={{
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 500,
                }}
                startIcon={<i className="bi bi-list-check" />}
              >
                Quản lý Đơn hàng
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                color="success"
                onClick={() => setTrackingBulkOpen(true)}
                sx={{
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 500,
                }}
                startIcon={<UploadIcon />}
              >
                Add Tracking Bulk
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                color="info"
                onClick={handleExportReport}
                sx={{
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 500,
                }}
                startIcon={<DownloadIcon />}
              >
                Xuất Dữ liệu
              </Button>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Button
                fullWidth
                variant="contained"
                color="warning"
                onClick={() => setAnalyticsOpen(true)}
                sx={{
                  py: 1.5,
                  textTransform: 'none',
                  fontWeight: 500,
                }}
                startIcon={<AnalyticsIcon />}
              >
                Báo cáo
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Charts Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} lg={8}>
          <RevenueChart />
        </Grid>
        <Grid item xs={12} lg={4}>
          <CategoryChart />
        </Grid>
      </Grid>

      {/* Tables Row */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Recent Orders */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Đơn hàng gần đây
                </Typography>
              }
            />
            <CardContent sx={{ pt: 0 }}>
              {recentOrders.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>Mã đơn</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Khách hàng</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Giá trị</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Trạng thái</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Hành động</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {recentOrders.map((order) => (
                        <TableRow key={order.id} hover>
                          <TableCell>{order.id}</TableCell>
                          <TableCell>{order.customer}</TableCell>
                          <TableCell sx={{ fontWeight: 500 }}>{order.value}</TableCell>
                          <TableCell>
                            <Chip
                              label={getStatusLabel(order.status)}
                              color={order.statusColor}
                              size="small"
                              sx={{ minWidth: 100 }}
                            />
                          </TableCell>
                          <TableCell>
                            <IconButton size="small" color="primary">
                              <ViewIcon fontSize="small" />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary">
                    Chưa có đơn hàng nào
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Các đơn hàng mới sẽ hiển thị tại đây
                  </Typography>
                </Box>
              )}
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button variant="contained" size="small" sx={{ textTransform: 'none' }}>
                  Xem tất cả đơn hàng
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Products */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardHeader
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Sản phẩm bán chạy
                </Typography>
              }
            />
            <CardContent sx={{ pt: 0 }}>
              {topProducts.length > 0 ? (
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell sx={{ fontWeight: 600 }}>Sản phẩm</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Danh mục</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Đã bán</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Doanh thu</TableCell>
                        <TableCell sx={{ fontWeight: 600 }}>Trend</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {topProducts.map((product, index) => (
                        <TableRow key={index} hover>
                          <TableCell sx={{ maxWidth: 150 }}>
                            <Typography variant="body2" noWrap>
                              {product.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" color="text.secondary">
                              {product.category}
                            </Typography>
                          </TableCell>
                          <TableCell>{product.sold}</TableCell>
                          <TableCell sx={{ fontWeight: 500 }}>{product.revenue}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              {product.trend === 'up' ? (
                                <TrendingUpIcon
                                  sx={{ color: 'success.main', fontSize: '1rem', mr: 0.5 }}
                                />
                              ) : (
                                <TrendingDownIcon
                                  sx={{ color: 'error.main', fontSize: '1rem', mr: 0.5 }}
                                />
                              )}
                              <Typography
                                variant="caption"
                                sx={{
                                  color: product.trend === 'up' ? 'success.main' : 'error.main',
                                  fontWeight: 500,
                                }}
                              >
                                {product.trendValue}
                              </Typography>
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary">
                    Chưa có sản phẩm nào
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sản phẩm bán chạy sẽ hiển thị tại đây
                  </Typography>
                </Box>
              )}
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button variant="contained" size="small" sx={{ textTransform: 'none' }}>
                  Xem tất cả sản phẩm
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Activity Timeline */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardHeader
              title={
                <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                  Hoạt động gần đây
                </Typography>
              }
            />
            <CardContent sx={{ pt: 0 }}>
              <Box sx={{ position: 'relative', pl: 4 }}>
                {/* Timeline line */}
                <Box
                  sx={{
                    position: 'absolute',
                    left: 15,
                    top: 0,
                    bottom: 0,
                    width: 2,
                    backgroundColor: 'grey.200',
                  }}
                />
                
                {activities.length > 0 ? activities.map((activity, index) => (
                  <Box key={index} sx={{ position: 'relative', mb: 3, last: { mb: 0 } }}>
                    {/* Timeline marker */}
                    <Box
                      sx={{
                        position: 'absolute',
                        left: -40,
                        top: 5,
                        width: 12,
                        height: 12,
                        borderRadius: '50%',
                        backgroundColor: activity.color,
                        border: '2px solid white',
                        boxShadow: '0 0 0 2px #e9ecef',
                      }}
                    />
                    
                    {/* Timeline content */}
                    <Box>
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
                        {activity.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {activity.time}
                      </Typography>
                    </Box>
                  </Box>
                )) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Typography variant="h6" color="text.secondary">
                      Chưa có hoạt động nào
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Các hoạt động gần đây sẽ hiển thị tại đây
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Modal Components */}
      <TrackingBulkModal
        open={trackingBulkOpen}
        onClose={() => setTrackingBulkOpen(false)}
      />
      
      <ExportOrdersModal
        open={exportOrdersOpen}
        onClose={() => setExportOrdersOpen(false)}
      />
      
      <OrderAnalyticsModal
        open={analyticsOpen}
        onClose={() => setAnalyticsOpen(false)}
      />
      
      <SyncModal
        open={syncModalOpen}
        onClose={() => setSyncModalOpen(false)}
      />
    </MainLayout>
  );
};

export default EbayDashboard;