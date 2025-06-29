import React, { useState, useEffect } from 'react';
import { BarChart3, DollarSign, TrendingUp, Activity, AlertCircle, RefreshCw, CheckCircle, XCircle } from 'lucide-react';

// Tipos TypeScript
interface Account {
  buying_power: string;
  cash: string;
  portfolio_value: string;
  status: string;
  trading_blocked: boolean;
  crypto_status: string;
}

interface Signal {
  id: number;
  symbol: string;
  action: string;
  quantity: number;
  status: string;
  error_message?: string;
  timestamp: string;
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
}

interface PortfolioData {
  total_positions: number;
  max_positions: number;
  remaining_slots: number;
  cash: string;
  portfolio_value: string;
  buying_power: string;
  positions: Record<string, number>;
}

// API Service
const api = {
  baseUrl: 'http://localhost:8000/api/v1',

  async get(endpoint: string) {
    const response = await fetch(`${this.baseUrl}${endpoint}`);
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response.json();
  },

  async getAccount(): Promise<Account> {
    return this.get('/account');
  },

  async getSignals(): Promise<Signal[]> {
    return this.get('/signals');
  },

  async getOrders(): Promise<Order[]> {
    return this.get('/orders');
  },

  async getPositions(): Promise<PortfolioData> {
    return this.get('/positions');
  }
};

// Utility functions
const formatCurrency = (value: string | number) => {
  const num = typeof value === 'string' ? parseFloat(value) : value;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2
  }).format(num);
};

const formatTime = (timestamp: string) => {
  return new Date(timestamp).toLocaleString();
};

