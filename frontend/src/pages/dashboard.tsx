import React, { useState, useEffect } from 'react';
import { connectWebSocket } from '../services/ws';
import {
  BarChart3, DollarSign, TrendingUp, Activity, AlertCircle, RefreshCw,
  ArrowUp, ArrowDown, PieChart, Target, Briefcase,
  Clock, Shield, Zap
} from 'lucide-react';
import EquityCurveChart from '../components/EquityCurveChart';
import type { EquityPoint } from '../components/EquityCurveChart';
import WinRateSpeedometer from '../components/winrate_speedometer';

// Tipos TypeScript
interface Account {
  buying_power: string;
  cash: string;
  portfolio_value: string;
  status: string;
  trading_blocked: boolean;
  crypto_status: string;
  user?: string;
}

interface Signal {
  id: number;
  symbol: string;
  action: string;
  quantity: number;
  status: string;
  error_message?: string;
  timestamp: string;
  strategy_id?: string;
  reason?: string;
  confidence?: number;
}

interface Order {
  id: string;
  symbol: string;
  qty: string;
  side: string;
  status: string;
  submitted_at: string;
  filled_at?: string;
  rejected_reason?: string;
  user?: string;
}

interface Trade {
  id: number;
  strategy_id: string;
  symbol: string;
  action: string;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  status: string;
  opened_at: string;
  closed_at: string | null;
  pnl: number | null;
}

interface PortfolioData {
  total_positions: number;
  max_positions: number;
  remaining_slots: number;
  cash: string;
  portfolio_value: string;
  buying_power: string;
  positions: Record<string, number>;
  user?: string;
}

// Función para obtener el token del localStorage
const getAuthToken = (): string | null => {
  return localStorage.getItem('token');
};

// Función para hacer requests autenticados
const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();

  if (!token) {
    console.error('❌ No authentication token found');
    throw new Error('No authentication token available');
  }

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers,
  };

  console.log('🔐 Making authenticated request to:', url);

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    console.log('📨 Response status:', response.status);

    // Si el token es inválido, limpiar y recargar
    if (response.status === 401) {
      console.error('❌ Token expired or invalid - clearing localStorage');
      localStorage.removeItem('token');
      window.location.reload();
      throw new Error('Authentication failed - token expired');
    }

    if (response.status === 403) {
      console.error('❌ Access forbidden - insufficient permissions');
      const errorText = await response.text();
      console.error('📋 Error details:', errorText);
      throw new Error('Access forbidden - insufficient permissions');
    }

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ API Error:', response.status, errorText);
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    return response;
  } catch (error) {
    console.error('💥 Network error:', error);
    throw error;
  }
};

// API Service con autenticación
const api = {
  baseUrl: '/api/v1',

  async getAccount(): Promise<Account | null> {
    console.log('🔄 Fetching account data...');
    const response = await authenticatedFetch(`${this.baseUrl}/account`);
    const data = await response.json();
    console.log('✅ Account data received:', data);
    if (data.error || typeof data.cash === 'undefined') {
      console.warn('⚠️ Invalid account data, portfolio may be disconnected');
      return null;
    }
    return data;
  },

  async getSignals(): Promise<Signal[]> {
    console.log('🔄 Fetching signals data...');
    const response = await authenticatedFetch(`${this.baseUrl}/signals`);
    const data = await response.json();
    console.log('✅ Signals data received:', data);
    return Array.isArray(data) ? data : [];
  },

  async getOrders(): Promise<Order[]> {
    console.log('🔄 Fetching orders data...');
    const response = await authenticatedFetch(`${this.baseUrl}/orders`);
    const data = await response.json();
    console.log('✅ Orders data received:', data);
    return Array.isArray(data.orders) ? data.orders : [];
  },

  async getTrades(): Promise<Trade[]> {
    const response = await authenticatedFetch(`${this.baseUrl}/trades`);
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  },

  async getPositions(): Promise<PortfolioData | null> {
    console.log('🔄 Fetching positions data...');
    const response = await authenticatedFetch(`${this.baseUrl}/positions`);
    const data = await response.json();
    console.log('✅ Positions data received:', data);
    if (data.error || typeof data.total_positions === 'undefined') {
      console.warn('⚠️ Invalid portfolio data, portfolio may be disconnected');
      return null;
    }
    return data;
  },

  async getEquityCurve(): Promise<EquityPoint[]> {
    const response = await authenticatedFetch(`${this.baseUrl}/trades/equity-curve`);
    const data = await response.json();
    return Array.isArray(data) ? data : [];
  }
};

// Utility functions
const formatCurrency = (value: string | number | null | undefined) => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (num === null || num === undefined || Number.isNaN(num)) {
    return '--';
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(num);
};


