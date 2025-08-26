import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  Alert,
  CircularProgress,
  Badge,
  Tab,
  Tabs,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  CheckCircle,
  Schedule,
  Speed,
  TrendingUp,
  Image,
  Message,
  Publish,
  PlayArrow,
  Pause,
  Done,
  Warning,
  Sync,
  Timer,
} from '@mui/icons-material';
import { draftsAPI, messagesAPI, productivityAPI, accountSheetsAPI } from '../services/api';

const EmployeeDashboard = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [currentEmployee] = useState('John Designer'); // This would come from auth context
  const [activeTab, setActiveTab] = useState(0);
  
  // State for dashboard data
  const [todayStats, setTodayStats] = useState({
    draftsCreated: 0,
    imagesApproved: 0,
    messagesReplied: 0,
    listingsPublished: 0,
    targetDrafts: 50,
    targetMessages: 20,
    targetListings: 30,
  });
  
  const [taskQueue, setTaskQueue] = useState([]);
  const [urgentMessages, setUrgentMessages] = useState([]);
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [sheetSyncStatus, setSheetSyncStatus] = useState([]);
  const [weeklyProgress, setWeeklyProgress] = useState({});

  // Timer state for productivity tracking
  const [isWorkingOnTask, setIsWorkingOnTask] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [timeSpent, setTimeSpent] = useState(0);

  useEffect(() => {
    loadDashboardData();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(loadDashboardData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Timer effect
  useEffect(() => {
    let interval = null;
    if (isWorkingOnTask) {
      interval = setInterval(() => {
        setTimeSpent((time) => time + 1);
      }, 1000);
    } else if (!isWorkingOnTask && timeSpent !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isWorkingOnTask, timeSpent]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load all data concurrently
      const [
        dailyStatsResponse,
        weeklyStatsResponse,
        taskQueueResponse,
        urgentMessagesResponse,
        pendingApprovalsResponse,
        sheetStatusResponse,
      ] = await Promise.allSettled([
        productivityAPI.getDailyStats(currentEmployee),
        productivityAPI.getWeeklyStats(currentEmployee),
        draftsAPI.getTaskQueue(currentEmployee),
        messagesAPI.getOverdue(),
        draftsAPI.getAll({ image_status: 'edited', limit: 10 }),
        accountSheetsAPI.getSheetsWithErrors(),
      ]);

      // Process daily stats
      if (dailyStatsResponse.status === 'fulfilled') {
        const stats = dailyStatsResponse.value.data.data || {};
        setTodayStats(prev => ({
          ...prev,
          draftsCreated: stats.drafts_created || 0,
          imagesApproved: stats.images_approved || 0,
          messagesReplied: stats.messages_replied || 0,
          listingsPublished: stats.listings_published || 0,
        }));
      }

      // Process task queue
      if (taskQueueResponse.status === 'fulfilled') {
        setTaskQueue(taskQueueResponse.value.data.data || []);
      }

      // Process urgent messages (mock data for now)
      setUrgentMessages([
        {
          id: 'msg1',
          subject: 'Question about iPhone 15',
          sender: 'buyer123',
          account: 'seller_pro_2025',
          priority: 'high',
          received: '2025-08-21T08:30:00Z',
          overdue: true,
        },
        {
          id: 'msg2', 
          subject: 'Shipping inquiry',
          sender: 'quickbuyer88',
          account: 'ebay_store_main',
          priority: 'normal',
          received: '2025-08-21T09:15:00Z',
          overdue: false,
        },
      ]);

      // Process pending approvals (mock data for now)
      setPendingApprovals([
        {
          id: 'draft1',
          title: 'Samsung Galaxy S24 Ultra',
          account: 'seller_pro_2025',
          imageCount: 8,
          editedBy: 'Sarah Editor',
          editedDate: '2025-08-21T07:00:00Z',
        },
        {
          id: 'draft2',
          title: 'MacBook Pro 16 inch',
          account: 'tech_deals_store',
          imageCount: 12,
          editedBy: 'Mike Designer',
          editedDate: '2025-08-21T08:45:00Z',
        },
      ]);

      // Process sheet sync status (mock data for now)
      setSheetSyncStatus([
        { account: 'seller_pro_2025', status: 'synced', lastSync: '2025-08-21T09:00:00Z' },
        { account: 'tech_deals_store', status: 'error', error: 'Permission denied' },
        { account: 'fashion_outlet', status: 'syncing', progress: 65 },
      ]);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartTask = (taskId) => {
    setCurrentTaskId(taskId);
    setIsWorkingOnTask(true);
    setTimeSpent(0);
  };

  const handleCompleteTask = async (taskId) => {
    try {
      if (currentTaskId === taskId) {
        setIsWorkingOnTask(false);
        // Here you would send the time spent to the backend
        console.log(`Task ${taskId} completed in ${timeSpent} seconds`);
      }
      
      await draftsAPI.updateTaskStatus(taskId, 'completed');
      await loadDashboardData(); // Refresh data
    } catch (error) {
      console.error('Error completing task:', error);
    }
  };

  const handleBulkApproveImages = async () => {
    try {
      const draftIds = pendingApprovals.map(draft => draft.id);
      await draftsAPI.bulkUpdateStatus({
        draft_ids: draftIds,
        image_status: 'approved',
        edited_by: currentEmployee,
      });
      await loadDashboardData(); // Refresh data
    } catch (error) {
      console.error('Error bulk approving images:', error);
    }
  };

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hrs > 0) {
      return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgressColor = (current, target) => {
    const percentage = (current / target) * 100;
    if (percentage >= 100) return 'success';
    if (percentage >= 75) return 'info';
    if (percentage >= 50) return 'warning';
    return 'error';
  };

  const getProgressValue = (current, target) => Math.min((current / target) * 100, 100);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={40} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with Employee Info */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Avatar sx={{ mr: 2, bgcolor: theme.palette.primary.main }}>
            {currentEmployee.split(' ').map(n => n[0]).join('')}
          </Avatar>
          <Box>
            <Typography variant="h4" fontWeight="600">
              Chào {currentEmployee}! 👋
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              Hôm nay là {new Date().toLocaleDateString('vi-VN', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </Typography>
          </Box>
        </Box>
        
        {/* Timer Display */}
        {isWorkingOnTask && (
          <Card sx={{ bgcolor: theme.palette.warning.light, color: theme.palette.warning.contrastText }}>
            <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Timer sx={{ mr: 1, fontSize: 20 }} />
                <Typography variant="h6" fontWeight="600">
                  {formatTime(timeSpent)}
                </Typography>
              </Box>
              <Typography variant="caption">
                Đang làm task...
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>

      {/* Today's Progress Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {[
          { 
            label: 'Drafts Created', 
            current: todayStats.draftsCreated, 
            target: todayStats.targetDrafts,
            icon: <Speed />,
            color: 'primary'
          },
          { 
            label: 'Images Approved', 
            current: todayStats.imagesApproved, 
            target: 25,
            icon: <Image />,
            color: 'success'
          },
          { 
            label: 'Messages Replied', 
            current: todayStats.messagesReplied, 
            target: todayStats.targetMessages,
            icon: <Message />,
            color: 'info'
          },
          { 
            label: 'Listings Published', 
            current: todayStats.listingsPublished, 
            target: todayStats.targetListings,
            icon: <Publish />,
            color: 'warning'
          },
        ].map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: `${stat.color}.light`, mr: 2 }}>
                    {stat.icon}
                  </Avatar>
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="h4" fontWeight="700" color={`${stat.color}.main`}>
                      {stat.current}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      /{stat.target} {stat.label}
                    </Typography>
                  </Box>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={getProgressValue(stat.current, stat.target)}
                  color={getProgressColor(stat.current, stat.target)}
                  sx={{ height: 8, borderRadius: 4 }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  {Math.round(getProgressValue(stat.current, stat.target))}% hoàn thành
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Main Content Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Task Queue" />
          <Tab label="Urgent Messages" />
          <Tab label="Image Approvals" />
          <Tab label="Sheet Status" />
        </Tabs>

        <CardContent>
          {/* Task Queue Tab */}
          {activeTab === 0 && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="600">
                  🎯 Hàng đợi công việc ({taskQueue.length} tasks)
                </Typography>
                <Chip label={`Đang làm: ${isWorkingOnTask ? 'Task đang chạy' : 'Không'}`} 
                      color={isWorkingOnTask ? 'warning' : 'default'} />
              </Box>

              {taskQueue.length === 0 ? (
                <Alert severity="success">
                  🎉 Tuyệt vời! Bạn đã hoàn thành tất cả task hôm nay.
                </Alert>
              ) : (
                <List>
                  {taskQueue.slice(0, 5).map((task, index) => (
                    <ListItem key={task.id || index} divider>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'primary.light' }}>
                          {task.type === 'draft' ? <Speed /> : <Image />}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={`${task.title || `Task ${index + 1}: Create draft for multiple accounts`}`}
                        secondary={
                          <Box>
                            <Typography variant="caption" display="block">
                              Account: {task.account || 'seller_pro_2025'} • 
                              Priority: <Chip label={task.priority || 'Medium'} size="small" />
                            </Typography>
                            {task.dueTime && (
                              <Typography variant="caption" color="warning.main">
                                ⏰ Due: {task.dueTime}
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                      <ListItemSecondaryAction>
                        {currentTaskId === (task.id || index) ? (
                          <Button 
                            variant="contained" 
                            color="success"
                            startIcon={<Done />}
                            onClick={() => handleCompleteTask(task.id || index)}
                          >
                            Complete
                          </Button>
                        ) : (
                          <Tooltip title="Start working on this task">
                            <IconButton 
                              color="primary"
                              onClick={() => handleStartTask(task.id || index)}
                            >
                              <PlayArrow />
                            </IconButton>
                          </Tooltip>
                        )}
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          )}

          {/* Urgent Messages Tab */}
          {activeTab === 1 && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="600">
                  🚨 Tin nhắn cần xử lý ({urgentMessages.length})
                </Typography>
                <Button variant="outlined" size="small">
                  Bulk Reply Templates
                </Button>
              </Box>

              {urgentMessages.length === 0 ? (
                <Alert severity="info">
                  📬 Không có tin nhắn khẩn cấp nào. Tuyệt vời!
                </Alert>
              ) : (
                <List>
                  {urgentMessages.map((message, index) => (
                    <ListItem key={message.id} divider>
                      <ListItemAvatar>
                        <Badge badgeContent={message.overdue ? '!' : null} color="error">
                          <Avatar sx={{ bgcolor: message.priority === 'high' ? 'error.light' : 'info.light' }}>
                            <Message />
                          </Avatar>
                        </Badge>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="subtitle2">
                              {message.subject}
                            </Typography>
                            {message.overdue && (
                              <Chip label="OVERDUE" color="error" size="small" sx={{ ml: 1 }} />
                            )}
                          </Box>
                        }
                        secondary={
                          <>
                            <Typography variant="caption" display="block">
                              From: {message.sender} • Account: {message.account}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {new Date(message.received).toLocaleString('vi-VN')}
                            </Typography>
                          </>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Button variant="contained" color="primary" size="small">
                          Reply
                        </Button>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          )}

          {/* Image Approvals Tab */}
          {activeTab === 2 && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="600">
                  🖼️ Images cần approval ({pendingApprovals.length})
                </Typography>
                <Button 
                  variant="contained" 
                  color="success"
                  startIcon={<CheckCircle />}
                  onClick={handleBulkApproveImages}
                  disabled={pendingApprovals.length === 0}
                >
                  Approve All ({pendingApprovals.length})
                </Button>
              </Box>

              {pendingApprovals.length === 0 ? (
                <Alert severity="success">
                  ✅ Tất cả images đã được approved. Great job!
                </Alert>
              ) : (
                <List>
                  {pendingApprovals.map((draft, index) => (
                    <ListItem key={draft.id} divider>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: 'warning.light' }}>
                          <Image />
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={draft.title}
                        secondary={
                          <>
                            <Typography variant="caption" display="block">
                              {draft.imageCount} images • Edited by: {draft.editedBy}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              Account: {draft.account} • 
                              {new Date(draft.editedDate).toLocaleString('vi-VN')}
                            </Typography>
                          </>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Button variant="outlined" size="small">
                            Preview
                          </Button>
                          <Button variant="contained" color="success" size="small">
                            Approve
                          </Button>
                        </Box>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>
          )}

          {/* Sheet Status Tab */}
          {activeTab === 3 && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight="600">
                  📊 Google Sheets Sync Status
                </Typography>
                <Button variant="outlined" startIcon={<Sync />} size="small">
                  Sync All Sheets
                </Button>
              </Box>

              <List>
                {sheetSyncStatus.map((sheet, index) => (
                  <ListItem key={sheet.account} divider>
                    <ListItemAvatar>
                      <Avatar sx={{ 
                        bgcolor: sheet.status === 'synced' ? 'success.light' : 
                                sheet.status === 'error' ? 'error.light' : 'warning.light' 
                      }}>
                        {sheet.status === 'synced' ? <CheckCircle /> : 
                         sheet.status === 'error' ? <Warning /> : <Sync />}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={sheet.account}
                      secondary={
                        <>
                          <Typography variant="caption" display="block">
                            Status: <Chip 
                              label={sheet.status.toUpperCase()} 
                              color={sheet.status === 'synced' ? 'success' : 
                                     sheet.status === 'error' ? 'error' : 'warning'} 
                              size="small" 
                            />
                          </Typography>
                          {sheet.status === 'synced' && (
                            <Typography variant="caption" color="text.secondary">
                              Last sync: {new Date(sheet.lastSync).toLocaleString('vi-VN')}
                            </Typography>
                          )}
                          {sheet.status === 'error' && (
                            <Typography variant="caption" color="error.main">
                              Error: {sheet.error}
                            </Typography>
                          )}
                          {sheet.status === 'syncing' && (
                            <LinearProgress 
                              variant="determinate" 
                              value={sheet.progress} 
                              sx={{ mt: 1, width: '100px' }}
                            />
                          )}
                        </>
                      }
                    />
                    <ListItemSecondaryAction>
                      {sheet.status === 'error' && (
                        <Button variant="contained" color="primary" size="small">
                          Retry
                        </Button>
                      )}
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Quick Action Buttons */}
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6} md={3}>
          <Button 
            fullWidth 
            variant="contained" 
            size="large" 
            startIcon={<Speed />}
            href="/drafts"
          >
            Create New Drafts
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button 
            fullWidth 
            variant="outlined" 
            size="large" 
            startIcon={<Message />}
            href="/messages"
          >
            Check Messages
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button 
            fullWidth 
            variant="outlined" 
            size="large" 
            startIcon={<TrendingUp />}
            href="/productivity"
          >
            View Performance
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button 
            fullWidth 
            variant="outlined" 
            size="large" 
            startIcon={<Sync />}
            href="/account-sheets"
          >
            Sync Sheets
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
};

export default EmployeeDashboard;