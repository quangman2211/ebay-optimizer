import React from 'react';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ebayTheme from './theme/ebayTheme';

// Pages
import EbayDashboard from './pages/EbayDashboard';
import ListingsPage from './pages/ListingsPage';
import OrdersPage from './pages/OrdersPage';
import CreateListingPage from './pages/CreateListingPage';
import OptimizePage from './pages/OptimizePage';
import SourcesPage from './pages/SourcesPage';
import SuppliersPage from './pages/SuppliersPage';
import AccountsPage from './pages/AccountsPage';
import SettingsPage from './pages/SettingsPage';

// Auth Components
import Login from './components/Login/Login';
import { useAuth } from './context/AuthContext';
import { Navigate } from 'react-router-dom';

// LoginPage component để handle login với redirect
const LoginPage = () => {
  const { isAuthenticated, login, loading } = useAuth();
  const [error, setError] = React.useState(null);

  // Wait for auth initialization to complete before any redirects
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        flexDirection: 'column'
      }}>
        <div style={{ marginBottom: '20px' }}>🔄 Đang khởi tạo...</div>
        <div style={{ 
          width: '40px', 
          height: '40px', 
          border: '3px solid #f3f3f3',
          borderTop: '3px solid #0064D2', 
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }}></div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Only redirect after loading is complete and user is authenticated
  if (!loading && isAuthenticated) {
    console.log('LoginPage: Redirecting to dashboard, user authenticated');
    return <Navigate to="/dashboard" replace />;
  }

  const handleLogin = async (credentials) => {
    setError(null);
    const result = await login(credentials);
    
    if (!result.success) {
      setError(result.error);
    }
    // No need to manually redirect here - the state change will trigger re-render
  };

  console.log('LoginPage: Rendering login form, loading:', loading, 'isAuthenticated:', isAuthenticated);
  
  return (
    <Login 
      onLogin={handleLogin}
      loading={loading}
      error={error}
    />
  );
};

function App() {
  return (
    <ThemeProvider theme={ebayTheme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Public Login Route */}
              <Route path="/login" element={<LoginPage />} />
              
              {/* Protected Routes */}
              <Route path="*" element={
                <ProtectedRoute>
                  <Routes>
                    <Route path="/" element={<EbayDashboard />} />
                    <Route path="/dashboard" element={<EbayDashboard />} />
                    <Route path="/listings" element={<ListingsPage />} />
                    <Route path="/listings/create" element={<CreateListingPage />} />
                    <Route path="/listings/optimize" element={<OptimizePage />} />
                    <Route path="/orders" element={<OrdersPage />} />
                    <Route path="/sources" element={<SourcesPage />} />
                    <Route path="/suppliers" element={<SuppliersPage />} />
                    <Route path="/accounts" element={<AccountsPage />} />
                    <Route path="/settings" element={<SettingsPage />} />
                  </Routes>
                </ProtectedRoute>
              } />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;