// Component: Summary Cards
const SummaryCards: React.FC<{ account: Account | null; portfolio: PortfolioData | null }> = ({ account, portfolio }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center">
          <div className="p-2 bg-blue-100 rounded-lg">
            <BarChart3 className="h-6 w-6 text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Portfolio Value</p>
            <p className="text-2xl font-bold text-gray-900">
              {account ? formatCurrency(account.portfolio_value) : '--'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center">
          <div className="p-2 bg-green-100 rounded-lg">
            <DollarSign className="h-6 w-6 text-green-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Available Cash</p>
            <p className="text-2xl font-bold text-gray-900">
              {account ? formatCurrency(account.cash) : '--'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center">
          <div className="p-2 bg-purple-100 rounded-lg">
            <TrendingUp className="h-6 w-6 text-purple-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Buying Power</p>
            <p className="text-2xl font-bold text-gray-900">
              {account ? formatCurrency(account.buying_power) : '--'}
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center">
          <div className="p-2 bg-orange-100 rounded-lg">
            <Activity className="h-6 w-6 text-orange-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-600">Positions</p>
            <p className="text-2xl font-bold text-gray-900">
              {portfolio ? `${portfolio.total_positions}/${portfolio.max_positions}` : '--'}
            </p>
            <p className="text-xs text-gray-500">
              {portfolio && `${portfolio.remaining_slots} slots available`}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Component: Signals Table
const SignalsTable: React.FC<{ signals: Signal[] }> = ({ signals }) => {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="h-4 w-4 text-green-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
        return <RefreshCw className="h-4 w-4 text-yellow-600 animate-spin" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getActionBadge = (action: string) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    return action === 'buy'
      ? `${baseClasses} bg-green-100 text-green-800`
      : `${baseClasses} bg-red-100 text-red-800`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Recent Signals</h3>
      </div>
      <div className="overflow-x-auto">
        {signals.length === 0 ? (
          <div className="p-8 text-center">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No signals received yet</p>
            <p className="text-sm text-gray-400">Signals from TradingView will appear here</p>
          </div>
        ) : (
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {signals.map((signal) => (
                <tr key={signal.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(signal.status)}
                      <span className="ml-2 text-sm text-gray-900 capitalize">{signal.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-gray-900">{signal.symbol}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={getActionBadge(signal.action)}>
                      {signal.action.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {signal.quantity || 'Auto'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTime(signal.timestamp)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {signal.error_message && (
                      <div className="flex items-center text-red-600">
                        <AlertCircle className="h-4 w-4 mr-1" />
                        <span className="text-xs truncate max-w-32" title={signal.error_message}>
                          {signal.error_message}
                        </span>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Component: Orders Table
const OrdersTable: React.FC<{ orders: Order[] }> = ({ orders }) => {
  const getStatusBadge = (status: string) => {
    const baseClasses = "px-2 py-1 rounded-full text-xs font-medium";
    switch (status.toLowerCase()) {
      case 'filled':
        return `${baseClasses} bg-green-100 text-green-800`;
      case 'rejected':
      case 'canceled':
        return `${baseClasses} bg-red-100 text-red-800`;
      case 'pending_new':
      case 'new':
        return `${baseClasses} bg-blue-100 text-blue-800`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800`;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Recent Orders</h3>
      </div>
      <div className="overflow-x-auto">
        {orders.length === 0 ? (
          <div className="p-8 text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No orders executed yet</p>
            <p className="text-sm text-gray-400">Orders will appear here when signals are processed</p>
          </div>
        ) : (
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filled</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {orders.map((order) => (
                <tr key={order.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-medium text-gray-900">{order.symbol}</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={order.side === 'buy' ? 'text-green-600' : 'text-red-600'}>
                      {order.side.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {order.qty}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={getStatusBadge(order.status)}>
                      {order.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatTime(order.submitted_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {order.filled_at ? formatTime(order.filled_at) : '--'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Component: Positions Table
const PositionsTable: React.FC<{ portfolio: PortfolioData | null }> = ({ portfolio }) => {
  if (!portfolio) return null;

  return (
    <div className="bg-white rounded-lg shadow-md">
      <div className="px-6 py-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Current Positions</h3>
      </div>
      <div className="overflow-x-auto">
        {Object.keys(portfolio.positions).length === 0 ? (
          <div className="p-8 text-center">
            <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No positions currently held</p>
            <p className="text-sm text-gray-400">
              Positions will appear here when you have open trades
            </p>
          </div>
        ) : (
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Est. Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Allocation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {Object.entries(portfolio.positions).map(([symbol, quantity]) => {
                const estimatedPrice = 150; // En producción obtener precio real
                const estimatedValue = quantity * estimatedPrice;
                const totalValue = parseFloat(portfolio.portfolio_value);
                const allocation = ((estimatedValue / totalValue) * 100).toFixed(1);

                return (
                  <tr key={symbol} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">{symbol}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {quantity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {formatCurrency(estimatedValue)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${Math.min(parseFloat(allocation), 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">{allocation}%</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

// Component: System Status
const SystemStatus: React.FC<{ account: Account | null }> = ({ account }) => {
  const getStatusIndicator = (isActive: boolean) => (
    <div className={`w-3 h-3 rounded-full ${isActive ? 'bg-green-500' : 'bg-red-500'}`}></div>
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex items-center">
          {getStatusIndicator(account?.status === 'ACTIVE')}
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">Trading Account</p>
            <p className="text-xs text-gray-500">{account?.status || 'Unknown'}</p>
          </div>
        </div>

        <div className="flex items-center">
          {getStatusIndicator(!account?.trading_blocked)}
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">Trading Status</p>
            <p className="text-xs text-gray-500">
              {account?.trading_blocked ? 'Blocked' : 'Active'}
            </p>
          </div>
        </div>

        <div className="flex items-center">
          {getStatusIndicator(account?.crypto_status === 'ACTIVE')}
          <div className="ml-3">
            <p className="text-sm font-medium text-gray-900">Crypto Trading</p>
            <p className="text-xs text-gray-500">{account?.crypto_status || 'Unknown'}</p>
          </div>
        </div>
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchAllData = async () => {
    try {
      const [accountData, signalsData, ordersData, portfolioData] = await Promise.all([
        api.getAccount(),
        api.getSignals(),
        api.getOrders(),
        api.getPositions()
      ]);

      setAccount(accountData);
      setSignals(signalsData);
      setOrders(ordersData);
      setPortfolio(portfolioData);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      setError('Failed to load data. Check if your backend is running.');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Trading Bot Dashboard</h1>
              <p className="text-sm text-gray-500">
                Last updated: {lastUpdate.toLocaleTimeString()}
              </p>
            </div>

            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <div className={`w-2 h-2 rounded-full mr-2 ${account?.status === 'ACTIVE' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600">
                  {account?.status === 'ACTIVE' ? 'Live' : 'Inactive'}
                </span>
              </div>

              <button
                onClick={fetchAllData}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
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

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <SummaryCards account={account} portfolio={portfolio} />

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <SignalsTable signals={signals} />
          <OrdersTable orders={orders} />
        </div>

        {/* Full Width Sections */}
        <div className="space-y-8">
          <PositionsTable portfolio={portfolio} />
          <SystemStatus account={account} />
        </div>
      </main>
    </div>
  );
};

export default TradingDashboard;