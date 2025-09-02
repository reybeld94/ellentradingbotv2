import React, { useState, useEffect } from 'react';
import {
  Filter, Download, RefreshCw, BarChart3,
  LayoutGrid, List as ListIcon
} from 'lucide-react';
import TradeCard from '../components/trades/TradeCard';
import TradeMetrics from '../components/trades/TradeMetrics';
import TradeFilters from '../components/trades/TradeFilters';
import PnLChart from '../components/trades/PnLChart';

interface Trade {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  entry_price: number;
  exit_price?: number;
  current_price?: number;
  realized_pnl?: number;
  unrealized_pnl?: number;
  pnl_percent?: number;
  entry_time: string;
  exit_time?: string;
  duration?: number;
  status: 'open' | 'closed';
  strategy_id?: string;
  strategy_name?: string;
  fees?: number;
  commission?: number;
  tags?: string[];
}

interface Strategy {
  id: string;
  name: string;
}

interface FilterOptions {
  search: string;
  status: string[];
  side: string[];
  dateRange: string;
  strategy: string[];
  minPnL: string;
  maxPnL: string;
  profitableOnly: boolean;
  minDuration: string;
  maxDuration: string;
}

const TradesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const [filters, setFilters] = useState<FilterOptions>({
    search: '',
    status: [],
    side: [],
    dateRange: '30d',
    strategy: [],
    minPnL: '',
    maxPnL: '',
    profitableOnly: false,
    minDuration: '',
    maxDuration: ''
  });

  const getAuthToken = (): string | null => {
    return localStorage.getItem('token');
  };

  const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token available');

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
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response;
  };

  const fetchTrades = async () => {
    try {
      setLoading(true);
      const response = await authenticatedFetch('/api/v1/trades');
      const data = await response.json();
      setTrades(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching trades:', error);
      setTrades([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStrategies = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/strategies');
      const data = await response.json();
      setStrategies(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching strategies:', error);
      setStrategies([]);
    }
  };

  useEffect(() => {
    fetchTrades();
    fetchStrategies();
    
    // Auto-refresh every 30 seconds for open positions
    const interval = setInterval(fetchTrades, 30000);
    return () => clearInterval(interval);
  }, []);

  // Filter trades based on current filters
  const filteredTrades = trades.filter(trade => {
    // Search filter
    if (filters.search && 
        !trade.symbol.toLowerCase().includes(filters.search.toLowerCase()) &&
        !trade.id.toLowerCase().includes(filters.search.toLowerCase()) &&
        !trade.strategy_name?.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }

    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(trade.status)) {
      return false;
    }

    // Side filter
    if (filters.side.length > 0 && !filters.side.includes(trade.side)) {
      return false;
    }

    // Strategy filter
    if (filters.strategy.length > 0 && !filters.strategy.includes(trade.strategy_id || '')) {
      return false;
    }

    // Profitable only filter
    if (filters.profitableOnly) {
      const pnl = trade.realized_pnl || trade.unrealized_pnl || 0;
      if (pnl <= 0) return false;
    }

    // P&L range filter
    const pnl = trade.realized_pnl || trade.unrealized_pnl || 0;
    if (filters.minPnL && pnl < parseFloat(filters.minPnL)) {
      return false;
    }
    if (filters.maxPnL && pnl > parseFloat(filters.maxPnL)) {
      return false;
    }

    // Duration filter
    if (filters.minDuration && trade.duration && trade.duration < parseInt(filters.minDuration)) {
      return false;
    }
    if (filters.maxDuration && trade.duration && trade.duration > parseInt(filters.maxDuration)) {
      return false;
    }

    // Date range filter
    const tradeDate = new Date(trade.entry_time);
    const now = new Date();
    const daysDiff = Math.floor((now.getTime() - tradeDate.getTime()) / (1000 * 60 * 60 * 24));
    
    switch (filters.dateRange) {
      case 'today':
        return daysDiff === 0;
      case '7d':
        return daysDiff <= 7;
      case '30d':
        return daysDiff <= 30;
      case '90d':
        return daysDiff <= 90;
      case '1y':
        return daysDiff <= 365;
      default:
        return true;
    }
  });

  // Calculate comprehensive metrics
  const calculateMetrics = () => {
    const closedTrades = trades.filter(t => t.status === 'closed' && t.realized_pnl !== undefined);
    const openTrades = trades.filter(t => t.status === 'open');
    
    const winningTrades = closedTrades.filter(t => (t.realized_pnl || 0) > 0);
    const losingTrades = closedTrades.filter(t => (t.realized_pnl || 0) < 0);
    
    const totalPnL = trades.reduce((sum, t) => sum + (t.realized_pnl || t.unrealized_pnl || 0), 0);
    
    const avgWin = winningTrades.length > 0 
      ? winningTrades.reduce((sum, t) => sum + (t.realized_pnl || 0), 0) / winningTrades.length 
      : 0;
    const avgLoss = losingTrades.length > 0 
      ? Math.abs(losingTrades.reduce((sum, t) => sum + (t.realized_pnl || 0), 0) / losingTrades.length)
      : 0;
    
    const bestTrade = Math.max(...trades.map(t => t.realized_pnl || t.unrealized_pnl || 0));
    const worstTrade = Math.min(...trades.map(t => t.realized_pnl || t.unrealized_pnl || 0));
    
    const avgHoldTime = closedTrades.length > 0
      ? closedTrades.reduce((sum, t) => sum + (t.duration || 0), 0) / closedTrades.length
      : 0;
    
    const grossProfit = winningTrades.reduce((sum, t) => sum + (t.realized_pnl || 0), 0);
    const grossLoss = Math.abs(losingTrades.reduce((sum, t) => sum + (t.realized_pnl || 0), 0));
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 999 : 0;
    
    const totalVolume = trades.reduce((sum, t) => sum + (t.quantity * t.entry_price), 0);
    
    // Mock additional metrics (replace with real calculations)
    const sharpeRatio = 1.2; // Calculate based on returns and volatility
    const maxDrawdown = 15.5; // Calculate based on peak-to-trough analysis
    
    return {
      totalTrades: trades.length,
      openTrades: openTrades.length,
      closedTrades: closedTrades.length,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      totalPnL,
      winRate: closedTrades.length > 0 ? (winningTrades.length / closedTrades.length) * 100 : 0,
      avgWin,
      avgLoss,
      bestTrade,
      worstTrade,
      avgHoldTime,
      profitFactor,
      sharpeRatio,
      maxDrawdown,
      totalVolume
    };
  };

  const metrics = calculateMetrics();

  // Generate chart data (mock - replace with real data)
  const generateChartData = () => {
    return Array.from({ length: 30 }, (_, i) => ({
      date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      cumulativePnL: Math.random() * 10000 - 5000 + i * 100,
      dailyPnL: Math.random() * 1000 - 500,
      tradeCount: Math.floor(Math.random() * 5) + 1
    }));
  };

  const chartData = generateChartData();

  const handleCloseTrade = async (tradeId: string) => {
    try {
      await authenticatedFetch(`/api/v1/trades/${tradeId}/close`, {
        method: 'POST'
      });
      fetchTrades();
    } catch (error) {
      console.error('Error closing trade:', error);
    }
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      status: [],
      side: [],
      dateRange: '30d',
      strategy: [],
      minPnL: '',
      maxPnL: '',
      profitableOnly: false,
      minDuration: '',
      maxDuration: ''
    });
  };

  const exportTrades = () => {
    console.log('Exporting trades...');
  };

  if (loading && trades.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <BarChart3 className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Trades</h2>
          <p className="text-slate-600">Analyzing your trading performance...</p>
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
            <h1 className="text-3xl font-bold text-slate-900">Trade History</h1>
            <p className="text-slate-600 mt-1">
              Comprehensive analysis of your trading performance and positions
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              className="btn-ghost"
            >
              {viewMode === 'grid' ? <ListIcon className="w-4 h-4" /> : <LayoutGrid className="w-4 h-4" />}
            </button>
            
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn-secondary ${showFilters ? 'bg-primary-50 text-primary-700 border-primary-200' : ''}`}
            >
              <Filter className="w-4 h-4 mr-2" />
              Filters
            </button>
            
            <button onClick={exportTrades} className="btn-ghost">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            
            <button onClick={fetchTrades} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Metrics */}
        <TradeMetrics metrics={metrics} loading={loading} />

        {/* P&L Chart */}
        <PnLChart data={chartData} loading={loading} />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          {showFilters && (
            <div className="lg:col-span-1">
              <TradeFilters
                filters={filters}
                onFiltersChange={setFilters}
                strategies={strategies}
                onReset={resetFilters}
              />
            </div>
          )}

          {/* Trades List */}
          <div className={showFilters ? 'lg:col-span-3' : 'lg:col-span-4'}>
            {filteredTrades.length === 0 ? (
              <div className="card p-12 text-center">
                <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <BarChart3 className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">No Trades Found</h3>
                <p className="text-slate-600 mb-6">
                  {trades.length === 0 
                    ? "You haven't executed any trades yet. Your trading history will appear here once you start trading."
                    : "No trades match your current filters. Try adjusting your search criteria."
                  }
                </p>
                {trades.length > 0 && (
                  <button onClick={resetFilters} className="btn-secondary">
                    Clear Filters
                  </button>
                )}
              </div>
            ) : (
              <div className={`space-y-4 ${
                viewMode === 'grid' 
                  ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-2 gap-6 space-y-0' 
                  : ''
              }`}>
                {filteredTrades.map((trade) => (
                  <TradeCard
                    key={trade.id}
                    trade={trade}
                    compact={viewMode === 'list'}
                    onClose={handleCloseTrade}

                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Load More */}
        {filteredTrades.length >= 20 && (
          <div className="text-center pt-8">
            <button className="btn-secondary">
              Load More Trades
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradesPage;
