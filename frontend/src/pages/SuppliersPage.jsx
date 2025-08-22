import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Tooltip,
  Alert,
  Snackbar,
  LinearProgress,
  Rating,
  Fab,
  Menu,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  Business as BusinessIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Language as WebsiteIcon,
  TrendingUp as PerformanceIcon,
  Assignment as OrdersIcon,
  Speed as ReliabilityIcon
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';

const SuppliersPage = () => {
  // State management
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [businessTypeFilter, setBusinessTypeFilter] = useState('');
  const [countryFilter, setCountryFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalSuppliers, setTotalSuppliers] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState(null);
  const [formData, setFormData] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedSupplier, setSelectedSupplier] = useState(null);

  // Constants
  const SUPPLIER_STATUSES = ['active', 'inactive', 'suspended', 'pending'];
  const BUSINESS_TYPES = ['manufacturer', 'distributor', 'wholesaler', 'dropshipper', 'retailer'];
  const DISCOUNT_TIERS = ['basic', 'standard', 'premium', 'vip'];

  // Load suppliers data
  const loadSuppliers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        size: '20',
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter }),
        ...(businessTypeFilter && { business_type: businessTypeFilter }),
        ...(countryFilter && { country: countryFilter })
      });

      const response = await fetch(`/api/v1/suppliers?${params}`);
      const data = await response.json();
      
      if (data.success !== false) {
        setSuppliers(data.items || []);
        setTotalSuppliers(data.total || 0);
      } else {
        throw new Error(data.message || 'Failed to load suppliers');
      }
    } catch (error) {
      console.error('Error loading suppliers:', error);
      showSnackbar('Lỗi khi tải danh sách nhà cung cấp', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load data on component mount and filter changes
  useEffect(() => {
    loadSuppliers();
  }, [page, searchTerm, statusFilter, businessTypeFilter, countryFilter]);

  // Utility functions
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const resetForm = () => {
    setFormData({
      name: '',
      company_name: '',
      contact_person: '',
      email: '',
      phone: '',
      address: '',
      country: '',
      website: '',
      business_type: 'manufacturer',
      payment_terms: 'NET 30',
      minimum_order_value: 0,
      currency: 'USD',
      discount_tier: 'standard',
      priority_level: 3,
      notes: '',
      tags: ''
    });
  };

  // Dialog handlers
  const handleOpenDialog = (supplier = null) => {
    setEditingSupplier(supplier);
    if (supplier) {
      setFormData({
        name: supplier.name || '',
        company_name: supplier.company_name || '',
        contact_person: supplier.contact_person || '',
        email: supplier.email || '',
        phone: supplier.phone || '',
        address: supplier.address || '',
        country: supplier.country || '',
        website: supplier.website || '',
        business_type: supplier.business_type || 'manufacturer',
        payment_terms: supplier.payment_terms || 'NET 30',
        minimum_order_value: supplier.minimum_order_value || 0,
        currency: supplier.currency || 'USD',
        discount_tier: supplier.discount_tier || 'standard',
        priority_level: supplier.priority_level || 3,
        notes: supplier.notes || '',
        tags: supplier.tags || ''
      });
    } else {
      resetForm();
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingSupplier(null);
    resetForm();
  };

  const handleFormChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleSaveSupplier = async () => {
    try {
      const url = editingSupplier 
        ? `/api/v1/suppliers/${editingSupplier.id}`
        : '/api/v1/suppliers';
      
      const method = editingSupplier ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await response.json();
      
      if (data.success) {
        showSnackbar(
          editingSupplier 
            ? 'Cập nhật nhà cung cấp thành công'
            : 'Thêm nhà cung cấp thành công'
        );
        handleCloseDialog();
        loadSuppliers();
      } else {
        throw new Error(data.message || 'Failed to save supplier');
      }
    } catch (error) {
      console.error('Error saving supplier:', error);
      showSnackbar('Lỗi khi lưu thông tin nhà cung cấp', 'error');
    }
  };

  // Menu handlers
  const handleMenuOpen = (event, supplier) => {
    setMenuAnchor(event.currentTarget);
    setSelectedSupplier(supplier);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedSupplier(null);
  };

  const handleDeleteSupplier = async () => {
    if (!selectedSupplier) return;

    try {
      const response = await fetch(`/api/v1/suppliers/${selectedSupplier.id}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        showSnackbar('Xóa nhà cung cấp thành công');
        loadSuppliers();
      } else {
        throw new Error(data.message || 'Failed to delete supplier');
      }
    } catch (error) {
      console.error('Error deleting supplier:', error);
      showSnackbar('Lỗi khi xóa nhà cung cấp', 'error');
    }
    handleMenuClose();
  };

  const handleUpdatePerformance = async () => {
    if (!selectedSupplier) return;

    try {
      const response = await fetch(`/api/v1/suppliers/${selectedSupplier.id}/update-performance`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        showSnackbar('Cập nhật hiệu suất thành công');
        loadSuppliers();
      } else {
        throw new Error(data.message || 'Failed to update performance');
      }
    } catch (error) {
      console.error('Error updating performance:', error);
      showSnackbar('Lỗi khi cập nhật hiệu suất', 'error');
    }
    handleMenuClose();
  };

  // Status color mapping
  const getStatusColor = (status) => {
    const colors = {
      active: 'success',
      inactive: 'default',
      suspended: 'error',
      pending: 'warning'
    };
    return colors[status] || 'default';
  };

  const getBusinessTypeIcon = (type) => {
    const icons = {
      manufacturer: <BusinessIcon />,
      distributor: <BusinessIcon />,
      wholesaler: <BusinessIcon />,
      dropshipper: <BusinessIcon />,
      retailer: <BusinessIcon />
    };
    return icons[type] || <BusinessIcon />;
  };

  return (
    <MainLayout>
      <Box p={3}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" fontWeight="bold">
            Quản Lý Nhà Cung Cấp
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white'
            }}
          >
            Thêm Nhà Cung Cấp
          </Button>
        </Box>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  placeholder="Tìm kiếm nhà cung cấp..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                  }}
                />
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Trạng thái</InputLabel>
                  <Select
                    value={statusFilter}
                    label="Trạng thái"
                    onChange={(e) => setStatusFilter(e.target.value)}
                  >
                    <MenuItem value="">Tất cả</MenuItem>
                    {SUPPLIER_STATUSES.map(status => (
                      <MenuItem key={status} value={status}>
                        {status === 'active' ? 'Hoạt động' :
                         status === 'inactive' ? 'Không hoạt động' :
                         status === 'suspended' ? 'Tạm dừng' : 'Chờ duyệt'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Loại hình</InputLabel>
                  <Select
                    value={businessTypeFilter}
                    label="Loại hình"
                    onChange={(e) => setBusinessTypeFilter(e.target.value)}
                  >
                    <MenuItem value="">Tất cả</MenuItem>
                    {BUSINESS_TYPES.map(type => (
                      <MenuItem key={type} value={type}>
                        {type === 'manufacturer' ? 'Nhà sản xuất' :
                         type === 'distributor' ? 'Nhà phân phối' :
                         type === 'wholesaler' ? 'Bán sỉ' :
                         type === 'dropshipper' ? 'Dropshipper' : 'Bán lẻ'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <TextField
                  fullWidth
                  placeholder="Quốc gia"
                  value={countryFilter}
                  onChange={(e) => setCountryFilter(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('');
                    setBusinessTypeFilter('');
                    setCountryFilter('');
                  }}
                >
                  Xóa bộ lọc
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Loading */}
        {loading && <LinearProgress sx={{ mb: 2 }} />}

        {/* Suppliers Table */}
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Nhà cung cấp</TableCell>
                  <TableCell>Thông tin liên hệ</TableCell>
                  <TableCell>Loại hình</TableCell>
                  <TableCell>Hiệu suất</TableCell>
                  <TableCell>Điều kiện kinh doanh</TableCell>
                  <TableCell>Trạng thái</TableCell>
                  <TableCell align="center">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {suppliers.map((supplier) => (
                  <TableRow key={supplier.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {supplier.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {supplier.company_name}
                        </Typography>
                        {supplier.website && (
                          <Box display="flex" alignItems="center" mt={0.5}>
                            <WebsiteIcon sx={{ fontSize: 14, mr: 0.5 }} />
                            <Typography variant="caption">
                              {supplier.website}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Box>
                        {supplier.contact_person && (
                          <Box display="flex" alignItems="center" mb={0.5}>
                            <PersonIcon sx={{ fontSize: 14, mr: 0.5 }} />
                            <Typography variant="body2">
                              {supplier.contact_person}
                            </Typography>
                          </Box>
                        )}
                        {supplier.email && (
                          <Box display="flex" alignItems="center" mb={0.5}>
                            <EmailIcon sx={{ fontSize: 14, mr: 0.5 }} />
                            <Typography variant="body2">
                              {supplier.email}
                            </Typography>
                          </Box>
                        )}
                        {supplier.phone && (
                          <Box display="flex" alignItems="center">
                            <PhoneIcon sx={{ fontSize: 14, mr: 0.5 }} />
                            <Typography variant="body2">
                              {supplier.phone}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {getBusinessTypeIcon(supplier.business_type)}
                        <Box ml={1}>
                          <Typography variant="body2">
                            {supplier.business_type === 'manufacturer' ? 'Nhà sản xuất' :
                             supplier.business_type === 'distributor' ? 'Nhà phân phối' :
                             supplier.business_type === 'wholesaler' ? 'Bán sỉ' :
                             supplier.business_type === 'dropshipper' ? 'Dropshipper' : 'Bán lẻ'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {supplier.country}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Box>
                        <Box display="flex" alignItems="center" mb={0.5}>
                          <PerformanceIcon sx={{ fontSize: 14, mr: 0.5 }} />
                          <Rating 
                            value={supplier.performance_rating || 0} 
                            precision={0.1}
                            size="small" 
                            readOnly 
                          />
                          <Typography variant="caption" ml={0.5}>
                            ({supplier.performance_rating?.toFixed(1) || '0.0'})
                          </Typography>
                        </Box>
                        <Box display="flex" alignItems="center" mb={0.5}>
                          <ReliabilityIcon sx={{ fontSize: 14, mr: 0.5 }} />
                          <Typography variant="body2">
                            {supplier.reliability_score || 0}%
                          </Typography>
                        </Box>
                        <Box display="flex" alignItems="center">
                          <OrdersIcon sx={{ fontSize: 14, mr: 0.5 }} />
                          <Typography variant="body2">
                            {supplier.total_orders || 0} đơn hàng
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Typography variant="body2">
                        {supplier.payment_terms}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Min: {supplier.minimum_order_value} {supplier.currency}
                      </Typography>
                      <Chip 
                        label={supplier.discount_tier?.toUpperCase() || 'STANDARD'} 
                        size="small"
                        color={supplier.discount_tier === 'premium' ? 'primary' : 'default'}
                      />
                    </TableCell>

                    <TableCell>
                      <Chip
                        label={
                          supplier.status === 'active' ? 'Hoạt động' :
                          supplier.status === 'inactive' ? 'Không hoạt động' :
                          supplier.status === 'suspended' ? 'Tạm dừng' : 'Chờ duyệt'
                        }
                        color={getStatusColor(supplier.status)}
                        size="small"
                      />
                    </TableCell>

                    <TableCell align="center">
                      <IconButton
                        onClick={(e) => handleMenuOpen(e, supplier)}
                        size="small"
                      >
                        <MoreVertIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>

        {/* Action Menu */}
        <Menu
          anchorEl={menuAnchor}
          open={Boolean(menuAnchor)}
          onClose={handleMenuClose}
        >
          <MenuItem onClick={() => {
            handleOpenDialog(selectedSupplier);
            handleMenuClose();
          }}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Chỉnh sửa</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleUpdatePerformance}>
            <ListItemIcon>
              <PerformanceIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Cập nhật hiệu suất</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleDeleteSupplier}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Xóa</ListItemText>
          </MenuItem>
        </Menu>

        {/* Add/Edit Dialog */}
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingSupplier ? 'Chỉnh sửa nhà cung cấp' : 'Thêm nhà cung cấp mới'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Tên nhà cung cấp *"
                  value={formData.name || ''}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Tên công ty"
                  value={formData.company_name || ''}
                  onChange={(e) => handleFormChange('company_name', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Người liên hệ"
                  value={formData.contact_person || ''}
                  onChange={(e) => handleFormChange('contact_person', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => handleFormChange('email', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Số điện thoại"
                  value={formData.phone || ''}
                  onChange={(e) => handleFormChange('phone', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Website"
                  value={formData.website || ''}
                  onChange={(e) => handleFormChange('website', e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Địa chỉ"
                  multiline
                  rows={2}
                  value={formData.address || ''}
                  onChange={(e) => handleFormChange('address', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Quốc gia"
                  value={formData.country || ''}
                  onChange={(e) => handleFormChange('country', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Loại hình kinh doanh</InputLabel>
                  <Select
                    value={formData.business_type || 'manufacturer'}
                    label="Loại hình kinh doanh"
                    onChange={(e) => handleFormChange('business_type', e.target.value)}
                  >
                    {BUSINESS_TYPES.map(type => (
                      <MenuItem key={type} value={type}>
                        {type === 'manufacturer' ? 'Nhà sản xuất' :
                         type === 'distributor' ? 'Nhà phân phối' :
                         type === 'wholesaler' ? 'Bán sỉ' :
                         type === 'dropshipper' ? 'Dropshipper' : 'Bán lẻ'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Điều kiện thanh toán"
                  value={formData.payment_terms || ''}
                  onChange={(e) => handleFormChange('payment_terms', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Đơn hàng tối thiểu"
                  type="number"
                  value={formData.minimum_order_value || 0}
                  onChange={(e) => handleFormChange('minimum_order_value', parseFloat(e.target.value) || 0)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Loại chiết khấu</InputLabel>
                  <Select
                    value={formData.discount_tier || 'standard'}
                    label="Loại chiết khấu"
                    onChange={(e) => handleFormChange('discount_tier', e.target.value)}
                  >
                    {DISCOUNT_TIERS.map(tier => (
                      <MenuItem key={tier} value={tier}>
                        {tier.toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Mức độ ưu tiên</InputLabel>
                  <Select
                    value={formData.priority_level || 3}
                    label="Mức độ ưu tiên"
                    onChange={(e) => handleFormChange('priority_level', parseInt(e.target.value))}
                  >
                    <MenuItem value={1}>Rất cao</MenuItem>
                    <MenuItem value={2}>Cao</MenuItem>
                    <MenuItem value={3}>Trung bình</MenuItem>
                    <MenuItem value={4}>Thấp</MenuItem>
                    <MenuItem value={5}>Rất thấp</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Ghi chú"
                  multiline
                  rows={3}
                  value={formData.notes || ''}
                  onChange={(e) => handleFormChange('notes', e.target.value)}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Hủy</Button>
            <Button 
              onClick={handleSaveSupplier} 
              variant="contained"
              disabled={!formData.name}
            >
              {editingSupplier ? 'Cập nhật' : 'Thêm mới'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
        >
          <Alert 
            onClose={handleCloseSnackbar} 
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Box>
    </MainLayout>
  );
};

export default SuppliersPage;