import React, { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { connectWebSocket } from '../services/ws';
import {
  Activity, CheckCircle, XCircle, Clock, AlertCircle, RefreshCw, Filter,
  Search, TrendingUp, TrendingDown,
  ArrowUp, ArrowDown, Calendar, Eye, Settings2
} from 'lucide-react';
import Pagination from '../components/Pagination';
import SymbolLogo from '../components/SymbolLogo';

interface Signal {
  id: number;
  symbol: string;
  action: string;
  quantity: number;
  status: string;
  error_message?: string;
  timestamp: string;
  source: string;
  strategy_id?: string;
  reason?: string;
  confidence?: number;
}

const SignalsPage: React.FC = () => {
  const [signals, setSignals] = useState<Signal[]>([]); // Inicializar como array vacío
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'processed' | 'error' | 'pending'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'timestamp' | 'confidence' | 'symbol'>('timestamp');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 10;

  useEffect(() => {
    setCurrentPage(1);
  }, [filter, searchTerm, sortBy, sortOrder]);

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

      if (response.status === 401) {
        console.error('❌ Token expired or invalid');
        localStorage.removeItem('token');
        window.location.reload();
        throw new Error('Authentication failed - token expired');
      }

      if (response.status === 403) {
        console.error('❌ Access forbidden');
        const errorText = await response.text();
        console.error('📋 Error details:', errorText);
        throw new Error('Access forbidden - check permissions');
      }

      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API Error:', response.status, errorText);
        throw new Error(`API Error: ${response.status}`);
      }

      return response;
    } catch (error) {
      console.error('💥 Network error:', error);
      throw error;
    }
  };

  const fetchSignals = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔄 Fetching signals...');
      const response = await authenticatedFetch('/api/v1/signals');
      const data = await response.json();

      console.log('✅ Signals fetched successfully:', data);

      // Asegurar que data es un array
      if (Array.isArray(data)) {
        setSignals(data);
      } else {
        console.warn('⚠️ Signals response is not an array:', data);
        setSignals([]); // Fallback a array vacío
      }

    } catch (err: any) {
      console.error('❌ Error fetching signals:', err);
      setError(err.message || 'Failed to load signals');
      setSignals([]); // IMPORTANTE: asegurar que signals sea un array vacío en caso de error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSignals();
    const ws = connectWebSocket({
      onSignal: (sig) => setSignals((prev) => [sig, ...prev]),
    });
    return () => ws.close();
  }, []);

  // Stats Card Component
  const StatsCard: React.FC<{
    title: string;
    value: string | number;
    icon: React.ComponentType<any>;
    gradient: string;
    trend?: { value: string; positive: boolean };
  }> = ({ title, value, icon: Icon, gradient, trend }) => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all duration-300 group">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
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

  // Filter Button Component
  const FilterButton: React.FC<{
    active: boolean;
    onClick: () => void;
    children: ReactNode;
    count?: number;
  }> = ({ active, onClick, children, count }) => (
    <button
      onClick={onClick}
      className={`relative px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-blue-100 text-blue-800 shadow-sm'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {children}
      {count !== undefined && count > 0 && (
        <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center">
          {count}
        </span>
      )}
    </button>
  );

  // Signal Row Component
  const SignalRow: React.FC<{ signal: Signal }> = ({ signal }) => {
    const getStatusIcon = () => {
      switch (signal.status) {
        case 'processed':
          return <CheckCircle className="h-5 w-5 text-emerald-600" />;
        case 'error':
          return (
            <span title={signal.error_message}>
              <XCircle className="h-5 w-5 text-red-600" />
            </span>
          );
        case 'pending':
          return <Clock className="h-5 w-5 text-yellow-600" />;
        default:
          return <AlertCircle className="h-5 w-5 text-gray-600" />;
      }
    };

    const getStatusColor = (status: string) => {
      switch (status) {
        case 'processed': return 'bg-emerald-100 text-emerald-800';
        case 'error': return 'bg-red-100 text-red-800';
        case 'pending': return 'bg-yellow-100 text-yellow-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    };

    return (
      <tr className="hover:bg-gray-50 transition-colors duration-200 group">
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            {getStatusIcon()}
            {signal.status !== 'error' && (
              <span className={`ml-2 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(signal.status)}`}>
                {signal.status}
              </span>
            )}
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            <SymbolLogo symbol={signal.symbol} className="mr-3" />
            <span className="text-sm font-semibold text-gray-900">{signal.symbol}</span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            {signal.action === 'buy' ?
              <TrendingUp className="h-4 w-4 text-emerald-600 mr-2" /> :
              <TrendingDown className="h-4 w-4 text-red-600 mr-2" />
            }
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              signal.action === 'buy' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
            }`}>
              {signal.action.toUpperCase()}
            </span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div>
            <p className="text-sm font-medium text-gray-900">{signal.strategy_id || 'Unknown'}</p>
            {signal.reason && (
              <p className="text-xs text-gray-500 truncate max-w-32" title={signal.reason}>
                {signal.reason}
              </p>
            )}
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          {signal.quantity || 'Auto'}
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          {signal.confidence ? (
            <div className="flex items-center">
              <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                <div
                  className={`h-2 rounded-full ${
                    signal.confidence >= 80 ? 'bg-emerald-500' :
                    signal.confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${signal.confidence}%` }}
                ></div>
              </div>
              <span className="text-sm font-medium text-gray-600">{signal.confidence}%</span>
            </div>
          ) : (
            <span className="text-sm text-gray-400">--</span>
          )}
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          <div>
            <p>{new Date(signal.timestamp).toLocaleDateString()}</p>
            <p className="text-xs">{new Date(signal.timestamp).toLocaleTimeString()}</p>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <button className="p-1 text-gray-400 hover:text-blue-600 transition-colors duration-200">
              <Eye className="h-4 w-4" />
            </button>
            <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200">
              <Settings2 className="h-4 w-4" />
            </button>
          </div>
        </td>
      </tr>
    );
  };

  // Asegurar que signals es un array antes de usar filter
  const safeSignals = Array.isArray(signals) ? signals : [];

  // Filtrar y ordenar signals
  const filteredAndSortedSignals = safeSignals
    .filter(signal => {
      const matchesFilter = filter === 'all' || signal.status === filter;
      const matchesSearch = signal.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           signal.strategy_id?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           signal.source.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    })
    .sort((a, b) => {
      let aVal, bVal;
      switch (sortBy) {
        case 'confidence':
          aVal = a.confidence || 0;
          bVal = b.confidence || 0;
          break;
        case 'symbol':
          aVal = a.symbol;
          bVal = b.symbol;
          break;
        default:
          aVal = new Date(a.timestamp).getTime();
          bVal = new Date(b.timestamp).getTime();
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

  const totalPages = Math.ceil(filteredAndSortedSignals.length / PAGE_SIZE);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages || 1);
    }
  }, [totalPages, currentPage]);

  const paginatedSignals = filteredAndSortedSignals.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const stats = {
    total: safeSignals.length,
    processed: safeSignals.filter(s => s.status === 'processed').length,
    errors: safeSignals.filter(s => s.status === 'error').length,
    pending: safeSignals.filter(s => s.status === 'pending').length,
  };

  const successRate = stats.total > 0 ? ((stats.processed / stats.total) * 100).toFixed(1) : '0';

  if (loading) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600 font-medium">Loading signals...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Signals</h1>
            <p className="text-gray-600">Monitor and analyze all trading signals from TradingView</p>
          </div>
          <div className="mt-4 lg:mt-0 flex flex-wrap gap-3">
            <button
              onClick={fetchSignals}
              className="flex items-center px-4 py-2 border border-gray-300 rounded-xl hover:bg-gray-50 transition-all duration-200"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Total Signals"
          value={stats.total}
          icon={Activity}
          gradient="bg-gradient-to-r from-blue-500 to-indigo-500"
        />
        <StatsCard
          title="Processed"
          value={stats.processed}
          icon={CheckCircle}
          gradient="bg-gradient-to-r from-emerald-500 to-green-500"
          trend={{ value: `${successRate}% success`, positive: parseFloat(successRate) > 70 }}
        />
        <StatsCard
          title="Pending"
          value={stats.pending}
          icon={Clock}
          gradient="bg-gradient-to-r from-yellow-500 to-orange-500"
        />
        <StatsCard
          title="Errors"
          value={stats.errors}
          icon={XCircle}
          gradient="bg-gradient-to-r from-red-500 to-pink-500"
        />
      </div>

      {/* Error Alert */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
              <button
                onClick={fetchSignals}
                className="mt-2 text-sm text-red-600 underline hover:text-red-500"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 mb-6">
        <div className="p-6 border-b border-gray-100">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
            <div className="flex flex-col sm:flex-row sm:items-center space-y-4 sm:space-y-0 sm:space-x-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search signals, symbols, strategies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none w-80 transition-all duration-200"
                />
              </div>
              <div className="flex items-center space-x-2">
                <Filter className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">Filter:</span>
                <div className="flex space-x-2">
                  <FilterButton
                    active={filter === 'all'}
                    onClick={() => setFilter('all')}
                    count={stats.total}
                  >
                    All
                  </FilterButton>
                  <FilterButton
                    active={filter === 'processed'}
                    onClick={() => setFilter('processed')}
                    count={stats.processed}
                  >
                    Processed
                  </FilterButton>
                  <FilterButton
                    active={filter === 'pending'}
                    onClick={() => setFilter('pending')}
                    count={stats.pending}
                  >
                    Pending
                  </FilterButton>
                  <FilterButton
                    active={filter === 'error'}
                    onClick={() => setFilter('error')}
                    count={stats.errors}
                  >
                    Errors
                  </FilterButton>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500">Sort by:</span>
              <select
                value={`${sortBy}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortBy(field as any);
                  setSortOrder(order as any);
                }}
                className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                <option value="timestamp-desc">Latest first</option>
                <option value="timestamp-asc">Oldest first</option>
                <option value="confidence-desc">Confidence high to low</option>
                <option value="confidence-asc">Confidence low to high</option>
                <option value="symbol-asc">Symbol A-Z</option>
                <option value="symbol-desc">Symbol Z-A</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Signals Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Signals ({filteredAndSortedSignals.length})
            </h3>
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-gray-400" />
              <span className="text-sm text-gray-500">Last 30 days</span>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          {filteredAndSortedSignals.length === 0 ? (
            <div className="p-12 text-center">
              <Activity className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg mb-2">
                {error ? 'Unable to load signals' : 'No signals found'}
              </p>
              <p className="text-gray-400 mb-4">
                {filter !== 'all' && !error ? 'Try adjusting your filters' : 'Signals from TradingView will appear here'}
              </p>
              {filter !== 'all' && !error && (
                <button
                  onClick={() => {
                    setFilter('all');
                    setSearchTerm('');
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-200"
                >
                  Clear filters
                </button>
              )}
              {error && (
                <button
                  onClick={fetchSignals}
                  className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-200"
                >
                  Retry
                </button>
              )}
            </div>
          ) : (
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Symbol</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Action</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Strategy</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Confidence</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Timestamp</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {paginatedSignals.map((signal) => (
                  <SignalRow key={signal.id} signal={signal} />
                ))}
              </tbody>
            </table>
          )}
        </div>
        <Pagination
          currentPage={currentPage}
          totalItems={filteredAndSortedSignals.length}
          pageSize={PAGE_SIZE}
          onPageChange={setCurrentPage}
        />
      </div>
    </div>
  );
};

export default SignalsPage;