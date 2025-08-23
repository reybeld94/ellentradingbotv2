import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target, 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Zap, 
  Brain,
  ArrowUpRight,
  ArrowDownRight,
  BarChart3,
  Eye,
  EyeOff
} from 'lucide-react';

interface AccountData {
  cash: number;
  portfolio_value: number;
  buying_power: number;
  day_trade_buying_power: number;
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
  percentage: number;
}

interface RiskData {
  current_positions: Position[];
  account_info: {
    buying_power: number;
    portfolio_value: number;
    total_unrealized_pl: number;
  };
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
  const [positions, setPositions] = useState<Position[]>([]);
  const [riskData, setRiskData] = useState<RiskData | null>(null);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [strategyMetrics, setStrategyMetrics] = useState<StrategyMetrics | null>(null);
  const [showValues, setShowValues] = useState(true);

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

  const fetchRiskData = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/risk/status');
      const data = await response.json();
      setRiskData(data);
      setPositions(data.current_positions || []);
    } catch (error) {
      console.error('Error fetching risk data:', error);
      setPositions([]);
      setRiskData(null);
    }
  };

  useEffect(() => {
    fetchAccountData();
    fetchRiskData();
    fetchSignals();
    fetchStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      fetchStrategyMetrics(selectedStrategy);
    }
  }, [selectedStrategy]);

  const totalPnL = riskData?.account_info?.total_unrealized_pl || 0;
  const winningTrades = positions.filter(pos => (pos.unrealized_pl || 0) > 0).length;
  const winRate = positions.length > 0 ? (winningTrades / positions.length) * 100 : 0;

  const formatCurrency = (value: number | null | undefined) => {
    if (!showValues) return '••••••';
    if (value == null || value === undefined || isNaN(value)) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Math.abs(value));
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSignalStatusIcon = (status: string) => {
    switch (status) {
      case 'executed': return <CheckCircle className="w-3 h-3 text-emerald-500" />;
      case 'pending': return <Clock className="w-3 h-3 text-amber-500" />;
      case 'rejected': return <XCircle className="w-3 h-3 text-rose-500" />;
      default: return <AlertTriangle className="w-3 h-3 text-slate-400" />;
    }
  };

  if (!accountData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <BarChart3 className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Dashboard</h2>
          <p className="text-slate-600">Preparing your trading insights...</p>
        </div>
      </div>
    );
  }

  const dayPnLChange = totalPnL >= 0 ? 'positive' : 'negative';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Trading Dashboard</h1>
            <p className="text-slate-600 mt-1">Real-time portfolio insights and performance metrics</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowValues(!showValues)}
              className="flex items-center space-x-2 px-4 py-2 bg-white/80 backdrop-blur-sm border border-white/20 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-white transition-all duration-200 shadow-sm"
            >
              {showValues ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              <span className="text-sm font-medium">{showValues ? 'Hide' : 'Show'} Values</span>
            </button>
            <div className="flex items-center space-x-2 px-4 py-2 bg-white/80 backdrop-blur-sm border border-white/20 rounded-xl">
              <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-slate-700">Live</span>
            </div>
          </div>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Portfolio Value */}
          <div className="group relative bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white transition-all duration-300 shadow-sm hover:shadow-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-500 mb-1">Portfolio Value</p>
                <p className="text-2xl font-bold text-slate-900 mb-1">
                  {formatCurrency(accountData.portfolio_value)}
                </p>
                <div className="flex items-center text-sm text-emerald-600">
                  <ArrowUpRight className="w-4 h-4 mr-1" />
                  <span>+2.4% today</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>

          {/* Day P&L */}
          <div className={`group relative bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white transition-all duration-300 shadow-sm hover:shadow-lg ${dayPnLChange === 'positive' ? 'ring-1 ring-emerald-100' : 'ring-1 ring-rose-100'}`}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-500 mb-1">Day P&L</p>
                <p className={`text-2xl font-bold mb-1 ${totalPnL >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {totalPnL >= 0 ? '+' : '-'}{formatCurrency(totalPnL)}
                </p>
                <div className={`flex items-center text-sm ${totalPnL >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {totalPnL >= 0 ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
                  <span>{totalPnL >= 0 ? '+' : ''}{((totalPnL / accountData.portfolio_value) * 100).toFixed(2)}%</span>
                </div>
              </div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300 ${totalPnL >= 0 ? 'bg-gradient-to-br from-emerald-500 to-emerald-600' : 'bg-gradient-to-br from-rose-500 to-rose-600'}`}>
                {totalPnL >= 0 ? <TrendingUp className="w-6 h-6 text-white" /> : <TrendingDown className="w-6 h-6 text-white" />}
              </div>
            </div>
          </div>

          {/* Buying Power */}
          <div className="group relative bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white transition-all duration-300 shadow-sm hover:shadow-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-500 mb-1">Buying Power</p>
                <p className="text-2xl font-bold text-slate-900 mb-1">
                  {formatCurrency(accountData.buying_power)}
                </p>
                <div className="flex items-center text-sm text-slate-600">
                  <Activity className="w-4 h-4 mr-1" />
                  <span>Available</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Activity className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>

          {/* Win Rate */}
          <div className="group relative bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white transition-all duration-300 shadow-sm hover:shadow-lg">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-500 mb-1">Win Rate</p>
                <p className="text-2xl font-bold text-slate-900 mb-1">{winRate.toFixed(1)}%</p>
                <div className="flex items-center text-sm text-slate-600">
                  <span>{winningTrades}/{positions.length} positions</span>
                </div>
              </div>
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <Target className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-12 gap-6">
          {/* Active Trades */}
          <div className="col-span-12 lg:col-span-5">
            <div className="bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300">
              <div className="p-6 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Active Positions</h3>
                    <p className="text-sm text-slate-500">Real-time P&L tracking</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1.5 rounded-full">
                      {positions.length} positions
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {positions.length === 0 ? (
                    <div className="text-center py-12">
                      <BarChart3 className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                      <p className="text-slate-500 font-medium">No active positions</p>
                      <p className="text-sm text-slate-400">Your positions will appear here when opened</p>
                    </div>
                  ) : (
                    positions.map((position) => (
                      <div key={position.symbol} className="group flex items-center justify-between p-4 hover:bg-slate-50 rounded-xl transition-all duration-200 border border-transparent hover:border-slate-200">
                        <div className="flex items-center space-x-4">
                          <div className={`w-3 h-3 rounded-full ${position.unrealized_pl >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                          <div>
                            <div className="flex items-center space-x-2">
                              <p className="font-bold text-slate-900">{position.symbol}</p>
                              <span className="text-xs px-2 py-1 rounded-full font-medium bg-blue-100 text-blue-800">
                                LONG
                              </span>
                            </div>
                            <p className="text-sm text-slate-500">{position.quantity.toFixed(4)} shares @ ${position.avg_entry_price.toFixed(4)}</p>
                            <p className="text-xs text-slate-400">Value: ${position.market_value.toFixed(2)}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-bold text-lg ${position.unrealized_pl >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {position.unrealized_pl >= 0 ? '+' : ''}${showValues ? position.unrealized_pl.toFixed(2) : '••••'}
                          </p>
                          <p className={`text-sm font-medium ${position.unrealized_pl >= 0 ? 'text-emerald-500' : 'text-rose-500'}`}>
                            {position.unrealized_plpc >= 0 ? '+' : ''}{showValues ? position.unrealized_plpc.toFixed(4) : '••.••'}%
                          </p>
                          <p className="text-xs text-slate-400">${showValues ? position.current_price.toFixed(4) : '••••'}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Recent Signals */}
          <div className="col-span-12 lg:col-span-4">
            <div className="bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300">
              <div className="p-6 border-b border-slate-100">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Trading Signals</h3>
                    <p className="text-sm text-slate-500">Recent algorithmic signals</p>
                  </div>
                  <Zap className="w-5 h-5 text-amber-500" />
                </div>
              </div>
              <div className="p-4">
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {signals.length === 0 ? (
                    <div className="text-center py-12">
                      <Zap className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                      <p className="text-slate-500 font-medium">No recent signals</p>
                      <p className="text-sm text-slate-400">Algorithmic signals will appear here</p>
                    </div>
                  ) : (
                    signals.map((signal) => (
                      <div key={signal.id} className="group flex items-center justify-between p-4 hover:bg-slate-50 rounded-xl transition-all duration-200">
                        <div className="flex items-center space-x-4">
                          {getSignalStatusIcon(signal.status)}
                          <div>
                            <div className="flex items-center space-x-2">
                              <p className="font-bold text-slate-900">{signal.symbol}</p>
                              <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                                signal.action === 'BUY' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                              }`}>
                                {signal.action}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2 text-sm text-slate-500">
                              <span>${signal.price}</span>
                              <span>•</span>
                              <span className="font-medium">{signal.confidence}% confidence</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-slate-400">{formatTime(signal.created_at)}</p>
                          <div className={`text-xs px-2 py-1 rounded-full font-medium mt-1 ${
                            signal.status === 'executed' ? 'bg-emerald-100 text-emerald-800' :
                            signal.status === 'pending' ? 'bg-amber-100 text-amber-800' :
                            'bg-rose-100 text-rose-800'
                          }`}>
                            {signal.status}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Strategy Metrics */}
          <div className="col-span-12 lg:col-span-3">
            <div className="bg-white/80 backdrop-blur-sm border border-white/20 rounded-2xl shadow-sm hover:shadow-lg transition-all duration-300">
              <div className="p-6 border-b border-slate-100">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-slate-900">Strategy Analytics</h3>
                    <p className="text-sm text-slate-500">Performance metrics</p>
                  </div>
                  <Brain className="w-5 h-5 text-indigo-500" />
                </div>
                <select 
                  value={selectedStrategy} 
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="w-full text-sm border border-slate-200 rounded-lg px-3 py-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
                >
                  {strategies.map((strategy) => (
                    <option key={strategy.id} value={strategy.id}>
                      {strategy.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="p-6">
                {strategyMetrics ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-4 bg-slate-50 rounded-xl">
                        <p className="text-xs font-medium text-slate-500 mb-1">Total Trades</p>
                        <p className="text-xl font-bold text-slate-900">{strategyMetrics.total_trades}</p>
                      </div>
                      <div className="text-center p-4 bg-blue-50 rounded-xl">
                        <p className="text-xs font-medium text-slate-500 mb-1">Win Rate</p>
                        <p className="text-xl font-bold text-blue-600">{(strategyMetrics.win_rate || 0).toFixed(1)}%</p>
                      </div>
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                        <span className="text-sm font-medium text-slate-600">Total P&L</span>
                        <span className={`font-bold ${strategyMetrics.total_pnl >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {formatCurrency(strategyMetrics.total_pnl)}
                        </span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-emerald-50 rounded-lg">
                        <span className="text-sm font-medium text-slate-600">Avg Win</span>
                        <span className="font-bold text-emerald-600">{formatCurrency(strategyMetrics.avg_win)}</span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-rose-50 rounded-lg">
                        <span className="text-sm font-medium text-slate-600">Avg Loss</span>
                        <span className="font-bold text-rose-600">{formatCurrency(Math.abs(strategyMetrics.avg_loss))}</span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                        <span className="text-sm font-medium text-slate-600">Max Drawdown</span>
                        <span className="font-bold text-rose-600">{formatCurrency(Math.abs(strategyMetrics.max_drawdown))}</span>
                      </div>
                      
                      <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                        <span className="text-sm font-medium text-slate-600">Sharpe Ratio</span>
                        <span className="font-bold text-blue-600">{strategyMetrics.sharpe_ratio}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Brain className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500 font-medium">Loading metrics...</p>
                    <div className="mt-3 flex justify-center">
                      <div className="animate-pulse flex space-x-1">
                        <div className="w-2 h-2 bg-slate-300 rounded-full"></div>
                        <div className="w-2 h-2 bg-slate-300 rounded-full"></div>
                        <div className="w-2 h-2 bg-slate-300 rounded-full"></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
