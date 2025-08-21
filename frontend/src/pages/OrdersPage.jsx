import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  TextField,
  InputAdornment,
  Button,
  FormControlLabel,
  Switch,
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
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Download as ExportIcon,
  CloudUpload as BulkIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import { ordersAPI } from '../services/api';
import { SyncModal } from '../components/Modals';

const OrdersPage = () => {
  const [loading, setLoading] = useState(true);
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [alertFilter, setAlertFilter] = useState(false);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [showFilters, setShowFilters] = useState(false);
  const [actionMenu, setActionMenu] = useState(null);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [error, setError] = useState(null);

  // Mock data removed - now using real API

  const statusOptions = [
    { value: '', label: 'Tất cả trạng thái' },
    { value: 'pending', label: 'Chờ xử lý' },
    { value: 'processing', label: 'Đang xử lý' },
    { value: 'shipped', label: 'Đã gửi hàng' },
    { value: 'delivered', label: 'Đã giao hàng' },
    { value: 'cancelled', label: 'Đã hủy' },
  ];

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('OrdersPage: Fetching orders from API...');
        const response = await ordersAPI.getAll({
          page: 1,
          size: 100, // Get more orders for display
          sort_by: 'order_date',
          sort_order: 'desc'
        });
        
        // Check if response has data (PaginatedResponse doesn't include success field)
        if (response.data && response.data.items) {
          const apiOrders = response.data.items || [];
          console.log(`OrdersPage: Fetched ${apiOrders.length} orders`);
          
          // Transform API data to component format
          const transformedOrders = apiOrders.map(order => ({
            id: order.id,
            orderNumber: order.order_number || `ORD-${order.id}`,
            itemId: order.item_id || 'N/A',
            machine: order.machine || 'N/A',
            nameProduct: order.product_name || 'Unknown Product',
            productLink: order.product_link || '#',
            productOption: order.product_option || 'Standard',
            tracking: order.tracking_number || '',
            customerName: order.customer_name || 'Unknown Customer',
            usernameEbay: order.username_ebay || 'N/A',
            address: order.shipping_address || 'N/A',
            phone: order.customer_phone || 'N/A',
            netEB: parseFloat(order.price_ebay || 0),
            orderDate: order.order_date ? new Date(order.order_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
            paidDate: order.order_date ? new Date(order.order_date).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
            trackingAddedDate: order.actual_ship_date ? new Date(order.actual_ship_date).toISOString().split('T')[0] : '',
            status: order.status || 'pending',
            alerts: order.alerts || [],
          }));
          
          setOrders(transformedOrders);
          setFilteredOrders(transformedOrders);
        } else {
          // Handle case where API returns empty or invalid data
          console.warn('OrdersPage: API response missing items field:', response.data);
          throw new Error('Invalid API response format');
        }
      } catch (err) {
        console.error('OrdersPage: Error fetching orders:', err);
        setError(`Không thể tải dữ liệu đơn hàng: ${err.message}`);
        
        // Set empty state instead of mock data
        setOrders([]);
        setFilteredOrders([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchOrders();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, statusFilter, alertFilter, orders]); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for sync modal events
  useEffect(() => {
    const handleOpenSync = () => setSyncModalOpen(true);
    window.addEventListener('openSyncModal', handleOpenSync);
    return () => window.removeEventListener('openSyncModal', handleOpenSync);
  }, []);

  const applyFilters = () => {
    let filtered = [...orders];

    if (searchTerm) {
      filtered = filtered.filter(order =>
        order.orderNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.nameProduct.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.tracking.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter) {
      filtered = filtered.filter(order => order.status === statusFilter);
    }

    if (alertFilter) {
      filtered = filtered.filter(order => order.alerts && order.alerts.length > 0);
    }

    setFilteredOrders(filtered);
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: { color: 'warning', label: 'Chờ xử lý' },
      processing: { color: 'info', label: 'Đang xử lý' },
      shipped: { color: 'primary', label: 'Đã gửi hàng' },
      delivered: { color: 'success', label: 'Đã giao hàng' },
      cancelled: { color: 'error', label: 'Đã hủy' },
    };
    return statusMap[status] || { color: 'default', label: status };
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  const handleSelectOrder = (orderId) => {
    setSelectedOrders(prev =>
      prev.includes(orderId)
        ? prev.filter(id => id !== orderId)
        : [...prev, orderId]
    );
  };

  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelectedOrders(filteredOrders.map(order => order.id));
    } else {
      setSelectedOrders([]);
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
          <CircularProgress />
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
            Quản lý Đơn hàng
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Theo dõi và quản lý tất cả đơn hàng eBay của bạn
          </Typography>
        </Box>
      </Box>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {orders.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tổng đơn hàng
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main', mb: 1 }}>
                {orders.filter(o => o.status === 'pending').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Chờ xử lý
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main', mb: 1 }}>
                {orders.filter(o => ['processing', 'shipped'].includes(o.status)).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Đang giao
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'error.main', mb: 1 }}>
                {orders.filter(o => o.alerts && o.alerts.length > 0).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Cảnh báo
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Controls */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="Tìm kiếm đơn hàng..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ minWidth: 250 }}
            />

            <Button
              variant="outlined"
              startIcon={<FilterIcon />}
              onClick={() => setShowFilters(!showFilters)}
            >
              Bộ lọc
            </Button>

            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              <Button variant="outlined" startIcon={<ExportIcon />} size="small">
                Xuất Excel
              </Button>
              <Button variant="contained" startIcon={<BulkIcon />} size="small">
                Bulk Actions
              </Button>
            </Box>
          </Box>

          {showFilters && (
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid #e0e0e0' }}>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Trạng thái</InputLabel>
                    <Select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      label="Trạng thái"
                    >
                      {statusOptions.map(option => (
                        <MenuItem key={option.value} value={option.value}>
                          {option.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFilter}
                        onChange={(e) => setAlertFilter(e.target.checked)}
                      />
                    }
                    label="Chỉ hiển thị đơn có cảnh báo"
                  />
                </Grid>
              </Grid>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardHeader
          title={
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Danh sách đơn hàng ({filteredOrders.length})
            </Typography>
          }
        />
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell width="40">
                  <Checkbox
                    checked={selectedOrders.length === filteredOrders.length && filteredOrders.length > 0}
                    indeterminate={selectedOrders.length > 0 && selectedOrders.length < filteredOrders.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 300 }}>THÔNG TIN ĐƠN HÀNG</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 250 }}>KHÁCH HÀNG</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 120, textAlign: 'right' }}>$NET</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 200 }}>TIMELINE</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 80 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredOrders.map((order) => {
                const statusInfo = getStatusBadge(order.status);
                return (
                  <TableRow key={order.id} hover>
                    <TableCell>
                      <Checkbox
                        checked={selectedOrders.includes(order.id)}
                        onChange={() => handleSelectOrder(order.id)}
                      />
                    </TableCell>
                    
                    {/* THÔNG TIN ĐƠN HÀNG */}
                    <TableCell>
                      {/* Line 1: Status */}
                      <Box sx={{ mb: 1 }}>
                        <Chip
                          label={statusInfo.label}
                          color={statusInfo.color}
                          size="small"
                        />
                        {order.alerts && order.alerts.length > 0 && (
                          <Chip
                            label={`${order.alerts.length} cảnh báo`}
                            color="error"
                            size="small"
                            variant="outlined"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                      
                      {/* Line 2: Order info with | separators */}
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          <span style={{ color: '#1976d2', fontWeight: 500 }}>#{order.orderNumber}</span> | 
                          <span> {order.itemId}</span> | 
                          <span> {order.machine}</span>
                        </Typography>
                      </Box>
                      
                      {/* Line 3: Product title */}
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {order.nameProduct}
                        </Typography>
                      </Box>
                      
                      {/* Line 4: Product link */}
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="primary">
                          <a href={order.productLink} target="_blank" rel="noopener noreferrer">
                            {order.productLink}
                          </a>
                        </Typography>
                      </Box>
                      
                      {/* Line 5: Product option */}
                      <Box sx={{ mb: 1 }}>
                        <Typography variant="caption" color="text.secondary">
                          {order.productOption}
                        </Typography>
                      </Box>
                      
                      {/* Line 6: Tracking */}
                      <Box>
                        <Typography variant="caption">
                          <strong>Tracking:</strong> {order.tracking || 'Chưa có'}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* KHÁCH HÀNG */}
                    <TableCell>
                      {/* Line 1: Customer name */}
                      <Box sx={{ mb: 0.5 }}>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {order.customerName}
                        </Typography>
                      </Box>
                      
                      {/* Line 2: eBay username */}
                      <Box sx={{ mb: 0.5 }}>
                        <Typography variant="caption" color="primary">
                          @{order.usernameEbay}
                        </Typography>
                      </Box>
                      
                      {/* Line 3: Phone */}
                      <Box sx={{ mb: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">
                          📞 {order.phone}
                        </Typography>
                      </Box>
                      
                      {/* Line 4-6: Address (wrapped) */}
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          📍 {order.address}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* $NET */}
                    <TableCell sx={{ textAlign: 'right' }}>
                      <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                        ${order.netEB.toFixed(2)}
                      </Typography>
                    </TableCell>
                    
                    {/* TIMELINE */}
                    <TableCell>
                      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                        <Typography variant="caption">
                          📅 <strong>Đặt hàng:</strong> {formatDate(order.orderDate)}
                        </Typography>
                        <Typography variant="caption">
                          💳 <strong>Thanh toán:</strong> {formatDate(order.paidDate)}
                        </Typography>
                        <Typography variant="caption">
                          🚚 <strong>Tracking:</strong> {formatDate(order.trackingAddedDate)}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* Actions */}
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={(e) => setActionMenu(e.currentTarget)}
                      >
                        <MoreIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
          
          {/* Empty State */}
          {!loading && filteredOrders.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || statusFilter ? 'Không tìm thấy đơn hàng phù hợp' : 'Chưa có đơn hàng nào'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm || statusFilter ? 'Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm' : 'Đơn hàng mới sẽ hiển thị tại đây khi có'}
              </Typography>
            </Box>
          )}
        </TableContainer>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenu}
        open={Boolean(actionMenu)}
        onClose={() => setActionMenu(null)}
      >
        <MenuItem onClick={() => setActionMenu(null)}>Xem chi tiết</MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>Chỉnh sửa</MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>In đơn hàng</MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>Hủy đơn</MenuItem>
      </Menu>

      {/* Sync Modal */}
      <SyncModal
        open={syncModalOpen}
        onClose={() => setSyncModalOpen(false)}
      />
    </MainLayout>
  );
};

export default OrdersPage;