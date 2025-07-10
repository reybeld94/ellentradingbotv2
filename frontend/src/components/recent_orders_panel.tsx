import React from 'react';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';

interface Order {
  id: string;
  symbol: string;
  qty: string;
  side: string;
  status: string;
  submitted_at: string;
  filled_at?: string;
  rejected_reason?: string;
}

const OrderItem: React.FC<{ order: Order }> = ({ order }) => {
  const sideBg = order.side === 'buy' ? 'bg-emerald-100' : 'bg-red-100';
  const sideIcon = order.side === 'buy' ? (
    <TrendingUp className="h-5 w-5 text-emerald-600" />
  ) : (
    <TrendingDown className="h-5 w-5 text-red-600" />
  );

  const statusColor =
    order.status === 'filled'
      ? 'bg-emerald-100 text-emerald-800'
      : order.status === 'rejected'
      ? 'bg-red-100 text-red-800'
      : 'bg-blue-100 text-blue-800';

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors duration-200">
      <div className="flex items-center">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${sideBg}`}>{sideIcon}</div>
        <div className="ml-3">
          <p className="font-semibold text-gray-900">{order.symbol}</p>
          <p className="text-sm text-gray-600">{order.qty} units</p>
        </div>
      </div>
      <div className="text-right">
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColor}`}>{order.status}</span>
        <p className="text-xs text-gray-500 mt-1">{new Date(order.submitted_at).toLocaleTimeString()}</p>
      </div>
    </div>
  );
};

const RecentOrdersPanel: React.FC<{ orders: Order[] }> = ({ orders }) => {
  const displayed = Array.isArray(orders) ? orders.slice(0, 5) : [];
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Recent Orders</h3>
        <span className="text-sm text-gray-500">{orders.length} total</span>
      </div>
      <div className="space-y-4">
        {displayed.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No orders found</p>
          </div>
        ) : (
          displayed.map((o) => <OrderItem key={o.id} order={o} />)
        )}
      </div>
    </div>
  );
};

export default RecentOrdersPanel;
