import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Avatar,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Checkbox,
  Tooltip,
  CircularProgress,
  LinearProgress,
  useTheme,
} from '@mui/material';
import {
  Add,
  Image,
  CheckCircle,
  Schedule,
  Edit,
  Visibility,
  Delete,
  Speed,
  AccountCircle,
  FilterList,
  Download,
  Upload,
  Refresh,
  PlayArrow,
  Stop,
} from '@mui/icons-material';
import { draftsAPI, accountsAPI, sourcesAPI, workflowAPI } from '../services/api';

const DraftsPage = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [drafts, setDrafts] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [imageStatusFilter, setImageStatusFilter] = useState('all');
  const [selectedDrafts, setSelectedDrafts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // Dialog states
  const [batchCreateDialog, setBatchCreateDialog] = useState(false);
  const [sourceProducts, setSourceProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [targetAccounts, setTargetAccounts] = useState([]);

  // Kanban columns
  const [kanbanColumns, setKanbanColumns] = useState({
    draft: [],
    editing: [],
    ready: [],
    listed: [],
  });

  const [viewMode, setViewMode] = useState('kanban'); // 'kanban' or 'list'

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    loadDrafts();
  }, [selectedAccount, statusFilter, imageStatusFilter, searchQuery]);

  const loadInitialData = async () => {
    try {
      const [accountsResponse, sourcesResponse] = await Promise.allSettled([
        accountsAPI.getAll(),
        sourcesAPI.getAll(),
      ]);

      if (accountsResponse.status === 'fulfilled') {
        setAccounts(accountsResponse.value.data.data || []);
      }

      if (sourcesResponse.status === 'fulfilled') {
        const sources = sourcesResponse.value.data.data || [];
        // Get products from all sources
        const allProducts = [];
        for (const source of sources.slice(0, 3)) { // Limit for demo
          try {
            const productsResponse = await sourcesAPI.getProducts(source.id);
            allProducts.push(...(productsResponse.data.data || []));
          } catch (error) {
            console.log(`Could not load products for source ${source.id}`);
          }
        }
        setSourceProducts(allProducts);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };

  const loadDrafts = async () => {
    try {
      setLoading(true);
      
      const params = {};
      if (selectedAccount) params.account_id = selectedAccount;
      if (statusFilter !== 'all') params.status = statusFilter;
      if (imageStatusFilter !== 'all') params.image_status = imageStatusFilter;
      if (searchQuery) params.search = searchQuery;

      const response = await draftsAPI.getAll(params);
      const draftsData = response.data.data || [];
      setDrafts(draftsData);

      // Organize into Kanban columns
      const columns = {
        draft: draftsData.filter(d => d.status === 'draft'),
        editing: draftsData.filter(d => d.image_status === 'edited' && d.status === 'draft'),
        ready: draftsData.filter(d => d.status === 'ready'),
        listed: draftsData.filter(d => d.status === 'listed'),
      };
      setKanbanColumns(columns);

    } catch (error) {
      console.error('Error loading drafts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleBatchCreateFromProduct = () => {
    setBatchCreateDialog(true);
  };

  const handleExecuteBatchCreate = async () => {
    if (!selectedProduct || targetAccounts.length === 0) return;

    try {
      // Create customizations for each account
      const customizations = targetAccounts.map((accountId, index) => ({
        account_id: accountId,
        title: `${selectedProduct.title} - Account ${index + 1} Edition`,
        price: selectedProduct.suggested_ebay_price + (index * 5), // Different prices
        description: `${selectedProduct.description}\n\nCustomized for account-specific audience.`,
      }));

      await workflowAPI.batchCreateDrafts(selectedProduct.id, targetAccounts, customizations);
      
      setBatchCreateDialog(false);
      setSelectedProduct(null);
      setTargetAccounts([]);
      loadDrafts(); // Refresh data
      
    } catch (error) {
      console.error('Error creating batch drafts:', error);
    }
  };

  const handleBulkApproveImages = async () => {
    if (selectedDrafts.length === 0) return;

    try {
      await draftsAPI.bulkUpdateStatus({
        draft_ids: selectedDrafts,
        status: 'ready',
      });

      setSelectedDrafts([]);
      loadDrafts(); // Refresh data
    } catch (error) {
      console.error('Error bulk approving images:', error);
    }
  };

  const handleImageStatusUpdate = async (draftId, newStatus) => {
    try {
      await draftsAPI.updateImageStatus(draftId, {
        image_status: newStatus,
        edited_by: 'Current Employee', // This would come from auth context
      });
      loadDrafts(); // Refresh data
    } catch (error) {
      console.error('Error updating image status:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft': return 'default';
      case 'ready': return 'success';
      case 'listed': return 'primary';
      default: return 'default';
    }
  };

  const getImageStatusColor = (imageStatus) => {
    switch (imageStatus) {
      case 'pending': return 'warning';
      case 'edited': return 'info';
      case 'approved': return 'success';
      default: return 'default';
    }
  };

  const DraftCard = ({ draft, showActions = true }) => (
    <Card sx={{ mb: 2, border: selectedDrafts.includes(draft.id) ? 2 : 0, borderColor: 'primary.main' }}>
      <CardContent sx={{ pb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            {showActions && (
              <Checkbox
                checked={selectedDrafts.includes(draft.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedDrafts([...selectedDrafts, draft.id]);
                  } else {
                    setSelectedDrafts(selectedDrafts.filter(id => id !== draft.id));
                  }
                }}
                sx={{ position: 'absolute', top: 8, right: 8 }}
              />
            )}
            
            <Typography variant="subtitle2" fontWeight="600" gutterBottom>
              {draft.title}
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
              <Chip 
                label={draft.status?.toUpperCase() || 'DRAFT'} 
                color={getStatusColor(draft.status)} 
                size="small" 
              />
              <Chip 
                label={`IMG: ${draft.image_status?.toUpperCase() || 'PENDING'}`} 
                color={getImageStatusColor(draft.image_status)} 
                size="small" 
              />
              <Chip 
                label={`$${draft.price || '0.00'}`} 
                variant="outlined" 
                size="small" 
              />
            </Box>
            
            <Typography variant="caption" color="text.secondary" display="block">
              Account: {accounts.find(a => a.id === draft.account_id)?.ebay_username || 'Unknown'}
            </Typography>
            
            {draft.edited_by && (
              <Typography variant="caption" color="text.secondary" display="block">
                Edited by: {draft.edited_by} • {new Date(draft.updated_at || Date.now()).toLocaleDateString('vi-VN')}
              </Typography>
            )}
          </Box>
        </Box>

        {showActions && (
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            {draft.image_status === 'edited' && (
              <Button 
                size="small" 
                variant="contained" 
                color="success"
                startIcon={<CheckCircle />}
                onClick={() => handleImageStatusUpdate(draft.id, 'approved')}
              >
                Approve
              </Button>
            )}
            
            <Button size="small" variant="outlined" startIcon={<Visibility />}>
              Preview
            </Button>
            
            <Button size="small" variant="outlined" startIcon={<Edit />}>
              Edit
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const KanbanColumn = ({ title, items, status, bgColor }) => (
    <Card sx={{ height: 'fit-content', minHeight: '400px' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ 
            width: 12, 
            height: 12, 
            borderRadius: '50%', 
            bgcolor: bgColor, 
            mr: 1.5 
          }} />
          <Typography variant="h6" fontWeight="600">
            {title}
          </Typography>
          <Chip label={items.length} size="small" sx={{ ml: 'auto' }} />
        </Box>
        
        <Box sx={{ maxHeight: '600px', overflowY: 'auto' }}>
          {items.map((draft) => (
            <DraftCard key={draft.id} draft={draft} showActions={true} />
          ))}
          
          {items.length === 0 && (
            <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
              Không có drafts trong trạng thái này
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="600" gutterBottom>
            📝 Draft Listings Management
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Employee workflow: Create → Edit Images → Approve → Publish
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="contained" 
            startIcon={<Add />}
            onClick={handleBatchCreateFromProduct}
          >
            Batch Create Drafts
          </Button>
          <Button 
            variant="outlined"
            startIcon={<Refresh />}
            onClick={loadDrafts}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Account</InputLabel>
                <Select
                  value={selectedAccount}
                  label="Account"
                  onChange={(e) => setSelectedAccount(e.target.value)}
                >
                  <MenuItem value="">All Accounts</MenuItem>
                  {accounts.map((account) => (
                    <MenuItem key={account.id} value={account.id}>
                      {account.ebay_username}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  label="Status"
                  onChange={(e) => setStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Status</MenuItem>
                  <MenuItem value="draft">Draft</MenuItem>
                  <MenuItem value="ready">Ready</MenuItem>
                  <MenuItem value="listed">Listed</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Image Status</InputLabel>
                <Select
                  value={imageStatusFilter}
                  label="Image Status"
                  onChange={(e) => setImageStatusFilter(e.target.value)}
                >
                  <MenuItem value="all">All Images</MenuItem>
                  <MenuItem value="pending">Pending</MenuItem>
                  <MenuItem value="edited">Edited</MenuItem>
                  <MenuItem value="approved">Approved</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                size="small"
                label="Search drafts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant={viewMode === 'kanban' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setViewMode('kanban')}
                >
                  Kanban
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'contained' : 'outlined'}
                  size="small"
                  onClick={() => setViewMode('list')}
                >
                  List
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Bulk Actions */}
      {selectedDrafts.length > 0 && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                color="inherit" 
                size="small"
                onClick={handleBulkApproveImages}
                startIcon={<CheckCircle />}
              >
                Approve Images ({selectedDrafts.length})
              </Button>
              <Button 
                color="inherit" 
                size="small"
                onClick={() => setSelectedDrafts([])}
              >
                Clear Selection
              </Button>
            </Box>
          }
        >
          Selected {selectedDrafts.length} drafts for bulk actions
        </Alert>
      )}

      {/* Main Content */}
      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress size={40} />
        </Box>
      ) : (
        <>
          {viewMode === 'kanban' ? (
            // Kanban View - Employee Workflow Focused
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <KanbanColumn
                  title="📝 Draft"
                  items={kanbanColumns.draft}
                  status="draft"
                  bgColor={theme.palette.grey[400]}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <KanbanColumn
                  title="🖼️ Image Editing"
                  items={kanbanColumns.editing}
                  status="editing"
                  bgColor={theme.palette.info.main}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <KanbanColumn
                  title="✅ Ready to List"
                  items={kanbanColumns.ready}
                  status="ready"
                  bgColor={theme.palette.success.main}
                />
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <KanbanColumn
                  title="🚀 Published"
                  items={kanbanColumns.listed}
                  status="listed"
                  bgColor={theme.palette.primary.main}
                />
              </Grid>
            </Grid>
          ) : (
            // List View
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  All Drafts ({drafts.length})
                </Typography>
                <Grid container spacing={2}>
                  {drafts.map((draft) => (
                    <Grid item xs={12} sm={6} md={4} key={draft.id}>
                      <DraftCard draft={draft} showActions={true} />
                    </Grid>
                  ))}
                </Grid>
                
                {drafts.length === 0 && (
                  <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
                    Không có drafts nào. Hãy tạo drafts mới từ source products.
                  </Typography>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Batch Create Dialog */}
      <Dialog open={batchCreateDialog} onClose={() => setBatchCreateDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          🚀 Batch Create Drafts từ 1 Product
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Chọn 1 source product và multiple accounts để tạo drafts với customization khác nhau.
          </Typography>

          {/* Product Selection */}
          <Typography variant="subtitle2" fontWeight="600" gutterBottom>
            1. Chọn Source Product:
          </Typography>
          <List sx={{ mb: 3, maxHeight: 200, overflowY: 'auto', bgcolor: 'grey.50' }}>
            {sourceProducts.slice(0, 5).map((product) => (
              <ListItem 
                key={product.id} 
                button 
                selected={selectedProduct?.id === product.id}
                onClick={() => setSelectedProduct(product)}
              >
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'primary.light' }}>
                    📦
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={product.title || `Product ${product.id}`}
                  secondary={`$${product.price || '0.00'} • ${product.category || 'General'}`}
                />
              </ListItem>
            ))}
          </List>

          {/* Account Selection */}
          <Typography variant="subtitle2" fontWeight="600" gutterBottom>
            2. Chọn Target Accounts ({targetAccounts.length} selected):
          </Typography>
          <List sx={{ maxHeight: 200, overflowY: 'auto', bgcolor: 'grey.50' }}>
            {accounts.map((account) => (
              <ListItem key={account.id}>
                <Checkbox
                  checked={targetAccounts.includes(account.id)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setTargetAccounts([...targetAccounts, account.id]);
                    } else {
                      setTargetAccounts(targetAccounts.filter(id => id !== account.id));
                    }
                  }}
                />
                <ListItemText
                  primary={account.ebay_username}
                  secondary={`${account.email} • ${account.country}`}
                />
              </ListItem>
            ))}
          </List>

          {selectedProduct && targetAccounts.length > 0 && (
            <Alert severity="success" sx={{ mt: 2 }}>
              ✅ Sẽ tạo {targetAccounts.length} drafts từ product "{selectedProduct.title}" 
              với customization khác nhau cho mỗi account.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setBatchCreateDialog(false)}>
            Cancel
          </Button>
          <Button 
            variant="contained"
            onClick={handleExecuteBatchCreate}
            disabled={!selectedProduct || targetAccounts.length === 0}
          >
            Create {targetAccounts.length} Drafts
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DraftsPage;