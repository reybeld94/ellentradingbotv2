import React, { useState, useEffect } from 'react';
import { Filter, Download, RefreshCw, BarChart3 } from 'lucide-react';
import TradeCard from '../../components/trades/TradeCard';
import TradeMetrics from '../../components/trades/TradeMetrics';
import TradeFilters from '../../components/trades/TradeFilters';
import AlpacaStyleChart from '../../components/dashboard/AlpacaStyleChart';
import ValidationAlert from '../../components/ValidationAlert';
import { api } from '../../services/api';

interface Trade {
  id: string;
  symbol: string;
  action: 'buy' | 'sell';
  quantity: number;
  entry_price: number;
  exit_price?: number;
  pnl?: number;
  opened_at: string;
  closed_at?: string;
  status: 'open' | 'closed';
  strategy_id?: string;
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

interface StrategyStat {
  id: string;
  name: string;
  totalPnL: number;
  winRate: number;
  trades: number;
}

const defaultMetrics = {
  totalTrades: 0,
  openTrades: 0,
  closedTrades: 0,
  winningTrades: 0,
  losingTrades: 0,
  totalPnL: 0,
  winRate: 0,
  avgWin: 0,
  avgLoss: 0,
  bestTrade: 0,
  worstTrade: 0,
  avgHoldTime: 0,
  profitFactor: 0,
  sharpeRatio: 0,
  maxDrawdown: 0,
  totalVolume: 0,
};

const TradesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [strategyStats, setStrategyStats] = useState<StrategyStat[]>([]);
  const [stats, setStats] = useState(defaultMetrics);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  // const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [validationIssues, setValidationIssues] = useState<any[]>([]);
  const [showValidationPanel, setShowValidationPanel] = useState(false);

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
      const parsed = Array.isArray(data)
        ? data.map((t: any) => ({
            id: t.id.toString(),
            symbol: t.symbol,
            action: t.action,
            quantity: t.quantity,
            entry_price: t.entry_price,
            exit_price: t.exit_price ?? undefined,
            pnl: t.pnl ?? 0,
            opened_at: t.opened_at,
            closed_at: t.closed_at ?? undefined,
            status: t.status,
            strategy_id: t.strategy_id ?? undefined,
          }))
        : [];
      setTrades(parsed);
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

  const fetchRealMetrics = async () => {
    try {
      const data = await api.analytics.getPerformanceMetrics('1M');
      setStats({
        totalPnL: data.total_pnl,
        totalTrades: data.total_trades,
        winningTrades: data.winning_trades,
        losingTrades: data.losing_trades,
        winRate: data.win_rate,
        avgWin: data.avg_win,
        avgLoss: data.avg_loss,
        bestTrade: data.largest_win,
        avgHoldTime: data.avg_hold_time,
        openTrades: trades.filter(t => t.status === 'open').length,
        closedTrades: data.total_trades,
        profitFactor: data.profit_factor || 0,
        maxDrawdown: data.max_drawdown || 0,
        sharpeRatio: data.sharpe_ratio || 0,
        totalVolume: 0,
        worstTrade: 0,
      });
    } catch (error) {
      console.error('Error fetching real metrics:', error);
      // Fallback to calculated metrics only if API fails
      setStats(calculateMetrics(trades));
    }
  };

  const fetchStrategyPerformance = async () => {
    try {
      const results = await Promise.all(
        strategies.map(async s => {
          try {
            const res = await authenticatedFetch(`/api/v1/trades/by-strategy/${s.id}`);
            const data = await res.json();
            const trades = Array.isArray(data) ? data : [];
            const totalPnL = trades.reduce((sum: number, t: any) => sum + (t.pnl || t.realized_pnl || 0), 0);
            const wins = trades.filter((t: any) => (t.pnl || t.realized_pnl || 0) > 0).length;
            const winRate = trades.length > 0 ? (wins / trades.length) * 100 : 0;
            return { id: s.id, name: s.name, totalPnL, winRate, trades: trades.length };
          } catch {
            return { id: s.id, name: s.name, totalPnL: 0, winRate: 0, trades: 0 };
          }
        })
      );
      setStrategyStats(results);
    } catch (error) {
      console.error('Error fetching strategy performance:', error);
      setStrategyStats([]);
    }
  };

