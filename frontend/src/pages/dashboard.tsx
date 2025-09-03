import React, { useState, useEffect } from 'react';
import {
  DollarSign, TrendingUp, TrendingDown, Activity, Target,
  BarChart3, Eye, EyeOff, RefreshCw
} from 'lucide-react';
import MetricCard from '../components/dashboard/MetricCard';
import AlpacaStyleChart from '../components/dashboard/AlpacaStyleChart';
import RecentActivity from '../components/dashboard/RecentActivity';
import QuickActions from '../components/dashboard/QuickActions';
import { api } from '../services/api';

interface AccountData {
  cash: number;
  portfolio_value: number;
  buying_power: number;
  day_trade_buying_power: number;
  day_change: number;
}

interface Position {
  symbol: string;
  quantity: number;
  market_value: number;
  unrealized_pl: number;
  unrealized_plpc: number;
  cost_basis: number;
  avg_entry_price: number;
  current_price: number;
}

interface ActivityItem {
  id: string;
  type: 'trade' | 'signal' | 'order' | 'alert';
  symbol: string;
  action: 'BUY' | 'SELL';
  status: 'success' | 'pending' | 'error' | 'warning';
  amount?: number;
  price?: number;
  quantity?: number;
  timestamp: string;
  description: string;
}

const Dashboard: React.FC = () => {
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [showValues, setShowValues] = useState(true);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [accountRes, positionsRes, signalsRes, ordersRes] = await Promise.all([
        api.trading.getAccount(),
        api.trading.getPositions(),
        api.trading.getSignals(),
        api.trading.getOrders()
      ]);

      const accountJson = await accountRes.json();
      setAccountData({
        cash: parseFloat(accountJson.cash) || 0,
        portfolio_value: parseFloat(accountJson.portfolio_value) || 0,
        buying_power: parseFloat(accountJson.buying_power) || 0,
        day_trade_buying_power: parseFloat(accountJson.day_trade_buying_power) || 0,
        day_change: parseFloat(accountJson.day_change) || 0,
      });

      const positionsJson = await positionsRes.json();
      let parsedPositions: Position[] = [];
      if (Array.isArray(positionsJson)) {
        parsedPositions = positionsJson as Position[];
      } else if (Array.isArray(positionsJson.positions)) {
        parsedPositions = positionsJson.positions as Position[];
      } else if (positionsJson.positions && typeof positionsJson.positions === 'object') {
        parsedPositions = Object.entries(positionsJson.positions).map(([symbol, quantity]) => ({
          symbol,
          quantity: Number(quantity),
          market_value: 0,
          unrealized_pl: 0,
          unrealized_plpc: 0,
          cost_basis: 0,
          avg_entry_price: 0,
          current_price: 0,
        }));
      }
      setPositions(parsedPositions.slice(0, 5));


      const signalsJson = await signalsRes.json();
      const ordersJson = await ordersRes.json();

      const signalActivities: ActivityItem[] = Array.isArray(signalsJson)
        ? signalsJson.slice(0, 3).map((sig: any) => ({
            id: `signal-${sig.id}`,
            type: 'signal',
            symbol: sig.symbol,
            action: (sig.action || 'BUY').toUpperCase(),
            status:
              sig.status === 'processed'
                ? 'success'
                : sig.status === 'error'
                ? 'error'
                : sig.status === 'canceled'
                ? 'warning'
                : 'pending',
            quantity: sig.quantity,
            timestamp: sig.timestamp,
            description: `Signal ${sig.status}`,
          }))
        : [];

      const orderActivities: ActivityItem[] = Array.isArray(ordersJson?.orders)
        ? ordersJson.orders.slice(0, 2).map((ord: any) => ({
            id: `order-${ord.id}`,
            type: 'order',
            symbol: ord.symbol,
            action: (ord.side || 'buy').toUpperCase(),
            status:
              ord.status === 'filled'
                ? 'success'
                : ord.status === 'rejected'
                ? 'error'
                : ord.status === 'canceled'
                ? 'warning'
                : 'pending',
            quantity: parseFloat(ord.filled_qty || ord.qty),
            price: parseFloat(ord.filled_avg_price),
            amount:
              parseFloat(ord.filled_avg_price || 0) *
              parseFloat(ord.filled_qty || ord.qty || 0),
            timestamp: ord.submitted_at,
            description: `Order ${ord.status}`,
          }))
        : [];

      const combinedActivities = [...signalActivities, ...orderActivities]
        .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
        .slice(0, 5);
      setActivities(combinedActivities);

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError(error instanceof Error ? error.message : 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number | null | undefined) => {
    if (!showValues) return '••••••';
    if (value == null || isNaN(value)) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Math.abs(value));
  };

  const totalValue = accountData?.portfolio_value || 0;
  const dayChange = accountData
    ? accountData.day_change > 0
      ? 'positive'
      : accountData.day_change < 0
      ? 'negative'
      : 'neutral'
    : 'neutral';
  const dayChangeAmount = accountData?.day_change ?? 0;

  const handleQuickAction = (action: string) => {
    switch (action) {
      case 'new-strategy':
        // Navigate to strategies page
        break;
      case 'view-signals':
        // Navigate to signals page
        break;
      case 'analytics':
        // Navigate to analytics page
        break;
      case 'risk-check':
        // Navigate to risk page
        break;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <BarChart3 className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Dashboard</h2>
          <p className="text-slate-600">Preparing your trading insights...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Trading Dashboard</h1>
            <p className="text-slate-600 mt-1">
              Welcome back! Here's what's happening with your portfolio.
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowValues(!showValues)}
              className="btn-ghost"
            >
              {showValues ? <EyeOff className="w-4 h-4 mr-2" /> : <Eye className="w-4 h-4 mr-2" />}
              {showValues ? 'Hide' : 'Show'} Values
            </button>
            <button
              onClick={fetchDashboardData}
              className="btn-secondary"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
        {error && (
          <div className="bg-error-50 text-error-700 border border-error-200 p-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Portfolio Value"
            value={formatCurrency(totalValue)}
            change={{
              value: `${dayChangeAmount >= 0 ? '+' : ''}${formatCurrency(Math.abs(dayChangeAmount))}`,
              type: dayChange as 'positive' | 'negative' | 'neutral',
              period: 'Today'
            }}
            icon={DollarSign}
            loading={loading}
          />
          <MetricCard
            title="Available Cash"
            value={formatCurrency(accountData?.cash)}
            icon={TrendingUp}
            loading={loading}
          />
          <MetricCard
            title="Active Positions"
            value={positions.length.toString()}
            change={{
              value: `${positions.filter(p => p.unrealized_pl > 0).length} profitable`,
              type: 'neutral',
              period: 'Current'
            }}
            icon={Activity}
            loading={loading}
          />
          <MetricCard
            title="Buying Power"
            value={formatCurrency(accountData?.buying_power)}
            icon={Target}
            loading={loading}
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Portfolio Chart - Takes 2 columns on large screens */}
          <div className="lg:col-span-2">
            <AlpacaStyleChart loading={loading} />
          </div>

          {/* Quick Actions */}
          <div>
            <QuickActions onAction={handleQuickAction} />
          </div>
        </div>

        {/* Bottom Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <RecentActivity activities={activities} loading={loading} />

          {/* Top Positions */}
          <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-slate-900">Top Positions</h3>
              <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
                View All
              </button>
            </div>

            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <div key={i} className="flex items-center space-x-4 animate-pulse">
                    <div className="w-10 h-10 bg-slate-200 rounded-xl"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                      <div className="h-3 bg-slate-200 rounded w-1/2"></div>
                    </div>
                    <div className="h-4 bg-slate-200 rounded w-16"></div>
                  </div>
                ))}
              </div>
            ) : positions.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="h-8 w-8 text-slate-400" />
                </div>
                <p className="text-slate-500">No open positions</p>
                <p className="text-sm text-slate-400 mt-1">
                  Your positions will appear here once you start trading
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {positions.slice(0, 5).map((position) => {
                  const isProfit = position.unrealized_pl >= 0;
                  const percentChange = position.unrealized_plpc || 0;
                  
                  return (
                    <div
                      key={position.symbol}
                      className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 transition-colors duration-200"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary-100 rounded-xl flex items-center justify-center">
                          <span className="text-primary-700 font-semibold text-sm">
                            {position.symbol.substring(0, 2)}
                          </span>
                        </div>
                        <div>
                          <p className="font-semibold text-slate-900">{position.symbol}</p>
                          <p className="text-sm text-slate-600">
                            {Math.abs(position.quantity)} shares
                          </p>
                        </div>
                      </div>
                      
                      <div className="text-right">
                        <p className="font-semibold text-slate-900">
                          {formatCurrency(position.market_value)}
                        </p>
                        <div className={`flex items-center text-sm font-medium ${
                          isProfit ? 'text-success-600' : 'text-error-600'
                        }`}>
                          {isProfit ? (
                            <TrendingUp className="h-3 w-3 mr-1" />
                          ) : (
                            <TrendingDown className="h-3 w-3 mr-1" />
                          )}
                          <span>
                            {isProfit ? '+' : ''}{formatCurrency(position.unrealized_pl)} 
                            ({percentChange.toFixed(2)}%)
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Market Status Footer */}
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-success-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-slate-900">Market Open</span>
              </div>
              <div className="text-sm text-slate-600">
                Last updated: {new Date().toLocaleTimeString()}
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm">
              <div>
                <span className="text-slate-500">SPY: </span>
                <span className="font-medium text-success-600">+0.45%</span>
              </div>
              <div>
                <span className="text-slate-500">QQQ: </span>
                <span className="font-medium text-success-600">+0.32%</span>
              </div>
              <div>
                <span className="text-slate-500">VIX: </span>
                <span className="font-medium text-error-600">-2.1%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

