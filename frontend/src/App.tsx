import React, { useState } from 'react';
import { BarChart3, Activity, List, Settings, Menu, X } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import SignalsPage from './pages/signals';
import OrdersPage from './pages/orders';
// Tipos para las páginas
type Page = 'dashboard' | 'signals' | 'orders' | 'settings';

// Componente de navegación
const Sidebar: React.FC<{
  currentPage: Page;
  onPageChange: (page: Page) => void;
  isOpen: boolean;
  onToggle: () => void;
}> = ({ currentPage, onPageChange, isOpen, onToggle }) => {

  const menuItems = [
    { id: 'dashboard' as Page, name: 'Dashboard', icon: BarChart3 },
    { id: 'signals' as Page, name: 'Signals', icon: Activity },
    { id: 'orders' as Page, name: 'Orders', icon: List },
    { id: 'settings' as Page, name: 'Settings', icon: Settings },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed lg:static lg:translate-x-0 inset-y-0 left-0 z-50
        w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h2 className="text-xl font-bold text-gray-800">Trading Bot</h2>
            <button
              onClick={onToggle}
              className="lg:hidden p-2 rounded-md text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
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
                        w-full flex items-center px-4 py-3 text-left rounded-lg transition-colors
                        ${isActive
                          ? 'bg-blue-100 text-blue-700 border-r-2 border-blue-700'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-800'
                        }
                      `}
                    >
                      <Icon className="h-5 w-5 mr-3" />
                      {item.name}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Footer */}
          <div className="p-4 border-t">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
              <span className="text-sm text-gray-600">API Connected</span>
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

// Componente temporal para páginas no implementadas
const ComingSoon: React.FC<{ title: string }> = ({ title }) => (
  <div className="flex-1 p-8">
    <div className="text-center py-20">
      <div className="mx-auto h-24 w-24 text-gray-400 mb-4">
        <Activity className="h-full w-full" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500">This page is coming soon...</p>
    </div>
  </div>
);

// Componente principal App
const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard />;
      case 'signals':
        return <SignalsPage title="Signals Page" />;
      case 'orders':
        return <OrdersPage title="Orders Page" />;
      case 'settings':
        return <ComingSoon title="Settings Page" />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex">
      {/* Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onPageChange={setCurrentPage}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top bar for mobile */}
        <div className="lg:hidden bg-white shadow-sm p-4 flex items-center justify-between">
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-md text-gray-400 hover:text-gray-600"
          >
            <Menu className="h-6 w-6" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900">
            {currentPage.charAt(0).toUpperCase() + currentPage.slice(1)}
          </h1>
          <div></div> {/* Spacer para centrar el título */}
        </div>

        {/* Page content */}
        <main className="flex-1">
          {renderCurrentPage()}
        </main>
      </div>
    </div>
  );
};

export default App;