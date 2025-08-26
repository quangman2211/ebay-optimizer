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
  Alert,
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
import { accountsAPI } from '../services/api';

const AccountsPage = () => {
  const [loading, setLoading] = useState(true);
  const [accounts, setAccounts] = useState([]);
  const [filteredAccounts, setFilteredAccounts] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [actionMenu, setActionMenu] = useState(null);
  const [error, setError] = useState(null);

  // Fetch accounts from API
  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('AccountsPage: Fetching accounts from API...');
        const response = await accountsAPI.getAll({
          page: 1,
          size: 100,
          sort_by: 'last_activity',
          sort_order: 'desc'
        });
        
        if (response.data && response.data.items) {
          const apiAccounts = response.data.items || [];
          console.log(`AccountsPage: Fetched ${apiAccounts.length} accounts`);
          
          // Transform API data to component format
          const transformedAccounts = apiAccounts.map(account => ({
            id: account.id,
            username: account.username || `account_${account.id}`,
            email: account.email || 'N/A',
            country: account.country || 'Unknown',
            flag: getFlagFromCountry(account.country),
            status: account.status || 'active',
            healthScore: calculateHealthScore(account),
            totalListings: account.total_listings || 0,
            activeListings: account.active_listings || 0,
            totalSales: account.total_sales || 0,
            monthlyRevenue: parseFloat(account.monthly_revenue || 0),
            feedbackScore: parseFloat(account.feedback_score || 95.0),
            feedbackCount: account.feedback_count || 0,
            joinDate: account.created_at ? new Date(account.created_at).toISOString().split('T')[0] : '2020-01-01',
            lastActivity: account.last_activity ? new Date(account.last_activity).toLocaleString('vi-VN') : 'Không có hoạt động',
            limits: {
              monthlyListing: account.monthly_listing_limit || 500,
              monthlyRevenue: account.monthly_revenue_limit || 25000,
              usedListing: account.active_listings || 0,
              usedRevenue: parseFloat(account.monthly_revenue || 0)
            }
          }));
          
          setAccounts(transformedAccounts);
          setFilteredAccounts(transformedAccounts);
        } else {
          console.warn('AccountsPage: No accounts data in response');
          // Set fallback mock data if API returns empty
          const fallbackAccounts = [
            {
              id: 1,
              username: 'demo_seller',
              email: 'demo@ebay.com',
              country: 'US',
              flag: '🇺🇸',
              status: 'active',
              healthScore: 85,
              totalListings: 50,
              activeListings: 45,
              totalSales: 250,
              monthlyRevenue: 5000,
              feedbackScore: 98.5,
              feedbackCount: 500,
              joinDate: '2020-01-01',
              lastActivity: new Date().toLocaleString('vi-VN'),
              limits: {
                monthlyListing: 500,
                monthlyRevenue: 10000,
                usedListing: 45,
                usedRevenue: 5000
              }
            }
          ];
          setAccounts(fallbackAccounts);
          setFilteredAccounts(fallbackAccounts);
        }
        
      } catch (err) {
        console.error('AccountsPage: Error fetching accounts:', err);
        setError('Không thể tải danh sách tài khoản. Vui lòng thử lại.');
        
        // Set fallback data on error
        const fallbackAccounts = [
          {
            id: 1,
            username: 'demo_seller',
            email: 'demo@ebay.com',
            country: 'US',
            flag: '🇺🇸',
            status: 'active',
            healthScore: 85,
            totalListings: 50,
            activeListings: 45,
            totalSales: 250,
            monthlyRevenue: 5000,
            feedbackScore: 98.5,
            feedbackCount: 500,
            joinDate: '2020-01-01',
            lastActivity: new Date().toLocaleString('vi-VN'),
            limits: {
              monthlyListing: 500,
              monthlyRevenue: 10000,
              usedListing: 45,
              usedRevenue: 5000
            }
          }
        ];
        setAccounts(fallbackAccounts);
        setFilteredAccounts(fallbackAccounts);
      } finally {
        setLoading(false);
      }
    };

    fetchAccounts();
  }, []);

  // Helper functions
  const getFlagFromCountry = (country) => {
    const flags = {
      'US': '🇺🇸',
      'VN': '🇻🇳', 
      'UK': '🇬🇧',
      'CA': '🇨🇦',
      'AU': '🇦🇺',
      'DE': '🇩🇪'
    };
    return flags[country] || '🌍';
  };
  
  const calculateHealthScore = (account) => {
    let score = 70; // Base score
    if (account.status === 'active') score += 20;
    if ((account.feedback_score || 0) > 95) score += 10;
    if ((account.monthly_revenue || 0) > 1000) score += 5;
    return Math.min(score, 100);
  };

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

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'restricted': return 'warning';
      case 'suspended': return 'error';
      case 'under_review': return 'info';
      default: return 'default';
    }
  };

  const getStatusLabel = (status) => {
    const statusMap = {
      'active': 'Hoạt động',
      'restricted': 'Bị hạn chế',
      'suspended': 'Bị đình chỉ',
      'under_review': 'Đang xem xét'
    };
    return statusMap[status] || status;
  };

  const getHealthScoreColor = (score) => {
    if (score >= 90) return '#4caf50';
    if (score >= 70) return '#ff9800';
    return '#f44336';
  };

  const handleActionClick = (event, account) => {
    setActionMenu({ anchorEl: event.currentTarget, account });
  };

  const handleActionClose = () => {
    setActionMenu(null);
  };

  if (loading) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ ml: 2 }}>Đang tải tài khoản eBay...</Typography>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {error && (
        <Alert severity="warning" sx={{ mb: 3 }}>
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
      )}

      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4" fontWeight="bold">
          🏪 Quản lý Tài khoản eBay
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<SyncIcon />}>
            Đồng bộ
          </Button>
          <Button variant="contained" startIcon={<AddIcon />}>
            Thêm tài khoản
          </Button>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
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
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Trạng thái</InputLabel>
                <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                  {statusOptions.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControl fullWidth>
                <InputLabel>Quốc gia</InputLabel>
                <Select value={countryFilter} onChange={(e) => setCountryFilter(e.target.value)}>
                  {countryOptions.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<ExportIcon />}
              >
                Export
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Accounts Grid */}
      <Grid container spacing={3}>
        {filteredAccounts.map((account) => (
          <Grid item xs={12} md={6} lg={4} key={account.id}>
            <Card 
              sx={{ 
                height: '100%',
                border: `2px solid ${account.status === 'active' ? '#4caf50' : account.status === 'restricted' ? '#ff9800' : '#f44336'}`,
                '&:hover': { boxShadow: 3 }
              }}
            >
              <CardHeader
                avatar={
                  <Avatar sx={{ bgcolor: getHealthScoreColor(account.healthScore) }}>
                    {account.flag}
                  </Avatar>
                }
                title={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="h6" fontWeight="bold">
                      {account.username}
                    </Typography>
                    <Chip 
                      label={getStatusLabel(account.status)}
                      color={getStatusColor(account.status)}
                      size="small"
                    />
                  </Box>
                }
                subheader={account.email}
                action={
                  <IconButton onClick={(e) => handleActionClick(e, account)}>
                    <MoreIcon />
                  </IconButton>
                }
              />
              
              <CardContent>
                {/* Health Score */}
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2" color="textSecondary">
                      Health Score
                    </Typography>
                    <Typography variant="body2" fontWeight="bold" color={getHealthScoreColor(account.healthScore)}>
                      {account.healthScore}/100
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={account.healthScore} 
                    sx={{ 
                      height: 8, 
                      borderRadius: 4,
                      backgroundColor: '#f0f0f0',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getHealthScoreColor(account.healthScore),
                        borderRadius: 4
                      }
                    }}
                  />
                </Box>

                {/* Statistics */}
                <Grid container spacing={2} sx={{ mb: 2 }}>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Listings</Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {account.activeListings}/{account.totalListings}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Total Sales</Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {account.totalSales}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Monthly Revenue</Typography>
                    <Typography variant="h6" fontWeight="bold" color="primary.main">
                      ${account.monthlyRevenue.toLocaleString()}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption" color="textSecondary">Feedback</Typography>
                    <Typography variant="h6" fontWeight="bold">
                      {account.feedbackScore}% ({account.feedbackCount})
                    </Typography>
                  </Grid>
                </Grid>

                {/* Usage Limits */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Listing Limit: {account.limits.usedListing}/{account.limits.monthlyListing}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(account.limits.usedListing / account.limits.monthlyListing) * 100} 
                    sx={{ height: 4, borderRadius: 2, mb: 1 }}
                  />
                  <Typography variant="body2" color="textSecondary">
                    Revenue Limit: ${account.limits.usedRevenue.toLocaleString()}/${account.limits.monthlyRevenue.toLocaleString()}
                  </Typography>
                  <LinearProgress 
                    variant="determinate" 
                    value={(account.limits.usedRevenue / account.limits.monthlyRevenue) * 100} 
                    sx={{ height: 4, borderRadius: 2 }}
                  />
                </Box>

                {/* Last Activity */}
                <Typography variant="caption" color="textSecondary">
                  Last Activity: {account.lastActivity}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {filteredAccounts.length === 0 && !loading && (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <AccountIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h5" color="textSecondary" gutterBottom>
            Không tìm thấy tài khoản
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Thử thay đổi bộ lọc hoặc thêm tài khoản mới
          </Typography>
        </Box>
      )}

      {/* Action Menu */}
      <Menu
        anchorEl={actionMenu?.anchorEl}
        open={Boolean(actionMenu)}
        onClose={handleActionClose}
      >
        <MenuItem onClick={handleActionClose}>
          <ViewIcon sx={{ mr: 1 }} /> Xem chi tiết
        </MenuItem>
        <MenuItem onClick={handleActionClose}>
          <EditIcon sx={{ mr: 1 }} /> Chỉnh sửa
        </MenuItem>
        <MenuItem onClick={handleActionClose}>
          <SyncIcon sx={{ mr: 1 }} /> Đồng bộ
        </MenuItem>
        <MenuItem onClick={handleActionClose} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} /> Xóa
        </MenuItem>
      </Menu>
    </MainLayout>
  );
};

export default AccountsPage;