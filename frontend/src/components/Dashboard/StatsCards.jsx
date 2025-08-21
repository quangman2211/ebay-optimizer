import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
} from '@mui/material';
import {
  ShoppingCart as CartIcon,
  AttachMoney as MoneyIcon,
  LocalOffer as TagsIcon,
  TrendingUp as TrendIcon,
  TrendingDown as TrendDownIcon,
  TrendingFlat as TrendFlatIcon,
} from '@mui/icons-material';

const StatsCards = ({ stats }) => {
  const statsData = stats || [
    {
      title: 'Tổng đơn hàng (Tháng)',
      value: '1,245',
      change: '+12.5%',
      changeText: 'so với tháng trước',
      trend: 'up',
      icon: <CartIcon />,
      color: 'primary',
      borderColor: '#0064D2',
    },
    {
      title: 'Doanh thu (Tháng)',
      value: '$45,850',
      change: '+8.3%',
      changeText: 'so với tháng trước',
      trend: 'up',
      icon: <MoneyIcon />,
      color: 'success',
      borderColor: '#28a745',
    },
    {
      title: 'Active Listings',
      value: '847',
      progress: 75,
      progressText: '75% đã tối ưu',
      icon: <TagsIcon />,
      color: 'info',
      borderColor: '#17a2b8',
    },
    {
      title: 'Tỷ lệ chuyển đổi',
      value: '3.2%',
      change: '-0.5%',
      changeText: 'cần cải thiện',
      trend: 'down',
      icon: <TrendIcon />,
      color: 'warning',
      borderColor: '#ffc107',
    },
  ];

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <TrendIcon sx={{ fontSize: '1rem' }} />;
      case 'down':
        return <TrendDownIcon sx={{ fontSize: '1rem' }} />;
      default:
        return <TrendFlatIcon sx={{ fontSize: '1rem' }} />;
    }
  };

  const getTrendColor = (trend) => {
    switch (trend) {
      case 'up':
        return 'success.main';
      case 'down':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      {statsData.map((stat, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card
            sx={{
              borderLeft: `4px solid ${stat.borderColor}`,
              height: '100%',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
              },
            }}
          >
            <CardContent sx={{ p: 2.5 }}>
              <Grid container spacing={0} alignItems="center">
                <Grid item xs>
                  <Typography
                    variant="overline"
                    sx={{
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      color: `${stat.color}.main`,
                      textTransform: 'uppercase',
                      mb: 1,
                      display: 'block',
                    }}
                  >
                    {stat.title}
                  </Typography>
                  
                  <Typography
                    variant="h4"
                    sx={{
                      fontWeight: 'bold',
                      color: 'text.primary',
                      mb: 1.5,
                    }}
                  >
                    {stat.value}
                  </Typography>

                  {/* Progress Bar (for Active Listings) */}
                  {stat.progress !== undefined && (
                    <Box sx={{ mt: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={stat.progress}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: 'grey.200',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: stat.borderColor,
                          },
                        }}
                      />
                      <Typography
                        variant="caption"
                        sx={{ color: 'text.secondary', mt: 0.5, display: 'block' }}
                      >
                        {stat.progressText}
                      </Typography>
                    </Box>
                  )}

                  {/* Trend Indicator */}
                  {stat.change && (
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        mt: 1.5,
                      }}
                    >
                      <Box
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          color: getTrendColor(stat.trend),
                          mr: 1,
                        }}
                      >
                        {getTrendIcon(stat.trend)}
                        <Typography
                          variant="caption"
                          sx={{
                            ml: 0.5,
                            fontWeight: 500,
                            fontSize: '0.8rem',
                          }}
                        >
                          {stat.change}
                        </Typography>
                      </Box>
                      <Typography
                        variant="caption"
                        sx={{
                          color: 'text.secondary',
                          fontSize: '0.8rem',
                        }}
                      >
                        {stat.changeText}
                      </Typography>
                    </Box>
                  )}
                </Grid>
                
                {/* Icon */}
                <Grid item>
                  <Box
                    sx={{
                      color: 'grey.400',
                      fontSize: '3rem',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      '& .MuiSvgIcon-root': {
                        fontSize: '3rem',
                      },
                    }}
                  >
                    {stat.icon}
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default StatsCards;