// Component: Enhanced Stats Card
const StatsCard: React.FC<{
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ComponentType<any>;
  gradient: string;
  trend?: { value: string; positive: boolean };
  loading?: boolean;
}> = ({ title, value, subtitle, icon: Icon, gradient, trend, loading = false }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all duration-300 group">
    <div className="flex items-center justify-between">
      <div className="flex-1">
        <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
        {loading ? (
          <div className="h-8 bg-gray-200 rounded animate-pulse mb-2"></div>
        ) : (
          <p className="text-3xl font-bold text-gray-900 mb-1">{value}</p>
        )}
        {subtitle && (
          <p className="text-xs text-gray-500">{subtitle}</p>
        )}
        {trend && (
          <div className={`flex items-center mt-2 text-sm font-medium ${
            trend.positive ? 'text-emerald-600' : 'text-red-500'
          }`}>
            {trend.positive ?
              <ArrowUp className="h-4 w-4 mr-1" /> :
              <ArrowDown className="h-4 w-4 mr-1" />
            }
            {trend.value}
          </div>
        )}
      </div>
      <div className={`p-4 rounded-2xl ${gradient} group-hover:scale-110 transition-transform duration-300`}>
        <Icon className="h-7 w-7 text-white" />
      </div>
    </div>
  </div>
);

