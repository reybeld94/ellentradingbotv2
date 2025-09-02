import React, { useState, useEffect } from 'react';
import {
  Plus, Filter, Download, RefreshCw, Zap,
  LayoutGrid, List as ListIcon
} from 'lucide-react';
import SignalCard from '../components/signals/SignalCard';
import SignalFilters from '../components/signals/SignalFilters';
import SignalStats from '../components/signals/SignalStats';
import SignalModal from '../components/signals/SignalModal';

export type SignalStatus =
  | 'pending'
  | 'validated'
  | 'rejected'
  | 'executed'
  | 'bracket_created'
  | 'bracket_failed'
  | 'error';

interface Signal {
  id: number;
  symbol: string;
  action: 'buy' | 'sell';
  strategy_id: string;
  status: SignalStatus;
  timestamp: string;
  quantity?: number;
  confidence?: number;
  reason?: string;
  error_message?: string;
  // Optional legacy fields
  strategy_name?: string;
}

interface Strategy {
  id: string;
  name: string;
}

interface FilterOptions {
  search: string;
  status: string[];
  action: string[];
  confidence: [number, number];
  dateRange: string;
  strategy: string[];
}

const SignalsPage: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const [filters, setFilters] = useState<FilterOptions>({
    search: '',
    status: [],
    action: [],
    confidence: [0, 100],
    dateRange: '30d',
    strategy: []
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

  const fetchSignals = async () => {
    try {
      setLoading(true);
      const response = await authenticatedFetch('/api/v1/signals');
      const data = await response.json();
      setSignals(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching signals:', error);
      setSignals([]);
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
    fetchSignals();
    fetchStrategies();
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(fetchSignals, 15000);
    return () => clearInterval(interval);
  }, []);

  // Filter signals based on current filters
  const filteredSignals = signals.filter(signal => {
    // Search filter
    if (
      filters.search &&
      !signal.symbol.toLowerCase().includes(filters.search.toLowerCase()) &&
      !signal.strategy_id.toLowerCase().includes(filters.search.toLowerCase())
    ) {
      return false;
    }

    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(signal.status)) {
      return false;
    }

    // Action filter
    if (filters.action.length > 0 && !filters.action.includes(signal.action)) {
      return false;
    }

    // Confidence filter
    const conf = signal.confidence ?? 0;
    if (conf < filters.confidence[0] || conf > filters.confidence[1]) {
      return false;
    }

    // Strategy filter
    if (filters.strategy.length > 0 && !filters.strategy.includes(signal.strategy_id)) {
      return false;
    }

    // Date range filter
    const signalDate = new Date(signal.timestamp);
    const now = new Date();
    const daysDiff = Math.floor((now.getTime() - signalDate.getTime()) / (1000 * 60 * 60 * 24));
    
    switch (filters.dateRange) {
      case 'today':
        return daysDiff === 0;
      case '7d':
        return daysDiff <= 7;
      case '30d':
        return daysDiff <= 30;
      case '90d':
        return daysDiff <= 90;
      default:
        return true;
    }
  });

  // Calculate stats
  const stats = {
    total: signals.length,
    pending: signals.filter(s => s.status === 'pending').length,
    executed: signals.filter(s => ['executed', 'bracket_created'].includes(s.status)).length,
    failed: signals.filter(s => ['error', 'bracket_failed', 'rejected'].includes(s.status)).length,
    averageConfidence:
      signals.length > 0
        ?
            signals.reduce(
              (sum, s) => sum + (s.confidence ?? 0),
              0,
            ) / signals.length
        : 0,
    successRate:
      signals.length > 0
        ?
            (signals.filter(s => ['executed', 'bracket_created'].includes(s.status)).length /
              signals.length) *
            100
        : 0,
    todayCount: signals.filter(s => {
      const signalDate = new Date(s.timestamp);
      const today = new Date();
      return signalDate.toDateString() === today.toDateString();
    }).length,
    topStrategy: 'AI Momentum',
  };

  const handleApproveSignal = async (signalId: number) => {
    try {
      await authenticatedFetch(`/api/v1/signals/${signalId}/approve`, {
        method: 'POST',
      });
      fetchSignals();
    } catch (error) {
      console.error('Error approving signal:', error);
    }
  };

  const handleRejectSignal = async (signalId: number) => {
    try {
      await authenticatedFetch(`/api/v1/signals/${signalId}/reject`, {
        method: 'POST',
      });
      fetchSignals();
    } catch (error) {
      console.error('Error rejecting signal:', error);
    }
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      status: [],
      action: [],
      confidence: [0, 100],
      dateRange: '30d',
      strategy: []
    });
  };

  const exportSignals = () => {
    // Implementation for exporting signals to CSV
    console.log('Exporting signals...');
  };

  if (loading && signals.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Signals</h2>
          <p className="text-slate-600">Fetching your trading signals...</p>
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
            <h1 className="text-3xl font-bold text-slate-900">Trading Signals</h1>
            <p className="text-slate-600 mt-1">
              AI-generated trading opportunities and market insights
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
            
            <button onClick={exportSignals} className="btn-ghost">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            
            <button onClick={fetchSignals} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            <button className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              Manual Signal
            </button>
          </div>
        </div>

        {/* Stats */}
        <SignalStats stats={stats} loading={loading} />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          {showFilters && (
            <div className="lg:col-span-1">
              <SignalFilters
                filters={filters}
                onFiltersChange={setFilters}
                strategies={strategies}
                onReset={resetFilters}
              />
            </div>
          )}

          {/* Signals List */}
          <div className={showFilters ? 'lg:col-span-3' : 'lg:col-span-4'}>
            {filteredSignals.length === 0 ? (
              <div className="card p-12 text-center">
                <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Zap className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">No Signals Found</h3>
                <p className="text-slate-600 mb-6">
                  {signals.length === 0 
                    ? "No trading signals have been generated yet."
                    : "No signals match your current filters. Try adjusting your search criteria."
                  }
                </p>
                {signals.length > 0 && (
                  <button onClick={resetFilters} className="btn-secondary">
                    Clear Filters
                  </button>
                )}
              </div>
            ) : (
              <div className={`space-y-4 ${
                viewMode === 'grid' 
                  ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 space-y-0' 
                  : ''
              }`}>
                {filteredSignals.map((signal) => (
                  <SignalCard
                    key={signal.id}
                    signal={signal}
                    compact={viewMode === 'list'}
                    onApprove={handleApproveSignal}
                    onReject={handleRejectSignal}
                    onViewDetails={setSelectedSignal}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Load More */}
        {filteredSignals.length >= 20 && (
          <div className="text-center pt-8">
            <button className="btn-secondary">
              Load More Signals
            </button>
          </div>
        )}
      </div>

      {/* Signal Detail Modal */}
      <SignalModal
        signal={selectedSignal}
        isOpen={selectedSignal !== null}
        onClose={() => setSelectedSignal(null)}
        onApprove={handleApproveSignal}
        onReject={handleRejectSignal}
      />
    </div>
  );
};

export default SignalsPage;
