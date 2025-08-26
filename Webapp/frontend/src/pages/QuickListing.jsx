import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Alert,
  LinearProgress,
  Autocomplete,
  Divider,
  Switch,
  FormControlLabel,
  Paper
} from '@mui/material';
import {
  Save as SaveIcon,
  Publish as PublishIcon,
  Speed as SpeedIcon,
  PhotoCamera as PhotoIcon,
  Link as LinkIcon,
  AutoAwesome as AIIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import { useAuth } from '../context/AuthContext';

const QuickListing = () => {
  const { user } = useAuth();
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    category: '',
    price: '',
    condition: 'new',
    description: '',
    keywords: [],
    account: 'seller123@email.com',
    sheetName: 'Listings'
  });
  
  // UI states
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationScore, setOptimizationScore] = useState(0);
  const [suggestions, setSuggestions] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [accounts, setAccounts] = useState([
    { email: 'seller123@email.com', active: true, sheetId: 'abc123' },
    { email: 'seller456@email.com', active: true, sheetId: 'def456' },
    { email: 'seller789@email.com', active: false, sheetId: 'ghi789' }
  ]);

  // Sample data
  const categories = [
    'Electronics',
    'Fashion',
    'Home & Garden', 
    'Sports & Outdoors',
    'Toys & Games',
    'Books & Movies'
  ];

  const conditionOptions = [
    { value: 'new', label: 'New' },
    { value: 'like_new', label: 'Like New' },
    { value: 'used', label: 'Used - Good' },
    { value: 'fair', label: 'Used - Fair' }
  ];

  const titleSuggestions = [
    'NEW Samsung Galaxy S24 Ultra 256GB Unlocked Smartphone',
    'Apple iPhone 15 Pro Max 128GB Blue Titanium Factory Unlocked',
    'Sony WH-1000XM5 Wireless Noise Canceling Headphones'
  ];

  const keywordSuggestions = [
    'smartphone', 'unlocked', 'new', 'factory sealed', 'warranty',
    'fast shipping', 'genuine', 'original', 'brand new'
  ];

  // Handle form changes
  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Trigger optimization score calculation
    calculateOptimizationScore({ ...formData, [field]: value });
  };

  const calculateOptimizationScore = (data) => {
    let score = 0;
    
    // Title optimization (40 points)
    if (data.title) {
      if (data.title.length >= 60 && data.title.length <= 80) score += 20;
      else if (data.title.length >= 40) score += 10;
      
      if (data.title.includes('NEW') || data.title.includes('Brand')) score += 10;
      if (data.title.match(/\b\d+GB\b/) || data.title.match(/\b\d+TB\b/)) score += 10;
    }
    
    // Category (10 points)
    if (data.category) score += 10;
    
    // Price (10 points) 
    if (data.price && data.price > 0) score += 10;
    
    // Description (20 points)
    if (data.description) {
      if (data.description.length >= 200) score += 15;
      else if (data.description.length >= 100) score += 10;
      
      if (data.description.includes('•') || data.description.includes('✓')) score += 5;
    }
    
    // Keywords (10 points)
    if (data.keywords.length >= 5) score += 10;
    else if (data.keywords.length >= 3) score += 5;
    
    // Condition (5 points)
    if (data.condition) score += 5;
    
    // Account selection (5 points)
    if (data.account) score += 5;
    
    setOptimizationScore(score);
  };

  const handleOptimizeTitle = async () => {
    setIsOptimizing(true);
    
    // Simulate AI optimization
    setTimeout(() => {
      const optimizedTitle = `NEW ${formData.category || 'Premium'} Item - High Quality - Fast Shipping - ${formData.title}`.substring(0, 80);
      setFormData(prev => ({ ...prev, title: optimizedTitle }));
      setIsOptimizing(false);
    }, 2000);
  };

  const handleGenerateDescription = () => {
    const template = `✨ PREMIUM QUALITY ${formData.category?.toUpperCase() || 'ITEM'} ✨

🔥 KEY FEATURES:
• Brand new condition
• Fast and secure shipping
• 100% authentic guaranteed  
• Professional packaging

📦 WHAT YOU GET:
• ${formData.title || 'Premium item'}
• Original packaging
• User manual (if applicable)
• Warranty information

⚡ WHY CHOOSE US:
✓ Same-day handling
✓ Trusted seller with 99.5% feedback
✓ Easy returns within 30 days
✓ Excellent customer service

💰 PRICE: $${formData.price || 'XX.XX'} - BEST VALUE!

Order now for fast delivery! 📦⚡`;

    setFormData(prev => ({ ...prev, description: template }));
  };

  const handleSaveDraft = () => {
    console.log('Saving draft:', formData);
    // Implementation would save to backend
  };

  const handlePublishNow = () => {
    console.log('Publishing listing:', formData);
    // Implementation would publish to eBay via backend
  };

  const getScoreColor = () => {
    if (optimizationScore >= 80) return '#4caf50';
    if (optimizationScore >= 60) return '#ff9800';
    return '#f44336';
  };

  return (
    <MainLayout>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <SpeedIcon sx={{ fontSize: 40, color: '#1976d2' }} />
        <Box>
          <Typography variant="h4" fontWeight="bold">
            ⚡ Quick Listing Creator
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Tạo listing eBay nhanh chóng với AI optimization
          </Typography>
        </Box>
      </Box>

      {/* Optimization Score Alert */}
      <Alert 
        severity={optimizationScore >= 80 ? 'success' : optimizationScore >= 60 ? 'warning' : 'error'}
        sx={{ mb: 3 }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
          <Typography variant="body1" fontWeight="bold">
            Optimization Score: {optimizationScore}/100
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={optimizationScore} 
            sx={{ 
              flexGrow: 1, 
              height: 8, 
              borderRadius: 4,
              backgroundColor: '#f0f0f0',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getScoreColor(),
                borderRadius: 4
              }
            }}
          />
          {optimizationScore >= 80 && <CheckIcon color="success" />}
        </Box>
      </Alert>

      <Grid container spacing={3}>
        {/* Main Form */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📝 Listing Information
              </Typography>
              
              {/* Title */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2" fontWeight="bold">Title *</Typography>
                  <Chip 
                    size="small" 
                    label={`${formData.title.length}/80`} 
                    color={formData.title.length > 80 ? 'error' : formData.title.length > 60 ? 'warning' : 'default'}
                  />
                </Box>
                <TextField
                  fullWidth
                  value={formData.title}
                  onChange={handleChange('title')}
                  placeholder="Nhập tiêu đề sản phẩm..."
                  multiline
                  rows={2}
                  InputProps={{
                    endAdornment: (
                      <IconButton onClick={handleOptimizeTitle} disabled={isOptimizing}>
                        {isOptimizing ? <RefreshIcon className="spin" /> : <AIIcon />}
                      </IconButton>
                    )
                  }}
                />
                <Autocomplete
                  freeSolo
                  multiple
                  options={titleSuggestions}
                  renderTags={() => null}
                  renderInput={() => null}
                  onChange={(event, newValue) => {
                    if (newValue.length > 0) {
                      setFormData(prev => ({ ...prev, title: newValue[newValue.length - 1] }));
                    }
                  }}
                />
              </Box>

              {/* Category & Price */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Category *</InputLabel>
                    <Select value={formData.category} onChange={handleChange('category')}>
                      {categories.map(cat => (
                        <MenuItem key={cat} value={cat}>{cat}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Price *"
                    type="number"
                    value={formData.price}
                    onChange={handleChange('price')}
                    InputProps={{
                      startAdornment: <Typography sx={{ mr: 1 }}>$</Typography>
                    }}
                  />
                </Grid>
              </Grid>

              {/* Condition */}
              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Condition</InputLabel>
                <Select value={formData.condition} onChange={handleChange('condition')}>
                  {conditionOptions.map(option => (
                    <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Description */}
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="body2" fontWeight="bold">Description</Typography>
                  <Button 
                    size="small" 
                    startIcon={<AIIcon />} 
                    onClick={handleGenerateDescription}
                  >
                    Generate Template
                  </Button>
                </Box>
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  value={formData.description}
                  onChange={handleChange('description')}
                  placeholder="Nhập mô tả sản phẩm hoặc click Generate Template..."
                />
                <Typography variant="caption" color="textSecondary">
                  {formData.description.length} characters
                </Typography>
              </Box>

              {/* Keywords */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="body2" fontWeight="bold" gutterBottom>
                  Keywords
                </Typography>
                <Autocomplete
                  multiple
                  freeSolo
                  options={keywordSuggestions}
                  value={formData.keywords}
                  onChange={(event, newValue) => {
                    setFormData(prev => ({ ...prev, keywords: newValue }));
                  }}
                  renderTags={(value, getTagProps) =>
                    value.map((option, index) => (
                      <Chip
                        variant="outlined"
                        label={option}
                        {...getTagProps({ index })}
                      />
                    ))
                  }
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      placeholder="Thêm keywords..."
                      helperText={`${formData.keywords.length} keywords added`}
                    />
                  )}
                />
              </Box>

              {/* Images Section */}
              <Paper variant="outlined" sx={{ p: 3, mb: 3, textAlign: 'center' }}>
                <PhotoIcon sx={{ fontSize: 48, color: '#bbb', mb: 2 }} />
                <Typography variant="h6" gutterBottom>Upload Images</Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Drag & drop images or click to browse
                </Typography>
                <Button variant="outlined" startIcon={<PhotoIcon />} sx={{ mr: 2 }}>
                  Browse Files
                </Button>
                <Button variant="outlined" startIcon={<LinkIcon />}>
                  Import from URL
                </Button>
              </Paper>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          {/* Account Selection */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🎯 Publishing Options
              </Typography>
              
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>eBay Account</InputLabel>
                <Select value={formData.account} onChange={handleChange('account')}>
                  {accounts.filter(acc => acc.active).map(account => (
                    <MenuItem key={account.email} value={account.email}>
                      {account.email}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="Sheet Name"
                value={formData.sheetName}
                onChange={handleChange('sheetName')}
                sx={{ mb: 3 }}
              />

              <Divider sx={{ my: 2 }} />

              {/* Action Buttons */}
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveDraft}
                  >
                    Save Draft
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    fullWidth
                    variant="contained"
                    startIcon={<PublishIcon />}
                    onClick={handlePublishNow}
                    disabled={optimizationScore < 50}
                  >
                    Publish Now
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Optimization Tips */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                💡 Optimization Tips
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Title Optimization:
                </Typography>
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: '0.875rem' }}>
                  <li>Sử dụng 60-80 ký tự</li>
                  <li>Bao gồm từ khóa quan trọng ở đầu</li>
                  <li>Thêm thông số kỹ thuật (GB, TB, size)</li>
                </ul>
              </Box>

              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Description Best Practices:
                </Typography>
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: '0.875rem' }}>
                  <li>Sử dụng bullet points</li>
                  <li>Highlight key features</li>
                  <li>Include warranty/return info</li>
                </ul>
              </Box>

              <Box>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Keyword Strategy:
                </Typography>
                <ul style={{ margin: 0, paddingLeft: 16, fontSize: '0.875rem' }}>
                  <li>5-8 keywords optimum</li>
                  <li>Mix broad + specific terms</li>
                  <li>Include brand/model names</li>
                </ul>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <style>
        {`
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          .spin {
            animation: spin 1s linear infinite;
          }
        `}
      </style>
    </MainLayout>
  );
};

export default QuickListing;