import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Box,
} from '@mui/material';
import { MoreVert as MoreVertIcon } from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const RevenueChart = ({ data, period = '30 ngày' }) => {
  const [anchorEl, setAnchorEl] = React.useState(null);

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  // Sample data matching the HTML version
  const chartData = data || {
    labels: [
      '1/10', '3/10', '5/10', '7/10', '9/10', '11/10', '13/10', 
      '15/10', '17/10', '19/10', '21/10', '23/10', '25/10', '27/10', '29/10'
    ],
    datasets: [
      {
        label: 'Doanh thu',
        data: [1200, 1900, 1500, 2500, 2200, 3000, 2800, 3500, 3200, 3800, 3600, 4200, 4000, 4500, 4300],
        borderColor: '#4bc0c0',
        backgroundColor: 'rgba(75, 192, 192, 0.1)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#4bc0c0',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(75, 192, 192, 0.8)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          label: (context) => `Doanh thu: $${context.parsed.y.toLocaleString()}`,
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          color: '#6c757d',
          font: {
            size: 12,
          },
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          lineWidth: 1,
        },
        ticks: {
          color: '#6c757d',
          font: {
            size: 12,
          },
          callback: (value) => `$${value.toLocaleString()}`,
        },
      },
    },
    elements: {
      point: {
        hoverBackgroundColor: '#4bc0c0',
        hoverBorderColor: '#fff',
        hoverBorderWidth: 3,
      },
    },
    interaction: {
      intersect: false,
      mode: 'index',
    },
  };

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardHeader
        title={
          <Typography variant="h6" sx={{ fontWeight: 'bold', color: 'primary.main' }}>
            Biểu đồ doanh thu {period}
          </Typography>
        }
        action={
          <IconButton onClick={handleMenuClick}>
            <MoreVertIcon sx={{ color: 'grey.400' }} />
          </IconButton>
        }
        sx={{
          pb: 1,
          '& .MuiCardHeader-content': {
            overflow: 'visible',
          },
        }}
      />
      
      <CardContent sx={{ flex: 1, pt: 0 }}>
        <Box
          sx={{
            position: 'relative',
            height: 300,
            width: '100%',
          }}
        >
          <Line data={chartData} options={options} />
        </Box>
      </CardContent>

      {/* Options Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
        PaperProps={{
          sx: {
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
            borderRadius: 2,
            minWidth: 120,
          },
        }}
      >
        <MenuItem onClick={handleMenuClose} sx={{ py: 1 }}>
          <Typography variant="caption" color="text.secondary">
            Tùy chọn:
          </Typography>
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>7 ngày</MenuItem>
        <MenuItem onClick={handleMenuClose}>30 ngày</MenuItem>
        <MenuItem onClick={handleMenuClose}>90 ngày</MenuItem>
      </Menu>
    </Card>
  );
};

export default RevenueChart;