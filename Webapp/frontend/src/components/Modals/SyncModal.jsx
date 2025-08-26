import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Alert,
  Card,
  CardContent,
  Grid,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  CircularProgress,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  CloudSync as SyncIcon,
  CloudDownload as ImportIcon,
  CloudUpload as ExportIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Schedule as ScheduleIcon,
} from '@mui/icons-material';
import BaseModal from './BaseModal';
import { syncAPI } from '../../services/api';

const SyncModal = ({ open, onClose }) => {
  const [syncDirection, setSyncDirection] = useState('bidirectional');
  const [conflictResolution, setConflictResolution] = useState('merge_all');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncHistory, setSyncHistory] = useState([]);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  const [spreadsheetId, setSpreadsheetId] = useState('');
  const [syncResult, setSyncResult] = useState(null);

  // Fetch sync status and history when modal opens
  useEffect(() => {
    if (open) {
      fetchSyncData();
    }
  }, [open]);

  const fetchSyncData = async () => {
    try {
      const [statusResponse, historyResponse, connectionResponse] = await Promise.all([
        syncAPI.getStatus(),
        syncAPI.getHistory(10),
        syncAPI.testConnection()
      ]);

      setSyncStatus(statusResponse.data);
      setSyncHistory(historyResponse.data.data || []);
      setConnectionStatus(connectionResponse.data.success ? 'connected' : 'disconnected');
    } catch (err) {
      console.error('Failed to fetch sync data:', err);
      setConnectionStatus('error');
    }
  };

  const handleSync = async () => {
    try {
      setLoading(true);
      setError(null);
      setSyncResult(null);

      // Update conflict resolution config
      await syncAPI.updateSyncConfig({
        conflict_resolution: conflictResolution
      });

      const response = await syncAPI.fullSync(syncDirection);
      
      if (response.data.success) {
        setSyncResult(response.data);
        await fetchSyncData(); // Refresh data
        
        // Show detailed success message
        const summary = response.data.summary || {};
        const message = `Đồng bộ thành công!\n` +
          `• ${summary.total_new_items || 0} items mới được merge\n` +
          `• ${summary.total_conflicts_resolved || 0} conflicts đã giải quyết\n` +
          `• ${summary.items_preserved || 0} items được bảo toàn`;
        
        alert(message);
      } else {
        throw new Error(response.data.message || 'Sync failed');
      }
    } catch (err) {
      console.error('Sync failed:', err);
      setError(err.response?.data?.detail || err.message || 'Sync operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleImportFromSheets = async () => {
    if (!spreadsheetId.trim()) {
      setError('Vui lòng nhập Spreadsheet ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Call import endpoints for each type
      const importPromises = [
        fetch('/api/v1/sync/import-listings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ 
            spreadsheet_id: spreadsheetId,
            sheet_name: 'Listings' 
          })
        }),
        fetch('/api/v1/sync/import-orders', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ 
            spreadsheet_id: spreadsheetId,
            sheet_name: 'Orders' 
          })
        }),
        fetch('/api/v1/sync/import-sources', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ 
            spreadsheet_id: spreadsheetId,
            sheet_name: 'Sources' 
          })
        })
      ];

      const responses = await Promise.all(importPromises);
      const results = await Promise.all(responses.map(r => r.json()));
      
      // Check results
      const successCount = results.filter(r => r.success).length;
      const totalCount = results.length;
      
      if (successCount > 0) {
        alert(`Import thành công ${successCount}/${totalCount} loại dữ liệu!`);
        await fetchSyncData(); // Refresh data
        setSpreadsheetId(''); // Clear input
      } else {
        throw new Error('Tất cả import đều thất bại');
      }
      
    } catch (err) {
      console.error('Import failed:', err);
      setError(err.message || 'Import operation failed');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (success) => {
    if (success === true) return <SuccessIcon color="success" />;
    if (success === false) return <ErrorIcon color="error" />;
    return <InfoIcon color="info" />;
  };

  const getConnectionStatusChip = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Chip icon={<SuccessIcon />} label="Đã kết nối" color="success" size="small" />;
      case 'disconnected':
        return <Chip icon={<ErrorIcon />} label="Mất kết nối" color="error" size="small" />;
      case 'error':
        return <Chip icon={<ErrorIcon />} label="Lỗi kết nối" color="error" size="small" />;
      default:
        return <Chip icon={<ScheduleIcon />} label="Đang kiểm tra..." color="default" size="small" />;
    }
  };

  const actions = (
    <>
      <Button onClick={onClose} color="inherit" disabled={loading}>
        Đóng
      </Button>
      <Button
        onClick={handleSync}
        variant="contained"
        disabled={loading || connectionStatus !== 'connected'}
        startIcon={loading ? <CircularProgress size={16} /> : <SyncIcon />}
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
          },
        }}
      >
        {loading ? 'Đang đồng bộ...' : 'Bắt đầu đồng bộ'}
      </Button>
    </>
  );

  return (
    <BaseModal
      open={open}
      onClose={onClose}
      title="Đồng bộ dữ liệu với Google Sheets"
      actions={actions}
      maxWidth="md"
    >
      <Box>
        {/* Connection Status */}
        <Alert 
          severity={connectionStatus === 'connected' ? 'success' : 'warning'} 
          sx={{ mb: 3 }}
          action={getConnectionStatusChip()}
        >
          <Typography variant="body2">
            {connectionStatus === 'connected' 
              ? 'Kết nối Google Sheets hoạt động bình thường'
              : 'Kiểm tra kết nối Google Sheets. Một số tính năng có thể bị hạn chế.'
            }
          </Typography>
        </Alert>

        {/* Error Message */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Grid container spacing={3}>
          {/* Google Sheets Import */}
          <Grid item xs={12}>
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <ImportIcon sx={{ mr: 1, color: '#ed6c02' }} />
                  Import từ Google Sheets
                </Typography>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Nhập ID của Google Spreadsheet để import dữ liệu vào hệ thống:
                </Typography>
                
                <Grid container spacing={2} alignItems="center">
                  <Grid item xs={12} md={8}>
                    <TextField
                      fullWidth
                      size="small"
                      label="Spreadsheet ID"
                      placeholder="1ABC123DEF456GHI..."
                      value={spreadsheetId}
                      onChange={(e) => setSpreadsheetId(e.target.value)}
                      helperText="Ví dụ: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
                      disabled={loading}
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Button
                      fullWidth
                      variant="outlined"
                      onClick={handleImportFromSheets}
                      disabled={loading || !spreadsheetId.trim()}
                      startIcon={loading ? <CircularProgress size={16} /> : <ImportIcon />}
                      sx={{
                        borderColor: '#ed6c02',
                        color: '#ed6c02',
                        '&:hover': {
                          borderColor: '#d84315',
                          backgroundColor: 'rgba(237, 108, 2, 0.04)',
                        },
                      }}
                    >
                      Import ngay
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Sync Options */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Tùy chọn đồng bộ
                </Typography>
                
                <FormControl component="fieldset" sx={{ mt: 2 }}>
                  <FormLabel component="legend">Hướng đồng bộ</FormLabel>
                  <RadioGroup
                    value={syncDirection}
                    onChange={(e) => setSyncDirection(e.target.value)}
                  >
                    <FormControlLabel
                      value="bidirectional"
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <SyncIcon sx={{ mr: 1, color: '#1976d2' }} />
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              Hai chiều (Khuyến nghị)
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Đồng bộ cả import và export
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="to_sheets"
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <ExportIcon sx={{ mr: 1, color: '#2e7d32' }} />
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              Export to Sheets
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Chỉ xuất dữ liệu lên Google Sheets
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="from_sheets"
                      control={<Radio />}
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <ImportIcon sx={{ mr: 1, color: '#ed6c02' }} />
                          <Box>
                            <Typography variant="body2" fontWeight={500}>
                              Import from Sheets
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Chỉ nhập dữ liệu từ Google Sheets
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                  </RadioGroup>
                </FormControl>

                <Divider sx={{ my: 3 }} />

                <FormControl component="fieldset">
                  <FormLabel component="legend">Xử lý xung đột dữ liệu</FormLabel>
                  <RadioGroup
                    value={conflictResolution}
                    onChange={(e) => setConflictResolution(e.target.value)}
                  >
                    <FormControlLabel
                      value="merge_all"
                      control={<Radio />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            Merge tất cả (Khuyến nghị)
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Kết hợp dữ liệu từ cả 2 nguồn, không mất dữ liệu
                          </Typography>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="sqlite_wins"
                      control={<Radio />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            SQLite ưu tiên
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Giữ dữ liệu trong database, ghi đè Sheets
                          </Typography>
                        </Box>
                      }
                    />
                    <FormControlLabel
                      value="sheets_wins"
                      control={<Radio />}
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight={500}>
                            Sheets ưu tiên
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Ưu tiên dữ liệu từ Google Sheets
                          </Typography>
                        </Box>
                      }
                    />
                  </RadioGroup>
                </FormControl>
              </CardContent>
            </Card>
          </Grid>

          {/* Sync Status */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Trạng thái đồng bộ
                </Typography>
                
                {syncStatus ? (
                  <Box>
                    <Grid container spacing={2} sx={{ mb: 2 }}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          SQLite Listings:
                        </Typography>
                        <Typography variant="h6">
                          {syncStatus.sqlite_counts?.listings || 0}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Sheets Listings:
                        </Typography>
                        <Typography variant="h6">
                          {syncStatus.sheets_counts?.listings || 0}
                        </Typography>
                      </Grid>
                    </Grid>

                    <Divider sx={{ my: 2 }} />

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Lần export cuối:
                    </Typography>
                    <Typography variant="body2">
                      {syncStatus.last_export?.timestamp 
                        ? new Date(syncStatus.last_export.timestamp).toLocaleString('vi-VN')
                        : 'Chưa có'
                      }
                    </Typography>

                    <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mt: 1 }}>
                      Lần import cuối:
                    </Typography>
                    <Typography variant="body2">
                      {syncStatus.last_import?.timestamp 
                        ? new Date(syncStatus.last_import.timestamp).toLocaleString('vi-VN')
                        : 'Chưa có'
                      }
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    <Typography>Đang tải trạng thái...</Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Sync Result */}
          {syncResult && (
            <Grid item xs={12}>
              <Card sx={{ backgroundColor: '#f8f9fa', border: '1px solid #e9ecef' }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: 'success.main' }}>
                    🎉 Kết quả đồng bộ thành công
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Items mới merged:
                      </Typography>
                      <Typography variant="h6" color="success.main">
                        {syncResult.summary?.total_new_items || 0}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Conflicts giải quyết:
                      </Typography>
                      <Typography variant="h6" color="warning.main">
                        {syncResult.summary?.total_conflicts_resolved || 0}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Items bảo toàn:
                      </Typography>
                      <Typography variant="h6" color="info.main">
                        {syncResult.summary?.items_preserved || 0}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} md={3}>
                      <Typography variant="body2" color="text.secondary">
                        Conflicts phát hiện:
                      </Typography>
                      <Typography variant="h6" color="error.main">
                        {syncResult.summary?.conflicts_detected || 0}
                      </Typography>
                    </Grid>
                  </Grid>

                  <Typography variant="body2" sx={{ mt: 2, fontStyle: 'italic' }}>
                    {syncResult.message}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          )}

          {/* Sync History */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Lịch sử đồng bộ (10 lần gần nhất)
                </Typography>
                
                {syncHistory.length > 0 ? (
                  <List>
                    {syncHistory.map((item, index) => (
                      <ListItem key={item.id || index} divider={index < syncHistory.length - 1}>
                        <ListItemIcon>
                          {getStatusIcon(item.success)}
                        </ListItemIcon>
                        <ListItemText
                          primary={item.description || item.action}
                          secondary={
                            <Box>
                              <Typography variant="caption" display="block">
                                {new Date(item.timestamp).toLocaleString('vi-VN')}
                              </Typography>
                              {item.error && (
                                <Typography variant="caption" color="error" display="block">
                                  Lỗi: {item.error}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                ) : (
                  <Typography color="text.secondary" textAlign="center" py={2}>
                    Chưa có lịch sử đồng bộ
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </BaseModal>
  );
};

export default SyncModal;