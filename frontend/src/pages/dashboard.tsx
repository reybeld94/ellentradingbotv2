import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Target, Activity, Clock, CheckCircle, XCircle, AlertTriangle, Zap, Brain } from 'lucide-react';

interface AccountData {
  cash: number;
  portfolio_value: number;
  buying_power: number;
  day_trade_buying_power: number;
}

interface Trade {
  id: number;
  symbol: string;
  action: 'BUY' | 'SELL';
  quantity: number;
  entry_price: number;
  current_price: number;
  pnl: number;
  pnl_percent: number;
  opened_at: string;
  strategy_id: string;
}

interface Signal {
  id: number;
  symbol: string;
  action: 'BUY' | 'SELL';
  price: number;
  confidence: number;
  strategy_id: string;
  created_at: string;
  status: 'pending' | 'executed' | 'rejected';
}

interface StrategyMetrics {
  id: string;
  name: string;
  total_trades: number;
  win_rate: number;
  total_pnl: number;
  avg_win: number;
  avg_loss: number;
  max_drawdown: number;
  sharpe_ratio: number;
}

interface Strategy {
  id: string;
  name: string;
}

const Dashboard: React.FC = () => {
  const [accountData, setAccountData] = useState<AccountData | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [strategyMetrics, setStrategyMetrics] = useState<StrategyMetrics | null>(null);

  const getAuthToken = (): string | null => {
    return localStorage.getItem('token');
  };

  const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
    const token = getAuthToken();
    if (!token) {
      throw new Error('No authentication token available');
    }

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });

    if (response.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
      throw new Error('Authentication failed');
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response;
  };

  const fetchSignals = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/signals?limit=10');
      const data = await response.json();
      setSignals(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching signals:', error);
      setSignals([]);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/strategies');
      const data = await response.json();
      const strategiesList = Array.isArray(data) ? data : [];
      setStrategies(strategiesList);
      if (strategiesList.length > 0 && !selectedStrategy) {
        setSelectedStrategy(strategiesList[0].id);
      }
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setStrategies([]);
    }
  };

  const fetchStrategyMetrics = async (strategyId: string) => {
    if (!strategyId) return;
    try {
      const response = await authenticatedFetch(`/api/v1/strategies/${strategyId}/metrics`);
      const data = await response.json();
      setStrategyMetrics(data);
    } catch (error) {
      console.error('Error fetching strategy metrics:', error);
      setStrategyMetrics(null);
    }
  };

  const fetchAccountData = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/account');
      const data = await response.json();
      setAccountData(data);
    } catch (error) {
      console.error('Error fetching account data:', error);
      setAccountData(null);
    }
  };

  const fetchTrades = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/trades');
      const data = await response.json();
      setTrades(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching trades:', error);
      setTrades([]);
    }
  };

  useEffect(() => {
    fetchAccountData();
    fetchTrades();
    fetchSignals();
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      fetchStrategyMetrics(selectedStrategy);
    }
  }, [selectedStrategy]);

  const totalPnL = trades.reduce((sum, trade) => sum + trade.pnl, 0);
  const winningTrades = trades.filter(trade => trade.pnl > 0).length;
  const winRate = trades.length > 0 ? (winningTrades / trades.length) * 100 : 0;

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSignalStatusIcon = (status: string) => {
    switch (status) {
      case 'executed': return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'pending': return <Clock className="h-3 w-3 text-yellow-500" />;
      case 'rejected': return <XCircle className="h-3 w-3 text-red-500" />;
      default: return <AlertTriangle className="h-3 w-3 text-gray-500" />;
    }
  };

  if (!accountData) {
    return <div className="p-4">Loading...</div>;
  }

  return (
    <div className="p-4 space-y-4 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Portfolio Value</p>
              <p className="text-lg font-bold text-gray-900">{formatCurrency(accountData.portfolio_value)}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <DollarSign className="h-4 w-4 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Day P&L</p>
              <p className={`text-lg font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}> 
                {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL)}
              </p>
            </div>
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${totalPnL >= 0 ? 'bg-green-100' : 'bg-red-100'}`}>
              {totalPnL >= 0 ? 
                <TrendingUp className="h-4 w-4 text-green-600" /> : 
                <TrendingDown className="h-4 w-4 text-red-600" />
              }
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Buying Power</p>
              <p className="text-lg font-bold text-gray-900">{formatCurrency(accountData.buying_power)}</p>
            </div>
            <div className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">
              <Activity className="h-4 w-4 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-100">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Win Rate</p>
              <p className="text-lg font-bold text-blue-600">{winRate.toFixed(1)}%</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
              <Target className="h-4 w-4 text-blue-600" />
            </div>
          </div>
        </div>
      </div>

        <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 lg:col-span-5 bg-white rounded-lg shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Active Trades</h3>
              <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2 py-1 rounded">
                {trades.length}
              </span>
            </div>
          </div>
          <div className="p-2">
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {trades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${trade.pnl >= 0 ? 'bg-green-500' : 'bg-red-500'}`} />
                    <div>
                      <p className="font-medium text-sm text-gray-900">{trade.symbol}</p>
                      <p className="text-xs text-gray-500">{trade.quantity} @ {trade.entry_price}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`font-medium text-sm ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(0)}
                    </p>
                    <p className={`text-xs ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {trade.pnl_percent >= 0 ? '+' : ''}{trade.pnl_percent}%
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 bg-white rounded-lg shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Recent Signals</h3>
              <Zap className="h-4 w-4 text-gray-400" />
            </div>
          </div>
          <div className="p-2">
            <div className="space-y-1 max-h-80 overflow-y-auto">
              {signals.map((signal) => (
                <div key={signal.id} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="flex items-center space-x-3">
                    {getSignalStatusIcon(signal.status)}
                    <div>
                      <div className="flex items-center space-x-2">
                        <p className="font-medium text-sm text-gray-900">{signal.symbol}</p>
                        <span className={`text-xs px-1.5 py-0.5 rounded ${
                          signal.action === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {signal.action}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">${signal.price} • {signal.confidence}%</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-500">{formatTime(signal.created_at)}</p>
                  </div>
                </div>
              ))}
              {signals.length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <Zap className="h-8 w-8 mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No recent signals</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 bg-white rounded-lg shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Strategy Metrics</h3>
              <Brain className="h-4 w-4 text-gray-400" />
            </div>
            <select 
              value={selectedStrategy} 
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {strategies.map((strategy) => (
                <option key={strategy.id} value={strategy.id}>
                  {strategy.name}
                </option>
              ))}
            </select>
          </div>
          <div className="p-4">
            {strategyMetrics ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Total Trades</p>
                    <p className="text-lg font-bold text-gray-900">{strategyMetrics.total_trades}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-xs text-gray-500">Win Rate</p>
                    <p className="text-lg font-bold text-blue-600">{strategyMetrics.win_rate}%</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Total P&L</span>
                    <span className={`text-sm font-medium ${strategyMetrics.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(strategyMetrics.total_pnl)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Avg Win</span>
                    <span className="text-sm font-medium text-green-600">{formatCurrency(strategyMetrics.avg_win)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Avg Loss</span>
                    <span className="text-sm font-medium text-red-600">{formatCurrency(strategyMetrics.avg_loss)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Max Drawdown</span>
                    <span className="text-sm font-medium text-red-600">{formatCurrency(strategyMetrics.max_drawdown)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Sharpe Ratio</span>
                    <span className="text-sm font-medium text-blue-600">{strategyMetrics.sharpe_ratio}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Brain className="h-8 w-8 mx-auto mb-2 opacity-30" />
                <p className="text-sm">Loading metrics...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  </div>
  );
};

export default Dashboard;

