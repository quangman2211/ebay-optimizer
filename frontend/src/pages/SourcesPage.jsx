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
} from '@mui/material';
import {
  Search as SearchIcon,
  MoreVert as MoreIcon,
  Download as ExportIcon,
  Add as AddIcon,
  Sync as SyncIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import { sourcesAPI } from '../services/api';
import { Alert } from '@mui/material';
import { SyncModal } from '../components/Modals';

const SourcesPage = () => {
  const [loading, setLoading] = useState(true);
  const [suppliers, setSuppliers] = useState([]);
  const [filteredSuppliers, setFilteredSuppliers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedSuppliers, setSelectedSuppliers] = useState([]);
  // showFilters removed - not used in current UI
  const [actionMenu, setActionMenu] = useState(null);
  const [syncModalOpen, setSyncModalOpen] = useState(false);
  const [error, setError] = useState(null);

  // Mock data removed - now using real API

  const statusOptions = [
    { value: '', label: 'Tất cả trạng thái' },
    { value: 'connected', label: 'Kết nối' },
    { value: 'disconnected', label: 'Mất kết nối' },
    { value: 'error', label: 'Lỗi' },
  ];

  // categoryOptions removed - not used in current UI

  useEffect(() => {
    const fetchSources = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('SourcesPage: Fetching sources from API...');
        const response = await sourcesAPI.getAll({
          page: 1,
          size: 100,
          sort_by: 'last_sync',
          sort_order: 'desc'
        });
        
        // Check if response has data (PaginatedResponse doesn't include success field)
        if (response.data && response.data.items) {
          const apiSources = response.data.items || [];
          console.log(`SourcesPage: Fetched ${apiSources.length} sources`);
          
          // Transform API data to component format
          const transformedSources = apiSources.map(source => ({
            id: source.id,
            name: source.name || 'Unknown Source',
            logo: '🛒', // Default emoji
            url: source.website_url || 'N/A',
            products: parseInt(source.total_products || 0),
            inStock: parseInt(source.active_products || 0),
            outOfStock: parseInt((source.total_products || 0) - (source.active_products || 0)),
            roi: parseFloat(source.average_roi || 0),
            status: source.status || 'disconnected',
            lastUpdate: source.last_sync ? new Date(source.last_sync).toLocaleString('vi-VN') : 'Chưa đồng bộ',
            category: source.supplier_type || 'Unknown',
            totalRevenue: parseFloat(source.total_revenue || 0),
            avgPrice: parseFloat(source.average_cost || 0),
          }));
          
          setSuppliers(transformedSources);
          setFilteredSuppliers(transformedSources);
        } else {
          // Handle case where API returns empty or invalid data
          console.warn('SourcesPage: API response missing items field:', response.data);
          throw new Error('Invalid API response format');
        }
      } catch (err) {
        console.error('SourcesPage: Error fetching sources:', err);
        setError(`Không thể tải dữ liệu nguồn hàng: ${err.message}`);
        
        // Set empty state instead of mock data
        setSuppliers([]);
        setFilteredSuppliers([]);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSources();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [searchTerm, statusFilter, suppliers]); // eslint-disable-line react-hooks/exhaustive-deps

  // Listen for sync modal events
  useEffect(() => {
    const handleOpenSync = () => setSyncModalOpen(true);
    window.addEventListener('openSyncModal', handleOpenSync);
    return () => window.removeEventListener('openSyncModal', handleOpenSync);
  }, []);

  const applyFilters = () => {
    let filtered = [...suppliers];

    if (searchTerm) {
      filtered = filtered.filter(supplier =>
        supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        supplier.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
        supplier.category.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (statusFilter) {
      filtered = filtered.filter(supplier => supplier.status === statusFilter);
    }

    setFilteredSuppliers(filtered);
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      connected: { color: 'success', label: 'Kết nối' },
      disconnected: { color: 'error', label: 'Mất kết nối' },
      error: { color: 'warning', label: 'Lỗi' },
    };
    return statusMap[status] || { color: 'default', label: status };
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDateTime = (dateTimeString) => {
    return new Date(dateTimeString).toLocaleString('vi-VN');
  };

  const getRoiColor = (roi) => {
    if (roi >= 25) return 'success';
    if (roi >= 15) return 'warning';
    return 'error';
  };

  const handleSelectSupplier = (supplierId) => {
    setSelectedSuppliers(prev =>
      prev.includes(supplierId)
        ? prev.filter(id => id !== supplierId)
        : [...prev, supplierId]
    );
  };

  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelectedSuppliers(filteredSuppliers.map(supplier => supplier.id));
    } else {
      setSelectedSuppliers([]);
    }
  };

  const handleSyncSupplier = (supplierId) => {
    // Simulate sync operation
    alert(`Đang đồng bộ dữ liệu nhà cung cấp ${supplierId}...`);
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
            Nguồn hàng
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Quản lý và theo dõi các nhà cung cấp sản phẩm
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
          Thêm Nhà Cung Cấp
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {suppliers.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tổng nhà cung cấp
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main', mb: 1 }}>
                {suppliers.filter(s => s.status === 'connected').length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Đang kết nối
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main', mb: 1 }}>
                {suppliers.reduce((sum, s) => sum + s.products, 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tổng sản phẩm
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main', mb: 1 }}>
                {Math.round(suppliers.reduce((sum, s) => sum + s.roi, 0) / suppliers.length)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ROI trung bình
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
              placeholder="Tìm kiếm nhà cung cấp..."
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

      {/* Suppliers Table - 8 columns exact design */}
      <Card>
        <CardHeader
          title={
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              Danh sách nhà cung cấp ({filteredSuppliers.length})
            </Typography>
          }
        />
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell width="40">
                  <Checkbox
                    checked={selectedSuppliers.length === filteredSuppliers.length && filteredSuppliers.length > 0}
                    indeterminate={selectedSuppliers.length > 0 && selectedSuppliers.length < filteredSuppliers.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell sx={{ fontWeight: 600, width: 80 }}>Icon</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 200 }}>TÊN NHÀ CUNG CẤP</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 120 }}>SẢN PHẨM</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 100 }}>ROI</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 120 }}>TRẠNG THÁI</TableCell>
                <TableCell sx={{ fontWeight: 600, minWidth: 150 }}>CẬP NHẬT CUỐI</TableCell>
                <TableCell sx={{ fontWeight: 600, width: 50 }}></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredSuppliers.map((supplier) => {
                const statusInfo = getStatusBadge(supplier.status);
                const roiColor = getRoiColor(supplier.roi);
                
                return (
                  <TableRow key={supplier.id} hover>
                    <TableCell>
                      <Checkbox
                        checked={selectedSuppliers.includes(supplier.id)}
                        onChange={() => handleSelectSupplier(supplier.id)}
                      />
                    </TableCell>
                    
                    {/* Icon */}
                    <TableCell>
                      <Avatar
                        sx={{ 
                          width: 40, 
                          height: 40, 
                          bgcolor: 'transparent',
                          fontSize: '1.5rem'
                        }}
                      >
                        {supplier.logo}
                      </Avatar>
                    </TableCell>
                    
                    {/* TÊN NHÀ CUNG CẤP */}
                    <TableCell>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                          {supplier.name}
                        </Typography>
                        <Typography variant="caption" color="primary" sx={{ display: 'block' }}>
                          {supplier.url}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {supplier.category}
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* SẢN PHẨM */}
                    <TableCell>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
                          {supplier.products} sản phẩm
                        </Typography>
                        <Typography variant="caption" color="success.main" sx={{ display: 'block' }}>
                          ✅ {supplier.inStock} còn hàng
                        </Typography>
                        <Typography variant="caption" color="error.main">
                          ❌ {supplier.outOfStock} hết hàng
                        </Typography>
                      </Box>
                    </TableCell>
                    
                    {/* ROI */}
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            fontWeight: 'bold',
                            color: roiColor === 'success' ? 'success.main' : 
                                   roiColor === 'warning' ? 'warning.main' : 'error.main'
                          }}
                        >
                          {supplier.roi}%
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        {formatCurrency(supplier.totalRevenue)}
                      </Typography>
                    </TableCell>
                    
                    {/* TRẠNG THÁI */}
                    <TableCell>
                      <Chip
                        label={statusInfo.label}
                        color={statusInfo.color}
                        size="small"
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
                        Avg: {formatCurrency(supplier.avgPrice)}
                      </Typography>
                    </TableCell>
                    
                    {/* CẬP NHẬT CUỐI */}
                    <TableCell>
                      <Typography variant="body2" sx={{ mb: 0.5 }}>
                        {formatDateTime(supplier.lastUpdate)}
                      </Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<SyncIcon />}
                        onClick={() => handleSyncSupplier(supplier.id)}
                        sx={{ textTransform: 'none' }}
                      >
                        Đồng bộ
                      </Button>
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
          {!loading && filteredSuppliers.length === 0 && (
            <Box sx={{ textAlign: 'center', py: 8 }}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                {searchTerm || statusFilter ? 'Không tìm thấy nhà cung cấp phù hợp' : 'Chưa có nhà cung cấp nào'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {searchTerm || statusFilter ? 'Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm' : 'Nhà cung cấp mới sẽ hiển thị tại đây khi có'}
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
          Kiểm tra kết nối
        </MenuItem>
        <MenuItem onClick={() => setActionMenu(null)} sx={{ color: 'error.main' }}>
          <DeleteIcon sx={{ mr: 1 }} />
          Xóa nhà cung cấp
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

export default SourcesPage;