import React, { useState, useEffect } from 'react';
import {
  Plus, Filter, Download, RefreshCw,
  LayoutGrid, List as ListIcon, TrendingUp
} from 'lucide-react';
import OrderCard from '../../components/orders/OrderCard';
import OrderFilters from '../../components/orders/OrderFilters';
import OrderTimeline from '../../components/orders/OrderTimeline';

type OrderStatus =
  | 'new'
  | 'sent'
  | 'accepted'
  | 'partially_filled'
  | 'filled'
  | 'canceled'
  | 'rejected'
  | 'pending_cancel';

interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop' | 'stop_limit';
  status: OrderStatus;
  qty: number;
  filled_qty?: number;
  limit_price?: number;
  stop_price?: number;
  avg_fill_price?: number;
  submitted_at: string;
  filled_at?: string;
  time_in_force?: 'day' | 'gtc' | 'ioc' | 'fok';
  strategy_id?: string;
  strategy_name?: string;
  trail_percent?: number;
  client_order_id?: string;
}

interface Strategy {
  id: string;
  name: string;
}

interface FilterOptions {
  search: string;
  status: string[];
  side: string[];
  type: string[];
  dateRange: string;
  strategy: string[];
  minAmount: string;
  maxAmount: string;
}

const OrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const [filters, setFilters] = useState<FilterOptions>({
    search: '',
    status: [],
    side: [],
    type: [],
    dateRange: '30d',
    strategy: [],
    minAmount: '',
    maxAmount: ''
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

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const response = await authenticatedFetch('/api/v1/orders/my');
      const data = await response.json();
      console.log('Orders API Response:', data); // DEBUG - remover después

      const parsed = Array.isArray(data.orders)
        ? data.orders.map((o: any) => ({
            id: o.id,
            symbol: o.symbol,
            side: o.side,
            order_type: o.order_type,
            status: o.status,
            qty: parseFloat(o.quantity), // API retorna 'quantity', no 'qty'
            filled_qty: parseFloat(o.filled_quantity || '0'), // API retorna 'filled_quantity'
            limit_price: o.limit_price ? parseFloat(o.limit_price) : undefined,
            stop_price: o.stop_price ? parseFloat(o.stop_price) : undefined,
            avg_fill_price: o.avg_fill_price ? parseFloat(o.avg_fill_price) : undefined,
            submitted_at: o.created_at, // API retorna 'created_at', no 'submitted_at'
            filled_at: o.filled_at,
            time_in_force: o.time_in_force,
            strategy_id: o.signal_id, // API retorna 'signal_id'
            strategy_name: undefined, // No viene en la respuesta
            client_order_id: o.client_order_id
          }))
        : [];

      console.log('Parsed orders:', parsed.length, 'orders'); // DEBUG - remover después
      setOrders(parsed);
    } catch (error) {
      console.error('Error fetching orders:', error);
      setOrders([]);
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
    fetchOrders();
    fetchStrategies();
    
    // Auto-refresh every 10 seconds for pending orders
    const interval = setInterval(fetchOrders, 10000);
    return () => clearInterval(interval);
  }, []);

  // Filter orders based on current filters
  const filteredOrders = orders.filter(order => {
    // Search filter
    if (filters.search && !order.symbol.toLowerCase().includes(filters.search.toLowerCase()) &&
        !order.id.toLowerCase().includes(filters.search.toLowerCase()) &&
        !order.strategy_name?.toLowerCase().includes(filters.search.toLowerCase())) {
      return false;
    }

    // Status filter
    if (filters.status.length > 0 && !filters.status.includes(order.status)) {
      return false;
    }

    // Side filter
    if (filters.side.length > 0 && !filters.side.includes(order.side)) {
      return false;
    }

    // Type filter
    if (filters.type.length > 0) {
      const isBracket = order.client_order_id?.toLowerCase().includes('bracket');
      if (!filters.type.some(t => (t === 'bracket' ? isBracket : t === order.order_type))) {
        return false;
      }
    }

    // Strategy filter
    if (filters.strategy.length > 0 && !filters.strategy.includes(order.strategy_id || '')) {
      return false;
    }

    // Amount filter
    const orderValue = (order.limit_price || 0) * order.qty;
    if (filters.minAmount && orderValue < parseFloat(filters.minAmount)) {
      return false;
    }
    if (filters.maxAmount && orderValue > parseFloat(filters.maxAmount)) {
      return false;
    }

    // Date range filter
    const orderDate = new Date(order.submitted_at);
    const now = new Date();
    const daysDiff = Math.floor((now.getTime() - orderDate.getTime()) / (1000 * 60 * 60 * 24));
    
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
    total: orders.length,
    pending: orders.filter(o => ['new', 'sent', 'accepted', 'pending_cancel'].includes(o.status)).length,
    filled: orders.filter(o => o.status === 'filled').length,
    partiallyFilled: orders.filter(o => o.status === 'partially_filled').length,
    canceled: orders.filter(o => o.status === 'canceled').length,
    totalValue: orders.reduce((sum, o) => sum + ((o.limit_price || 0) * o.qty), 0),
    filledValue: orders
      .filter(o => o.status === 'filled')
      .reduce((sum, o) => sum + ((o.avg_fill_price || o.limit_price || 0) * o.qty), 0)
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      await authenticatedFetch(`/api/v1/orders/${orderId}`, {
        method: 'DELETE'
      });
      // Refresh orders after cancellation
      fetchOrders();
    } catch (error) {
      console.error('Error cancelling order:', error);
    }
  };

  const handleModifyOrder = async (order: Order) => {
    // Implementation for order modification
    console.log('Modifying order:', order.id);
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      status: [],
      side: [],
      type: [],
      dateRange: '30d',
      strategy: [],
      minAmount: '',
      maxAmount: ''
    });
  };

  const exportOrders = () => {
    // Implementation for exporting orders to CSV
    console.log('Exporting orders...');
  };

  if (loading && orders.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <TrendingUp className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Orders</h2>
          <p className="text-slate-600">Fetching your order history...</p>
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
            <h1 className="text-3xl font-bold text-slate-900">Order Management</h1>
            <p className="text-slate-600 mt-1">
              Track and manage your trading orders in real-time
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
            
            <button onClick={exportOrders} className="btn-ghost">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            
            <button onClick={fetchOrders} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            <button className="btn-primary">
              <Plus className="w-4 h-4 mr-2" />
              New Order
            </button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
            <p className="text-sm text-slate-600">Total Orders</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-warning-600">{stats.pending}</p>
            <p className="text-sm text-slate-600">Pending</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-success-600">{stats.filled}</p>
            <p className="text-sm text-slate-600">Filled</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-primary-600">{stats.partiallyFilled}</p>
            <p className="text-sm text-slate-600">Partial</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-2xl font-bold text-slate-500">{stats.canceled}</p>
            <p className="text-sm text-slate-600">Canceled</p>
          </div>
          <div className="card p-4 text-center">
            <p className="text-lg font-bold text-slate-900">
              ${stats.filledValue.toLocaleString()}
            </p>
            <p className="text-sm text-slate-600">Filled Value</p>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          {showFilters && (
            <div className="lg:col-span-1">
              <OrderFilters
                filters={filters}
                onFiltersChange={setFilters}
                strategies={strategies}
                onReset={resetFilters}
              />
            </div>
          )}

          {/* Orders List */}
          <div className={showFilters ? 'lg:col-span-3' : 'lg:col-span-4'}>
            {filteredOrders.length === 0 ? (
              <div className="card p-12 text-center">
                <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <TrendingUp className="w-10 h-10 text-slate-400" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">No Orders Found</h3>
                <p className="text-slate-600 mb-6">
                  {orders.length === 0 
                    ? "You haven't placed any orders yet. Create your first order to get started."
                    : "No orders match your current filters. Try adjusting your search criteria."
                  }
                </p>
                {orders.length > 0 && (
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
                {filteredOrders.map((order) => (
                  <OrderCard
                    key={order.id}
                    order={order}
                    compact={viewMode === 'list'}
                    onCancel={handleCancelOrder}
                    onModify={handleModifyOrder}
                    onViewDetails={setSelectedOrder}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Load More */}
        {filteredOrders.length >= 20 && (
          <div className="text-center pt-8">
            <button className="btn-secondary">
              Load More Orders
            </button>
          </div>
        )}

        {/* Order Timeline Sidebar */}
        {selectedOrder && (
          <div className="fixed right-6 top-24 w-96 h-96 z-40">
            <div className="relative">
              <button
                onClick={() => setSelectedOrder(null)}
                className="absolute -top-2 -right-2 p-1 bg-slate-600 text-white rounded-full hover:bg-slate-700 z-50"
              >
                ×
              </button>
              <OrderTimeline 
                events={[
                  {
                    id: '1',
                    type: 'created',
                    timestamp: selectedOrder.submitted_at,
                    description: 'Order created',
                    details: `${selectedOrder.side.toUpperCase()} ${selectedOrder.qty} ${selectedOrder.symbol}`
                  },
                  {
                    id: '2',
                    type: 'submitted',
                    timestamp: selectedOrder.submitted_at,
                    description: 'Order submitted to exchange',
                    details: 'Waiting for execution'
                  }
                ]}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrdersPage;

