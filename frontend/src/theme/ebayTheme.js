import { createTheme } from '@mui/material/styles';

const ebayTheme = createTheme({
  palette: {
    primary: {
      main: '#0064D2', // Ebay-UI primary color
      light: '#4A90E2',
      dark: '#004A9F',
      contrastText: '#fff',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#a4001e',
      contrastText: '#fff',
    },
    success: {
      main: '#28a745',
      light: '#5cb85c',
      dark: '#1e7e34',
    },
    warning: {
      main: '#ffc107',
      light: '#ffeb3b',
      dark: '#ff8f00',
    },
    error: {
      main: '#dc3545',
      light: '#f56565',
      dark: '#c53030',
    },
    info: {
      main: '#17a2b8',
      light: '#5bc0de',
      dark: '#138496',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#343a40',
      secondary: '#6c757d',
    },
    grey: {
      100: '#f8f9fa',
      200: '#e9ecef',
      300: '#dee2e6',
      400: '#ced4da',
      500: '#adb5bd',
      600: '#6c757d',
      700: '#495057',
      800: '#343a40',
      900: '#212529',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
    fontSize: 14,
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 600,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 600,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 600,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 600,
    },
    subtitle1: {
      fontSize: '1rem',
      fontWeight: 500,
    },
    subtitle2: {
      fontSize: '0.875rem',
      fontWeight: 500,
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.5,
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.5,
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.66,
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      textTransform: 'uppercase',
      letterSpacing: '0.1em',
    },
  },
  shape: {
    borderRadius: 12,
  },
  spacing: 8,
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 0.15rem 1.75rem 0 rgba(33, 40, 50, 0.15)',
          border: 'none',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 0.25rem 2rem 0 rgba(33, 40, 50, 0.2)',
          },
        },
      },
    },
    MuiCardHeader: {
      styleOverrides: {
        root: {
          backgroundColor: 'transparent',
          borderBottom: '1px solid rgba(0, 0, 0, 0.125)',
          borderRadius: '12px 12px 0 0',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
          textTransform: 'none',
          padding: '8px 16px',
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-1px)',
          },
        },
        contained: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 15px rgba(0, 100, 210, 0.4)',
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          transition: 'all 0.2s ease',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            '& fieldset': {
              borderColor: '#d1d3e2',
            },
            '&:hover fieldset': {
              borderColor: '#0064D2',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#0064D2',
              boxShadow: '0 0 0 0.2rem rgba(0, 100, 210, 0.25)',
            },
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
        elevation1: {
          boxShadow: '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
        },
        elevation4: {
          boxShadow: '0 0.15rem 1.75rem 0 rgba(33, 40, 50, 0.15)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
          fontSize: '0.75rem',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          border: 'none',
        },
      },
    },
    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          overflow: 'hidden',
        },
      },
    },
    MuiTableHead: {
      styleOverrides: {
        root: {
          '& .MuiTableCell-head': {
            backgroundColor: '#f8f9fc',
            fontWeight: 600,
            color: '#5a5c69',
            borderTop: 'none',
          },
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(0, 0, 0, 0.02)',
          },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 8,
          boxShadow: '0 0.15rem 1.75rem 0 rgba(33, 40, 50, 0.15)',
          border: '1px solid #e3e6f0',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          padding: '8px 16px',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: '#f8f9fc',
          },
        },
      },
    },
    MuiBadge: {
      styleOverrides: {
        badge: {
          fontSize: '0.65rem',
          minWidth: 18,
          height: 18,
          borderRadius: 9,
        },
      },
    },
  },
  // Custom theme extensions for Ebay-UI specific styles
  custom: {
    sidebar: {
      width: '280px',
      collapsedWidth: '80px',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    },
    topbar: {
      height: '70px',
      background: '#ffffff',
      shadow: '0 2px 10px rgba(0,0,0,0.1)',
    },
    borderColors: {
      primary: '#0064D2',
      success: '#28a745',
      info: '#17a2b8',
      warning: '#ffc107',
      danger: '#dc3545',
    },
    gradients: {
      primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      sidebar: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      button: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    },
    animations: {
      hover: 'all 0.2s ease',
      transform: 'all 0.3s ease',
    },
  },
});

export default ebayTheme;