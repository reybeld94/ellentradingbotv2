import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './pages/AuthPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Dashboard from './pages/dashboard';
import SignalsPage from './pages/signals';
import OrdersPage from './pages/orders';
import Profile from './pages/Profile';
import TradesPage from './pages/trades';
import StrategiesPage from './pages/strategies';
import RiskDashboard from './pages/RiskDashboard';
import Analytics from './pages/Analytics';
import ExitRulesManager from './components/ExitRulesManager';
import Layout from './components/layout/Layout';
import type { Page } from './components/layout/Sidebar';

const AuthenticatedApp: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [pendingSignalsCount, setPendingSignalsCount] = useState(0);
  const navigate = useNavigate();
  const location = useLocation();

  // Fetch signals count logic (mantener el existente)
  useEffect(() => {
    const fetchSignalsCount = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('/api/v1/signals', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          const signals = Array.isArray(data) ? data : [];
          const pendingCount = signals.filter(s =>
            s.status === 'pending' || s.status === 'error'
          ).length;
          setPendingSignalsCount(pendingCount);
        }
      } catch (error) {
        console.error('Error fetching signals count:', error);
        setPendingSignalsCount(0);
      }
    };

    fetchSignalsCount();
    const interval = setInterval(fetchSignalsCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (currentPage === 'exit-rules') {
      navigate('/exit-rules');
    } else {
      navigate('/');
    }
  }, [currentPage, navigate]);

  useEffect(() => {
    if (location.pathname === '/exit-rules') {
      setCurrentPage('exit-rules');
    } else {
      setCurrentPage(prev => (prev === 'exit-rules' ? 'dashboard' : prev));
    }
  }, [location.pathname]);

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'signals':
        return <SignalsPage />;
      case 'orders':
        return <OrdersPage />;
      case 'trades':
        return <TradesPage />;
      case 'strategies':
        return <StrategiesPage />;
      case 'exit-rules':
        return <ExitRulesManager />;
      case 'risk':
        return <RiskDashboard />;
      case 'analytics':
        return <Analytics />;
      case 'settings':
        return <Profile />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout
      currentPage={currentPage}
      onPageChange={setCurrentPage}
      pendingSignalsCount={pendingSignalsCount}
    >
      <Routes>
        <Route path="/exit-rules" element={<ExitRulesManager />} />
        <Route path="*" element={renderCurrentPage()} />
      </Routes>
    </Layout>
  );
};

const LoadingScreen: React.FC = () => (
  <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center">
    <div className="text-center">
      <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl mb-6 shadow-lg">
        <RefreshCw className="h-8 w-8 text-white animate-spin" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Loading TradingBot Pro</h2>
      <p className="text-gray-600 mb-4">Preparing your trading dashboard...</p>
      <div className="w-64 bg-gray-200 rounded-full h-2 mx-auto">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full animate-pulse" style={{width: '60%'}}></div>
      </div>
    </div>
  </div>
);

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
};

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingScreen />;
  }

  return (
    <>
      {isAuthenticated ? (
        <ProtectedRoute>
          <AuthenticatedApp />
        </ProtectedRoute>
      ) : (
        <AuthPage />
      )}
    </>
  );
};

export default App;

