import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  FileDownload as DownloadIcon,
} from '@mui/icons-material';
import BaseModal from './BaseModal';

const TrackingBulkModal = ({ open, onClose }) => {
  const [trackingData, setTrackingData] = useState('');
  const [carrier, setCarrier] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const carriers = [
    { value: 'vnpost', label: 'VNPost' },
    { value: 'ghn', label: 'Giao Hàng Nhanh' },
    { value: 'viettel', label: 'Viettel Post' },
    { value: 'jnt', label: 'J&T Express' },
    { value: 'other', label: 'Khác' },
  ];

  const handleUpload = async () => {
    if (!trackingData.trim() || !carrier) {
      alert('Vui lòng nhập đầy đủ thông tin!');
      return;
    }

    setUploading(true);
    setProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setUploading(false);
          alert('Upload tracking numbers thành công!');
          onClose();
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleDownloadTemplate = () => {
    const csvContent = 'Order Number,Tracking Number\nORD-001,VN12345678\nORD-002,VN87654321';
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'tracking_template.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const actions = (
    <>
      <Button onClick={onClose} color="inherit">
        Hủy
      </Button>
      <Button
        onClick={handleUpload}
        variant="contained"
        disabled={uploading}
        startIcon={<UploadIcon />}
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          '&:hover': {
            background: 'linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%)',
          },
        }}
      >
        {uploading ? 'Đang upload...' : 'Upload Tracking'}
      </Button>
    </>
  );

  return (
    <BaseModal
      open={open}
      onClose={onClose}
      title="Upload Tracking Numbers Hàng loạt"
      actions={actions}
      maxWidth="md"
    >
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            Tải lên tracking numbers hàng loạt cho các đơn hàng. 
            Hỗ trợ định dạng CSV hoặc nhập trực tiếp.
          </Typography>
        </Alert>

        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <Button
            onClick={handleDownloadTemplate}
            variant="outlined"
            startIcon={<DownloadIcon />}
            size="small"
          >
            Tải Template CSV
          </Button>
          <Button
            variant="outlined"
            size="small"
            component="label"
          >
            Chọn file CSV
            <input
              type="file"
              hidden
              accept=".csv"
              onChange={(e) => {
                const file = e.target.files[0];
                if (file) {
                  const reader = new FileReader();
                  reader.onload = (event) => {
                    setTrackingData(event.target.result);
                  };
                  reader.readAsText(file);
                }
              }}
            />
          </Button>
        </Box>

        <FormControl fullWidth sx={{ mb: 3 }}>
          <InputLabel>Đơn vị vận chuyển</InputLabel>
          <Select
            value={carrier}
            onChange={(e) => setCarrier(e.target.value)}
            label="Đơn vị vận chuyển"
          >
            {carriers.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <TextField
          fullWidth
          multiline
          rows={8}
          label="Dữ liệu Tracking (CSV hoặc nhập trực tiếp)"
          value={trackingData}
          onChange={(e) => setTrackingData(e.target.value)}
          placeholder="Order Number,Tracking Number&#10;ORD-001,VN12345678&#10;ORD-002,VN87654321"
          sx={{ mb: 2 }}
        />

        {uploading && (
          <Box sx={{ width: '100%', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Đang xử lý... {progress}%
              </Typography>
            </Box>
            <LinearProgress variant="determinate" value={progress} />
          </Box>
        )}

        <Typography variant="body2" color="text.secondary">
          Định dạng: Order Number, Tracking Number (mỗi dòng một cặp)
        </Typography>
      </Box>
    </BaseModal>
  );
};

export default TrackingBulkModal;