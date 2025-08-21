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
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  IconButton,
  Avatar,
  CircularProgress,
  LinearProgress,
  Menu,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreIcon,
  Download as ExportIcon,
  Add as AddIcon,
  Sync as SyncIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  AccountBox as AccountIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';

const AccountsPage = () => {
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState([]);
  const [filteredAccounts, setFilteredAccounts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [actionMenu, setActionMenu] = useState(null);

  // Mock data based on Ebay-UI-New structure - cards design
  const mockAccounts = [
    {
      id: 1,
      username: 'seller_pro_2025',
      email: 'seller.pro@email.com',
      country: 'US',
      flag: '🇺🇸',
      status: 'active',
      healthScore: 92,
      totalListings: 147,
      activeListings: 132,
      totalSales: 1247,
      monthlyRevenue: 15420.50,
      feedbackScore: 99.2,
      feedbackCount: 2847,
      joinDate: '2018-03-15',
      lastActivity: '2025-08-20 14:30',
      limits: {
        monthlyListing: 500,
        monthlyRevenue: 25000,
        usedListing: 132,
        usedRevenue: 15420.50
      }
    },
    {
      id: 2,
      username: 'global_trader_vn',
      email: 'trader.vn@email.com',
      country: 'VN',
      flag: '🇻🇳',
      status: 'active',
      healthScore: 85,
      totalListings: 89,
      activeListings: 76,
      totalSales: 892,
      monthlyRevenue: 8750.25,
      feedbackScore: 98.7,
      feedbackCount: 1523,
      joinDate: '2019-07-22',
      lastActivity: '2025-08-20 13:15',
      limits: {
        monthlyListing: 250,
        monthlyRevenue: 15000,
        usedListing: 76,
        usedRevenue: 8750.25
      }
    },
    {
      id: 3,
      username: 'tech_seller_uk',
      email: 'tech.uk@email.com',
      country: 'UK',
      flag: '🇬🇧',
      status: 'restricted',
      healthScore: 68,
      totalListings: 45,
      activeListings: 23,
      totalSales: 234,
      monthlyRevenue: 3240.80,
      feedbackScore: 96.5,
      feedbackCount: 456,
      joinDate: '2020-11-08',
      lastActivity: '2025-08-19 16:45',
      limits: {
        monthlyListing: 100,
        monthlyRevenue: 5000,
        usedListing: 23,
        usedRevenue: 3240.80
      }
    },
    {
      id: 4,
      username: 'fashion_store_ca',
      email: 'fashion.ca@email.com',
      country: 'CA',
      flag: '🇨🇦',
      status: 'suspended',
      healthScore: 45,
      totalListings: 67,
      activeListings: 0,
      totalSales: 567,
      monthlyRevenue: 0,
      feedbackScore: 94.2,
      feedbackCount: 789,
      joinDate: '2019-05-12',
      lastActivity: '2025-08-15 09:20',
      limits: {
        monthlyListing: 200,
        monthlyRevenue: 10000,
        usedListing: 0,
        usedRevenue: 0
      }
    },
  ];

  const statusOptions = [
    { value: '', label: 'Tất cả trạng thái' },
    { value: 'active', label: 'Hoạt động' },
    { value: 'restricted', label: 'Bị hạn chế' },
    { value: 'suspended', label: 'Bị đình chỉ' },
    { value: 'under_review', label: 'Đang xem xét' },
  ];

  const countryOptions = [
    { value: '', label: 'Tất cả quốc gia' },
    { value: 'US', label: 'United States' },
    { value: 'VN', label: 'Vietnam' },
    { value: 'UK', label: 'United Kingdom' },
    { value: 'CA', label: 'Canada' },
  ];

  useEffect(() => {
    // Simulate data loading
    setTimeout(() => {
      setAccounts(mockAccounts);
      setFilteredAccounts(mockAccounts);
      setLoading(false);
    }, 1000);
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, statusFilter, countryFilter, accounts]);

  const applyFilters = () => {
    let filtered = [...accounts];

    if (searchTerm) {
      filtered = filtered.filter(account =>
        account.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        account.email.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter) {
      filtered = filtered.filter(account => account.status === statusFilter);
    }

    if (countryFilter) {
      filtered = filtered.filter(account => account.country === countryFilter);
    }

    setFilteredAccounts(filtered);
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      active: { color: 'success', label: 'Hoạt động' },
      restricted: { color: 'warning', label: 'Bị hạn chế' },
      suspended: { color: 'error', label: 'Bị đình chỉ' },
      under_review: { color: 'info', label: 'Đang xem xét' },
    };
    return statusMap[status] || { color: 'default', label: status };
  };

  const getHealthScoreColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('vi-VN');
  };

  const formatDateTime = (dateTimeString) => {
    return new Date(dateTimeString).toLocaleString('vi-VN');
  };

  const handleSyncAccount = (accountId) => {
    alert(`Đang đồng bộ tài khoản ${accountId}...`);
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
            Tài khoản eBay
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Quản lý và theo dõi các tài khoản eBay
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
            },
          }}
        >
          Thêm Tài Khoản
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {accounts.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tổng tài khoản
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main', mb: 1 }}>
                {accounts.filter(a => a.status === 'active').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Đang hoạt động
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main', mb: 1 }}>
                {accounts.reduce((sum, a) => sum + a.totalListings, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tổng listings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main', mb: 1 }}>
                {Math.round(accounts.reduce((sum, a) => sum + a.healthScore, 0) / accounts.length)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Health Score TB
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
              placeholder="Tìm kiếm tài khoản..."
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

            <FormControl size="small" sx={{ minWidth: 150 }}>
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

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Quốc gia</InputLabel>
              <Select
                value={countryFilter}
                onChange={(e) => setCountryFilter(e.target.value)}
                label="Quốc gia"
              >
                {countryOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              <Button variant="outlined" startIcon={<SyncIcon />} size="small">
                Đồng bộ tất cả
              </Button>
              <Button variant="outlined" startIcon={<ExportIcon />} size="small">
                Xuất Excel
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Account Cards Grid */}
      <Grid container spacing={3}>
        {filteredAccounts.map((account) => {
          const statusInfo = getStatusBadge(account.status);
          const healthColor = getHealthScoreColor(account.healthScore);
          const listingProgress = (account.limits.usedListing / account.limits.monthlyListing) * 100;
          const revenueProgress = (account.limits.usedRevenue / account.limits.monthlyRevenue) * 100;

          return (
            <Grid item xs={12} md={6} lg={4} key={account.id}>
              <Card 
                sx={{ 
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  '&:hover': {
                    boxShadow: 3,
                  }
                }}
              >
                {/* Card Header */}
                <CardHeader
                  avatar={
                    <Avatar sx={{ bgcolor: 'primary.main' }}>
                      <AccountIcon />
                    </Avatar>
                  }
                  action={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="h6" sx={{ mr: 1 }}>
                        {account.flag}
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={(e) => setActionMenu(e.currentTarget)}
                      >
                        <MoreIcon />
                      </IconButton>
                    </Box>
                  }
                  title={
                    <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                      {account.username}
                    </Typography>
                  }
                  subheader={
                    <Typography variant="body2" color="text.secondary">
                      {account.email}
                    </Typography>
                  }
                />

                <CardContent sx={{ flexGrow: 1, pt: 0 }}>
                  {/* Status and Health Score */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <Chip
                      label={statusInfo.label}
                      color={statusInfo.color}
                      size="small"
                    />
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        Health Score:
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontWeight: 'bold',
                          color: healthColor === 'success' ? 'success.main' : 
                                 healthColor === 'warning' ? 'warning.main' : 'error.main'
                        }}
                      >
                        {account.healthScore}%
                      </Typography>
                    </Box>
                  </Box>

                  {/* Performance Metrics */}
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Total Listings
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {account.totalListings}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Active Listings
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                        {account.activeListings}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Total Sales
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                        {account.totalSales}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="caption" color="text.secondary">
                        Monthly Revenue
                      </Typography>
                      <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                        {formatCurrency(account.monthlyRevenue)}
                      </Typography>
                    </Grid>
                  </Grid>

                  {/* Feedback Score */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Feedback:</strong> {account.feedbackScore}% ({account.feedbackCount} reviews)
                    </Typography>
                  </Box>

                  {/* Usage Limits */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                      Listing Limit
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={listingProgress}
                      color={listingProgress > 80 ? 'error' : listingProgress > 60 ? 'warning' : 'success'}
                      sx={{ height: 6, borderRadius: 3, mb: 0.5 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {account.limits.usedListing} / {account.limits.monthlyListing} listings
                    </Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ mb: 1, fontWeight: 500 }}>
                      Revenue Limit
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={revenueProgress}
                      color={revenueProgress > 80 ? 'error' : revenueProgress > 60 ? 'warning' : 'success'}
                      sx={{ height: 6, borderRadius: 3, mb: 0.5 }}
                    />
                    <Typography variant="caption" color="text.secondary">
                      {formatCurrency(account.limits.usedRevenue)} / {formatCurrency(account.limits.monthlyRevenue)}
                    </Typography>
                  </Box>

                  {/* Account Info */}
                  <Box sx={{ borderTop: '1px solid #e0e0e0', pt: 2 }}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                      <strong>Joined:</strong> {formatDate(account.joinDate)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      <strong>Last Activity:</strong> {formatDateTime(account.lastActivity)}
                    </Typography>
                  </Box>
                </CardContent>

                {/* Card Actions */}
                <Box sx={{ p: 2, pt: 0 }}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SyncIcon />}
                    onClick={() => handleSyncAccount(account.id)}
                    sx={{ textTransform: 'none' }}
                  >
                    Đồng bộ tài khoản
                  </Button>
                </Box>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenu}
        open={Boolean(actionMenu)}
        onClose={() => setActionMenu(null)}
      >
        <MenuItem onClick={() => setActionMenu(null)}>
          <ViewIcon sx={{ mr: 1 }} />
          Xem chi tiết
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>
          <EditIcon sx={{ mr: 1 }} />
          Chỉnh sửa
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>
          <SyncIcon sx={{ mr: 1 }} />
          Đồng bộ ngay
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>
          Kiểm tra health
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Xóa tài khoản
        </MenuItem>
      </Menu>
    </MainLayout>
  );
};

export default AccountsPage;