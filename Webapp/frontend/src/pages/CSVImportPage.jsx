import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  Box,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Upload as UploadIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Preview as PreviewIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const CSVImportPage = () => {
  const { user } = useAuth();
  const [importHistory, setImportHistory] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Import form state
  const [importForm, setImportForm] = useState({
    sheetId: '',
    accountId: '',
    importType: 'orders',
    estimatedRecords: 0
  });
  
  // Preview state
  const [previewDialog, setPreviewDialog] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  
  // Import status polling
  const [activeImports, setActiveImports] = useState([]);

  useEffect(() => {
    fetchInitialData();
    
    // Poll for active import status every 5 seconds
    const interval = setInterval(() => {
      if (activeImports.length > 0) {
        pollImportStatus();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [activeImports]);

  const fetchInitialData = async () => {
    setLoading(true);
    try {
      const [historyResponse, accountsResponse] = await Promise.all([
        api.get('/csv/import/history'),
        api.get('/accounts')
      ]);
      
      setImportHistory(historyResponse.data.imports || []);
      setAccounts(accountsResponse.data.accounts || []);
    } catch (err) {
      console.error('Failed to fetch initial data:', err);
      setError('Failed to load page data');
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewSheet = async () => {
    if (!importForm.sheetId) {
      setError('Please enter a Sheet ID first');
      return;
    }
    
    setPreviewLoading(true);
    setPreviewDialog(true);
    
    try {
      const response = await api.get(`/csv/sheets/${importForm.sheetId}/preview`, {
        params: {
          sheet_name: importForm.importType === 'orders' ? 'Orders' : 'Listings',
          limit: 10
        }
      });
      
      setPreviewData(response.data);
      setImportForm(prev => ({
        ...prev,
        estimatedRecords: response.data.total_rows || 0
      }));
    } catch (err) {
      console.error('Preview failed:', err);
      setError('Failed to preview sheet data');
      setPreviewDialog(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleStartImport = async () => {
    if (!importForm.sheetId || !importForm.accountId) {
      setError('Please fill in all required fields');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const endpoint = importForm.importType === 'orders' ? 
        '/csv/import/orders' : '/csv/import/listings';
      
      const response = await api.post(endpoint, {
        sheet_id: importForm.sheetId,
        account_id: parseInt(importForm.accountId),
        import_type: importForm.importType,
        estimated_records: importForm.estimatedRecords,
        options: {}
      });
      
      if (response.data.success) {
        setSuccess(`Import started successfully! Import ID: ${response.data.import_id}`);
        
        // Add to active imports for polling
        setActiveImports(prev => [...prev, {
          id: response.data.import_id,
          type: importForm.importType,
          status: response.data.status
        }]);
        
        // Reset form
        setImportForm({
          sheetId: '',
          accountId: '',
          importType: 'orders',
          estimatedRecords: 0
        });
        
        // Refresh history
        fetchInitialData();
      } else {
        setError('Import failed to start');
      }
    } catch (err) {
      console.error('Import failed:', err);
      setError(`Import failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
      setPreviewDialog(false);
    }
  };

  const pollImportStatus = async () => {
    const statusPromises = activeImports.map(importItem => 
      api.get(`/csv/import/status/${importItem.id}`)
        .then(response => ({ ...importItem, ...response.data }))
        .catch(() => importItem) // Keep original on error
    );
    
    try {
      const updatedImports = await Promise.all(statusPromises);
      
      // Remove completed/failed imports from active polling
      const stillActive = updatedImports.filter(imp => 
        imp.status === 'processing' || imp.status === 'pending'
      );
      
      setActiveImports(stillActive);
      
      // Refresh history if any completed
      if (stillActive.length < activeImports.length) {
        fetchInitialData();
      }
    } catch (err) {
      console.error('Status polling failed:', err);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'processing':
        return <RefreshIcon className="animate-spin" />;
      default:
        return <RefreshIcon />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'processing':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        CSV Data Import
      </Typography>
      
      <Typography variant="subtitle1" color="textSecondary" paragraph>
        Import eBay orders and listings data from Google Sheets
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Import Form */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Start New Import
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Google Sheet ID"
              value={importForm.sheetId}
              onChange={(e) => setImportForm(prev => ({ ...prev, sheetId: e.target.value }))}
              placeholder="1ABC123_your_sheet_id"
              helperText="Enter the Google Sheet ID containing your eBay data"
            />
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Account</InputLabel>
              <Select
                value={importForm.accountId}
                onChange={(e) => setImportForm(prev => ({ ...prev, accountId: e.target.value }))}
              >
                {accounts.map((account) => (
                  <MenuItem key={account.id} value={account.id}>
                    {account.name} ({account.ebay_user_id})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth>
              <InputLabel>Data Type</InputLabel>
              <Select
                value={importForm.importType}
                onChange={(e) => setImportForm(prev => ({ ...prev, importType: e.target.value }))}
              >
                <MenuItem value="orders">Orders</MenuItem>
                <MenuItem value="listings">Listings</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                startIcon={<PreviewIcon />}
                onClick={handlePreviewSheet}
                disabled={!importForm.sheetId || loading}
              >
                Preview Data
              </Button>
              
              <Button
                variant="contained"
                startIcon={<UploadIcon />}
                onClick={handleStartImport}
                disabled={!importForm.sheetId || !importForm.accountId || loading}
              >
                Start Import
              </Button>
            </Box>
          </Grid>
          
          {importForm.estimatedRecords > 0 && (
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary">
                Estimated records to import: {importForm.estimatedRecords}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Active Imports */}
      {activeImports.length > 0 && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Active Imports
          </Typography>
          
          {activeImports.map((importItem) => (
            <Box key={importItem.id} sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                {getStatusIcon(importItem.status)}
                <Typography variant="subtitle2">
                  {importItem.type} Import - {importItem.id}
                </Typography>
                <Chip 
                  label={importItem.status} 
                  color={getStatusColor(importItem.status)}
                  size="small"
                />
              </Box>
              
              {importItem.status === 'processing' && (
                <LinearProgress sx={{ width: '100%' }} />
              )}
              
              {importItem.progress && (
                <Typography variant="body2" color="textSecondary">
                  Progress: {importItem.progress}% - {importItem.message}
                </Typography>
              )}
            </Box>
          ))}
        </Paper>
      )}

      {/* Import History */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Import History
        </Typography>
        
        {loading ? (
          <LinearProgress />
        ) : importHistory.length === 0 ? (
          <Typography color="textSecondary">
            No imports yet. Start your first import above.
          </Typography>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Import ID</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Account</TableCell>
                  <TableCell>Records</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Date</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {importHistory.map((importItem) => (
                  <TableRow key={importItem.import_id}>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {importItem.import_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={importItem.import_type} 
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      {accounts.find(acc => acc.id === importItem.account_id)?.name || 'Unknown'}
                    </TableCell>
                    <TableCell>
                      {importItem.imported_count} / {importItem.total_records}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(importItem.status)}
                        <Chip 
                          label={importItem.status} 
                          color={getStatusColor(importItem.status)}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    <TableCell>
                      {new Date(importItem.created_at).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      {/* Preview Dialog */}
      <Dialog 
        open={previewDialog} 
        onClose={() => setPreviewDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Sheet Data Preview - {importForm.importType}
        </DialogTitle>
        
        <DialogContent>
          {previewLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <LinearProgress sx={{ width: '100%' }} />
            </Box>
          ) : previewData ? (
            <>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Showing first 10 rows of {previewData.total_rows} total records
              </Typography>
              
              <TableContainer sx={{ maxHeight: 400 }}>
                <Table stickyHeader size="small">
                  <TableHead>
                    <TableRow>
                      {previewData.headers?.map((header, index) => (
                        <TableCell key={index}>
                          <Typography variant="caption" sx={{ fontWeight: 'bold' }}>
                            {header}
                          </Typography>
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {previewData.sample_rows?.map((row, rowIndex) => (
                      <TableRow key={rowIndex}>
                        {row.map((cell, cellIndex) => (
                          <TableCell key={cellIndex}>
                            <Typography variant="body2" sx={{ 
                              maxWidth: 150, 
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}>
                              {cell}
                            </Typography>
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          ) : (
            <Typography color="error">
              Failed to load preview data
            </Typography>
          )}
        </DialogContent>
        
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>
            Cancel
          </Button>
          {previewData && (
            <Button
              variant="contained"
              onClick={handleStartImport}
              disabled={loading}
            >
              Import This Data
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CSVImportPage;