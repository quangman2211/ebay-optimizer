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
  Avatar,
  CircularProgress,
  LinearProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  MoreVert as MoreIcon,
  Download as ExportIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { Alert } from '@mui/material';
import MainLayout from '../components/Layout/MainLayout';
import { listingsAPI } from '../services/api';
import { SyncModal } from '../components/Modals';

const ListingsPage = () => {
  const [loading, setLoading] = useState(true);
  const [listings, setListings] = useState([]);
  const [filteredListings, setFilteredListings] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedListings, setSelectedListings] = useState([]);
  const [actionMenu, setActionMenu] = useState(null);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [error, setError] = useState(null);

  // Mock data removed - now using real API

  const statusOptions = [
    { value: '', label: 'Tất cả trạng thái' },
    { value: 'active', label: 'Đang bán' },
    { value: 'sold', label: 'Đã bán' },
    { value: 'paused', label: 'Tạm dừng' },
  ];

  const categoryOptions = [
    { value: '', label: 'Tất cả danh mục' },
    { value: 'Electronics', label: 'Điện tử' },
    { value: 'Computers', label: 'Máy tính' },
  ];

  useEffect(() => {
    const fetchListings = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('ListingsPage: Fetching listings from API...');
        const response = await listingsAPI.getAll({
          page: 1,
          size: 100,
          sort_by: 'created_at',
          sort_order: 'desc'
        });
        
        // Check if response has data (PaginatedResponse doesn't include success field)
        if (response.data && response.data.items) {
          const apiListings = response.data.items || [];
          console.log(`ListingsPage: Fetched ${apiListings.length} listings`);
          
          // Transform API data to component format
          const transformedListings = apiListings.map(listing => ({
            id: listing.id,
            title: listing.title || 'Unknown Product',
            image: listing.images && listing.images.length > 0 ? listing.images[0] : 'https://via.placeholder.com/80x80?text=No+Image',
            category: listing.category || 'Uncategorized',
            currentPrice: parseFloat(listing.price_ebay || 0),
            originalPrice: parseFloat(listing.price_cost || listing.price_ebay || 0),
            status: listing.status || 'active',
            watchers: parseInt(listing.watchers || 0),
            views: parseInt(listing.page_views || 0),
            sold: parseInt(listing.sold_quantity || 0),
            stock: parseInt(listing.quantity || 0),
            performance: parseInt(listing.performance_score || 0),
            listedDate: listing.created_at ? new Date(listing.created_at).toISOString().split('T')[0] : new Date().toISOString().split('T')[0],
            endDate: listing.end_date ? new Date(listing.end_date).toISOString().split('T')[0] : new Date(Date.now() + 30*24*60*60*1000).toISOString().split('T')[0],
          }));
          
          setListings(transformedListings);
          setFilteredListings(transformedListings);
        } else {
          // Handle case where API returns empty or invalid data
          console.warn('ListingsPage: API response missing items field:', response.data);
          throw new Error('Invalid API response format');
        }
      } catch (err) {
        console.error('ListingsPage: Error fetching listings:', err);
        setError(`Không thể tải dữ liệu listings: ${err.message}`);
        
        // Set empty state instead of mock data
        setListings([]);
        setFilteredListings([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchListings();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, categoryFilter, statusFilter, listings]); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for sync modal events
  useEffect(() => {
    const handleOpenSync = () => setSyncModalOpen(true);
    window.addEventListener('openSyncModal', handleOpenSync);
    return () => window.removeEventListener('openSyncModal', handleOpenSync);
  }, []);

  const applyFilters = () => {
    let filtered = [...listings];

    if (searchTerm) {
      filtered = filtered.filter(listing =>
        listing.title.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (categoryFilter) {
      filtered = filtered.filter(listing => listing.category === categoryFilter);
    }

    if (statusFilter) {
      filtered = filtered.filter(listing => listing.status === statusFilter);
    }

    setFilteredListings(filtered);
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      active: { color: 'success', label: 'Đang bán' },
      sold: { color: 'info', label: 'Đã bán' },
      paused: { color: 'warning', label: 'Tạm dừng' },
    };
    return statusMap[status] || { color: 'default', label: status };
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

  const getPerformanceColor = (performance) => {
    if (performance >= 80) return 'success';
    if (performance >= 60) return 'warning';
    return 'error';
  };

  const handleSelectListing = (listingId) => {
    setSelectedListings(prev =>
      prev.includes(listingId)
        ? prev.filter(id => id !== listingId)
        : [...prev, listingId]
    );
  };

  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelectedListings(filteredListings.map(listing => listing.id));
    } else {
      setSelectedListings([]);
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
      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
            Quản lý Listings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Theo dõi và quản lý tất cả sản phẩm bán trên eBay
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
          Tạo Listing Mới
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {listings.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tổng Listings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main', mb: 1 }}>
                {listings.filter(l => l.status === 'active').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Đang bán
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main', mb: 1 }}>
                {listings.reduce((sum, l) => sum + l.sold, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Đã bán
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main', mb: 1 }}>
                {Math.round(listings.reduce((sum, l) => sum + l.performance, 0) / listings.length)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Hiệu suất TB
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
              placeholder="Tìm kiếm sản phẩm..."
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
              <InputLabel>Danh mục</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="Danh mục"
              >
                {categoryOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

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

            <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
              <Button variant="outlined" startIcon={<ExportIcon />} size="small">
                Xuất Excel
              </Button>
              <Button variant="contained" startIcon={<EditIcon />} size="small">
                Bulk Edit
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Listings Table - 7 columns exact design */}
      <Card>
        <CardHeader
          title={
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Danh sách sản phẩm ({filteredListings.length})
            </Typography>
          }
        />
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell width="40">
                  <Checkbox
                    checked={selectedListings.length === filteredListings.length && filteredListings.length > 0}
                    indeterminate={selectedListings.length > 0 && selectedListings.length < filteredListings.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell sx={{ fontWeight: 600, width: 120 }}>Hình ảnh</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 300 }}>THÔNG TIN SẢN PHẨM</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 150 }}>GIÁ CẢ</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 120 }}>TRẠNG THÁI</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 180 }}>HIỆU SUẤT</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 80 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredListings.map((listing) => {
                const statusInfo = getStatusBadge(listing.status);
                const performanceColor = getPerformanceColor(listing.performance);
                
                return (
                  <TableRow key={listing.id} hover>
                    <TableCell>
                      <Checkbox
                        checked={selectedListings.includes(listing.id)}
                        onChange={() => handleSelectListing(listing.id)}
                      />
                    </TableCell>
                    
                    {/* Hình ảnh */}
                    <TableCell>
                      <Avatar
                        src={listing.image}
                        variant="rounded"
                        sx={{ width: 60, height: 60 }}
                      >
                        <i className="bi bi-image" />
                      </Avatar>
                    </TableCell>
                    
                    {/* THÔNG TIN SẢN PHẨM */}
                    <TableCell>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
                          {listing.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          <strong>Danh mục:</strong> {listing.category}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          <strong>Ngày đăng:</strong> {formatDate(listing.listedDate)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          <strong>Hết hạn:</strong> {formatDate(listing.endDate)}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* GIÁ CẢ */}
                    <TableCell>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {formatCurrency(listing.currentPrice)}
                        </Typography>
                        {listing.originalPrice !== listing.currentPrice && (
                          <Typography 
                            variant="caption" 
                            sx={{ textDecoration: 'line-through', color: 'text.secondary' }}
                          >
                            {formatCurrency(listing.originalPrice)}
                          </Typography>
                        )}
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                          Tồn kho: {listing.stock}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* TRẠNG THÁI */}
                    <TableCell>
                      <Chip
                        label={statusInfo.label}
                        color={statusInfo.color}
                        size="small"
                        sx={{ mb: 1 }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        👀 {listing.watchers} người theo dõi
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        📊 {listing.views} lượt xem
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ✅ {listing.sold} đã bán
                      </Typography>
                    </TableCell>
                    
                    {/* HIỆU SUẤT */}
                    <TableCell>
                      <Box sx={{ width: '100%' }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 500, mr: 1 }}>
                            {listing.performance}%
                          </Typography>
                          <Chip
                            label={performanceColor === 'success' ? 'Tốt' : performanceColor === 'warning' ? 'Trung bình' : 'Thấp'}
                            color={performanceColor}
                            size="small"
                          />
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={listing.performance}
                          color={performanceColor}
                          sx={{ height: 6, borderRadius: 3 }}
                        />
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                          Conversion rate: {(listing.sold / listing.views * 100).toFixed(1)}%
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
          {!loading && filteredListings.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || categoryFilter || statusFilter ? 'Không tìm thấy listing phù hợp' : 'Chưa có listing nào'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm || categoryFilter || statusFilter ? 'Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm' : 'Listing mới sẽ hiển thị tại đây khi có'}
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
        <MenuItem onClick={() => setActionMenu(null)}>
          <ViewIcon sx={{ mr: 1 }} />
          Xem trên eBay
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>
          <EditIcon sx={{ mr: 1 }} />
          Chỉnh sửa
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>
          Duplicate Listing
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)}>
          Tạm dừng
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)} sx={{ color: 'error.main' }}>
          Xóa listing
        </MenuItem>
      </Menu>

      {/* Sync Modal */}
      <SyncModal
        open={syncModalOpen}
        onClose={() => setSyncModalOpen(false)}
      />
    </MainLayout>
  );
};

export default ListingsPage;