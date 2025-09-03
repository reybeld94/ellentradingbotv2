import React, { useState, useEffect } from 'react';
import {
  Bell, Search, Menu, Settings,
  ChevronDown, User, HelpCircle, MessageSquare
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../services/api';

const MarketStatusIndicator: React.FC = () => {
  const [marketStatus, setMarketStatus] = useState<{ isOpen: boolean; status: string }>(
    {
      isOpen: false,
      status: 'unknown',
    }
  );

  const fetchMarketStatus = async () => {
    try {
      const response = await api.trading.getMarketHours('SPY');
      if (response.ok) {
        const data = await response.json();
        setMarketStatus({
          isOpen: data.is_open || false,
          status: data.status || 'unknown',
        });
      }
    } catch (error) {
      console.error('Error fetching market status:', error);
      setMarketStatus({ isOpen: false, status: 'unknown' });
    }
  };

  useEffect(() => {
    fetchMarketStatus();
    const interval = setInterval(fetchMarketStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const getStatusStyles = () => {
    if (marketStatus.isOpen) {
      return {
        bg: 'bg-success-50',
        text: 'text-success-700',
        border: 'border-success-200',
        dot: 'bg-success-500',
        label: 'Market Open',
      };
    } else if (marketStatus.status === 'closed') {
      return {
        bg: 'bg-error-50',
        text: 'text-error-700',
        border: 'border-error-200',
        dot: 'bg-error-500',
        label: 'Market Closed',
      };
    } else {
      return {
        bg: 'bg-yellow-50',
        text: 'text-yellow-700',
        border: 'border-yellow-200',
        dot: 'bg-yellow-500',
        label: 'Market Status Unknown',
      };
    }
  };

  const styles = getStatusStyles();

  return (
    <div
      className={`hidden sm:flex items-center px-3 py-1.5 ${styles.bg} ${styles.text} rounded-lg border ${styles.border}`}
    >
      <div
        className={`w-2 h-2 ${styles.dot} rounded-full mr-2 ${
          marketStatus.isOpen ? 'animate-pulse' : ''
        }`}
      ></div>
      <span className="text-xs font-medium">{styles.label}</span>
    </div>
  );
};

interface HeaderProps {
  currentPage: string;
  onToggleMobileSidebar: () => void;
  isCollapsed?: boolean;
}

const Header: React.FC<HeaderProps> = ({
  currentPage,
  onToggleMobileSidebar,
  isCollapsed = false
}) => {
  const { user } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [notifications] = useState(3); // Mock notifications

  const pageNames: Record<string, string> = {
    dashboard: 'Dashboard',
    signals: 'Trading Signals',
    orders: 'Order Management',
    trades: 'Trade History',
    strategies: 'Strategy Manager',
    risk: 'Risk Dashboard',
    analytics: 'Portfolio Analytics',
    settings: 'Account Settings'
  };

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-40 backdrop-blur-sm bg-white/95">
      <div className="flex items-center justify-between">
        {/* Left Side */}
        <div className="flex items-center space-x-4">
          {/* Mobile Menu Button */}
          <button
            onClick={onToggleMobileSidebar}
            className="lg:hidden p-2 rounded-xl hover:bg-slate-100 text-slate-600 transition-colors duration-200"
          >
            <Menu className="h-5 w-5" />
          </button>

          {/* Page Title */}
          <div className={`${isCollapsed ? 'block' : 'hidden lg:block'}`}>
            <h1 className="text-xl font-bold text-slate-900">
              {pageNames[currentPage] || 'TradingBot Pro'}
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Real-time trading management platform
            </p>
          </div>
        </div>

        {/* Center - Search (Desktop) */}
        <div className="hidden md:flex flex-1 max-w-md mx-8">
          <div className="relative w-full">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search trades, symbols, strategies..."
              className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-xl bg-slate-50 text-sm
                       focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:bg-white
                       transition-all duration-200"
            />
          </div>
        </div>

        {/* Right Side */}
        <div className="flex items-center space-x-3">
          {/* Quick Actions */}
          <div className="hidden sm:flex items-center space-x-1">
            <button className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 transition-colors duration-200">
              <HelpCircle className="h-5 w-5" />
            </button>
            <button className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 transition-colors duration-200">
              <MessageSquare className="h-5 w-5" />
            </button>
          </div>

          {/* Notifications */}
          <div className="relative">
            <button className="p-2 rounded-xl hover:bg-slate-100 text-slate-600 transition-colors duration-200 relative">
              <Bell className="h-5 w-5" />
              {notifications > 0 && (
                <span className="absolute -top-1 -right-1 bg-primary-600 text-white text-xs font-semibold
                               min-w-[18px] h-[18px] rounded-full flex items-center justify-center border-2 border-white">
                  {notifications > 9 ? '9+' : notifications}
                </span>
              )}
            </button>
          </div>

          {/* Market Status Indicator */}
          <MarketStatusIndicator />

          {/* User Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-3 p-2 rounded-xl hover:bg-slate-100 transition-colors duration-200"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-semibold text-sm">
                  {user?.username?.[0]?.toUpperCase() || 'U'}
                </span>
              </div>
              <div className="hidden md:block text-left">
                <p className="text-sm font-semibold text-slate-900">{user?.username}</p>
                <p className="text-xs text-slate-500">
                  {user?.is_admin ? 'Administrator' : 'Trader'}
                </p>
              </div>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </button>

            {/* User Dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-strong border border-slate-200 z-50">
                <div className="p-3 border-b border-slate-100">
                  <p className="font-semibold text-slate-900">{user?.full_name || user?.username}</p>
                  <p className="text-sm text-slate-500">{user?.email}</p>
                </div>
                <div className="py-2">
                  <button className="w-full flex items-center px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">
                    <User className="h-4 w-4 mr-3 text-slate-400" />
                    Profile Settings
                  </button>
                  <button className="w-full flex items-center px-4 py-2 text-sm text-slate-700 hover:bg-slate-50">
                    <Settings className="h-4 w-4 mr-3 text-slate-400" />
                    Preferences
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;

