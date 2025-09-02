import React from 'react';
import { TrendingUp, TrendingDown, Clock, CheckCircle, XCircle, X, MoreVertical, Eye, Activity } from 'lucide-react';
import SymbolLogo from '../SymbolLogo';

interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  status: 'pending' | 'filled' | 'partially_filled' | 'cancelled' | 'rejected';
  quantity: number;
  filled_quantity?: number;
  limit_price?: number;
  stop_price?: number;
  avg_fill_price?: number;
  created_at: string;
  updated_at: string;
  time_in_force?: 'day' | 'gtc' | 'ioc' | 'fok';
  strategy_id?: string;
  strategy_name?: string;
  trail_percent?: number;
}

interface OrderCardProps {
  order: Order;
  onCancel?: (orderId: string) => void;
  onModify?: (order: Order) => void;
  onViewDetails?: (order: Order) => void;
  compact?: boolean;
}

const OrderCard: React.FC<OrderCardProps> = ({
  order,
  onCancel,
  onModify,
  onViewDetails,
  compact = false
}) => {
  const getStatusConfig = (status: Order['status']) => {
    switch (status) {
      case 'pending':
        return {
          icon: Clock,
          color: 'text-warning-600',
          bg: 'bg-warning-50',
          border: 'border-warning-200',
          label: 'Pending',
          pulse: true
        };
      case 'filled':
        return {
          icon: CheckCircle,
          color: 'text-success-600',
          bg: 'bg-success-50',
          border: 'border-success-200',
          label: 'Filled',
          pulse: false
        };
      case 'partially_filled':
        return {
          icon: Activity,
          color: 'text-primary-600',
          bg: 'bg-primary-50',
          border: 'border-primary-200',
          label: 'Partial',
          pulse: true
        };
      case 'cancelled':
        return {
          icon: X,
          color: 'text-slate-500',
          bg: 'bg-slate-50',
          border: 'border-slate-200',
          label: 'Cancelled',
          pulse: false
        };
      case 'rejected':
        return {
          icon: XCircle,
          color: 'text-error-600',
          bg: 'bg-error-50',
          border: 'border-error-200',
          label: 'Rejected',
          pulse: false
        };
    }
  };

  const getTypeConfig = (type: Order['type']) => {
    switch (type) {
      case 'market':
        return { label: 'Market', color: 'text-primary-700', bg: 'bg-primary-100' };
      case 'limit':
        return { label: 'Limit', color: 'text-indigo-700', bg: 'bg-indigo-100' };
      case 'stop':
        return { label: 'Stop', color: 'text-warning-700', bg: 'bg-warning-100' };
      case 'stop_limit':
        return { label: 'Stop Limit', color: 'text-error-700', bg: 'bg-error-100' };
    }
  };

  const getSideConfig = (side: 'buy' | 'sell') => {
    return side === 'buy'
      ? {
          color: 'text-success-700',
          bg: 'bg-success-100',
          border: 'border-success-200',
          icon: TrendingUp
        }
      : {
          color: 'text-error-700',
          bg: 'bg-error-100',
          border: 'border-error-200',
          icon: TrendingDown
        };
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateProgress = () => {
    if (order.status !== 'partially_filled' || !order.filled_quantity) return 0;
    return (order.filled_quantity / order.quantity) * 100;
  };

  const statusConfig = getStatusConfig(order.status);
  const typeConfig = getTypeConfig(order.type);
  const sideConfig = getSideConfig(order.side);
  const StatusIcon = statusConfig.icon;
  const SideIcon = sideConfig.icon;
  const progress = calculateProgress();

  if (compact) {
    return (
      <div className="card p-4 hover:shadow-medium transition-all duration-300">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <SymbolLogo symbol={order.symbol} className="w-8 h-8" />
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="font-semibold text-slate-900">{order.symbol}</span>
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-semibold border ${sideConfig.bg} ${sideConfig.color} ${sideConfig.border}`}>
                  <SideIcon className="w-3 h-3 mr-1" />
                  {order.side.toUpperCase()}
                </span>
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-semibold ${typeConfig.bg} ${typeConfig.color}`}>
                  {typeConfig.label}
                </span>
              </div>
              <p className="text-sm text-slate-600">
                {order.quantity} @ {order.limit_price ? `$${order.limit_price.toFixed(2)}` : 'Market'}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${statusConfig.bg} ${statusConfig.border} border`}>
              <StatusIcon className={`w-4 h-4 ${statusConfig.color} ${statusConfig.pulse ? 'animate-pulse' : ''}`} />
            </div>
            <span className="text-sm text-slate-500">{formatTime(order.created_at)}</span>
          </div>
        </div>

        {progress > 0 && progress < 100 && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-slate-600 mb-1">
              <span>Progress</span>
              <span>{progress.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="card p-6 hover:shadow-medium transition-all duration-300 group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-4">
          <SymbolLogo symbol={order.symbol} className="w-12 h-12" />
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-bold text-slate-900">{order.symbol}</h3>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${sideConfig.bg} ${sideConfig.color} ${sideConfig.border}`}>
                <SideIcon className="w-4 h-4 mr-2" />
                {order.side.toUpperCase()} Order
              </span>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold ${typeConfig.bg} ${typeConfig.color}`}>
                {typeConfig.label}
              </span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-slate-600">
              <span>Order #{order.id.slice(0, 8)}</span>
              <span>•</span>
              <span>{formatTime(order.created_at)}</span>
              {order.strategy_name && (
                <>
                  <span>•</span>
                  <span>{order.strategy_name}</span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border}`}>
            <StatusIcon className={`w-4 h-4 mr-2 ${statusConfig.pulse ? 'animate-pulse' : ''}`} />
            {statusConfig.label}
          </span>
          
          <div className="relative">
            <button className="p-2 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <MoreVertical className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Order Details Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Quantity</p>
          <p className="text-lg font-bold text-slate-900">{order.quantity}</p>
          {order.filled_quantity && order.filled_quantity > 0 && (
            <p className="text-xs text-primary-600">{order.filled_quantity} filled</p>
          )}
        </div>

        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Price</p>
          <p className="text-lg font-bold text-slate-900">
            {order.limit_price ? `$${order.limit_price.toFixed(2)}` : 'Market'}
          </p>
          {order.avg_fill_price && (
            <p className="text-xs text-success-600">Avg: ${order.avg_fill_price.toFixed(2)}</p>
          )}
        </div>

        {order.stop_price && (
          <div className="text-center p-3 bg-slate-50 rounded-xl">
            <p className="text-xs font-medium text-slate-500 mb-1">Stop Price</p>
            <p className="text-lg font-bold text-warning-600">${order.stop_price.toFixed(2)}</p>
          </div>
        )}

        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Value</p>
          <p className="text-lg font-bold text-slate-900">
            ${((order.limit_price || 0) * order.quantity).toLocaleString()}
          </p>
          {order.time_in_force && (
            <p className="text-xs text-slate-500">{order.time_in_force.toUpperCase()}</p>
          )}
        </div>
      </div>

      {/* Progress Bar for Partially Filled Orders */}
      {progress > 0 && progress < 100 && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-slate-600 mb-2">
            <span>Fill Progress</span>
            <span>{order.filled_quantity}/{order.quantity} ({progress.toFixed(1)}%)</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-primary-500 to-primary-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <div className="text-sm text-slate-600">
          {order.status === 'filled' && order.avg_fill_price && (
            <span>Filled at ${order.avg_fill_price.toFixed(2)} • {formatTime(order.updated_at)}</span>
          )}
          {order.status === 'pending' && (
            <span>Waiting for execution...</span>
          )}
          {order.status === 'partially_filled' && (
            <span>{((1 - progress/100) * order.quantity).toFixed(0)} remaining</span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onViewDetails?.(order)}
            className="btn-ghost text-sm"
          >
            <Eye className="w-4 h-4 mr-1" />
            Details
          </button>
          
          {(order.status === 'pending' || order.status === 'partially_filled') && (
            <>
              <button
                onClick={() => onModify?.(order)}
                className="btn-secondary text-sm"
              >
                Modify
              </button>
              <button
                onClick={() => onCancel?.(order.id)}
                className="btn-ghost text-error-600 hover:bg-error-50 text-sm"
              >
                <X className="w-4 h-4 mr-1" />
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrderCard;

