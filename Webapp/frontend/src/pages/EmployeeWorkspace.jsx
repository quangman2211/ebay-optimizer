import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardHeader,
  CardContent,
  Chip,
  Alert,
  LinearProgress,
  IconButton,
  Menu,
  MenuItem,
  Divider,
  Badge,
  CircularProgress,
  TextField,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemAvatar,
  Avatar,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tooltip
} from '@mui/material';
import {
  Add as AddIcon,
  Sync as SyncIcon,
  TrendingUp as OptimizeIcon,
  Speed as SpeedIcon,
  Assignment as TaskIcon,
  AccountCircle as AccountIcon,
  KeyboardArrowDown as ArrowDownIcon,
  CheckCircle as CompleteIcon,
  Schedule as PendingIcon,
  Search as SearchIcon,
  Business as SupplierIcon,
  Inventory as ProductIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Star as RatingIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import { useAuth } from '../context/AuthContext';
import { listingsAPI, ordersAPI, accountsAPI, dashboardAPI } from '../services/api';

const EmployeeWorkspace = () => {
  const { } = useAuth();
  const [selectedAccount, setSelectedAccount] = useState('seller123@email.com');
  const [accountMenuAnchor, setAccountMenuAnchor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Employee performance data - now from API
  const [todayStats, setTodayStats] = useState({
    listingsToday: 0,
    targetListings: 50,
    avgTimePerListing: 0,
    successRate: 0,
    weeklyListings: 0,
    monthlyListings: 0
  });

  // Work queue data - now from API
  const [workQueue, setWorkQueue] = useState({
    drafts: 0,
    pendingOptimization: 0,
    failedSyncs: 0,
    missingImages: 0
  });

  // Available accounts - now from API
  const [accounts, setAccounts] = useState([]);

  // New states for supplier directory and product lookup
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [supplierSearch, setSupplierSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [expandedSupplier, setExpandedSupplier] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [openProductDialog, setOpenProductDialog] = useState(false);
  const [quickLookupMode, setQuickLookupMode] = useState('supplier'); // 'supplier' or 'product'

  const currentAccount = accounts.find(acc => acc.email === selectedAccount) || {
    email: selectedAccount,
    status: 'active',
    syncTime: 'Đang tải...',
    listings: 0,
    revenue: 0
  };

  // Load suppliers and products for quick lookup
  const loadSuppliersAndProducts = async () => {
    try {
      // Load suppliers
      const suppliersResponse = await fetch('/api/v1/suppliers?size=50&status=active');
      const suppliersData = await suppliersResponse.json();
      if (suppliersData.success !== false) {
        setSuppliers(suppliersData.items || []);
      }

      // Load products
      const productsResponse = await fetch('/api/v1/products?size=100&status=active');
      const productsData = await productsResponse.json();
      if (productsData.success !== false) {
        setProducts(productsData.items || []);
      }
    } catch (error) {
      console.error('Error loading suppliers/products:', error);
    }
  };

  // Fetch data from API
  useEffect(() => {
    const fetchWorkspaceData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch accounts
        const accountsResponse = await accountsAPI.getAll({ page: 1, size: 100 });
        if (accountsResponse.data?.items) {
          const transformedAccounts = accountsResponse.data.items.map(account => ({
            email: account.username || account.email || `account_${account.id}`,
            status: account.status || 'active',
            syncTime: account.last_activity ? new Date(account.last_activity).toLocaleString('vi-VN') : 'Chưa có',
            listings: account.total_listings || 0,
            revenue: account.monthly_revenue || 0
          }));
          setAccounts(transformedAccounts);
          
          // Set first account as selected if none selected
          if (transformedAccounts.length > 0 && !selectedAccount) {
            setSelectedAccount(transformedAccounts[0].email);
          }
        }

        // Fetch dashboard stats
        const statsResponse = await dashboardAPI.getStats();
        if (statsResponse.data?.data) {
          const stats = statsResponse.data.data;
          setTodayStats({
            listingsToday: stats.daily_listings || 0,
            targetListings: 50,
            avgTimePerListing: 3.2, // This would come from employee metrics API
            successRate: Math.round((stats.active_listings / Math.max(stats.total_listings, 1)) * 100) || 0,
            weeklyListings: stats.weekly_listings || 0,
            monthlyListings: stats.monthly_listings || 0
          });
        }

        // Calculate work queue from listings and orders
        const listingsResponse = await listingsAPI.getAll({ page: 1, size: 100 });
        const ordersResponse = await ordersAPI.getAll({ page: 1, size: 100 });
        
        if (listingsResponse.data?.items) {
          const listings = listingsResponse.data.items;
          const orders = ordersResponse.data?.items || [];
          
          setWorkQueue({
            drafts: listings.filter(l => l.status === 'draft').length,
            pendingOptimization: listings.filter(l => (l.performance_score || 0) < 70).length,
            failedSyncs: orders.filter(o => !o.tracking_number && o.status === 'shipped').length,
            missingImages: listings.filter(l => !l.images || l.images.length === 0).length
          });
        }

        // Load suppliers and products for fulfillment lookup
        await loadSuppliersAndProducts();
        
      } catch (err) {
        console.error('EmployeeWorkspace: Error fetching data:', err);
        setError('Không thể tải dữ liệu workspace. Vui lòng thử lại.');
      } finally {
        setLoading(false);
      }
    };

    fetchWorkspaceData();
  }, [selectedAccount]);
  
  const handleAccountSwitch = (accountEmail) => {
    setSelectedAccount(accountEmail);
    setAccountMenuAnchor(null);
  };

  const getProgressPercentage = () => {
    return Math.min((todayStats.listingsToday / todayStats.targetListings) * 100, 100);
  };

  const getWorkQueueTotal = () => {
    return Object.values(workQueue).reduce((sum, count) => sum + count, 0);
  };

  const handleQuickAction = (action) => {
    switch(action) {
      case 'new-listing':
        window.location.href = '/listings/create';
        break;
      case 'bulk-optimize':
        // Open bulk optimization modal
        console.log('Opening bulk optimize modal');
        break;
      case 'sync-all':
        // Trigger sync for all accounts
        console.log('Syncing all accounts');
        break;
      default:
        break;
    }
  };

  // New utility functions for supplier/product lookup
  const filteredSuppliers = suppliers.filter(supplier =>
    supplier.name?.toLowerCase().includes(supplierSearch.toLowerCase()) ||
    supplier.company_name?.toLowerCase().includes(supplierSearch.toLowerCase()) ||
    supplier.contact_person?.toLowerCase().includes(supplierSearch.toLowerCase())
  );

  const filteredProducts = products.filter(product =>
    product.name?.toLowerCase().includes(productSearch.toLowerCase()) ||
    product.sku?.toLowerCase().includes(productSearch.toLowerCase()) ||
    product.category?.toLowerCase().includes(productSearch.toLowerCase())
  );

  const handleSupplierToggle = (supplierId) => {
    setExpandedSupplier(expandedSupplier === supplierId ? null : supplierId);
  };

  const handleProductView = (product) => {
    setSelectedProduct(product);
    setOpenProductDialog(true);
  };

  const getSupplierProducts = (supplierId) => {
    return products.filter(p => 
      p.primary_supplier_id === supplierId || p.backup_supplier_id === supplierId
    );
  };

  const getStockLevelColor = (stock, minStock) => {
    if (stock === 0) return 'error';
    if (stock <= minStock) return 'warning';
    return 'success';
  };

  const getStockIcon = (stock, minStock) => {
    if (stock === 0) return '🔴';
    if (stock <= minStock) return '🟡';
    return '🟢';
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  const calculateProfitMargin = (sellingPrice, costPrice) => {
    if (!sellingPrice || !costPrice) return 0;
    return ((sellingPrice - costPrice) / sellingPrice * 100).toFixed(1);
  };

  if (loading) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ ml: 2 }}>Đang tải workspace...</Typography>
        </Box>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
          <Button 
            variant="outlined" 
            size="small" 
            sx={{ ml: 2 }}
            onClick={() => window.location.reload()}
          >
            Thử lại
          </Button>
        </Alert>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Employee Quick Actions Bar */}
      <Card sx={{ 
        mb: 3,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}>
        <CardContent sx={{ py: 2 }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={8}>
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
                <Button
                  variant="contained"
                  color="inherit"
                  startIcon={<AddIcon />}
                  sx={{ 
                    bgcolor: 'rgba(255, 255, 255, 0.2)', 
                    '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.3)' },
                    color: 'white'
                  }}
                  onClick={() => window.location.href = '/quick-listing'}
                >
                  Tạo Listing (Ctrl+N)
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<OptimizeIcon />}
                  sx={{ 
                    borderColor: 'rgba(255, 255, 255, 0.5)', 
                    color: 'white',
                    '&:hover': { 
                      borderColor: 'white', 
                      bgcolor: 'rgba(255, 255, 255, 0.1)' 
                    }
                  }}
                  onClick={() => handleQuickAction('bulk-optimize')}
                >
                  Tối Ưu Hàng Loạt
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<SyncIcon />}
                  sx={{ 
                    borderColor: 'rgba(255, 255, 255, 0.5)', 
                    color: 'white',
                    '&:hover': { 
                      borderColor: 'white', 
                      bgcolor: 'rgba(255, 255, 255, 0.1)' 
                    }
                  }}
                  onClick={() => handleQuickAction('sync-all')}
                >
                  Đồng Bộ Tất Cả
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                <Typography variant="body2" sx={{ color: 'rgba(255, 255, 255, 0.8)' }}>
                  Tài khoản:
                </Typography>
                <Button
                  variant="text"
                  endIcon={<ArrowDownIcon />}
                  sx={{ 
                    color: 'white',
                    textTransform: 'none',
                    '&:hover': { bgcolor: 'rgba(255, 255, 255, 0.1)' }
                  }}
                  onClick={(e) => setAccountMenuAnchor(e.currentTarget)}
                >
                  {selectedAccount}
                </Button>
                <Menu
                  anchorEl={accountMenuAnchor}
                  open={Boolean(accountMenuAnchor)}
                  onClose={() => setAccountMenuAnchor(null)}
                >
                  {accounts.map((account) => (
                    <MenuItem 
                      key={account.email}
                      onClick={() => handleAccountSwitch(account.email)}
                      selected={account.email === selectedAccount}
                    >
                      <Box>
                        <Typography variant="body2">{account.email}</Typography>
                        <Typography variant="caption" color="textSecondary">
                          {account.listings} listings • ${account.revenue.toLocaleString()}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Menu>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Performance Dashboard */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e8f5e8', border: '2px solid #4caf50' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <SpeedIcon sx={{ fontSize: 40, color: '#4caf50', mb: 1 }} />
              <Typography variant="h3" color="success.main" fontWeight="bold">
                {todayStats.listingsToday}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Listings hôm nay
              </Typography>
              <LinearProgress 
                variant="determinate" 
                value={getProgressPercentage()} 
                sx={{ 
                  height: 6, 
                  borderRadius: 3,
                  bgcolor: '#c8e6c9',
                  '& .MuiLinearProgress-bar': { bgcolor: '#4caf50' }
                }}
              />
              <Typography variant="caption" color="success.main" sx={{ mt: 1, display: 'block' }}>
                Mục tiêu: {todayStats.targetListings} ({Math.round(getProgressPercentage())}%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#fff3e0', border: '2px solid #ff9800' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <TaskIcon sx={{ fontSize: 40, color: '#ff9800', mb: 1 }} />
              <Typography variant="h3" color="warning.main" fontWeight="bold">
                {todayStats.avgTimePerListing}m
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Thời gian TB/listing
              </Typography>
              <Typography variant="caption" color="success.main">
                Cải thiện: -0.8 phút (↑18%)
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e3f2fd', border: '2px solid #2196f3' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <CompleteIcon sx={{ fontSize: 40, color: '#2196f3', mb: 1 }} />
              <Typography variant="h3" color="primary.main" fontWeight="bold">
                {todayStats.successRate}%
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Tỷ lệ thành công
              </Typography>
              <Typography variant="caption" color="primary.main">
                {Math.floor((todayStats.successRate/100) * todayStats.listingsToday)}/{todayStats.listingsToday} published
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#fce4ec', border: '2px solid #e91e63' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Badge badgeContent={getWorkQueueTotal()} color="error">
                <PendingIcon sx={{ fontSize: 40, color: '#e91e63', mb: 1 }} />
              </Badge>
              <Typography variant="h3" color="secondary.main" fontWeight="bold">
                {getWorkQueueTotal()}
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Công việc chờ
              </Typography>
              <Typography variant="caption" color="secondary.main">
                Cần xử lý ngay
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Work Queue & Performance Analysis */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={7}>
          <Card>
            <CardHeader 
              title="🔥 Hàng Đợi Công Việc Ưu Tiên" 
              subheader="Các task cần xử lý ngay"
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ bgcolor: '#f3e5f5', border: '1px solid #9c27b0' }}>
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" color="primary" fontWeight="bold">
                        {workQueue.drafts}
                      </Typography>
                      <Typography variant="body2" gutterBottom>Drafts</Typography>
                      <Button 
                        size="small" 
                        variant="outlined" 
                        color="primary"
                        onClick={() => window.location.href = '/listings?filter=drafts'}
                      >
                        Xử lý
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ bgcolor: '#fff8e1', border: '1px solid #ff9800' }}>
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" color="warning.main" fontWeight="bold">
                        {workQueue.pendingOptimization}
                      </Typography>
                      <Typography variant="body2" gutterBottom>Cần tối ưu</Typography>
                      <Button 
                        size="small" 
                        variant="outlined" 
                        color="warning"
                        onClick={() => handleQuickAction('bulk-optimize')}
                      >
                        Tối ưu
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ bgcolor: '#ffebee', border: '1px solid #f44336' }}>
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" color="error" fontWeight="bold">
                        {workQueue.failedSyncs}
                      </Typography>
                      <Typography variant="body2" gutterBottom>Lỗi sync</Typography>
                      <Button 
                        size="small" 
                        variant="outlined" 
                        color="error"
                        onClick={() => window.location.href = '/sync?filter=failed'}
                      >
                        Khắc phục
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={6} sm={3}>
                  <Card variant="outlined" sx={{ bgcolor: '#e8f5e8', border: '1px solid #4caf50' }}>
                    <CardContent sx={{ textAlign: 'center', py: 2 }}>
                      <Typography variant="h4" color="success.main" fontWeight="bold">
                        {workQueue.missingImages}
                      </Typography>
                      <Typography variant="body2" gutterBottom>Thiếu hình</Typography>
                      <Button 
                        size="small" 
                        variant="outlined" 
                        color="success"
                        onClick={() => window.location.href = '/listings?filter=no-images'}
                      >
                        Upload
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={5}>
          <Card>
            <CardHeader 
              title="📊 Hiệu Suất Cá Nhân" 
              subheader="Tracking tiến độ và cải thiện"
            />
            <CardContent>
              {/* Current Account Info */}
              <Box sx={{ 
                p: 2, 
                bgcolor: currentAccount?.status === 'active' ? '#e8f5e8' : '#fff3e0', 
                borderRadius: 1, 
                mb: 2,
                border: `1px solid ${currentAccount?.status === 'active' ? '#4caf50' : '#ff9800'}`
              }}>
                <Typography variant="body2" color="textSecondary">Tài khoản hiện tại:</Typography>
                <Typography variant="h6">{selectedAccount}</Typography>
                <Typography variant="caption" color="textSecondary">
                  📊 {currentAccount?.listings.toLocaleString()} listings • 
                  💰 ${currentAccount?.revenue.toLocaleString()} • 
                  🔄 Sync: {currentAccount?.syncTime}
                </Typography>
              </Box>

              {/* Performance Progress */}
              <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="textSecondary">Tiến độ hôm nay</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {todayStats.listingsToday}/{todayStats.targetListings}
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={getProgressPercentage()} 
                  sx={{ 
                    height: 12, 
                    borderRadius: 6,
                    bgcolor: '#f0f0f0',
                    '& .MuiLinearProgress-bar': { 
                      borderRadius: 6,
                      background: 'linear-gradient(90deg, #4caf50 0%, #8bc34a 100%)'
                    }
                  }}
                />
                <Typography variant="caption" color="success.main" sx={{ mt: 0.5, display: 'block' }}>
                  🎯 Còn {Math.max(todayStats.targetListings - todayStats.listingsToday, 0)} listings để đạt mục tiêu
                </Typography>
              </Box>

              {/* Weekly/Monthly Stats */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={6}>
                  <Typography variant="caption" color="textSecondary">Tuần này</Typography>
                  <Typography variant="h6">{todayStats.weeklyListings}</Typography>
                  <Typography variant="caption" color="success.main">+8% ↗</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="caption" color="textSecondary">Tháng này</Typography>
                  <Typography variant="h6">{todayStats.monthlyListings}</Typography>
                  <Typography variant="caption" color="success.main">+15% ↗</Typography>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />
              
              <Button 
                variant="contained" 
                fullWidth 
                startIcon={<SpeedIcon />}
                onClick={() => window.location.href = '/analytics/personal'}
              >
                Xem báo cáo chi tiết
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Lookup Section for Fulfillment Staff */}
      <Card sx={{ mb: 3 }}>
        <CardHeader 
          title="⚡ Tra Cứu Nhanh - Fulfillment Support" 
          subheader="Tìm kiếm nhà cung cấp và sản phẩm cho việc fulfillment đơn hàng"
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={quickLookupMode === 'supplier' ? 'contained' : 'outlined'}
                size="small"
                startIcon={<SupplierIcon />}
                onClick={() => setQuickLookupMode('supplier')}
              >
                Nhà Cung Cấp
              </Button>
              <Button
                variant={quickLookupMode === 'product' ? 'contained' : 'outlined'}
                size="small"
                startIcon={<ProductIcon />}
                onClick={() => setQuickLookupMode('product')}
              >
                Sản Phẩm
              </Button>
            </Box>
          }
        />
        <CardContent>
          <Grid container spacing={3}>
            {/* Supplier Directory */}
            {quickLookupMode === 'supplier' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  placeholder="Tìm kiếm nhà cung cấp theo tên, công ty hoặc người liên hệ..."
                  value={supplierSearch}
                  onChange={(e) => setSupplierSearch(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    )
                  }}
                  sx={{ mb: 2 }}
                />
                
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  <List>
                    {filteredSuppliers.slice(0, 10).map((supplier) => {
                      const supplierProducts = getSupplierProducts(supplier.id);
                      const isExpanded = expandedSupplier === supplier.id;
                      
                      return (
                        <React.Fragment key={supplier.id}>
                          <ListItem 
                            button 
                            onClick={() => handleSupplierToggle(supplier.id)}
                            sx={{ 
                              border: '1px solid #e0e0e0', 
                              borderRadius: 1, 
                              mb: 1,
                              '&:hover': { bgcolor: '#f5f5f5' }
                            }}
                          >
                            <ListItemAvatar>
                              <Avatar sx={{ bgcolor: 'primary.main' }}>
                                <SupplierIcon />
                              </Avatar>
                            </ListItemAvatar>
                            <ListItemText
                              primary={
                                <Box>
                                  <Typography variant="subtitle1" fontWeight="bold">
                                    {supplier.name}
                                  </Typography>
                                  {supplier.company_name && (
                                    <Typography variant="body2" color="text.secondary">
                                      {supplier.company_name}
                                    </Typography>
                                  )}
                                </Box>
                              }
                              secondary={
                                <Box sx={{ mt: 1 }}>
                                  <Grid container spacing={2}>
                                    <Grid item xs={12} sm={6}>
                                      {supplier.contact_person && (
                                        <Box display="flex" alignItems="center" gap={0.5}>
                                          <AccountIcon sx={{ fontSize: 14 }} />
                                          <Typography variant="caption">
                                            {supplier.contact_person}
                                          </Typography>
                                        </Box>
                                      )}
                                      {supplier.phone && (
                                        <Box display="flex" alignItems="center" gap={0.5}>
                                          <PhoneIcon sx={{ fontSize: 14 }} />
                                          <Typography variant="caption">
                                            {supplier.phone}
                                          </Typography>
                                        </Box>
                                      )}
                                    </Grid>
                                    <Grid item xs={12} sm={6}>
                                      {supplier.email && (
                                        <Box display="flex" alignItems="center" gap={0.5}>
                                          <EmailIcon sx={{ fontSize: 14 }} />
                                          <Typography variant="caption">
                                            {supplier.email}
                                          </Typography>
                                        </Box>
                                      )}
                                      <Box display="flex" alignItems="center" gap={0.5}>
                                        <RatingIcon sx={{ fontSize: 14 }} />
                                        <Typography variant="caption">
                                          Rating: {supplier.performance_rating?.toFixed(1) || 'N/A'}
                                        </Typography>
                                      </Box>
                                    </Grid>
                                  </Grid>
                                  <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                                    <Chip 
                                      size="small" 
                                      label={`${supplierProducts.length} sản phẩm`}
                                      color="primary"
                                      variant="outlined"
                                    />
                                    <Chip 
                                      size="small" 
                                      label={supplier.payment_terms || 'NET 30'}
                                      color="default"
                                      variant="outlined"
                                    />
                                    <Chip 
                                      size="small" 
                                      label={`${supplier.average_delivery_days || 15} ngày`}
                                      color="success"
                                      variant="outlined"
                                    />
                                  </Box>
                                </Box>
                              }
                            />
                            <ListItemIcon>
                              {isExpanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                            </ListItemIcon>
                          </ListItem>
                          
                          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                            <Card variant="outlined" sx={{ ml: 2, mb: 1 }}>
                              <CardContent sx={{ py: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                  Sản phẩm từ nhà cung cấp này ({supplierProducts.length}):
                                </Typography>
                                {supplierProducts.length > 0 ? (
                                  <Grid container spacing={1}>
                                    {supplierProducts.slice(0, 6).map((product) => (
                                      <Grid item xs={12} sm={6} md={4} key={product.id}>
                                        <Card 
                                          variant="outlined" 
                                          sx={{ p: 1, cursor: 'pointer' }}
                                          onClick={() => handleProductView(product)}
                                        >
                                          <Typography variant="caption" fontWeight="bold">
                                            {product.name}
                                          </Typography>
                                          <Typography variant="caption" display="block" color="text.secondary">
                                            SKU: {product.sku}
                                          </Typography>
                                          <Box display="flex" justifyContent="space-between" alignItems="center" mt={0.5}>
                                            <Typography variant="caption">
                                              {getStockIcon(product.stock_level, product.minimum_stock)} {product.stock_level}
                                            </Typography>
                                            <Typography variant="caption" fontWeight="bold">
                                              {formatPrice(product.selling_price || 0)}
                                            </Typography>
                                          </Box>
                                        </Card>
                                      </Grid>
                                    ))}
                                    {supplierProducts.length > 6 && (
                                      <Grid item xs={12}>
                                        <Typography variant="caption" color="text.secondary">
                                          ... và {supplierProducts.length - 6} sản phẩm khác
                                        </Typography>
                                      </Grid>
                                    )}
                                  </Grid>
                                ) : (
                                  <Typography variant="body2" color="text.secondary" style={{ fontStyle: 'italic' }}>
                                    Chưa có sản phẩm nào từ nhà cung cấp này
                                  </Typography>
                                )}
                              </CardContent>
                            </Card>
                          </Collapse>
                        </React.Fragment>
                      );
                    })}
                    
                    {filteredSuppliers.length === 0 && supplierSearch && (
                      <ListItem>
                        <ListItemText 
                          primary="Không tìm thấy nhà cung cấp nào"
                          secondary="Thử từ khóa khác hoặc kiểm tra chính tả"
                        />
                      </ListItem>
                    )}
                  </List>
                </Box>
              </Grid>
            )}
            
            {/* Product Lookup */}
            {quickLookupMode === 'product' && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  placeholder="Tìm kiếm sản phẩm theo tên, SKU hoặc danh mục..."
                  value={productSearch}
                  onChange={(e) => setProductSearch(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon />
                      </InputAdornment>
                    )
                  }}
                  sx={{ mb: 2 }}
                />
                
                <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Sản phẩm</TableCell>
                        <TableCell>Nhà cung cấp</TableCell>
                        <TableCell>Giá & Lợi nhuận</TableCell>
                        <TableCell>Tồn kho</TableCell>
                        <TableCell align="center">Thao tác</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {filteredProducts.slice(0, 15).map((product) => {
                        const primarySupplier = suppliers.find(s => s.id === product.primary_supplier_id);
                        return (
                          <TableRow key={product.id} hover>
                            <TableCell>
                              <Typography variant="body2" fontWeight="bold">
                                {product.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                SKU: {product.sku} • {product.category}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {primarySupplier?.name || 'Không có'}
                              </Typography>
                              {primarySupplier && (
                                <Typography variant="caption" color="text.secondary">
                                  ⭐ {primarySupplier.performance_rating?.toFixed(1) || 'N/A'}
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" fontWeight="bold">
                                {formatPrice(product.selling_price || 0)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                Vốn: {formatPrice(product.cost_price || 0)}
                              </Typography>
                              <Typography variant="caption" color="success.main" display="block">
                                Lãi: {calculateProfitMargin(product.selling_price, product.cost_price)}%
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Box display="flex" alignItems="center" gap={0.5}>
                                <span>{getStockIcon(product.stock_level, product.minimum_stock)}</span>
                                <Typography 
                                  variant="body2"
                                  color={getStockLevelColor(product.stock_level, product.minimum_stock) + '.main'}
                                >
                                  {product.stock_level}
                                </Typography>
                              </Box>
                              <Typography variant="caption" color="text.secondary">
                                Min: {product.minimum_stock}
                              </Typography>
                            </TableCell>
                            <TableCell align="center">
                              <Tooltip title="Xem chi tiết">
                                <IconButton 
                                  size="small" 
                                  onClick={() => handleProductView(product)}
                                >
                                  <ViewIcon />
                                </IconButton>
                              </Tooltip>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                      
                      {filteredProducts.length === 0 && productSearch && (
                        <TableRow>
                          <TableCell colSpan={5} align="center">
                            <Typography variant="body2" color="text.secondary" style={{ fontStyle: 'italic' }}>
                              Không tìm thấy sản phẩm nào với từ khóa "{productSearch}"
                            </Typography>
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Grid>
            )}
          </Grid>
        </CardContent>
      </Card>

      {/* Product Detail Dialog */}
      <Dialog open={openProductDialog} onClose={() => setOpenProductDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Chi tiết sản phẩm - {selectedProduct?.name}
        </DialogTitle>
        <DialogContent>
          {selectedProduct && (
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Thông tin cơ bản</Typography>
                    <Typography><strong>SKU:</strong> {selectedProduct.sku}</Typography>
                    <Typography><strong>Tên:</strong> {selectedProduct.name}</Typography>
                    <Typography><strong>Danh mục:</strong> {selectedProduct.category}</Typography>
                    <Typography><strong>Mô tả:</strong> {selectedProduct.description || 'Không có'}</Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Giá và tồn kho</Typography>
                    <Typography><strong>Giá bán:</strong> {formatPrice(selectedProduct.selling_price || 0)}</Typography>
                    <Typography><strong>Giá vốn:</strong> {formatPrice(selectedProduct.cost_price || 0)}</Typography>
                    <Typography><strong>Lợi nhuận:</strong> {calculateProfitMargin(selectedProduct.selling_price, selectedProduct.cost_price)}%</Typography>
                    <Typography>
                      <strong>Tồn kho:</strong> {getStockIcon(selectedProduct.stock_level, selectedProduct.minimum_stock)} {selectedProduct.stock_level} 
                      (Min: {selectedProduct.minimum_stock})
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Nhà cung cấp</Typography>
                    {(() => {
                      const primarySupplier = suppliers.find(s => s.id === selectedProduct.primary_supplier_id);
                      const backupSupplier = suppliers.find(s => s.id === selectedProduct.backup_supplier_id);
                      return (
                        <Grid container spacing={2}>
                          {primarySupplier && (
                            <Grid item xs={12} md={6}>
                              <Typography variant="subtitle2">Nhà cung cấp chính:</Typography>
                              <Typography>{primarySupplier.name}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                📞 {primarySupplier.phone} • ✉️ {primarySupplier.email}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                ⭐ {primarySupplier.performance_rating?.toFixed(1) || 'N/A'} • 
                                🚚 {primarySupplier.average_delivery_days || 15} ngày
                              </Typography>
                            </Grid>
                          )}
                          {backupSupplier && (
                            <Grid item xs={12} md={6}>
                              <Typography variant="subtitle2">Nhà cung cấp dự phòng:</Typography>
                              <Typography>{backupSupplier.name}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                📞 {backupSupplier.phone} • ✉️ {backupSupplier.email}
                              </Typography>
                              <Typography variant="body2" color="text.secondary">
                                ⭐ {backupSupplier.performance_rating?.toFixed(1) || 'N/A'} • 
                                🚚 {backupSupplier.average_delivery_days || 15} ngày
                              </Typography>
                            </Grid>
                          )}
                        </Grid>
                      );
                    })()}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenProductDialog(false)}>Đóng</Button>
          <Button variant="contained" onClick={() => {
            // Navigate to product management or edit
            window.location.href = `/products/${selectedProduct?.id}/edit`;
          }}>
            Chỉnh sửa sản phẩm
          </Button>
        </DialogActions>
      </Dialog>

      {/* Quick Tips Alert */}
      <Alert 
        severity="info" 
        sx={{ 
          mb: 2,
          bgcolor: '#e3f2fd',
          '& .MuiAlert-icon': { color: '#1976d2' }
        }}
      >
        💡 <strong>Mẹo tăng hiệu suất:</strong> Sử dụng Ctrl+N để tạo listing nhanh, 
        "Tra cứu nhanh" để tìm thông tin nhà cung cấp và sản phẩm khi fulfillment đơn hàng, 
        hoặc nhấn vào "Tối ưu hàng loạt" để xử lý nhiều items cùng lúc. 
        Mục tiêu hôm nay: hoàn thành {todayStats.targetListings} listings!
      </Alert>
    </MainLayout>
  );
};

export default EmployeeWorkspace;