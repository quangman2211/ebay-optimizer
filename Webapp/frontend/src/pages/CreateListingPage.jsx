import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  Button,
  Grid,
  MenuItem,
  Alert,
  Divider,
} from '@mui/material';
import {
  InfoOutlined as InfoIcon,
  Inventory2Outlined as BoxIcon,
  LocalShippingOutlined as TruckIcon,
  VisibilityOutlined as EyeIcon,
  SaveOutlined as SaveIcon,
  AddCircleOutlined as PlusIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../components/Layout/MainLayout';

const CreateListingPage = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [previewData, setPreviewData] = useState({});
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    price: '',
    category: '',
    condition: 'new',
    brand: '',
    model: '',
    color: '',
    ebayAccount: '',
    shipping: '',
    tags: '',
  });

  const categories = [
    { value: 'electronics', label: 'Electronics' },
    { value: 'clothing', label: 'Clothing & Accessories' },
    { value: 'home', label: 'Home & Garden' },
    { value: 'sports', label: 'Sports & Recreation' },
    { value: 'toys', label: 'Toys & Games' },
  ];

  const conditions = [
    { value: 'new', label: 'Mới' },
    { value: 'like-new', label: 'Như mới' },
    { value: 'used', label: 'Đã sử dụng' },
    { value: 'refurbished', label: 'Tân trang' },
  ];

  const ebayAccounts = [
    { value: 'Store_VN_01', label: 'Store_VN_01' },
    { value: 'Store_VN_02', label: 'Store_VN_02' },
    { value: 'Store_US_01', label: 'Store_US_01' },
  ];

  const handleInputChange = (field) => (event) => {
    const value = event.target.value;
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Update preview for title and price
    if (field === 'title' || field === 'price') {
      setPreviewData(prev => ({ ...prev, [field]: value }));
    }
  };

  const validateForm = () => {
    const errors = [];
    
    if (!formData.title.trim()) {
      errors.push('Vui lòng nhập tiêu đề sản phẩm');
    }
    
    if (!formData.price || parseFloat(formData.price) <= 0) {
      errors.push('Vui lòng nhập giá bán hợp lệ');
    }
    
    if (!formData.category) {
      errors.push('Vui lòng chọn danh mục');
    }
    
    if (!formData.ebayAccount) {
      errors.push('Vui lòng chọn tài khoản eBay');
    }
    
    return errors;
  };

  const handleSaveDraft = async () => {
    if (!formData.title.trim()) {
      alert('❗ Vui lòng nhập tiêu đề sản phẩm');
      return;
    }

    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      alert('✅ Đã lưu listing vào nháp!\n\nBạn có thể tiếp tục chỉnh sửa sau.');
    } catch (error) {
      alert('❌ Có lỗi xảy ra khi lưu nháp');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateListing = async () => {
    const errors = validateForm();
    
    if (errors.length > 0) {
      alert('❗ Vui lòng kiểm tra lại:\n\n' + errors.join('\n'));
      return;
    }

    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      alert('🎉 Tạo listing thành công!\n\nListing đã được thêm vào danh sách và sẵn sàng để bán.');
      
      // Navigate to listings page after success
      setTimeout(() => {
        navigate('/listings');
      }, 1000);
    } catch (error) {
      alert('❌ Có lỗi xảy ra khi tạo listing');
    } finally {
      setIsLoading(false);
    }
  };

  const formatPrice = (price) => {
    const numPrice = parseFloat(price);
    return isNaN(numPrice) ? '0.00' : numPrice.toFixed(2);
  };

  return (
    <MainLayout>
      <Box sx={{ maxWidth: 800, mx: 'auto', mb: 4 }}>
        {/* Page Header */}
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 4 }}>
          Tạo Listing Mới
        </Typography>

        {/* Basic Information */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <InfoIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Thông tin cơ bản
              </Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Tiêu đề sản phẩm *"
                  value={formData.title}
                  onChange={handleInputChange('title')}
                  placeholder="Nhập tiêu đề hấp dẫn cho sản phẩm..."
                  inputProps={{ maxLength: 80 }}
                  helperText={`${formData.title.length}/80 ký tự. Bao gồm từ khóa quan trọng ở đầu.`}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={5}
                  label="Mô tả sản phẩm"
                  value={formData.description}
                  onChange={handleInputChange('description')}
                  placeholder="Mô tả chi tiết về sản phẩm của bạn..."
                  helperText="Mô tả càng chi tiết càng tốt để thu hút khách hàng."
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Giá bán ($) *"
                  value={formData.price}
                  onChange={handleInputChange('price')}
                  placeholder="0.00"
                  inputProps={{ step: '0.01', min: '0' }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Danh mục *"
                  value={formData.category}
                  onChange={handleInputChange('category')}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                >
                  <MenuItem value="">
                    <Typography color="text.secondary">Chọn danh mục</Typography>
                  </MenuItem>
                  {categories.map((category) => (
                    <MenuItem key={category.value} value={category.value}>
                      {category.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Product Details */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <BoxIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Chi tiết sản phẩm
              </Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Tình trạng *"
                  value={formData.condition}
                  onChange={handleInputChange('condition')}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                >
                  {conditions.map((condition) => (
                    <MenuItem key={condition.value} value={condition.value}>
                      {condition.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Thương hiệu"
                  value={formData.brand}
                  onChange={handleInputChange('brand')}
                  placeholder="Tên thương hiệu"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Model/Phiên bản"
                  value={formData.model}
                  onChange={handleInputChange('model')}
                  placeholder="Model hoặc số phiên bản"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Màu sắc"
                  value={formData.color}
                  onChange={handleInputChange('color')}
                  placeholder="Màu sắc sản phẩm"
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Shipping & Account */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <TruckIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Vận chuyển & Tài khoản
              </Typography>
            </Box>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  select
                  label="Tài khoản eBay *"
                  value={formData.ebayAccount}
                  onChange={handleInputChange('ebayAccount')}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                >
                  <MenuItem value="">
                    <Typography color="text.secondary">Chọn tài khoản</Typography>
                  </MenuItem>
                  {ebayAccounts.map((account) => (
                    <MenuItem key={account.value} value={account.value}>
                      {account.label}
                    </MenuItem>
                  ))}
                </TextField>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Phí vận chuyển ($)"
                  value={formData.shipping}
                  onChange={handleInputChange('shipping')}
                  placeholder="0.00"
                  inputProps={{ step: '0.01', min: '0' }}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
              
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Tags/Từ khóa"
                  value={formData.tags}
                  onChange={handleInputChange('tags')}
                  placeholder="iPhone, smartphone, unlocked, apple..."
                  helperText="Phân cách bằng dấu phẩy. Giúp khách hàng dễ tìm thấy sản phẩm."
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      borderRadius: 2,
                    },
                  }}
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Preview Section */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <EyeIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Xem trước
              </Typography>
            </Box>
            
            <Box
              sx={{
                background: '#f8f9fa',
                border: '2px dashed #dee2e6',
                borderRadius: 2,
                p: 3,
                textAlign: previewData.title || previewData.price ? 'left' : 'center',
                color: 'text.secondary',
              }}
            >
              {previewData.title || previewData.price ? (
                <Box>
                  <Typography variant="h5" sx={{ fontWeight: 600, mb: 2, color: 'text.primary' }}>
                    {previewData.title || 'Tiêu đề sản phẩm'}
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 600, color: 'success.main', mb: 2 }}>
                    ${formatPrice(previewData.price || '0')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Preview sẽ được cập nhật khi bạn nhập thông tin
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <EyeIcon sx={{ fontSize: '3rem', color: '#ccc', mb: 2 }} />
                  <Typography variant="body1" sx={{ mb: 1 }}>
                    Xem trước listing sẽ hiển thị ở đây
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Điền thông tin bên trên để xem preview
                  </Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <Card>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<SaveIcon />}
                onClick={handleSaveDraft}
                disabled={isLoading}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 4,
                  py: 1.5,
                }}
              >
                Lưu nháp
              </Button>
              <Button
                variant="contained"
                startIcon={<PlusIcon />}
                onClick={handleCreateListing}
                disabled={isLoading}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 4,
                  py: 1.5,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)',
                  },
                }}
              >
                {isLoading ? 'Đang tạo...' : 'Tạo Listing'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </MainLayout>
  );
};

export default CreateListingPage;