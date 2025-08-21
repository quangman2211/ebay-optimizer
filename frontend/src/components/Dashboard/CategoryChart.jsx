import React from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
} from '@mui/material';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend);

const CategoryChart = ({ data }) => {
  // Sample data matching the HTML version
  const chartData = data || {
    labels: ['Điện tử', 'Thời trang', 'Gia dụng', 'Sách', 'Khác'],
    datasets: [
      {
        data: [45, 25, 15, 10, 5],
        backgroundColor: [
          '#4e73df',  // Primary blue
          '#1cc88a',  // Success green
          '#36b9cc',  // Info cyan
          '#f6c23e',  // Warning yellow
          '#e74a3b',  // Danger red
        ],
        hoverBackgroundColor: [
          '#2e59d9',
          '#17a673',
          '#2c9faf',
          '#dda20a',
          '#be2617',
        ],
        borderWidth: 0,
        cutout: '60%', // Makes it a doughnut chart
        hoverOffset: 10,
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
        borderColor: 'rgba(255, 255, 255, 0.1)',
        borderWidth: 1,
        cornerRadius: 8,
        displayColors: true,
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((sum, val) => sum + val, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: ${value}% (${percentage}%)`;
          },
        },
      },
    },
    animation: {
      animateRotate: true,
      animateScale: true,
      duration: 1000,
    },
    interaction: {
      intersect: false,
    },
  };

  // Legend data with colors
  const legendData = [
    { label: 'Điện tử', color: '#4e73df', value: '45%' },
    { label: 'Thời trang', color: '#1cc88a', value: '25%' },
    { label: 'Gia dụng', color: '#36b9cc', value: '15%' },
    { label: 'Sách', color: '#f6c23e', value: '10%' },
    { label: 'Khác', color: '#e74a3b', value: '5%' },
  ];

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
            Danh mục bán chạy
          </Typography>
        }
        sx={{
          pb: 1,
        }}
      />
      
      <CardContent sx={{ flex: 1, pt: 0, pb: 2 }}>
        <Box
          sx={{
            position: 'relative',
            height: 250,
            width: '100%',
            mb: 3,
          }}
        >
          <Doughnut data={chartData} options={options} />
        </Box>

        {/* Custom Legend */}
        <Box
          sx={{
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'center',
            gap: 1,
            mt: 2,
          }}
        >
          {legendData.map((item, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 0.5,
                mb: 0.5,
              }}
            >
              <Box
                sx={{
                  width: 12,
                  height: 12,
                  borderRadius: '50%',
                  backgroundColor: item.color,
                  flexShrink: 0,
                }}
              />
              <Typography
                variant="caption"
                sx={{
                  fontSize: '0.75rem',
                  color: 'text.secondary',
                  whiteSpace: 'nowrap',
                }}
              >
                {item.label}
              </Typography>
            </Box>
          ))}
        </Box>

        {/* Stats Summary */}
        <Box
          sx={{
            mt: 2,
            p: 2,
            backgroundColor: 'grey.50',
            borderRadius: 2,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              fontWeight: 600,
              color: 'text.primary',
              textAlign: 'center',
            }}
          >
            Tổng danh mục: 5
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              textAlign: 'center',
              display: 'block',
              mt: 0.5,
            }}
          >
            Dựa trên doanh số 30 ngày qua
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default CategoryChart;