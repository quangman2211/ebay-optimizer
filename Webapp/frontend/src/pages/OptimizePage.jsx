import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  MenuItem,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  AutoFixHigh as OptimizeIcon,
  Visibility as EyeIcon,
  CompareArrows as CompareIcon,
  CheckCircle as ApplyIcon,
  Refresh as ResetIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../components/Layout/MainLayout';

const OptimizePage = () => {
  const navigate = useNavigate();
  const [selectedListing, setSelectedListing] = useState('');
  const [currentListing, setCurrentListing] = useState(null);
  const [optimizedListing, setOptimizedListing] = useState(null);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [showComparison, setShowComparison] = useState(false);

  const availableListings = [
    {
      id: 'LST001',
      title: 'iPhone 15 Pro Max 256GB Natural Titanium Unlocked',
      price: 1199.00,
      description: 'Brand new iPhone 15 Pro Max with 256GB storage.',
      score: 75
    },
    {
      id: 'LST002',
      title: 'Nike Air Max 90 White Black Size 10 Men\'s Sneakers',
      price: 120.00,
      description: 'Classic Nike Air Max 90 in white and black.',
      score: 68
    },
    {
      id: 'LST003',
      title: 'Samsung Galaxy S24 Ultra 512GB Phantom Black',
      price: 899.99,
      description: 'Latest Samsung Galaxy S24 Ultra with 512GB storage.',
      score: 82
    },
    {
      id: 'LST005',
      title: 'Apple Watch Series 9 45mm GPS Midnight Aluminum',
      price: 399.00,
      description: 'New Apple Watch Series 9 with advanced features.',
      score: 71
    },
    {
      id: 'LST008',
      title: 'AirPods Pro 2nd Generation with MagSafe Case',
      price: 249.00,
      description: 'Latest AirPods Pro with spatial audio.',
      score: 79
    }
  ];

  const handleListingSelect = (event) => {
    const listingId = event.target.value;
    setSelectedListing(listingId);
    
    if (listingId) {
      const listing = availableListings.find(l => l.id === listingId);
      setCurrentListing(listing);
    } else {
      setCurrentListing(null);
    }
    
    // Reset optimization results
    setOptimizedListing(null);
    setShowComparison(false);
  };

  const handleOptimize = async () => {
    if (!selectedListing) {
      alert('❗ Vui lòng chọn listing cần tối ưu');
      return;
    }

    setIsOptimizing(true);
    
    try {
      // Simulate AI optimization process
      await new Promise(resolve => setTimeout(resolve, 2500));
      
      const optimized = {
        ...currentListing,
        title: optimizeTitle(currentListing.title),
        description: optimizeDescription(currentListing.description),
        score: Math.min(95, currentListing.score + 15),
        improvements: {
          titleLength: currentListing.title.length - optimizeTitle(currentListing.title).length,
          keywordCount: 2,
          hotKeywordCount: 2,
          structuredDescription: true
        }
      };
      
      setOptimizedListing(optimized);
      setShowComparison(true);
    } catch (error) {
      alert('❌ Có lỗi xảy ra trong quá trình tối ưu');
    } finally {
      setIsOptimizing(false);
    }
  };

  const optimizeTitle = (title) => {
    if (title.includes('iPhone')) {
      return 'NEW iPhone 15 Pro Max 256GB Natural Titanium - FREE SHIPPING';
    }
    if (title.includes('Nike')) {
      return 'AUTHENTIC Nike Air Max 90 White Black Size 10 Men\'s - Brand New';
    }
    if (title.includes('Samsung')) {
      return 'NEW Samsung Galaxy S24 Ultra 512GB Phantom - Factory Unlocked';
    }
    if (title.includes('Apple Watch')) {
      return 'NEW Apple Watch Series 9 45mm GPS Midnight - Fast Shipping';
    }
    if (title.includes('AirPods')) {
      return 'NEW AirPods Pro 2nd Gen with MagSafe Case - Authentic';
    }
    return 'NEW ' + title + ' - Fast Shipping';
  };

  const optimizeDescription = (description) => {
    return `✅ ${description}

🚚 Fast & Free Shipping
📦 Brand New in Original Box  
🔒 100% Authentic Guarantee
💯 30-Day Return Policy
⭐ Top Rated Seller`;
  };

  const getScoreColor = (score) => {
    if (score >= 85) return 'success';
    if (score >= 70) return 'warning';
    return 'info';
  };

  const getScoreGradient = (score) => {
    if (score >= 85) return 'linear-gradient(135deg, #28a745, #20c997)';
    if (score >= 70) return 'linear-gradient(135deg, #ffc107, #fd7e14)';
    return 'linear-gradient(135deg, #17a2b8, #6f42c1)';
  };

  const handleApplyOptimization = () => {
    alert('🎉 Tối ưu đã được áp dụng thành công!\n\nListing của bạn đã được cập nhật với:\n• Tiêu đề tối ưu hơn\n• Mô tả có cấu trúc\n• Điểm chất lượng cao hơn');
    
    setTimeout(() => {
      navigate('/listings');
    }, 1500);
  };

  const handleReset = () => {
    setSelectedListing('');
    setCurrentListing(null);
    setOptimizedListing(null);
    setShowComparison(false);
  };

  return (
    <MainLayout>
      <Box sx={{ maxWidth: 900, mx: 'auto', mb: 4 }}>
        {/* Page Header */}
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'text.primary', mb: 4 }}>
          Tối ưu Listings
        </Typography>

        {/* Select Listing */}
        <Card sx={{ mb: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <SearchIcon sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Chọn Listing Để Tối Ưu
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
              <TextField
                select
                fullWidth
                label="Chọn listing cần tối ưu"
                value={selectedListing}
                onChange={handleListingSelect}
                sx={{
                  flex: 1,
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                  },
                }}
              >
                <MenuItem value="">
                  <Typography color="text.secondary">Chọn listing cần tối ưu...</Typography>
                </MenuItem>
                {availableListings.map((listing) => (
                  <MenuItem key={listing.id} value={listing.id}>
                    <Box>
                      <Typography>{listing.title}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        ID: {listing.id} • Điểm: {listing.score}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </TextField>
              
              <Button
                variant="contained"
                startIcon={isOptimizing ? <CircularProgress size={16} color="inherit" /> : <OptimizeIcon />}
                onClick={handleOptimize}
                disabled={!selectedListing || isOptimizing}
                sx={{
                  minWidth: 160,
                  height: 56,
                  borderRadius: 2,
                  textTransform: 'none',
                  background: 'linear-gradient(135deg, #28a745, #20c997)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #218838, #1ea88a)',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 4px 15px rgba(40, 167, 69, 0.4)',
                  },
                }}
              >
                {isOptimizing ? 'Đang tối ưu...' : 'Tối Ưu Ngay'}
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Current Listing Preview */}
        {currentListing && (
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <EyeIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Listing Hiện Tại
                </Typography>
              </Box>
              
              <Box
                sx={{
                  background: '#f8f9fa',
                  borderRadius: 2,
                  p: 3,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                      {currentListing.title}
                    </Typography>
                    <Typography variant="h6" sx={{ color: 'text.secondary', mb: 2 }}>
                      Giá: ${currentListing.price.toFixed(2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {currentListing.description}
                    </Typography>
                  </Box>
                  <Box sx={{ textAlign: 'center', minWidth: 100 }}>
                    <Box
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        background: getScoreGradient(currentListing.score),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '1.2rem',
                        mb: 2,
                      }}
                    >
                      {currentListing.score}
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Điểm hiện tại
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Optimization Results */}
        {optimizedListing && (
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <OptimizeIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Kết Quả Tối Ưu
                </Typography>
              </Box>
              
              <Box
                sx={{
                  background: 'linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%)',
                  borderLeft: '4px solid #28a745',
                  borderRadius: 2,
                  p: 3,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                      {optimizedListing.title}
                    </Typography>
                    <Typography variant="h6" sx={{ color: 'success.main', mb: 2 }}>
                      Giá: ${optimizedListing.price.toFixed(2)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ whiteSpace: 'pre-line', mb: 2 }}>
                      {optimizedListing.description}
                    </Typography>
                    <Chip 
                      label={`+${optimizedListing.score - currentListing.score} điểm cải thiện`} 
                      color="success" 
                      size="small"
                      sx={{ fontWeight: 500 }}
                    />
                  </Box>
                  <Box sx={{ textAlign: 'center', minWidth: 100 }}>
                    <Box
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: '50%',
                        background: getScoreGradient(optimizedListing.score),
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 700,
                        fontSize: '1.2rem',
                        mb: 2,
                      }}
                    >
                      {optimizedListing.score}
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      Điểm sau tối ưu
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        )}

        {/* Comparison Table */}
        {showComparison && (
          <Card sx={{ mb: 3 }}>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <CompareIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  So Sánh Chi Tiết
                </Typography>
              </Box>
              
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow sx={{ bgcolor: '#f8f9fa' }}>
                      <TableCell sx={{ fontWeight: 600 }}>Tiêu chí</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Trước</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Sau</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Cải thiện</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    <TableRow>
                      <TableCell><strong>Độ dài tiêu đề</strong></TableCell>
                      <TableCell>
                        <Typography color="error.main">{currentListing.title.length} ký tự</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography color="success.main">{optimizedListing.title.length} ký tự</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={`${currentListing.title.length - optimizedListing.title.length > 0 ? '-' : '+'}${Math.abs(currentListing.title.length - optimizedListing.title.length)} ký tự`}
                          color="success"
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Từ khóa chính</strong></TableCell>
                      <TableCell>3 từ khóa</TableCell>
                      <TableCell>5 từ khóa</TableCell>
                      <TableCell>
                        <Chip label="+2 từ khóa" color="success" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Từ khóa hot</strong></TableCell>
                      <TableCell>1 từ</TableCell>
                      <TableCell>3 từ</TableCell>
                      <TableCell>
                        <Chip label="+2 từ hot" color="success" size="small" />
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell><strong>Cấu trúc mô tả</strong></TableCell>
                      <TableCell>Text thường</TableCell>
                      <TableCell>Bullet points + emoji</TableCell>
                      <TableCell>
                        <Chip label="Có cấu trúc" color="success" size="small" />
                      </TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        )}

        {/* Action Buttons */}
        {showComparison && (
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<ResetIcon />}
                  onClick={handleReset}
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    px: 4,
                  }}
                >
                  Làm lại
                </Button>
                <Button
                  variant="contained"
                  startIcon={<ApplyIcon />}
                  onClick={handleApplyOptimization}
                  sx={{
                    borderRadius: 2,
                    textTransform: 'none',
                    px: 4,
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
                      transform: 'translateY(-2px)',
                    },
                  }}
                >
                  Áp dụng thay đổi
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}
      </Box>
    </MainLayout>
  );
};

export default OptimizePage;