import React, { useState } from 'react';
import {
  Box,
  Typography,
  FormGroup,
  FormControlLabel,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Button,
  RadioGroup,
  Radio,
  FormLabel,
  CircularProgress,
} from '@mui/material';
import {
  FileDownload as DownloadIcon,
  TableChart as ExcelIcon,
  PictureAsPdf as PdfIcon,
  CloudSync as SheetsIcon,
} from '@mui/icons-material';
import BaseModal from './BaseModal';
import { exportAPI, syncAPI } from '../../services/api';

const ExportOrdersModal = ({ open, onClose }) => {
  const [exportFormat, setExportFormat] = useState('csv');
  const [exportDestination, setExportDestination] = useState('download');
  const [dateRange, setDateRange] = useState('last7days');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedFields, setSelectedFields] = useState({
    orderNumber: true,
    customer: true,
    product: true,
    amount: true,
    status: true,
    date: true,
    tracking: false,
    notes: false,
  });

  const fields = [
    { key: 'orderNumber', label: 'Mã đơn hàng' },
    { key: 'customer', label: 'Thông tin khách hàng' },
    { key: 'product', label: 'Sản phẩm' },
    { key: 'amount', label: 'Số tiền' },
    { key: 'status', label: 'Trạng thái' },
    { key: 'date', label: 'Ngày đặt hàng' },
    { key: 'tracking', label: 'Tracking number' },
    { key: 'notes', label: 'Ghi chú' },
  ];

  const dateRanges = [
    { value: 'today', label: 'Hôm nay' },
    { value: 'yesterday', label: 'Hôm qua' },
    { value: 'last7days', label: '7 ngày gần đây' },
    { value: 'last30days', label: '30 ngày gần đây' },
    { value: 'thisMonth', label: 'Tháng này' },
    { value: 'lastMonth', label: 'Tháng trước' },
    { value: 'custom', label: 'Tùy chọn' },
  ];

  const handleFieldChange = (field) => {
    setSelectedFields(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };

  const handleExport = async () => {
    const selectedCount = Object.values(selectedFields).filter(Boolean).length;
    if (selectedCount === 0) {
      setError('Vui lòng chọn ít nhất một trường dữ liệu!');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Calculate date range
      const now = new Date();
      let dateFrom, dateTo = now;

      switch (dateRange) {
        case 'today':
          dateFrom = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          break;
        case 'yesterday':
          dateFrom = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1);
          dateTo = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 1, 23, 59, 59);
          break;
        case 'last7days':
          dateFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'last30days':
          dateFrom = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        case 'thisMonth':
          dateFrom = new Date(now.getFullYear(), now.getMonth(), 1);
          break;
        case 'lastMonth':
          dateFrom = new Date(now.getFullYear(), now.getMonth() - 1, 1);
          dateTo = new Date(now.getFullYear(), now.getMonth(), 0);
          break;
        default:
          dateFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
      }

      if (exportDestination === 'sheets') {
        // Export to Google Sheets
        const response = await syncAPI.syncOrdersToSheets();
        
        if (response.data.success) {
          alert('Đã xuất dữ liệu đơn hàng lên Google Sheets thành công!');
        } else {
          throw new Error(response.data.message || 'Export to Sheets failed');
        }
      } else {
        // Export and download file
        const response = await exportAPI.exportOrders({
          format: exportFormat,
          date_from: dateFrom.toISOString(),
          date_to: dateTo.toISOString()
        });

        // Handle file download
        const blob = new Blob([response.data], { 
          type: exportFormat === 'csv' ? 'text/csv' : 'application/json' 
        });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `orders_export_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        window.URL.revokeObjectURL(url);

        alert(`Đã tải xuống file thành công!`);
      }

      onClose();
    } catch (err) {
      console.error('Export failed:', err);
      setError(err.response?.data?.detail || err.message || 'Export failed');
    } finally {
      setLoading(false);
    }
  };

  const actions = (
    <>
      <Button onClick={onClose} color="inherit" disabled={loading}>
        Hủy
      </Button>
      <Button
        onClick={handleExport}
        variant="contained"
        disabled={loading}
        startIcon={loading ? <CircularProgress size={16} /> : <DownloadIcon />}
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
          },
        }}
      >
        {loading ? 'Đang xuất...' : 'Xuất dữ liệu'}
      </Button>
    </>
  );

  return (
    <BaseModal
      open={open}
      onClose={onClose}
      title="Xuất dữ liệu đơn hàng"
      actions={actions}
      maxWidth="sm"
    >
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Chọn định dạng, điểm đến xuất, khoảng thời gian và các trường dữ liệu cần xuất.
          </Typography>
        </Alert>

        {/* Error Message */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {/* Export Destination */}
        <FormControl component="fieldset" sx={{ mb: 3 }}>
          <FormLabel component="legend" sx={{ mb: 1, fontWeight: 600 }}>
            Điểm đến xuất
          </FormLabel>
          <RadioGroup
            value={exportDestination}
            onChange={(e) => setExportDestination(e.target.value)}
            row
          >
            <FormControlLabel
              value="download"
              control={<Radio />}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <DownloadIcon sx={{ mr: 1, color: '#1976d2' }} />
                  Tải xuống file
                </Box>
              }
            />
            <FormControlLabel
              value="sheets"
              control={<Radio />}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <SheetsIcon sx={{ mr: 1, color: '#34A853' }} />
                  Google Sheets
                </Box>
              }
            />
          </RadioGroup>
        </FormControl>

        {/* Export Format - Only show for file download */}
        {exportDestination === 'download' && (
          <FormControl component="fieldset" sx={{ mb: 3 }}>
            <FormLabel component="legend" sx={{ mb: 1, fontWeight: 600 }}>
              Định dạng file
            </FormLabel>
            <RadioGroup
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
              row
            >
              <FormControlLabel
                value="csv"
                control={<Radio />}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <ExcelIcon sx={{ mr: 1, color: '#4CAF50' }} />
                    CSV (.csv)
                  </Box>
                }
              />
              <FormControlLabel
                value="json"
                control={<Radio />}
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <PdfIcon sx={{ mr: 1, color: '#f44336' }} />
                    JSON (.json)
                  </Box>
                }
              />
            </RadioGroup>
          </FormControl>
        )}

        {/* Date Range */}
        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Khoảng thời gian</InputLabel>
          <Select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            label="Khoảng thời gian"
          >
            {dateRanges.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Data Fields */}
        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 2 }}>
          Chọn trường dữ liệu
        </Typography>
        <FormGroup>
          {fields.map((field) => (
            <FormControlLabel
              key={field.key}
              control={
                <Checkbox
                  checked={selectedFields[field.key]}
                  onChange={() => handleFieldChange(field.key)}
                />
              }
              label={field.label}
            />
          ))}
        </FormGroup>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Số trường đã chọn: {Object.values(selectedFields).filter(Boolean).length}/{fields.length}
        </Typography>
      </Box>
    </BaseModal>
  );
};

export default ExportOrdersModal;