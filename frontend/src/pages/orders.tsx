import React, { useState, useEffect } from 'react';
import { BarChart3, CheckCircle, XCircle, Clock, AlertCircle, RefreshCw, Filter, TrendingUp, TrendingDown } from 'lucide-react';

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
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'filled' | 'rejected' | 'pending'>('all');

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/orders');
      const data = await response.json();

      if (data.error) {
        setError(data.error);
        setOrders([]);
      } else {
        setOrders(data);
        setError(null);
      }
    } catch (err) {
      setError('Failed to load orders');
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 15000); // Refresh every 15s
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'filled':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
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
      case 'filled': return 'bg-green-100 text-green-800';
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
      <TrendingUp className="h-4 w-4 text-green-600" />
    ) : (
      <TrendingDown className="h-4 w-4 text-red-600" />
    );
  };

  const filteredOrders = orders.filter(order => {
    if (filter === 'all') return true;
    if (filter === 'filled') return order.status.toLowerCase() === 'filled';
    if (filter === 'rejected') return ['rejected', 'canceled'].includes(order.status.toLowerCase());
    if (filter === 'pending') return ['pending_new', 'new', 'accepted'].includes(order.status.toLowerCase());
    return true;
  });

  const stats = {
    total: orders.length,
    filled: orders.filter(o => o.status.toLowerCase() === 'filled').length,
    rejected: orders.filter(o => ['rejected', 'canceled'].includes(o.status.toLowerCase())).length,
    pending: orders.filter(o => ['pending_new', 'new', 'accepted'].includes(o.status.toLowerCase())).length,
  };

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

  if (loading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600" />
          <span className="ml-2 text-gray-600">Loading orders...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Trading Orders</h1>
            <p className="text-gray-600 mt-1">Monitor all orders executed through Alpaca</p>
          </div>
          <button
            onClick={fetchOrders}
            className="flex items-center px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <BarChart3 className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Orders</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <CheckCircle className="h-8 w-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Filled</p>
              <p className="text-2xl font-bold text-gray-900">{stats.filled}</p>
              <p className="text-xs text-gray-500">
                {stats.total > 0 ? `${((stats.filled / stats.total) * 100).toFixed(1)}%` : '0%'} success rate
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <Clock className="h-8 w-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Pending</p>
              <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <XCircle className="h-8 w-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Rejected</p>
              <p className="text-2xl font-bold text-gray-900">{stats.rejected}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <Filter className="h-5 w-5 text-gray-400" />
            <span className="text-sm font-medium text-gray-700">Filter by status:</span>
            <div className="flex space-x-2">
              {[
                { key: 'all', label: 'All Orders' },
                { key: 'filled', label: 'Filled' },
                { key: 'pending', label: 'Pending' },
                { key: 'rejected', label: 'Rejected' }
              ].map((status) => (
                <button
                  key={status.key}
                  onClick={() => setFilter(status.key as any)}
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    filter === status.key
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {status.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">
            Orders ({filteredOrders.length})
          </h3>
        </div>

        {error && (
          <div className="px-6 py-4 bg-red-50 border-b border-red-200">
            <div className="flex items-center text-red-600">
              <AlertCircle className="h-5 w-5 mr-2" />
              {error}
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          {filteredOrders.length === 0 ? (
            <div className="p-8 text-center">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">
                {error ? 'Unable to load orders' : 'No orders found'}
              </p>
              {filter !== 'all' && !error && (
                <button
                  onClick={() => setFilter('all')}
                  className="mt-2 text-blue-600 hover:text-blue-700 underline"
                >
                  View all orders
                </button>
              )}
              {error && (
                <button
                  onClick={fetchOrders}
                  className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Retry
                </button>
              )}
            </div>
          ) : (
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Symbol</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Side</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quantity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filled</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Avg Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filled At</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredOrders.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(order.status)}
                        <span className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(order.status)}`}>
                          {order.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-900">{order.symbol}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getSideIcon(order.side)}
                        <span className={`ml-1 text-sm font-medium ${
                          order.side === 'buy' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {order.side.toUpperCase()}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.qty}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.filled_qty || '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {order.filled_avg_price ? formatCurrency(order.filled_avg_price) : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">
                        {order.order_type || 'market'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatTime(order.submitted_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.filled_at ? formatTime(order.filled_at) : '--'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">
                      {order.rejected_reason && (
                        <div className="flex items-center max-w-xs">
                          <AlertCircle className="h-4 w-4 mr-1 flex-shrink-0" />
                          <span className="truncate" title={order.rejected_reason}>
                            {order.rejected_reason}
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

      {/* Summary Section */}
      {filteredOrders.length > 0 && (
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Order Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Volume</p>
              <p className="text-xl font-bold text-gray-900">
                {filteredOrders.reduce((sum, order) => sum + parseInt(order.qty), 0)} shares
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Buy Orders</p>
              <p className="text-xl font-bold text-green-600">
                {filteredOrders.filter(o => o.side === 'buy').length}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Sell Orders</p>
              <p className="text-xl font-bold text-red-600">
                {filteredOrders.filter(o => o.side === 'sell').length}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrdersPage;