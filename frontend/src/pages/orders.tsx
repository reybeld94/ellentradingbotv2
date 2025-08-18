import React, { useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import {
  BarChart3, CheckCircle, XCircle, Clock, AlertCircle, RefreshCw, Filter,
  TrendingUp, TrendingDown, Search, Download, Calendar, DollarSign,
  ArrowUp, ArrowDown, Eye, MoreHorizontal, Target, PieChart
} from 'lucide-react';
import Pagination from '../components/Pagination';
import SymbolLogo from '../components/SymbolLogo';

interface Order {
  id: string;
  symbol: string;
  qty: string;
  side: string;
  status: string;
  submitted_at: string;
  filled_at?: string;
  rejected_reason?: string;
  filled_qty?: string;
  filled_avg_price?: string;
  order_type?: string;
  time_in_force?: string;
}

const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]); // Inicializar como array vacío
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'filled' | 'rejected' | 'pending'>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'submitted_at' | 'filled_at' | 'symbol' | 'qty'>('submitted_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedTimeRange, setSelectedTimeRange] = useState<'today' | 'week' | 'month' | 'all'>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const PAGE_SIZE = 10;

  useEffect(() => {
    setCurrentPage(1);
  }, [filter, searchTerm, sortBy, sortOrder, selectedTimeRange]);

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

  const fetchOrders = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('🔄 Fetching orders...');
      const response = await authenticatedFetch('/api/v1/orders');
      const data = await response.json();

      if (Array.isArray(data.orders)) {
        setOrders(data.orders);
      } else {
        console.warn('⚠️ No orders found in response:', data);
        setOrders([]);
      }

    } catch (err: any) {
      console.error('❌ Error fetching orders:', err);
      setError(err.message || 'Failed to load orders');
      setOrders([]); // IMPORTANTE: asegurar que orders sea un array vacío en caso de error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 15000); // Refresh every 15s
    return () => clearInterval(interval);
  }, []);

  // Stats Card Component
  const StatsCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ComponentType<any>;
    gradient: string;
    trend?: { value: string; positive: boolean };
  }> = ({ title, value, subtitle, icon: Icon, gradient, trend }) => (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-all duration-300 group">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
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

  // Time Range Button Component
  const TimeRangeButton: React.FC<{
    active: boolean;
    onClick: () => void;
    children: ReactNode;
  }> = ({ active, onClick, children }) => (
    <button
      onClick={onClick}
      className={`px-3 py-1 rounded-lg text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-blue-100 text-blue-800'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {children}
    </button>
  );

  // Order Row Component
  const OrderRow: React.FC<{ order: Order }> = ({ order }) => {
    const getStatusIcon = (status: string) => {
      switch (status.toLowerCase()) {
        case 'filled':
          return <CheckCircle className="h-5 w-5 text-emerald-600" />;
        case 'rejected':
        case 'canceled':
          return <XCircle className="h-5 w-5 text-red-600" />;
        case 'pending_new':
        case 'new':
        case 'accepted':
          return <Clock className="h-5 w-5 text-blue-600" />;
        default:
          return <AlertCircle className="h-5 w-5 text-gray-600" />;
      }
    };

    const getStatusColor = (status: string) => {
      switch (status.toLowerCase()) {
        case 'filled': return 'bg-emerald-100 text-emerald-800';
        case 'rejected':
        case 'canceled': return 'bg-red-100 text-red-800';
        case 'pending_new':
        case 'new':
        case 'accepted': return 'bg-blue-100 text-blue-800';
        case 'partially_filled': return 'bg-yellow-100 text-yellow-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    };

    const getSideIcon = (side: string) => {
      return side === 'buy' ? (
        <TrendingUp className="h-4 w-4 text-emerald-600" />
      ) : (
        <TrendingDown className="h-4 w-4 text-red-600" />
      );
    };

    const formatCurrency = (value: string | number) => {
      const num = typeof value === 'string' ? parseFloat(value) : value;
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
      }).format(num);
    };


    return (
      <tr className="hover:bg-gray-50 transition-colors duration-200 group">
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            {getStatusIcon(order.status)}
            <span className={`ml-2 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
              {order.status}
            </span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            <SymbolLogo symbol={order.symbol} className="mr-3" />
            <span className="text-sm font-semibold text-gray-900">{order.symbol}</span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center">
            {getSideIcon(order.side)}
            <span className={`ml-2 px-3 py-1 rounded-full text-xs font-medium ${
              order.side === 'buy' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
            }`}>
              {order.side.toUpperCase()}
            </span>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          <div>
            <p className="font-medium">{order.qty}</p>
            {order.filled_qty && order.filled_qty !== order.qty && (
              <p className="text-xs text-gray-500">Filled: {order.filled_qty}</p>
            )}
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
          {order.filled_avg_price ? (
            <div>
              <p className="font-medium">{formatCurrency(order.filled_avg_price)}</p>
              <p className="text-xs text-gray-500">
                Total: {formatCurrency(parseFloat(order.filled_avg_price) * parseFloat(order.filled_qty || order.qty))}
              </p>
            </div>
          ) : (
            <span className="text-gray-400">--</span>
          )}
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center space-x-2">
            <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-lg text-xs font-medium">
              {order.order_type || 'market'}
            </span>
            {order.time_in_force && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-lg text-xs font-medium">
                {order.time_in_force}
              </span>
            )}
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          <div>
            <p>{new Date(order.submitted_at).toLocaleDateString()}</p>
            <p className="text-xs">{new Date(order.submitted_at).toLocaleTimeString()}</p>
          </div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
          {order.filled_at ? (
            <div>
              <p>{new Date(order.filled_at).toLocaleDateString()}</p>
              <p className="text-xs">{new Date(order.filled_at).toLocaleTimeString()}</p>
            </div>
          ) : (
            <span className="text-gray-400">--</span>
          )}
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          {order.rejected_reason && (
            <div className="flex items-center max-w-48">
              <AlertCircle className="h-4 w-4 text-red-500 mr-1 flex-shrink-0" />
              <span className="text-sm text-red-600 truncate" title={order.rejected_reason}>
                {order.rejected_reason}
              </span>
            </div>
          )}
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
          <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <button className="p-1 text-gray-400 hover:text-blue-600 transition-colors duration-200">
              <Eye className="h-4 w-4" />
            </button>
            <button className="p-1 text-gray-400 hover:text-gray-600 transition-colors duration-200">
              <MoreHorizontal className="h-4 w-4" />
            </button>
          </div>
        </td>
      </tr>
    );
  };

  // Asegurar que orders es un array antes de usar filter
  const safeOrders = Array.isArray(orders) ? orders : [];

  // Filter by time range
  const filterByTimeRange = (orders: Order[]) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    return orders.filter(order => {
      const orderDate = new Date(order.submitted_at);
      switch (selectedTimeRange) {
        case 'today':
          return orderDate >= today;
        case 'week':
          return orderDate >= weekAgo;
        case 'month':
          return orderDate >= monthAgo;
        default:
          return true;
      }
    });
  };

  // Filtrar y ordenar orders
  const filteredAndSortedOrders = filterByTimeRange(safeOrders)
    .filter(order => {
      const matchesFilter = filter === 'all' ||
        (filter === 'filled' && order.status.toLowerCase() === 'filled') ||
        (filter === 'rejected' && ['rejected', 'canceled'].includes(order.status.toLowerCase())) ||
        (filter === 'pending' && ['pending_new', 'new', 'accepted'].includes(order.status.toLowerCase()));

      const matchesSearch = order.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           order.id.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    })
    .sort((a, b) => {
      let aVal, bVal;
      switch (sortBy) {
        case 'symbol':
          aVal = a.symbol;
          bVal = b.symbol;
          break;
        case 'qty':
          aVal = parseFloat(a.qty);
          bVal = parseFloat(b.qty);
          break;
        case 'filled_at':
          aVal = a.filled_at ? new Date(a.filled_at).getTime() : 0;
          bVal = b.filled_at ? new Date(b.filled_at).getTime() : 0;
          break;
        default:
          aVal = new Date(a.submitted_at).getTime();
          bVal = new Date(b.submitted_at).getTime();
      }

      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

  const totalPages = Math.ceil(filteredAndSortedOrders.length / PAGE_SIZE);

  useEffect(() => {
    if (currentPage > totalPages) {
      setCurrentPage(totalPages || 1);
    }
  }, [totalPages, currentPage]);

  const paginatedOrders = filteredAndSortedOrders.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE
  );

  const stats = {
    total: safeOrders.length,
    filled: safeOrders.filter(o => o.status.toLowerCase() === 'filled').length,
    rejected: safeOrders.filter(o => ['rejected', 'canceled'].includes(o.status.toLowerCase())).length,
    pending: safeOrders.filter(o => ['pending_new', 'new', 'accepted'].includes(o.status.toLowerCase())).length,
  };

  const successRate = stats.total > 0 ? ((stats.filled / stats.total) * 100).toFixed(1) : '0';
  const totalVolume = safeOrders.reduce((sum, order) => sum + parseInt(order.qty), 0);

  if (loading) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600 font-medium">Loading orders...</p>
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Orders</h1>
            <p className="text-gray-600">Monitor all orders executed through your broker</p>
          </div>
          <div className="mt-4 lg:mt-0 flex flex-wrap gap-3">
            <button
              onClick={fetchOrders}
              className="flex items-center px-4 py-2 border border-gray-300 rounded-xl hover:bg-gray-50 transition-all duration-200"
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </button>
            <button className="flex items-center px-4 py-2 border border-gray-300 rounded-xl hover:bg-gray-50 transition-all duration-200">
              <Download className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          title="Total Orders"
          value={stats.total}
          icon={BarChart3}
          gradient="bg-gradient-to-r from-blue-500 to-indigo-500"
        />
        <StatsCard
          title="Filled Orders"
          value={stats.filled}
          subtitle={`${successRate}% success rate`}
          icon={CheckCircle}
          gradient="bg-gradient-to-r from-emerald-500 to-green-500"
          trend={{ value: `${successRate}% success`, positive: parseFloat(successRate) > 80 }}
        />
        <StatsCard
          title="Pending Orders"
          value={stats.pending}
          icon={Clock}
          gradient="bg-gradient-to-r from-yellow-500 to-orange-500"
        />
        <StatsCard
          title="Total Volume"
          value={totalVolume.toLocaleString()}
          subtitle="shares traded"
          icon={Target}
          gradient="bg-gradient-to-r from-purple-500 to-pink-500"
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
                onClick={fetchOrders}
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
          <div className="flex flex-col space-y-4">
            {/* Top row: Search and Time Range */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search orders by symbol or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none w-80 transition-all duration-200"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Calendar className="h-5 w-5 text-gray-400" />
                <span className="text-sm font-medium text-gray-700">Time Range:</span>
                <div className="flex space-x-2">
                  <TimeRangeButton
                    active={selectedTimeRange === 'today'}
                    onClick={() => setSelectedTimeRange('today')}
                  >
                    Today
                  </TimeRangeButton>
                  <TimeRangeButton
                    active={selectedTimeRange === 'week'}
                    onClick={() => setSelectedTimeRange('week')}
                  >
                    Week
                  </TimeRangeButton>
                  <TimeRangeButton
                    active={selectedTimeRange === 'month'}
                    onClick={() => setSelectedTimeRange('month')}
                  >
                    Month
                  </TimeRangeButton>
                  <TimeRangeButton
                    active={selectedTimeRange === 'all'}
                    onClick={() => setSelectedTimeRange('all')}
                  >
                    All
                  </TimeRangeButton>
                </div>
              </div>
            </div>

            {/* Bottom row: Status filters and Sort */}
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Filter className="h-5 w-5 text-gray-400" />
                  <span className="text-sm font-medium text-gray-700">Status:</span>
                  <div className="flex space-x-2">
                    <FilterButton
                      active={filter === 'all'}
                      onClick={() => setFilter('all')}
                      count={stats.total}
                    >
                      All
                    </FilterButton>
                    <FilterButton
                      active={filter === 'filled'}
                      onClick={() => setFilter('filled')}
                      count={stats.filled}
                    >
                      Filled
                    </FilterButton>
                    <FilterButton
                      active={filter === 'pending'}
                      onClick={() => setFilter('pending')}
                      count={stats.pending}
                    >
                      Pending
                    </FilterButton>
                    <FilterButton
                      active={filter === 'rejected'}
                      onClick={() => setFilter('rejected')}
                      count={stats.rejected}
                    >
                      Rejected
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
                  <option value="submitted_at-desc">Latest submitted</option>
                  <option value="submitted_at-asc">Oldest submitted</option>
                  <option value="filled_at-desc">Latest filled</option>
                  <option value="filled_at-asc">Oldest filled</option>
                  <option value="symbol-asc">Symbol A-Z</option>
                  <option value="symbol-desc">Symbol Z-A</option>
                  <option value="qty-desc">Quantity high to low</option>
                  <option value="qty-asc">Quantity low to high</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">
              Orders ({filteredAndSortedOrders.length})
            </h3>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <DollarSign className="h-4 w-4" />
                <span>
                  Total Value: ${filteredAndSortedOrders
                    .filter(o => o.filled_avg_price)
                    .reduce((sum, o) => sum + (parseFloat(o.filled_avg_price!) * parseFloat(o.filled_qty || o.qty)), 0)
                    .toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          {filteredAndSortedOrders.length === 0 ? (
            <div className="p-12 text-center">
              <BarChart3 className="h-16 w-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg mb-2">
                {error ? 'Unable to load orders' : 'No orders found'}
              </p>
              <p className="text-gray-400 mb-4">
                {filter !== 'all' && !error ? 'Try adjusting your filters' : 'Orders will appear here when signals are processed'}
              </p>
              {filter !== 'all' && !error && (
                <button
                  onClick={() => {
                    setFilter('all');
                    setSearchTerm('');
                    setSelectedTimeRange('all');
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all duration-200"
                >
                  Clear filters
                </button>
              )}
              {error && (
                <button
                  onClick={fetchOrders}
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
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Side</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Quantity</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Avg Price</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Submitted</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Filled</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Reason</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {paginatedOrders.map((order) => (
                  <OrderRow key={order.id} order={order} />
                ))}
              </tbody>
            </table>
          )}
        </div>
        <Pagination
          currentPage={currentPage}
          totalItems={filteredAndSortedOrders.length}
          pageSize={PAGE_SIZE}
          onPageChange={setCurrentPage}
        />
      </div>

      {/* Summary Section */}
      {filteredAndSortedOrders.length > 0 && (
        <div className="mt-8 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-6">Order Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-4 border border-blue-100">
              <div className="flex items-center">
                <PieChart className="h-8 w-8 text-blue-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-blue-700">Total Volume</p>
                  <p className="text-xl font-bold text-blue-900">
                    {filteredAndSortedOrders.reduce((sum, order) => sum + parseInt(order.qty), 0).toLocaleString()} shares
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl p-4 border border-emerald-100">
              <div className="flex items-center">
                <TrendingUp className="h-8 w-8 text-emerald-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-emerald-700">Buy Orders</p>
                  <p className="text-xl font-bold text-emerald-900">
                    {filteredAndSortedOrders.filter(o => o.side === 'buy').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-red-50 to-pink-50 rounded-xl p-4 border border-red-100">
              <div className="flex items-center">
                <TrendingDown className="h-8 w-8 text-red-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-red-700">Sell Orders</p>
                  <p className="text-xl font-bold text-red-900">
                    {filteredAndSortedOrders.filter(o => o.side === 'sell').length}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-yellow-50 to-orange-50 rounded-xl p-4 border border-yellow-100">
              <div className="flex items-center">
                <Target className="h-8 w-8 text-yellow-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-yellow-700">Avg Order Size</p>
                  <p className="text-xl font-bold text-yellow-900">
                    {Math.round(filteredAndSortedOrders.reduce((sum, order) => sum + parseInt(order.qty), 0) / filteredAndSortedOrders.length).toLocaleString()} shares
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="mt-6 pt-6 border-t border-gray-100">
            <h4 className="text-md font-semibold text-gray-900 mb-4">Performance Metrics</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Fill Rate</span>
                <span className="text-sm font-semibold text-gray-900">{successRate}%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Avg Fill Time</span>
                <span className="text-sm font-semibold text-gray-900">2.3 min</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm text-gray-600">Today's Orders</span>
                <span className="text-sm font-semibold text-gray-900">
                  {safeOrders.filter(o => {
                    const today = new Date();
                    const orderDate = new Date(o.submitted_at);
                    return orderDate.toDateString() === today.toDateString();
                  }).length}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrdersPage;