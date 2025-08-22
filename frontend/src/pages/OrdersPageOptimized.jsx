import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  InputAdornment,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Checkbox,
  Menu,
  Grid,
  Alert,
  CircularProgress,
  Avatar,
  Tooltip,
  LinearProgress,
  Stack,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Download as ExportIcon,
  CloudUpload as BulkIcon,
  LocalShipping as ShippingIcon,
  Phone as PhoneIcon,
  AccountCircle as AccountIcon,
  LocationOn as LocationIcon,
  AttachMoney as MoneyIcon,
  CheckCircle as CompleteIcon,
  Schedule as PendingIcon,
  Cancel as CancelIcon,
  Refresh as RefreshIcon,
  Assessment as StatsIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import { ordersAPI } from '../services/api';
import { SyncModal } from '../components/Modals';

const OrdersPageOptimized = () => {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [actionMenu, setActionMenu] = useState(null);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    shipped: 0,
    delivered: 0,
    cancelled: 0
  });

  const statusOptions = [
    { value: '', label: 'Tất cả trạng thái' },
    { value: 'pending', label: 'Chờ xử lý', icon: <PendingIcon />, color: 'warning' },
    { value: 'processing', label: 'Đang xử lý', icon: <RefreshIcon />, color: 'info' },
    { value: 'shipped', label: 'Đã gửi hàng', icon: <ShippingIcon />, color: 'primary' },
    { value: 'delivered', label: 'Đã giao hàng', icon: <CompleteIcon />, color: 'success' },
    { value: 'cancelled', label: 'Đã hủy', icon: <CancelIcon />, color: 'error' },
  ];

  useEffect(() => {
    fetchOrders();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, statusFilter, orders]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('OrdersPageOptimized: Fetching orders from API...');
      const response = await ordersAPI.getAll({
        page: 1,
        size: 100,
        sort_by: 'order_date',
        sort_order: 'desc'
      });
      
      if (response.data && response.data.items) {
        const apiOrders = response.data.items || [];
        console.log(`OrdersPageOptimized: Fetched ${apiOrders.length} orders`);
        
        // Enhanced data transformation with better customer info
        const transformedOrders = apiOrders.map(order => ({
          id: order.id,
          orderNumber: order.order_number || `ORD-${order.id}`,
          itemId: order.item_id || 'N/A',
          machine: order.machine || 'N/A',
          nameProduct: order.product_name || 'Unknown Product',
          productLink: order.product_link || '#',
          productOption: order.product_option || 'Standard',
          tracking: order.tracking_number || '',
          
          // Enhanced Customer Data
          customerName: order.customer_name || 'Unknown Customer',
          customerEmail: order.customer_email || 'N/A',
          customerPhone: order.customer_phone || 'Chưa có SĐT',
          usernameEbay: order.username_ebay || 'Chưa có username',
          address: order.shipping_address || 'Chưa có địa chỉ',
          
          // Financial data
          netEB: parseFloat(order.price_ebay || 0),
          costPrice: parseFloat(order.price_cost || 0),
          netProfit: parseFloat(order.net_profit || 0),
          
          // Dates
          orderDate: order.order_date ? new Date(order.order_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
          expectedShipDate: order.expected_ship_date ? new Date(order.expected_ship_date).toISOString().split('T')[0] : null,
          actualShipDate: order.actual_ship_date ? new Date(order.actual_ship_date).toISOString().split('T')[0] : null,
          deliveryDate: order.delivery_date ? new Date(order.delivery_date).toISOString().split('T')[0] : null,
          
          // Status & alerts
          status: order.status || 'pending',
          alerts: order.alerts || [],
          carrier: order.carrier || 'N/A',
          notes: order.notes || '',
        }));

        setOrders(transformedOrders);
        
        // Calculate stats
        const statusCounts = transformedOrders.reduce((acc, order) => {
          acc[order.status] = (acc[order.status] || 0) + 1;
          return acc;
        }, {});
        
        setStats({
          total: transformedOrders.length,
          pending: statusCounts.pending || 0,
          processing: statusCounts.processing || 0,
          shipped: statusCounts.shipped || 0,
          delivered: statusCounts.delivered || 0,
          cancelled: statusCounts.cancelled || 0,
        });
        
      } else {
        console.log('OrdersPageOptimized: No items in response, using empty array');
        setOrders([]);
      }
      
    } catch (error) {
      console.error('OrdersPageOptimized: Error fetching orders:', error);
      setError(`Error loading orders: ${error.message}`);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...orders];

    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(order =>
        order.orderNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.nameProduct.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.usernameEbay.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter) {
      filtered = filtered.filter(order => order.status === statusFilter);
    }

    setFilteredOrders(filtered);
  };

  const getStatusColor = (status) => {
    const statusConfig = statusOptions.find(s => s.value === status);
    return statusConfig ? statusConfig.color : 'default';
  };

  const getStatusIcon = (status) => {
    const statusConfig = statusOptions.find(s => s.value === status);
    return statusConfig ? statusConfig.icon : <PendingIcon />;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelectedOrders(filteredOrders.map(order => order.id));
    } else {
      setSelectedOrders([]);
    }
  };

  const handleSelectOrder = (orderId) => {
    setSelectedOrders(prev =>
      prev.includes(orderId)
        ? prev.filter(id => id !== orderId)
        : [...prev, orderId]
    );
  };

  const StatsCard = ({ title, value, icon, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Avatar sx={{ bgcolor: `${color}.main`, width: 48, height: 48 }}>
          {icon}
        </Avatar>
        <Box>
          <Typography variant="h4" fontWeight="600">
            {value}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {title}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  const CustomerInfo = ({ order }) => (
    <Box>
      <Typography variant="subtitle2" fontWeight="600" gutterBottom>
        {order.customerName}
      </Typography>
      
      <Stack spacing={0.5}>
        {order.customerPhone !== 'Chưa có SĐT' && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <PhoneIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {order.customerPhone}
            </Typography>
          </Box>
        )}
        
        {order.usernameEbay !== 'Chưa có username' && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccountIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
            <Typography variant="caption" color="text.secondary">
              {order.usernameEbay}
            </Typography>
          </Box>
        )}
        
        {order.address !== 'Chưa có địa chỉ' && (
          <Tooltip title={order.address} arrow>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <LocationIcon sx={{ fontSize: 14, color: 'text.secondary' }} />
              <Typography variant="caption" color="text.secondary" noWrap>
                {order.address.substring(0, 30)}...
              </Typography>
            </Box>
          </Tooltip>
        )}
      </Stack>
    </Box>
  );

  const TimelineProgress = ({ order }) => {
    const steps = [
      { key: 'pending', label: 'Chờ xử lý' },
      { key: 'processing', label: 'Đang xử lý' },
      { key: 'shipped', label: 'Đã gửi' },
      { key: 'delivered', label: 'Đã giao' },
    ];

    const currentIndex = steps.findIndex(step => step.key === order.status);
    const progress = order.status === 'cancelled' ? 0 : ((currentIndex + 1) / steps.length) * 100;

    return (
      <Box>
        <LinearProgress 
          variant="determinate" 
          value={progress} 
          sx={{ 
            height: 8, 
            borderRadius: 4,
            bgcolor: order.status === 'cancelled' ? 'error.light' : 'grey.200',
            '& .MuiLinearProgress-bar': {
              bgcolor: order.status === 'cancelled' ? 'error.main' : 'success.main'
            }
          }} 
        />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {formatDate(order.orderDate)}
          </Typography>
          {order.tracking && (
            <Typography variant="caption" color="primary">
              {order.tracking}
            </Typography>
          )}
        </Box>
      </Box>
    );
  };

  return (
    <MainLayout>
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box>
            <Typography variant="h4" fontWeight="600" gutterBottom>
              📦 Quản lý Đơn hàng
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Theo dõi và xử lý đơn hàng eBay
            </Typography>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button variant="outlined" startIcon={<StatsIcon />}>
              Thống kê
            </Button>
            <Button variant="outlined" startIcon={<ExportIcon />}>
              Xuất Excel  
            </Button>
            <Button variant="contained" startIcon={<RefreshIcon />} onClick={fetchOrders}>
              Làm mới
            </Button>
          </Box>
        </Box>

        {/* Statistics Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={2}>
            <StatsCard title="Tổng đơn" value={stats.total} icon={<StatsIcon />} color="primary" />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <StatsCard title="Chờ xử lý" value={stats.pending} icon={<PendingIcon />} color="warning" />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <StatsCard title="Đang xử lý" value={stats.processing} icon={<RefreshIcon />} color="info" />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <StatsCard title="Đã gửi" value={stats.shipped} icon={<ShippingIcon />} color="primary" />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <StatsCard title="Đã giao" value={stats.delivered} icon={<CompleteIcon />} color="success" />
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <StatsCard title="Đã hủy" value={stats.cancelled} icon={<CancelIcon />} color="error" />
          </Grid>
        </Grid>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  size="small"
                  label="Tìm kiếm đơn hàng..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel>Trạng thái</InputLabel>
                  <Select
                    value={statusFilter}
                    label="Trạng thái"
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    {statusOptions.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {option.icon}
                          {option.label}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12} sm={6} md={2}>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  onClick={() => setShowFilters(!showFilters)}
                >
                  Lọc nâng cao
                </Button>
              </Grid>
              
              <Grid item xs={12} sm={6} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Hiển thị {filteredOrders.length} / {orders.length} đơn hàng
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Bulk Actions */}
        {selectedOrders.length > 0 && (
          <Alert 
            severity="info" 
            sx={{ mb: 3 }}
            action={
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button color="inherit" size="small">
                  Cập nhật trạng thái ({selectedOrders.length})
                </Button>
                <Button color="inherit" size="small">
                  Xuất đã chọn
                </Button>
                <Button color="inherit" size="small" onClick={() => setSelectedOrders([])}>
                  Bỏ chọn
                </Button>
              </Box>
            }
          >
            Đã chọn {selectedOrders.length} đơn hàng
          </Alert>
        )}

        {/* Main Content */}
        {loading ? (
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress size={40} />
          </Box>
        ) : (
          <Card>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={selectedOrders.length > 0 && selectedOrders.length < filteredOrders.length}
                        checked={filteredOrders.length > 0 && selectedOrders.length === filteredOrders.length}
                        onChange={handleSelectAll}
                      />
                    </TableCell>
                    <TableCell><strong>THÔNG TIN ĐƠN HÀNG</strong></TableCell>
                    <TableCell><strong>KHÁCH HÀNG</strong></TableCell>
                    <TableCell align="right"><strong>$NET</strong></TableCell>
                    <TableCell><strong>TIMELINE</strong></TableCell>
                    <TableCell align="center"><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredOrders.map((order) => (
                    <TableRow key={order.id} hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedOrders.includes(order.id)}
                          onChange={() => handleSelectOrder(order.id)}
                        />
                      </TableCell>
                      
                      {/* THÔNG TIN ĐƠN HÀNG */}
                      <TableCell>
                        <Box>
                          <Typography variant="subtitle2" fontWeight="600">
                            {order.orderNumber}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" noWrap>
                            {order.nameProduct}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                            <Chip 
                              label={order.status.toUpperCase()} 
                              color={getStatusColor(order.status)} 
                              size="small"
                              icon={getStatusIcon(order.status)}
                            />
                            {order.alerts.length > 0 && (
                              <Chip label="Alert" color="error" size="small" />
                            )}
                          </Box>
                        </Box>
                      </TableCell>
                      
                      {/* KHÁCH HÀNG */}
                      <TableCell>
                        <CustomerInfo order={order} />
                      </TableCell>
                      
                      {/* $NET */}
                      <TableCell align="right">
                        <Box>
                          <Typography variant="h6" fontWeight="600" color="success.main">
                            {formatCurrency(order.netEB)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Lợi nhuận: {formatCurrency(order.netProfit)}
                          </Typography>
                        </Box>
                      </TableCell>
                      
                      {/* TIMELINE */}
                      <TableCell sx={{ minWidth: 200 }}>
                        <TimelineProgress order={order} />
                      </TableCell>
                      
                      {/* Actions */}
                      <TableCell align="center">
                        <IconButton onClick={(e) => setActionMenu(e.currentTarget)}>
                          <MoreIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
            
            {filteredOrders.length === 0 && !loading && (
              <Box sx={{ textAlign: 'center', py: 6 }}>
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  Không tìm thấy đơn hàng
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm
                </Typography>
              </Box>
            )}
          </Card>
        )}

        {/* Action Menu */}
        <Menu
          anchorEl={actionMenu}
          open={Boolean(actionMenu)}
          onClose={() => setActionMenu(null)}
        >
          <MenuItem onClick={() => setActionMenu(null)}>Xem chi tiết</MenuItem>
          <MenuItem onClick={() => setActionMenu(null)}>Cập nhật trạng thái</MenuItem>
          <MenuItem onClick={() => setActionMenu(null)}>In nhãn vận chuyển</MenuItem>
          <MenuItem onClick={() => setActionMenu(null)}>Gửi email</MenuItem>
          <Divider />
          <MenuItem onClick={() => setActionMenu(null)} sx={{ color: 'error.main' }}>
            Hủy đơn hàng
          </MenuItem>
        </Menu>

        {/* Sync Modal */}
        <SyncModal 
          open={syncModalOpen} 
          onClose={() => setSyncModalOpen(false)}
          onSuccess={fetchOrders}
        />
      </Box>
    </MainLayout>
  );
};

export default OrdersPageOptimized;