  const validateTrades = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/trades/validate', {
        method: 'POST'
      });
      const validation = await response.json();
      setValidationIssues(validation.issues_found || []);
      setShowValidationPanel(true);
    } catch (error) {
      console.error('Error validating trades:', error);
    }
  };

  const cleanupOrphanedTrades = async (dryRun = true) => {
    try {
      const response = await authenticatedFetch(
        `/api/v1/trades/cleanup-orphaned?dry_run=${dryRun}`,
        { method: 'POST' }
      );
      const result = await response.json();
      console.log('Cleanup result:', result);
      if (!dryRun) {
        await fetchTrades();
        await fetchRealMetrics();
      }
      return result;
    } catch (error) {
      console.error('Error cleaning up trades:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      await fetchTrades();
      await fetchStrategies();
      await fetchRealMetrics(); // Usar métricas reales de la API
    };
    loadData();
  }, []);

  useEffect(() => {
    if (strategies.length > 0) {
      fetchStrategyPerformance();
    }
  }, [strategies]);

  const filteredTrades = trades.filter(trade => {
    if (filters.search &&
        !trade.symbol.toLowerCase().includes(filters.search.toLowerCase()) &&
        !trade.id.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }
    if (filters.status.length > 0 && !filters.status.includes(trade.status)) {
      return false;
    }
    if (filters.side.length > 0 && !filters.side.includes(trade.action)) {
      return false;
    }
    if (filters.strategy.length > 0 && !filters.strategy.includes(trade.strategy_id || '')) {
      return false;
    }
    if (filters.profitableOnly) {
      const pnl = trade.pnl || 0;
      if (pnl <= 0) return false;
    }
    const pnl = trade.pnl || 0;
    if (filters.minPnL && pnl < parseFloat(filters.minPnL)) {
      return false;
    }
    if (filters.maxPnL && pnl > parseFloat(filters.maxPnL)) {
      return false;
    }
    const tradeDate = new Date(trade.opened_at);
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

  const calculateMetrics = (list: Trade[]) => {
    // Solo usar como fallback si la API falla
    const closedTrades = list.filter(t => t.status === 'closed' && t.pnl !== undefined);
    const openTrades = list.filter(t => t.status === 'open');
    const winningTrades = closedTrades.filter(t => (t.pnl || 0) > 0);
    const losingTrades = closedTrades.filter(t => (t.pnl || 0) < 0);
    const totalPnL = closedTrades.reduce((sum, t) => sum + (t.pnl || 0), 0);

    return {
      totalPnL,
      totalTrades: closedTrades.length,
      winningTrades: winningTrades.length,
      losingTrades: losingTrades.length,
      winRate: closedTrades.length > 0 ? (winningTrades.length / closedTrades.length) * 100 : 0,
      avgWin: winningTrades.length > 0 ? winningTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / winningTrades.length : 0,
      avgLoss: losingTrades.length > 0 ? losingTrades.reduce((sum, t) => sum + (t.pnl || 0), 0) / losingTrades.length : 0,
      bestTrade: Math.max(...closedTrades.map(t => t.pnl || 0), 0),
      avgHoldTime: 'N/A' as any,
      openTrades: openTrades.length,
      closedTrades: closedTrades.length,
      profitFactor: 0,
      maxDrawdown: 0,
      sharpeRatio: 0,
      worstTrade: 0,
      totalVolume: 0,
    };
  };

  const handleCloseTrade = async (tradeId: string) => {
    try {
      await authenticatedFetch(`/api/v1/trades/${tradeId}/close`, { method: 'POST' });
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
      <div className='min-h-screen bg-slate-50 flex items-center justify-center'>
        <div className='text-center'>
          <div className='w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse'>
            <BarChart3 className='w-8 h-8 text-white' />
          </div>
          <h2 className='text-2xl font-bold text-slate-900 mb-2'>Loading Trades</h2>
          <p className='text-slate-600'>Analyzing your trading performance...</p>
        </div>
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-slate-50 p-6'>
      <div className='max-w-7xl mx-auto space-y-6'>
        <div className='flex items-center justify-between'>
          <div>
            <h1 className='text-3xl font-bold text-slate-900'>Trade History</h1>
            <p className='text-slate-600 mt-1'>Comprehensive analysis of your trading performance and positions</p>
          </div>
          <div className='flex items-center space-x-3'>
            {/* View mode toggle removed */}
            <button onClick={() => setShowFilters(!showFilters)} className={`btn-secondary ${showFilters ? 'bg-primary-50 text-primary-700 border-primary-200' : ''}`}>
              <Filter className='w-4 h-4 mr-2' />
              Filters
            </button>
            <button onClick={exportTrades} className='btn-ghost'>
              <Download className='w-4 h-4 mr-2' />
              Export
            </button>
            <button onClick={() => { fetchTrades(); fetchRealMetrics(); }} className='btn-secondary'>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button onClick={validateTrades} className='btn btn-warning'>
              Validate with Alpaca
            </button>
          </div>
        </div>

        <TradeMetrics metrics={stats} loading={loading} />

        {showValidationPanel && (
          <ValidationAlert
            issues={validationIssues}
            onClose={() => setShowValidationPanel(false)}
            onCleanup={cleanupOrphanedTrades}
          />
        )}

        {/* Portfolio Performance Chart */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Portfolio Performance</h3>
              <p className="text-sm text-slate-600">Track your trading performance over time</p>
            </div>
          </div>

          {/* Usar el mismo componente que funciona en Dashboard */}
          <AlpacaStyleChart loading={loading} />
        </div>

        {strategyStats.length > 0 && (
          <div className='card p-6'>
            <h3 className='text-lg font-semibold text-slate-900 mb-4'>Performance by Strategy</h3>
            <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
              {strategyStats.map(s => (
                <div key={s.id} className='p-4 rounded-xl bg-slate-50'>
                  <div className='flex items-center justify-between mb-2'>
                    <span className='font-medium text-slate-700'>{s.name}</span>
                    <span className={`text-sm font-semibold ${s.totalPnL >= 0 ? 'text-success-600' : 'text-error-600'}`}>
                      {s.totalPnL >= 0 ? '+' : ''}${Math.abs(s.totalPnL).toFixed(2)}
                    </span>
                  </div>
                  <div className='text-xs text-slate-500'>Win Rate: {s.winRate.toFixed(1)}% ({s.trades} trades)</div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className='grid grid-cols-1 lg:grid-cols-4 gap-6'>
          {showFilters && (
            <div className='lg:col-span-1'>
              <TradeFilters filters={filters} onFiltersChange={setFilters} strategies={strategies} onReset={resetFilters} />
            </div>
          )}
          <div className={showFilters ? 'lg:col-span-3' : 'lg:col-span-4'}>
            {filteredTrades.length === 0 ? (
              <div className='card p-12 text-center'>
                <div className='w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6'>
                  <BarChart3 className='w-10 h-10 text-slate-400' />
                </div>
                <h3 className='text-xl font-semibold text-slate-900 mb-2'>No Trades Found</h3>
                <p className='text-slate-600 mb-6'>
                  {trades.length === 0 ? "You haven't executed any trades yet. Your trading history will appear here once you start trading." : 'No trades match your current filters. Try adjusting your search criteria.'}
                </p>
                {trades.length > 0 && (
                  <button onClick={resetFilters} className='btn-secondary'>
                    Clear Filters
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {filteredTrades.map(trade => (
                  <TradeCard
                    key={trade.id}
                    trade={{
                      id: trade.id,
                      symbol: trade.symbol,
                      side: trade.action,
                      quantity: trade.quantity,
                      entry_price: trade.entry_price,
                      exit_price: trade.exit_price,
                      realized_pnl: trade.pnl,
                      entry_time: trade.opened_at,
                      exit_time: trade.closed_at,
                      status: trade.status,
                      strategy_id: trade.strategy_id,
                    }}
                    onClose={handleCloseTrade}
                    onViewDetails={(trade) => {
                      console.log('View details for trade:', trade.id);
                      // Aquí puedes añadir la lógica para mostrar detalles
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {filteredTrades.length >= 20 && (
          <div className='text-center pt-8'>
            <button className='btn-secondary'>
              Load More Trades
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default TradesPage;

