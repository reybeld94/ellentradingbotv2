import React, { useState, useEffect } from 'react';
import {
  BarChart3, Activity, List, Settings, Menu, X, LogOut, User,
  Home, Briefcase, Bell, Search, ChevronRight, Zap, Shield,
  TrendingUp, Clock, RefreshCw
} from 'lucide-react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthPage from './pages/AuthPage';
import ProtectedRoute from './components/auth/ProtectedRoute';
import Dashboard from './pages/Dashboard';
import SignalsPage from './pages/signals';
import OrdersPage from './pages/orders';
import Profile from './pages/Profile';
import TradesPage from './pages/trades';

// Tipos para las páginas
type Page = 'dashboard' | 'signals' | 'orders' | 'trades' |'settings';

// Componente de navegación mejorado
const Sidebar: React.FC<{
  currentPage: Page;
  onPageChange: (page: Page) => void;
  isOpen: boolean;
  onToggle: () => void;
  pendingSignalsCount: number; // ✅ NUEVO: Pasar el count como prop
}> = ({ currentPage, onPageChange, isOpen, onToggle, pendingSignalsCount }) => {
  const { user, logout } = useAuth();

  // ✅ ACTUALIZADO: menuItems con badge dinámico
  const menuItems = [
    {
      id: 'dashboard' as Page,
      name: 'Dashboard',
      icon: Home,
      description: 'Overview & analytics',
      badge: null
    },
    {
      id: 'signals' as Page,
      name: 'Signals',
      icon: Activity,
      description: 'Trading signals',
      badge: pendingSignalsCount > 0 ? pendingSignalsCount.toString() : null // ✅ DINÁMICO!
    },
    {
      id: 'orders' as Page,
      name: 'Orders',
      icon: List,
      description: 'Order history',
      badge: null
    },
    {
  id: 'trades' as Page,
  name: 'Trades',
  icon: BarChart3,
  description: 'Trade history',
  badge: null
  },
    {
      id: 'settings' as Page,
      name: 'Settings',
      icon: Settings,
      description: 'Account preferences',
      badge: null
    },
  ];

  const handleLogout = () => {
    logout();
    if (window.innerWidth < 1024) {
      onToggle();
    }
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden transition-opacity duration-300"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:static lg:translate-x-0 inset-y-0 left-0 z-50
        w-80 bg-white shadow-2xl transform transition-all duration-300 ease-in-out border-r border-gray-100
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mr-4 shadow-lg">
                  <Briefcase className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">TradingBot</h2>
                  <p className="text-sm text-blue-600 font-medium">Professional</p>
                </div>
              </div>
              <button
                onClick={onToggle}
                className="lg:hidden p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-white/50 transition-all duration-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* User Profile Card */}
          <div className="p-6 border-b border-gray-100">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-4 border border-blue-100">
              <div className="flex items-center">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                  <User className="h-6 w-6 text-white" />
                </div>
                <div className="ml-3 flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900 truncate">
                    {user?.full_name || user?.username}
                  </p>
                  <p className="text-xs text-gray-600 truncate">{user?.email}</p>
                  <div className="flex items-center mt-2 space-x-2">
                    {user?.is_admin && (
                      <span className="inline-flex px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
                        Admin
                      </span>
                    )}
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-emerald-500 rounded-full mr-1"></div>
                      <span className="text-xs text-emerald-600 font-medium">Active</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="p-6 border-b border-gray-100">
            <h3 className="text-sm font-semibold text-gray-700 mb-3">Quick Stats</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-100">
                <div className="flex items-center">
                  <TrendingUp className="h-4 w-4 text-emerald-600 mr-2" />
                  <div>
                    <p className="text-xs text-emerald-600 font-medium">Portfolio</p>
                    <p className="text-sm font-bold text-emerald-700">+2.5%</p>
                  </div>
                </div>
              </div>
              <div className="bg-blue-50 rounded-xl p-3 border border-blue-100">
                <div className="flex items-center">
                  <Zap className="h-4 w-4 text-blue-600 mr-2" />
                  <div>
                    <p className="text-xs text-blue-600 font-medium">Signals</p>
                    <p className="text-sm font-bold text-blue-700">
                      {pendingSignalsCount > 0 ? `${pendingSignalsCount} Pending` : 'All Clear'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4">
            <ul className="space-y-2">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.id;

                return (
                  <li key={item.id}>
                    <button
                      onClick={() => {
                        onPageChange(item.id);
                        // En mobile, cerrar sidebar al seleccionar
                        if (window.innerWidth < 1024) {
                          onToggle();
                        }
                      }}
                      className={`
                        w-full flex items-center px-4 py-4 text-left rounded-2xl transition-all duration-200 group
                        ${isActive
                          ? 'bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 shadow-sm border border-blue-100'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-800'
                        }
                      `}
                    >
                      <div className={`p-2 rounded-xl mr-3 ${
                        isActive ? 'bg-blue-100' : 'bg-gray-100 group-hover:bg-gray-200'
                      }`}>
                        <Icon className={`h-5 w-5 ${isActive ? 'text-blue-600' : 'text-gray-500'}`} />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{item.name}</p>
                        <p className="text-xs text-gray-500">{item.description}</p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {item.badge && (
                          <span className="bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
                            {item.badge}
                          </span>
                        )}
                        {isActive && (
                          <ChevronRight className="h-4 w-4 text-blue-600" />
                        )}
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* System Status */}
          <div className="p-4 border-t border-gray-100">
            <div className="bg-emerald-50 rounded-xl p-3 border border-emerald-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-emerald-100 rounded-lg flex items-center justify-center mr-3">
                    <Shield className="h-4 w-4 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-emerald-700">System Status</p>
                    <p className="text-xs text-emerald-600">All systems operational</p>
                  </div>
                </div>
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              </div>
            </div>
          </div>

          {/* Logout Button */}
          <div className="p-4 border-t border-gray-100">
            <button
              onClick={handleLogout}
              className="w-full flex items-center px-4 py-3 text-left rounded-2xl text-red-600 hover:bg-red-50 transition-all duration-200 group"
            >
              <div className="p-2 rounded-xl mr-3 bg-red-100 group-hover:bg-red-200">
                <LogOut className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="font-semibold text-sm">Sign Out</p>
                <p className="text-xs text-red-500">Logout from account</p>
              </div>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// Header mejorado para mobile
const MobileHeader: React.FC<{
  currentPage: Page;
  onToggleSidebar: () => void;
  user: any;
}> = ({ currentPage, onToggleSidebar, user }) => {
  const pageNames = {
    dashboard: 'Dashboard',
    signals: 'Signals',
    orders: 'Orders',
    settings: 'Settings'
  };

  return (
    <div className="lg:hidden bg-white shadow-sm border-b border-gray-100 sticky top-0 z-30">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center">
          <button
            onClick={onToggleSidebar}
            className="p-3 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200 mr-3"
          >
            <Menu className="h-6 w-6" />
          </button>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center mr-3">
              <Briefcase className="h-4 w-4 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">{pageNames[currentPage]}</h1>
              <p className="text-xs text-gray-500">TradingBot Pro</p>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button className="p-2 rounded-xl text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all duration-200">
            <Bell className="h-5 w-5" />
          </button>
          <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
            <User className="h-4 w-4 text-white" />
          </div>
        </div>
      </div>
    </div>
  );
};

// Componente temporal para páginas no implementadas
const ComingSoon: React.FC<{ title: string }> = ({ title }) => (
  <div className="flex-1 p-8 bg-gray-50 min-h-screen">
    <div className="text-center py-20">
      <div className="mx-auto h-24 w-24 text-gray-400 mb-4">
        <Activity className="h-full w-full" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500">This page is coming soon...</p>
    </div>
  </div>
);

// Componente principal del dashboard autenticado
const AuthenticatedApp: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // ✅ NUEVO: Estado para contar signals pendientes
  const [pendingSignalsCount, setPendingSignalsCount] = useState(0);
  const { user } = useAuth();

  // ✅ NUEVO: Función para obtener el count de signals
  useEffect(() => {
    const fetchSignalsCount = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;

        const response = await fetch('http://localhost:8000/api/v1/signals', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          const signals = Array.isArray(data) ? data : [];
          // Contar solo signals pendientes o con errores (que necesitan atención)
          const pendingCount = signals.filter(s =>
            s.status === 'pending' || s.status === 'error'
          ).length;
          setPendingSignalsCount(pendingCount);

          console.log(`📊 Signals count updated: ${pendingCount} pending/error signals`);
        }
      } catch (error) {
        console.error('Error fetching signals count:', error);
        setPendingSignalsCount(0);
      }
    };

    fetchSignalsCount();
    // Actualizar cada 30 segundos
    const interval = setInterval(fetchSignalsCount, 30000);
    return () => clearInterval(interval);
  }, []);

  // ✅ NUEVO: También actualizar el count cuando cambie de página a signals
  useEffect(() => {
    if (currentPage === 'signals') {
      // Resetear el count cuando el usuario ve la página de signals
      // (opcional: podrías mantenerlo o hacer un refetch)
    }
  }, [currentPage]);

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
      case 'settings':
        return <Profile />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        pendingSignalsCount={pendingSignalsCount} // ✅ PASAR el count como prop
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Mobile Header */}
        <MobileHeader
          currentPage={currentPage}
          onToggleSidebar={() => setSidebarOpen(true)}
          user={user}
        />

        {/* Page content */}
        <main className="flex-1">
          {renderCurrentPage()}
        </main>
      </div>
    </div>
  );
};

// Loading component mejorado
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

// Componente principal App con AuthProvider
const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

// Contenido de la app que puede acceder al contexto de auth
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