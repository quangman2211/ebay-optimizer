import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Card,
  CardContent,
  IconButton,
  Divider,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
} from '@mui/material';
import {
  Save as SaveIcon,
  Cancel as CancelIcon,
  AutoFixHigh as OptimizeIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import useStore from '../../utils/store';

const ListingEditor = ({ listing, onSave, onCancel }) => {
  const { updateListing, createListing, optimizeListing } = useStore();
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'general',
    price: '',
    quantity: '',
    keywords: [],
    item_specifics: {},
    status: 'draft',
  });

  const [optimizationResult, setOptimizationResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [keywordInput, setKeywordInput] = useState('');
  const [specificKey, setSpecificKey] = useState('');
  const [specificValue, setSpecificValue] = useState('');

  useEffect(() => {
    if (listing) {
      setFormData({
        ...listing,
        keywords: listing.keywords || [],
        item_specifics: listing.item_specifics || {},
      });
    }
  }, [listing]);

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value,
    });
  };

  const handleAddKeyword = () => {
    if (keywordInput && !formData.keywords.includes(keywordInput)) {
      setFormData({
        ...formData,
        keywords: [...formData.keywords, keywordInput],
      });
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((k) => k !== keyword),
    });
  };

  const handleAddSpecific = () => {
    if (specificKey && specificValue) {
      setFormData({
        ...formData,
        item_specifics: {
          ...formData.item_specifics,
          [specificKey]: specificValue,
        },
      });
      setSpecificKey('');
      setSpecificValue('');
    }
  };

  const handleRemoveSpecific = (key) => {
    const newSpecifics = { ...formData.item_specifics };
    delete newSpecifics[key];
    setFormData({
      ...formData,
      item_specifics: newSpecifics,
    });
  };

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const result = await optimizeListing({
        title: formData.title,
        description: formData.description,
        category: formData.category,
        keywords: formData.keywords,
        item_specifics: formData.item_specifics,
      });
      setOptimizationResult(result);
      setActiveTab(1); // Switch to optimization tab
    } catch (error) {
      console.error('Optimization failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApplyOptimization = () => {
    if (optimizationResult) {
      setFormData({
        ...formData,
        title: optimizationResult.optimized_title,
        description: optimizationResult.optimized_description || formData.description,
        keywords: optimizationResult.suggested_keywords,
        status: 'optimized',
      });
      setActiveTab(0); // Switch back to editor tab
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      if (listing?.id) {
        await updateListing(listing.id, formData);
      } else {
        await createListing(formData);
      }
      onSave();
    } catch (error) {
      console.error('Save failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5">
            {listing ? 'Edit Listing' : 'Create New Listing'}
          </Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<CancelIcon />}
              onClick={onCancel}
              sx={{ mr: 2 }}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={loading}
            >
              Save
            </Button>
          </Box>
        </Box>

        {loading && <LinearProgress sx={{ mb: 2 }} />}

        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 3 }}>
          <Tab label="Editor" />
          <Tab label="Optimization" />
          <Tab label="Preview" />
        </Tabs>

        {/* Editor Tab */}
        {activeTab === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Title"
                    value={formData.title}
                    onChange={handleChange('title')}
                    helperText={`${formData.title.length}/80 characters`}
                    error={formData.title.length > 80}
                  />
                </Grid>

                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={6}
                    label="Description"
                    value={formData.description}
                    onChange={handleChange('description')}
                    helperText={`${formData.description.length}/4000 characters`}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={formData.category}
                      label="Category"
                      onChange={handleChange('category')}
                    >
                      <MenuItem value="general">General</MenuItem>
                      <MenuItem value="electronics">Electronics</MenuItem>
                      <MenuItem value="clothing">Clothing</MenuItem>
                      <MenuItem value="collectibles">Collectibles</MenuItem>
                      <MenuItem value="home">Home</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Price"
                    type="number"
                    value={formData.price}
                    onChange={handleChange('price')}
                    InputProps={{
                      startAdornment: '$',
                    }}
                  />
                </Grid>

                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    label="Quantity"
                    type="number"
                    value={formData.quantity}
                    onChange={handleChange('quantity')}
                  />
                </Grid>

                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    color="secondary"
                    startIcon={<OptimizeIcon />}
                    onClick={handleOptimize}
                    disabled={!formData.title || loading}
                    fullWidth
                  >
                    Optimize Listing
                  </Button>
                </Grid>
              </Grid>
            </Grid>

            <Grid item xs={12} md={4}>
              {/* Keywords Section */}
              <Card sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Keywords
                  </Typography>
                  <Box display="flex" gap={1} mb={2}>
                    <TextField
                      size="small"
                      placeholder="Add keyword"
                      value={keywordInput}
                      onChange={(e) => setKeywordInput(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                    />
                    <Button variant="outlined" size="small" onClick={handleAddKeyword}>
                      Add
                    </Button>
                  </Box>
                  <Box display="flex" flexWrap="wrap" gap={1}>
                    {formData.keywords.map((keyword) => (
                      <Chip
                        key={keyword}
                        label={keyword}
                        onDelete={() => handleRemoveKeyword(keyword)}
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </CardContent>
              </Card>

              {/* Item Specifics Section */}
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Item Specifics
                  </Typography>
                  <Grid container spacing={1} mb={2}>
                    <Grid item xs={5}>
                      <TextField
                        size="small"
                        placeholder="Key"
                        value={specificKey}
                        onChange={(e) => setSpecificKey(e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={5}>
                      <TextField
                        size="small"
                        placeholder="Value"
                        value={specificValue}
                        onChange={(e) => setSpecificValue(e.target.value)}
                      />
                    </Grid>
                    <Grid item xs={2}>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={handleAddSpecific}
                        fullWidth
                      >
                        Add
                      </Button>
                    </Grid>
                  </Grid>
                  {Object.entries(formData.item_specifics).map(([key, value]) => (
                    <Box key={key} display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">
                        <strong>{key}:</strong> {value}
                      </Typography>
                      <IconButton size="small" onClick={() => handleRemoveSpecific(key)}>
                        <CancelIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  ))}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Optimization Tab */}
        {activeTab === 1 && (
          <Box>
            {optimizationResult ? (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Optimization complete! Review the suggestions below and apply them to your listing.
                  </Alert>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Original Title
                      </Typography>
                      <Typography variant="body1" paragraph>
                        {optimizationResult.original_title}
                      </Typography>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        Optimized Title
                      </Typography>
                      <Typography variant="body1" color="primary">
                        {optimizationResult.optimized_title}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Optimization Scores
                      </Typography>
                      <Box mb={2}>
                        <Typography variant="body2" gutterBottom>
                          Title Score: {optimizationResult.title_score.toFixed(1)}/100
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={optimizationResult.title_score}
                          color={getScoreColor(optimizationResult.title_score)}
                        />
                      </Box>
                      <Box mb={2}>
                        <Typography variant="body2" gutterBottom>
                          SEO Score: {optimizationResult.seo_score.toFixed(1)}/100
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={optimizationResult.seo_score}
                          color={getScoreColor(optimizationResult.seo_score)}
                        />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {optimizationResult.optimized_description && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Optimized Description
                        </Typography>
                        <TextField
                          fullWidth
                          multiline
                          rows={8}
                          value={optimizationResult.optimized_description}
                          InputProps={{
                            readOnly: true,
                          }}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Suggested Keywords
                      </Typography>
                      <Box display="flex" flexWrap="wrap" gap={1}>
                        {optimizationResult.suggested_keywords.map((keyword) => (
                          <Chip key={keyword} label={keyword} color="primary" />
                        ))}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>

                {optimizationResult.improvements.length > 0 && (
                  <Grid item xs={12}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Improvement Suggestions
                        </Typography>
                        {optimizationResult.improvements.map((improvement, index) => (
                          <Alert severity="info" sx={{ mb: 1 }} key={index}>
                            {improvement}
                          </Alert>
                        ))}
                      </CardContent>
                    </Card>
                  </Grid>
                )}

                <Grid item xs={12}>
                  <Box display="flex" justifyContent="center">
                    <Button
                      variant="contained"
                      color="primary"
                      size="large"
                      startIcon={<CheckIcon />}
                      onClick={handleApplyOptimization}
                    >
                      Apply Optimization
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            ) : (
              <Alert severity="info">
                Click "Optimize Listing" in the Editor tab to generate optimization suggestions.
              </Alert>
            )}
          </Box>
        )}

        {/* Preview Tab */}
        {activeTab === 2 && (
          <Box>
            <Card>
              <CardContent>
                <Typography variant="h5" gutterBottom>
                  {formData.title || 'Untitled Listing'}
                </Typography>
                <Divider sx={{ my: 2 }} />
                
                <Grid container spacing={2}>
                  <Grid item xs={12} md={8}>
                    <Typography variant="h6" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1" paragraph style={{ whiteSpace: 'pre-line' }}>
                      {formData.description || 'No description provided.'}
                    </Typography>
                  </Grid>
                  
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                      <Typography variant="h6" gutterBottom>
                        Details
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Category:</strong> {formData.category}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Price:</strong> ${formData.price || '0.00'}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Quantity:</strong> {formData.quantity || '0'}
                      </Typography>
                      <Typography variant="body2" gutterBottom>
                        <strong>Status:</strong> {formData.status}
                      </Typography>
                      
                      {Object.keys(formData.item_specifics).length > 0 && (
                        <>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="h6" gutterBottom>
                            Item Specifics
                          </Typography>
                          {Object.entries(formData.item_specifics).map(([key, value]) => (
                            <Typography key={key} variant="body2" gutterBottom>
                              <strong>{key}:</strong> {value}
                            </Typography>
                          ))}
                        </>
                      )}
                      
                      {formData.keywords.length > 0 && (
                        <>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="h6" gutterBottom>
                            Keywords
                          </Typography>
                          <Box display="flex" flexWrap="wrap" gap={0.5}>
                            {formData.keywords.map((keyword) => (
                              <Chip key={keyword} label={keyword} size="small" />
                            ))}
                          </Box>
                        </>
                      )}
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default ListingEditor;