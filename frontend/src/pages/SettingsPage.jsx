import React, { useState } from 'react';
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
} from '@mui/icons-material';
import MainLayout from '../components/Layout/MainLayout';

const SettingsPage = () => {
  const [apiConfigOpen, setApiConfigOpen] = useState(false);
  const [notificationOpen, setNotificationOpen] = useState(false);
  
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
            <Grid item xs={12} md={6}>
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

            {/* Notifications Card */}
            <Grid item xs={12} md={6}>
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
    </MainLayout>
  );
};

export default SettingsPage;