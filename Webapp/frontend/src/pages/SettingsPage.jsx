import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
} from '@mui/material';
import {
  Code as CodeIcon,
  Notifications as NotificationsIcon,
  Settings as SettingsIcon,
  TableChart as GoogleSheetsIcon,
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';
import { settingsAPI } from '../services/api';

const SettingsPage = () => {
  const [apiConfigOpen, setApiConfigOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  const [googleSheetsOpen, setGoogleSheetsOpen] = useState(false);
  
  // API Configuration state
  const [apiConfig, setApiConfig] = useState({
    clientId: '',
    clientSecret: '',
    redirectUri: '',
    environment: 'sandbox',
  });

  // Notification settings state
  const [notificationSettings, setNotificationSettings] = useState({
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
    orderAlerts: true,
    inventoryAlerts: true,
    performanceReports: false,
  });

  // Google Sheets settings state
  const [googleSheetsConfig, setGoogleSheetsConfig] = useState({
    spreadsheetId: '',
    listingsSheetName: 'Listings',
    ordersSheetName: 'Orders',
    sourcesSheetName: 'Sources',
    connectionStatus: 'disconnected', // disconnected, connecting, connected, error
  });

  // Loading states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await settingsAPI.getGoogleSheetsConfig();
      const data = response.data;
      
      if (data.google_sheets) {
        setGoogleSheetsConfig({
          spreadsheetId: data.google_sheets.spreadsheet_id || '',
          listingsSheetName: data.google_sheets.listings_sheet_name || 'Listings',
          ordersSheetName: data.google_sheets.orders_sheet_name || 'Orders',
          sourcesSheetName: data.google_sheets.sources_sheet_name || 'Sources',
          connectionStatus: data.google_sheets.connection_status || 'disconnected'
        });
      }
    } catch (error) {
      console.error('Error loading settings:', error);
      alert('Lỗi tải cấu hình. Sử dụng giá trị mặc định.');
    } finally {
      setLoading(false);
    }
  };

  const handleApiConfigSave = () => {
    // Simulate API save
    alert('Cấu hình API đã được lưu thành công!');
    setApiConfigOpen(false);
  };

  const handleNotificationSave = () => {
    // Simulate notification settings save
    alert('Cài đặt thông báo đã được lưu thành công!');
    setNotificationOpen(false);
  };

  const handleGoogleSheetsSave = async () => {
    try {
      setSaving(true);
      
      const configData = {
        spreadsheet_id: googleSheetsConfig.spreadsheetId,
        listings_sheet_name: googleSheetsConfig.listingsSheetName,
        orders_sheet_name: googleSheetsConfig.ordersSheetName,
        sources_sheet_name: googleSheetsConfig.sourcesSheetName
      };
      
      const response = await settingsAPI.updateGoogleSheetsConfig(configData);
      
      // Update connection status from response
      if (response.data.connection_status) {
        setGoogleSheetsConfig(prev => ({
          ...prev,
          connectionStatus: response.data.connection_status
        }));
      }
      
      alert('Cấu hình Google Sheets đã được lưu thành công!');
      setGoogleSheetsOpen(false);
    } catch (error) {
      console.error('Error saving Google Sheets config:', error);
      alert('Lỗi lưu cấu hình Google Sheets: ' + (error.response?.data?.detail || error.message));
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    try {
      setGoogleSheetsConfig(prev => ({ ...prev, connectionStatus: 'connecting' }));
      
      const configData = {
        spreadsheet_id: googleSheetsConfig.spreadsheetId,
        listings_sheet_name: googleSheetsConfig.listingsSheetName,
        orders_sheet_name: googleSheetsConfig.ordersSheetName,
        sources_sheet_name: googleSheetsConfig.sourcesSheetName
      };
      
      const response = await settingsAPI.testGoogleSheetsConnection(configData);
      
      const connectionStatus = response.data.connection_status;
      setGoogleSheetsConfig(prev => ({ ...prev, connectionStatus }));
      
      if (connectionStatus === 'connected') {
        alert('Kết nối Google Sheets thành công!');
      } else {
        alert('Lỗi kết nối Google Sheets. Vui lòng kiểm tra lại cấu hình.');
      }
    } catch (error) {
      console.error('Error testing connection:', error);
      setGoogleSheetsConfig(prev => ({ ...prev, connectionStatus: 'error' }));
      alert('Lỗi kiểm tra kết nối: ' + (error.response?.data?.detail || error.message));
    }
  };

  if (loading) {
    return (
      <MainLayout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <Typography>Đang tải cấu hình...</Typography>
        </Box>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      {/* Page Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box>
          <Typography variant="h3" sx={{ fontWeight: 600, color: 'text.primary', mb: 1 }}>
            Cài đặt
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Cấu hình hệ thống và thông báo
          </Typography>
        </Box>
      </Box>

      {/* Settings Cards - Simple 2-card design */}
      <Card sx={{ mb: 4 }}>
        <CardHeader
          title={
            <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
              <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
              Cài đặt hệ thống
            </Typography>
          }
        />
        <CardContent>
          <Grid container spacing={3}>
            {/* API Configuration Card */}
            <Grid item xs={12} md={4}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 2,
                  }
                }}
                onClick={() => setApiConfigOpen(true)}
              >
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <CodeIcon 
                    sx={{ 
                      fontSize: 48, 
                      color: 'primary.main', 
                      mb: 2 
                    }} 
                  />
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                    API Configuration
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Cấu hình kết nối eBay API
                  </Typography>
                  <Button 
                    variant="contained" 
                    size="small"
                    sx={{ textTransform: 'none' }}
                  >
                    Cài đặt
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {/* Google Sheets Card */}
            <Grid item xs={12} md={4}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 2,
                  }
                }}
                onClick={() => setGoogleSheetsOpen(true)}
              >
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <GoogleSheetsIcon 
                    sx={{ 
                      fontSize: 48, 
                      color: 'success.main', 
                      mb: 2 
                    }} 
                  />
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                    Google Sheets
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Cấu hình đồng bộ dữ liệu với Google Sheets
                  </Typography>
                  <Button 
                    variant="contained" 
                    size="small"
                    color="success"
                    sx={{ textTransform: 'none' }}
                  >
                    Cài đặt
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {/* Notifications Card */}
            <Grid item xs={12} md={4}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  '&:hover': {
                    boxShadow: 2,
                  }
                }}
                onClick={() => setNotificationOpen(true)}
              >
                <CardContent sx={{ textAlign: 'center', py: 4 }}>
                  <NotificationsIcon 
                    sx={{ 
                      fontSize: 48, 
                      color: 'warning.main', 
                      mb: 2 
                    }} 
                  />
                  <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 1 }}>
                    Notifications
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                    Cài đặt thông báo email và SMS
                  </Typography>
                  <Button 
                    variant="contained" 
                    size="small"
                    color="warning"
                    sx={{ textTransform: 'none' }}
                  >
                    Cài đặt
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* API Configuration Dialog */}
      <Dialog 
        open={apiConfigOpen} 
        onClose={() => setApiConfigOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CodeIcon sx={{ mr: 1 }} />
            API Configuration
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Cấu hình thông tin kết nối eBay API để đồng bộ dữ liệu listing và đơn hàng.
          </Alert>
          
          <TextField
            fullWidth
            label="Client ID"
            value={apiConfig.clientId}
            onChange={(e) => setApiConfig({ ...apiConfig, clientId: e.target.value })}
            margin="normal"
            placeholder="Nhập eBay Client ID"
          />
          
          <TextField
            fullWidth
            label="Client Secret"
            type="password"
            value={apiConfig.clientSecret}
            onChange={(e) => setApiConfig({ ...apiConfig, clientSecret: e.target.value })}
            margin="normal"
            placeholder="Nhập eBay Client Secret"
          />
          
          <TextField
            fullWidth
            label="Redirect URI"
            value={apiConfig.redirectUri}
            onChange={(e) => setApiConfig({ ...apiConfig, redirectUri: e.target.value })}
            margin="normal"
            placeholder="https://yourapp.com/oauth/callback"
          />

          <TextField
            fullWidth
            select
            label="Environment"
            value={apiConfig.environment}
            onChange={(e) => setApiConfig({ ...apiConfig, environment: e.target.value })}
            margin="normal"
            SelectProps={{
              native: true,
            }}
          >
            <option value="sandbox">Sandbox (Testing)</option>
            <option value="production">Production</option>
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setApiConfigOpen(false)}>
            Hủy
          </Button>
          <Button 
            onClick={handleApiConfigSave} 
            variant="contained"
            sx={{ textTransform: 'none' }}
          >
            Lưu cấu hình
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Settings Dialog */}
      <Dialog 
        open={notificationOpen} 
        onClose={() => setNotificationOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <NotificationsIcon sx={{ mr: 1 }} />
            Cài đặt thông báo
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Chọn các loại thông báo bạn muốn nhận qua email, SMS hoặc push notification.
          </Alert>

          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
            Kênh thông báo
          </Typography>
          
          <FormControlLabel
            control={
              <Switch
                checked={notificationSettings.emailNotifications}
                onChange={(e) => setNotificationSettings({ 
                  ...notificationSettings, 
                  emailNotifications: e.target.checked 
                })}
              />
            }
            label="Email notifications"
            sx={{ display: 'block', mb: 1 }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={notificationSettings.smsNotifications}
                onChange={(e) => setNotificationSettings({ 
                  ...notificationSettings, 
                  smsNotifications: e.target.checked 
                })}
              />
            }
            label="SMS notifications"
            sx={{ display: 'block', mb: 1 }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={notificationSettings.pushNotifications}
                onChange={(e) => setNotificationSettings({ 
                  ...notificationSettings, 
                  pushNotifications: e.target.checked 
                })}
              />
            }
            label="Push notifications"
            sx={{ display: 'block', mb: 3 }}
          />

          <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
            Loại thông báo
          </Typography>
          
          <FormControlLabel
            control={
              <Switch
                checked={notificationSettings.orderAlerts}
                onChange={(e) => setNotificationSettings({ 
                  ...notificationSettings, 
                  orderAlerts: e.target.checked 
                })}
              />
            }
            label="Cảnh báo đơn hàng mới"
            sx={{ display: 'block', mb: 1 }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={notificationSettings.inventoryAlerts}
                onChange={(e) => setNotificationSettings({ 
                  ...notificationSettings, 
                  inventoryAlerts: e.target.checked 
                })}
              />
            }
            label="Cảnh báo tồn kho thấp"
            sx={{ display: 'block', mb: 1 }}
          />
          
          <FormControlLabel
            control={
              <Switch
                checked={notificationSettings.performanceReports}
                onChange={(e) => setNotificationSettings({ 
                  ...notificationSettings, 
                  performanceReports: e.target.checked 
                })}
              />
            }
            label="Báo cáo hiệu suất hàng tuần"
            sx={{ display: 'block' }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNotificationOpen(false)}>
            Hủy
          </Button>
          <Button 
            onClick={handleNotificationSave} 
            variant="contained"
            color="warning"
            sx={{ textTransform: 'none' }}
          >
            Lưu cài đặt
          </Button>
        </DialogActions>
      </Dialog>

      {/* Google Sheets Configuration Dialog */}
      <Dialog 
        open={googleSheetsOpen} 
        onClose={() => setGoogleSheetsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <GoogleSheetsIcon sx={{ mr: 1 }} />
            Cấu hình Google Sheets
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 3 }}>
            Cấu hình kết nối với Google Sheets để đồng bộ dữ liệu listings, đơn hàng và sources.
          </Alert>

          {googleSheetsConfig.connectionStatus === 'connected' && (
            <Alert severity="success" sx={{ mb: 3 }}>
              ✅ Đã kết nối thành công với Google Sheets
            </Alert>
          )}

          {googleSheetsConfig.connectionStatus === 'error' && (
            <Alert severity="error" sx={{ mb: 3 }}>
              ❌ Lỗi kết nối Google Sheets. Vui lòng kiểm tra lại cấu hình.
            </Alert>
          )}
          
          <TextField
            fullWidth
            label="Spreadsheet ID"
            value={googleSheetsConfig.spreadsheetId}
            onChange={(e) => setGoogleSheetsConfig({ 
              ...googleSheetsConfig, 
              spreadsheetId: e.target.value,
              connectionStatus: 'disconnected'
            })}
            margin="normal"
            placeholder="Nhập ID của Google Spreadsheet"
            helperText="Ví dụ: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
          />

          <Box sx={{ mt: 3, mb: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
              Tên các Sheet trong Spreadsheet
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Sheet Listings"
                  value={googleSheetsConfig.listingsSheetName}
                  onChange={(e) => setGoogleSheetsConfig({ 
                    ...googleSheetsConfig, 
                    listingsSheetName: e.target.value 
                  })}
                  placeholder="Listings"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Sheet Orders"
                  value={googleSheetsConfig.ordersSheetName}
                  onChange={(e) => setGoogleSheetsConfig({ 
                    ...googleSheetsConfig, 
                    ordersSheetName: e.target.value 
                  })}
                  placeholder="Orders"
                />
              </Grid>
              
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Sheet Sources"
                  value={googleSheetsConfig.sourcesSheetName}
                  onChange={(e) => setGoogleSheetsConfig({ 
                    ...googleSheetsConfig, 
                    sourcesSheetName: e.target.value 
                  })}
                  placeholder="Sources"
                />
              </Grid>
            </Grid>
          </Box>

          <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
              📝 Hướng dẫn cấu hình:
            </Typography>
            <Typography variant="body2" component="div" sx={{ lineHeight: 1.6 }}>
              1. Tạo Google Spreadsheet mới hoặc sử dụng spreadsheet có sẵn<br/>
              2. Copy ID của spreadsheet từ URL (phần giữa /d/ và /edit)<br/>
              3. Tạo các sheet với tên tương ứng: Listings, Orders, Sources<br/>
              4. Chia sẻ spreadsheet với service account email<br/>
              5. Nhấn "Kiểm tra kết nối" để xác thực
            </Typography>
          </Box>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
            <Button 
              onClick={handleTestConnection}
              variant="outlined"
              disabled={googleSheetsConfig.connectionStatus === 'connecting'}
              sx={{ textTransform: 'none' }}
            >
              {googleSheetsConfig.connectionStatus === 'connecting' ? 'Đang kiểm tra...' : 'Kiểm tra kết nối'}
            </Button>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setGoogleSheetsOpen(false)}>
            Hủy
          </Button>
          <Button 
            onClick={handleGoogleSheetsSave} 
            variant="contained"
            color="success"
            disabled={saving}
            sx={{ textTransform: 'none' }}
          >
            {saving ? 'Đang lưu...' : 'Lưu cấu hình'}
          </Button>
        </DialogActions>
      </Dialog>
    </MainLayout>
  );
};

export default SettingsPage;