// Component: Recent Activity Item
const ActivityItem: React.FC<{
  type: 'signal' | 'order';
  data: Signal | Order;
}> = ({ type, data }) => {
  if (type === 'signal') {
    const signal = data as Signal;
    return (
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors duration-200">
        <div className="flex items-center">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            signal.action === 'buy' ? 'bg-emerald-100' : 'bg-red-100'
          }`}>
            {signal.action === 'buy' ?
              <TrendingUp className="h-5 w-5 text-emerald-600" /> :
              <TrendingUp className="h-5 w-5 text-red-600 rotate-180" />
            }
          </div>
          <div className="ml-3">
            <p className="font-semibold text-gray-900">{signal.symbol}</p>
            <p className="text-sm text-gray-600">{signal.strategy_id || 'Strategy'}</p>
          </div>
        </div>
        <div className="text-right">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            signal.status === 'processed' ? 'bg-emerald-100 text-emerald-800' :
            signal.status === 'error' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {signal.status}
          </span>
          {signal.confidence && (
            <p className="text-xs text-gray-500 mt-1">{signal.confidence}% confidence</p>
          )}
        </div>
      </div>
    );
  } else {
    const order = data as Order;
    return (
      <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors duration-200">
        <div className="flex items-center">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
            order.side === 'buy' ? 'bg-blue-100' : 'bg-purple-100'
          }`}>
            {order.side === 'buy' ?
              <TrendingUp className="h-5 w-5 text-blue-600" /> :
              <TrendingUp className="h-5 w-5 text-purple-600 rotate-180" />
            }
          </div>
          <div className="ml-3">
            <p className="font-semibold text-gray-900">{order.symbol}</p>
            <p className="text-sm text-gray-600">{order.qty} shares</p>
          </div>
        </div>
        <div className="text-right">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${
            order.status === 'filled' ? 'bg-emerald-100 text-emerald-800' :
            order.status === 'rejected' ? 'bg-red-100 text-red-800' :
            'bg-blue-100 text-blue-800'
          }`}>
            {order.status}
          </span>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(order.submitted_at).toLocaleTimeString()}
          </p>
        </div>
      </div>
    );
  }
};

// Component: System Status
const SystemStatus: React.FC<{ account: Account | null }> = ({ account }) => {
  const statusItems = [
    {
      name: 'Trading Account',
      status: account?.status === 'ACTIVE',
      description: account?.status || 'Unknown',
      icon: Briefcase
    },
    {
      name: 'Trading Engine',
      status: !account?.trading_blocked,
      description: account?.trading_blocked ? 'Blocked' : 'Active',
      icon: Zap
    },
    {
      name: 'Crypto Trading',
      status: account?.crypto_status === 'ACTIVE',
      description: account?.crypto_status || 'Unknown',
      icon: Shield
    }
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
        <div className="flex items-center text-emerald-600">
          <div className="w-2 h-2 bg-emerald-500 rounded-full mr-2 animate-pulse"></div>
          <span className="text-sm font-medium">All Systems Operational</span>
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {statusItems.map((item, index) => (
          <div key={index} className="flex items-center">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center mr-4 ${
              item.status ? 'bg-emerald-100' : 'bg-red-100'
            }`}>
              <item.icon className={`h-6 w-6 ${
                item.status ? 'text-emerald-600' : 'text-red-600'
              }`} />
            </div>
            <div>
              <p className="font-semibold text-gray-900">{item.name}</p>
              <p className={`text-sm ${
                item.status ? 'text-emerald-600' : 'text-red-600'
              }`}>
                {item.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Main Dashboard Component
const TradingDashboard: React.FC = () => {
  const [account, setAccount] = useState<Account | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [winRate, setWinRate] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchAllData = async () => {
    try {
      console.log('🔄 Fetching dashboard data with authentication...');

      // Verificar que tenemos token
      const token = getAuthToken();
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const [accountData, signalsData, ordersData, portfolioData, equityData, tradesData] = await Promise.all([
        api.getAccount(),
        api.getSignals(),
        api.getOrders(),
        api.getPositions(),
        api.getEquityCurve(),
        api.getTrades()
      ]);

      console.log('✅ All data fetched successfully');

      setAccount(accountData);
      setSignals(signalsData);
      setOrders(ordersData);
      setPortfolio(portfolioData);
      setEquityCurve(equityData);
      setTrades(tradesData);

      const closedTrades = tradesData.filter((t) => t.status === 'closed');
      const winningTrades = closedTrades.filter((t) => t.pnl !== null && t.pnl > 0);
      setWinRate(closedTrades.length ? (winningTrades.length / closedTrades.length) * 100 : 0);
      setError(null);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('❌ Dashboard error:', err);
      setError(err.message || 'Failed to load data. Please check your authentication.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const ws = connectWebSocket({
      onSignal: (sig) => setSignals((prev) => [sig, ...prev]),
      onOrder: (order) => setOrders((prev) => [order, ...prev]),
      onTrade: () => fetchAllData(),
      onAccountUpdate: (data) => {
        setAccount((prev) => prev ? { ...prev, ...data } : data);
        setPortfolio((prev) =>
          prev
            ? {
                ...prev,
                cash: data.cash,
                buying_power: data.buying_power,
                portfolio_value: data.portfolio_value,
                total_positions: data.total_positions,
                remaining_slots: Math.max(0, prev.max_positions - data.total_positions)
              }
            : prev
        );
        setLastUpdate(new Date());
      },
    });
    return () => ws.close();
  }, []);

  // Calculate portfolio performance
  const portfolioChange = account ? {
    value: '+2.5%',
    positive: true
  } : undefined;


  if (loading) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600 font-medium">Loading your dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
            <p className="text-gray-600">Welcome back to your trading command center</p>
          </div>
          <div className="mt-4 sm:mt-0 flex items-center space-x-4">
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="h-4 w-4 mr-1" />
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
            <button
              onClick={fetchAllData}
              className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-200 shadow-sm"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={fetchAllData}
                className="mt-2 text-sm text-red-600 underline hover:text-red-500"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <a href="/portfolio-monitor.html" target="_blank" rel="noopener noreferrer">
          <StatsCard
            title="Portfolio Value"
            value={account ? formatCurrency(account.portfolio_value) : '--'}
            icon={PieChart}
            gradient="bg-gradient-to-r from-blue-500 to-indigo-500"
            trend={portfolioChange}
            loading={loading}
          />
        </a>
        <StatsCard
          title="Available Cash"
          value={account ? formatCurrency(account.cash) : '--'}
          icon={DollarSign}
          gradient="bg-gradient-to-r from-emerald-500 to-green-500"
          loading={loading}
        />
        <StatsCard
          title="Active Positions"
          value={portfolio ? `${portfolio.total_positions}/${portfolio.max_positions}` : '--'}
          subtitle={portfolio ? `${portfolio.remaining_slots} slots available` : ''}
          icon={Target}
          gradient="bg-gradient-to-r from-orange-500 to-red-500"
          loading={loading}
        />
      </div>



      {/* Activity Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Recent Signals */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Recent Signals</h3>
            <span className="text-sm text-gray-500">{signals.length} total</span>
          </div>
          <div className="space-y-4">
            {signals.length === 0 ? (
              <div className="text-center py-8">
                <Activity className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No signals received yet</p>
                <p className="text-sm text-gray-400">Signals from TradingView will appear here</p>
              </div>
            ) : (
              signals.slice(0, 3).map((signal) => (
                <ActivityItem key={signal.id} type="signal" data={signal} />
              ))
            )}
          </div>
        </div>

        {/* Win Rate */}
        <WinRateSpeedometer winRate={winRate} totalTrades={trades.filter((t) => t.status === 'closed').length} />
      </div>

      {/* Equity Curve */}
      <div className="mb-8">
        <EquityCurveChart data={equityCurve} />
      </div>

      {/* System Status */}
      <SystemStatus account={account} />
    </div>
  );
};

export default TradingDashboard;