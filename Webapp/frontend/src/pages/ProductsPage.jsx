import React, { useState, useEffect, useCallback } from 'react';
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
  Alert,
  Snackbar,
  LinearProgress,
  Rating,
  Menu,
  ListItemIcon,
  ListItemText,
  InputAdornment,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  MoreVert as MoreVertIcon,
  TrendingUp as ProfitIcon,
  MonetizationOn as PriceIcon,
  Business as SupplierIcon,
  Star as RatingIcon,
  Warning as LowStockIcon,
  CheckCircle as InStockIcon,
  Calculate as CalculatorIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';

const ProductsPage = () => {
  
  // State management
  const [products, setProducts] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');
  const [stockFilter, setStockFilter] = useState('');
  const [page] = useState(1);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [formData, setFormData] = useState({});
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [openPricingDialog, setOpenPricingDialog] = useState(false);
  const [pricingData, setPricingData] = useState(null);

  // Constants
  const PRODUCT_STATUSES = ['active', 'inactive', 'discontinued', 'out_of_stock'];
  const CATEGORIES = ['Electronics', 'Clothing', 'Home & Garden', 'Automotive', 'Books', 'Sports', 'Health', 'Beauty'];

  // Load products data
  const loadProducts = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        size: '20',
        ...(searchTerm && { search: searchTerm }),
        ...(statusFilter && { status: statusFilter }),
        ...(categoryFilter && { category: categoryFilter }),
        ...(supplierFilter && { supplier_id: supplierFilter }),
        ...(stockFilter && { stock_level: stockFilter })
      });

      const response = await fetch(`/api/v1/products?${params}`);
      const data = await response.json();
      
      if (data.success !== false) {
        setProducts(data.items || []);
      } else {
        throw new Error(data.message || 'Failed to load products');
      }
    } catch (error) {
      console.error('Error loading products:', error);
      showSnackbar('Lỗi khi tải danh sách sản phẩm', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load suppliers for dropdowns
  const loadSuppliers = async () => {
    try {
      const response = await fetch('/api/v1/suppliers?size=100&status=active');
      const data = await response.json();
      if (data.success !== false) {
        setSuppliers(data.items || []);
      }
    } catch (error) {
      console.error('Error loading suppliers:', error);
    }
  };

  // Load data on component mount and filter changes
  useEffect(() => {
    loadProducts();
  }, [page, searchTerm, statusFilter, categoryFilter, supplierFilter, stockFilter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    loadSuppliers();
  }, []);

  // Utility functions
  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  const resetForm = () => {
    setFormData({
      sku: '',
      name: '',
      description: '',
      category: CATEGORIES[0],
      cost_price: 0,
      selling_price: 0,
      stock_level: 0,
      minimum_stock: 5,
      maximum_stock: 100,
      weight: 0,
      dimensions: '',
      primary_supplier_id: '',
      backup_supplier_id: '',
      status: 'active'
    });
  };

  // Dialog handlers
  const handleOpenDialog = (product = null) => {
    setEditingProduct(product);
    if (product) {
      setFormData({
        sku: product.sku || '',
        name: product.name || '',
        description: product.description || '',
        category: product.category || CATEGORIES[0],
        cost_price: product.cost_price || 0,
        selling_price: product.selling_price || 0,
        stock_level: product.stock_level || 0,
        minimum_stock: product.minimum_stock || 5,
        maximum_stock: product.maximum_stock || 100,
        weight: product.weight || 0,
        dimensions: product.dimensions || '',
        primary_supplier_id: product.primary_supplier_id || '',
        backup_supplier_id: product.backup_supplier_id || '',
        status: product.status || 'active'
      });
    } else {
      resetForm();
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingProduct(null);
    resetForm();
  };

  const handleFormChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const handleSaveProduct = async () => {
    try {
      const url = editingProduct 
        ? `/api/v1/products/${editingProduct.id}`
        : '/api/v1/products';
      
      const method = editingProduct ? 'PUT' : 'POST';
      
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
          editingProduct 
            ? 'Cập nhật sản phẩm thành công'
            : 'Thêm sản phẩm thành công'
        );
        handleCloseDialog();
        loadProducts();
      } else {
        throw new Error(data.message || 'Failed to save product');
      }
    } catch (error) {
      console.error('Error saving product:', error);
      showSnackbar('Lỗi khi lưu thông tin sản phẩm', 'error');
    }
  };

  // Menu handlers
  const handleMenuOpen = (event, product) => {
    setMenuAnchor(event.currentTarget);
    setSelectedProduct(product);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedProduct(null);
  };

  const handleDeleteProduct = async () => {
    if (!selectedProduct) return;

    try {
      const response = await fetch(`/api/v1/products/${selectedProduct.id}`, {
        method: 'DELETE'
      });

      const data = await response.json();
      
      if (data.success) {
        showSnackbar('Xóa sản phẩm thành công');
        loadProducts();
      } else {
        throw new Error(data.message || 'Failed to delete product');
      }
    } catch (error) {
      console.error('Error deleting product:', error);
      showSnackbar('Lỗi khi xóa sản phẩm', 'error');
    }
    handleMenuClose();
  };

  const handlePriceOptimization = async () => {
    if (!selectedProduct) return;

    try {
      const response = await fetch(`/api/v1/pricing/optimize/${selectedProduct.id}`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        setPricingData(data.data);
        setOpenPricingDialog(true);
      } else {
        throw new Error(data.message || 'Failed to optimize pricing');
      }
    } catch (error) {
      console.error('Error optimizing pricing:', error);
      showSnackbar('Lỗi khi tối ưu giá', 'error');
    }
    handleMenuClose();
  };

  // Utility functions for display
  const getStatusColor = (status) => {
    const colors = {
      active: 'success',
      inactive: 'default',
      discontinued: 'error',
      out_of_stock: 'warning'
    };
    return colors[status] || 'default';
  };

  const getStockLevelColor = (stock, minStock) => {
    if (stock === 0) return 'error';
    if (stock <= minStock) return 'warning';
    return 'success';
  };

  const getStockIcon = (stock, minStock) => {
    if (stock === 0) return <LowStockIcon color="error" />;
    if (stock <= minStock) return <LowStockIcon color="warning" />;
    return <InStockIcon color="success" />;
  };

  const calculateProfitMargin = (sellingPrice, costPrice) => {
    if (!sellingPrice || !costPrice) return 0;
    return ((sellingPrice - costPrice) / sellingPrice * 100).toFixed(1);
  };

  const getSupplierName = (supplierId) => {
    const supplier = suppliers.find(s => s.id === supplierId);
    return supplier ? supplier.name : 'Không có';
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'USD',
    }).format(price);
  };

  return (
    <MainLayout>
      <Box p={3}>
        {/* Header */}
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h4" fontWeight="bold">
            Quản Lý Sản Phẩm
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
            Thêm Sản Phẩm
          </Button>
        </Box>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  placeholder="Tìm kiếm sản phẩm..."
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
                    {PRODUCT_STATUSES.map(status => (
                      <MenuItem key={status} value={status}>
                        {status === 'active' ? 'Hoạt động' :
                         status === 'inactive' ? 'Không hoạt động' :
                         status === 'discontinued' ? 'Ngừng sản xuất' : 'Hết hàng'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Danh mục</InputLabel>
                  <Select
                    value={categoryFilter}
                    label="Danh mục"
                    onChange={(e) => setCategoryFilter(e.target.value)}
                  >
                    <MenuItem value="">Tất cả</MenuItem>
                    {CATEGORIES.map(category => (
                      <MenuItem key={category} value={category}>
                        {category}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={2}>
                <FormControl fullWidth>
                  <InputLabel>Nhà cung cấp</InputLabel>
                  <Select
                    value={supplierFilter}
                    label="Nhà cung cấp"
                    onChange={(e) => setSupplierFilter(e.target.value)}
                  >
                    <MenuItem value="">Tất cả</MenuItem>
                    {suppliers.map(supplier => (
                      <MenuItem key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <Button
                  variant="outlined"
                  startIcon={<FilterIcon />}
                  onClick={() => {
                    setSearchTerm('');
                    setStatusFilter('');
                    setCategoryFilter('');
                    setSupplierFilter('');
                    setStockFilter('');
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

        {/* Products Table */}
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Sản phẩm</TableCell>
                  <TableCell>Nhà cung cấp</TableCell>
                  <TableCell>Giá & Lợi nhuận</TableCell>
                  <TableCell>Tồn kho</TableCell>
                  <TableCell>Hiệu suất</TableCell>
                  <TableCell>Trạng thái</TableCell>
                  <TableCell align="center">Thao tác</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id} hover>
                    <TableCell>
                      <Box>
                        <Typography variant="subtitle2" fontWeight="bold">
                          {product.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          SKU: {product.sku}
                        </Typography>
                        <Chip 
                          label={product.category} 
                          size="small" 
                          variant="outlined"
                          sx={{ mt: 0.5 }}
                        />
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Box>
                        <Box display="flex" alignItems="center" mb={0.5}>
                          <SupplierIcon sx={{ fontSize: 14, mr: 0.5 }} />
                          <Typography variant="body2">
                            {getSupplierName(product.primary_supplier_id)}
                          </Typography>
                        </Box>
                        {product.backup_supplier_id && (
                          <Typography variant="caption" color="text.secondary">
                            Dự phòng: {getSupplierName(product.backup_supplier_id)}
                          </Typography>
                        )}
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Box>
                        <Box display="flex" alignItems="center" mb={0.5}>
                          <PriceIcon sx={{ fontSize: 14, mr: 0.5, color: 'primary.main' }} />
                          <Typography variant="body2" fontWeight="bold">
                            {formatPrice(product.selling_price || 0)}
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          Giá vốn: {formatPrice(product.cost_price || 0)}
                        </Typography>
                        <Box display="flex" alignItems="center">
                          <ProfitIcon sx={{ fontSize: 14, mr: 0.5, color: 'success.main' }} />
                          <Typography variant="body2" color="success.main">
                            {calculateProfitMargin(product.selling_price, product.cost_price)}%
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Box display="flex" alignItems="center" mb={0.5}>
                        {getStockIcon(product.stock_level, product.minimum_stock)}
                        <Typography 
                          variant="body2" 
                          ml={0.5}
                          color={getStockLevelColor(product.stock_level, product.minimum_stock) + '.main'}
                        >
                          {product.stock_level} đơn vị
                        </Typography>
                      </Box>
                      <Typography variant="caption" color="text.secondary">
                        Tối thiểu: {product.minimum_stock}
                      </Typography>
                    </TableCell>

                    <TableCell>
                      <Box>
                        <Box display="flex" alignItems="center" mb={0.5}>
                          <RatingIcon sx={{ fontSize: 14, mr: 0.5 }} />
                          <Rating 
                            value={product.average_rating || 0} 
                            precision={0.1}
                            size="small" 
                            readOnly 
                          />
                          <Typography variant="caption" ml={0.5}>
                            ({product.average_rating?.toFixed(1) || '0.0'})
                          </Typography>
                        </Box>
                        <Typography variant="body2" color="text.secondary">
                          {product.total_sales || 0} đã bán
                        </Typography>
                      </Box>
                    </TableCell>

                    <TableCell>
                      <Chip
                        label={
                          product.status === 'active' ? 'Hoạt động' :
                          product.status === 'inactive' ? 'Không hoạt động' :
                          product.status === 'discontinued' ? 'Ngừng sản xuất' : 'Hết hàng'
                        }
                        color={getStatusColor(product.status)}
                        size="small"
                      />
                    </TableCell>

                    <TableCell align="center">
                      <IconButton
                        onClick={(e) => handleMenuOpen(e, product)}
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
            handleOpenDialog(selectedProduct);
            handleMenuClose();
          }}>
            <ListItemIcon>
              <EditIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Chỉnh sửa</ListItemText>
          </MenuItem>
          <MenuItem onClick={handlePriceOptimization}>
            <ListItemIcon>
              <CalculatorIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Tối ưu giá</ListItemText>
          </MenuItem>
          <MenuItem onClick={handleDeleteProduct}>
            <ListItemIcon>
              <DeleteIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText>Xóa</ListItemText>
          </MenuItem>
        </Menu>

        {/* Add/Edit Product Dialog */}
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingProduct ? 'Chỉnh sửa sản phẩm' : 'Thêm sản phẩm mới'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="SKU *"
                  value={formData.sku || ''}
                  onChange={(e) => handleFormChange('sku', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Tên sản phẩm *"
                  value={formData.name || ''}
                  onChange={(e) => handleFormChange('name', e.target.value)}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Mô tả"
                  multiline
                  rows={3}
                  value={formData.description || ''}
                  onChange={(e) => handleFormChange('description', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Danh mục</InputLabel>
                  <Select
                    value={formData.category || CATEGORIES[0]}
                    label="Danh mục"
                    onChange={(e) => handleFormChange('category', e.target.value)}
                  >
                    {CATEGORIES.map(category => (
                      <MenuItem key={category} value={category}>
                        {category}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Trạng thái</InputLabel>
                  <Select
                    value={formData.status || 'active'}
                    label="Trạng thái"
                    onChange={(e) => handleFormChange('status', e.target.value)}
                  >
                    {PRODUCT_STATUSES.map(status => (
                      <MenuItem key={status} value={status}>
                        {status === 'active' ? 'Hoạt động' :
                         status === 'inactive' ? 'Không hoạt động' :
                         status === 'discontinued' ? 'Ngừng sản xuất' : 'Hết hàng'}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Giá vốn"
                  type="number"
                  value={formData.cost_price || 0}
                  onChange={(e) => handleFormChange('cost_price', parseFloat(e.target.value) || 0)}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Giá bán"
                  type="number"
                  value={formData.selling_price || 0}
                  onChange={(e) => handleFormChange('selling_price', parseFloat(e.target.value) || 0)}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>
                  }}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Tồn kho hiện tại"
                  type="number"
                  value={formData.stock_level || 0}
                  onChange={(e) => handleFormChange('stock_level', parseInt(e.target.value) || 0)}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Tồn kho tối thiểu"
                  type="number"
                  value={formData.minimum_stock || 5}
                  onChange={(e) => handleFormChange('minimum_stock', parseInt(e.target.value) || 5)}
                />
              </Grid>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Tồn kho tối đa"
                  type="number"
                  value={formData.maximum_stock || 100}
                  onChange={(e) => handleFormChange('maximum_stock', parseInt(e.target.value) || 100)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Nhà cung cấp chính</InputLabel>
                  <Select
                    value={formData.primary_supplier_id || ''}
                    label="Nhà cung cấp chính"
                    onChange={(e) => handleFormChange('primary_supplier_id', e.target.value)}
                  >
                    <MenuItem value="">Chọn nhà cung cấp</MenuItem>
                    {suppliers.map(supplier => (
                      <MenuItem key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Nhà cung cấp dự phòng</InputLabel>
                  <Select
                    value={formData.backup_supplier_id || ''}
                    label="Nhà cung cấp dự phòng"
                    onChange={(e) => handleFormChange('backup_supplier_id', e.target.value)}
                  >
                    <MenuItem value="">Không có</MenuItem>
                    {suppliers.map(supplier => (
                      <MenuItem key={supplier.id} value={supplier.id}>
                        {supplier.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Trọng lượng (kg)"
                  type="number"
                  value={formData.weight || 0}
                  onChange={(e) => handleFormChange('weight', parseFloat(e.target.value) || 0)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Kích thước (L x W x H)"
                  value={formData.dimensions || ''}
                  onChange={(e) => handleFormChange('dimensions', e.target.value)}
                  placeholder="20 x 15 x 10 cm"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Hủy</Button>
            <Button 
              onClick={handleSaveProduct} 
              variant="contained"
              disabled={!formData.sku || !formData.name}
            >
              {editingProduct ? 'Cập nhật' : 'Thêm mới'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Pricing Optimization Dialog */}
        <Dialog open={openPricingDialog} onClose={() => setOpenPricingDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            Tối ưu giá bán - {selectedProduct?.name}
          </DialogTitle>
          <DialogContent>
            {pricingData && (
              <Box>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Thông tin hiện tại
                        </Typography>
                        <Typography>Giá hiện tại: {formatPrice(pricingData.current_price || 0)}</Typography>
                        <Typography>Giá vốn: {formatPrice(pricingData.cost_price)}</Typography>
                        <Typography>Lợi nhuận hiện tại: {calculateProfitMargin(pricingData.current_price, pricingData.cost_price)}%</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Card variant="outlined" sx={{ bgcolor: 'success.50' }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom color="success.main">
                          Giá đề xuất
                        </Typography>
                        <Typography fontWeight="bold">Giá mới: {formatPrice(pricingData.recommended_price)}</Typography>
                        <Typography>Lợi nhuận dự kiến: {pricingData.recommended_analysis?.margin}%</Typography>
                        <Typography>Tăng lợi nhuận: {formatPrice(pricingData.recommended_analysis?.profit)}</Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                <Accordion sx={{ mt: 2 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography variant="h6">Chi tiết phân tích</Typography>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      {pricingData.pricing_analysis && Object.entries(pricingData.pricing_analysis).map(([key, analysis]) => (
                        <Grid item xs={12} md={4} key={key}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="subtitle1" gutterBottom>
                                {key === 'cost_based' ? 'Dựa trên chi phí' :
                                 key === 'performance_based' ? 'Dựa trên hiệu suất' : 'Cạnh tranh'}
                              </Typography>
                              <Typography>Giá: {formatPrice(analysis.price)}</Typography>
                              <Typography>Lợi nhuận: {analysis.margin}%</Typography>
                              <Typography>Thu nhập: {formatPrice(analysis.profit)}</Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenPricingDialog(false)}>Đóng</Button>
            <Button 
              variant="contained" 
              onClick={async () => {
                try {
                  // Apply the recommended price
                  const response = await fetch(`/api/v1/products/${selectedProduct.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                      selling_price: pricingData.recommended_price
                    })
                  });
                  
                  if (response.ok) {
                    showSnackbar('Áp dụng giá mới thành công');
                    setOpenPricingDialog(false);
                    loadProducts();
                  }
                } catch (error) {
                  showSnackbar('Lỗi khi áp dụng giá mới', 'error');
                }
              }}
            >
              Áp dụng giá đề xuất
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

export default ProductsPage;