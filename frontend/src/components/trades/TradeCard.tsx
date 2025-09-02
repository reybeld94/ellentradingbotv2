import React from 'react';
import {
  TrendingUp, TrendingDown, Target,
  Percent, DollarSign, Activity, Brain,
  ArrowUpRight, ArrowDownRight, Eye
} from 'lucide-react';
import SymbolLogo from '../SymbolLogo';

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

interface TradeCardProps {
  trade: Trade;
  onViewDetails?: (trade: Trade) => void;
  onClose?: (tradeId: string) => void;
  compact?: boolean;
}

const TradeCard: React.FC<TradeCardProps> = ({
  trade,
  onViewDetails,
  onClose,
  compact = false
}) => {
  const isProfit = (trade.realized_pnl || trade.unrealized_pnl || 0) >= 0;
  const totalPnl = trade.realized_pnl || trade.unrealized_pnl || 0;
  const pnlPercent = trade.pnl_percent || 0;
  
  const getSideConfig = (side: 'buy' | 'sell') => {
    return side === 'buy'
      ? {
          color: 'text-success-700',
          bg: 'bg-success-100',
          border: 'border-success-200',
          icon: TrendingUp,
          label: 'Long'
        }
      : {
          color: 'text-error-700',
          bg: 'bg-error-100',
          border: 'border-error-200',
          icon: TrendingDown,
          label: 'Short'
        };
  };

  const getStatusConfig = (status: 'open' | 'closed') => {
    return status === 'open'
      ? {
          color: 'text-primary-600',
          bg: 'bg-primary-50',
          border: 'border-primary-200',
          label: 'Open',
          pulse: true
        }
      : {
          color: 'text-slate-600',
          bg: 'bg-slate-50',
          border: 'border-slate-200',
          label: 'Closed',
          pulse: false
        };
  };

  const formatDuration = (minutes?: number) => {
    if (!minutes) return 'Active';
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d ${hours % 24}h`;
    if (hours > 0) return `${hours}h ${remainingMinutes}m`;
    return `${minutes}m`;
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(value));
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const sideConfig = getSideConfig(trade.side);
  const statusConfig = getStatusConfig(trade.status);
  const SideIcon = sideConfig.icon;

  if (compact) {
    return (
      <div className="card p-4 hover:shadow-medium transition-all duration-300">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <SymbolLogo symbol={trade.symbol} className="w-8 h-8" />
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <span className="font-semibold text-slate-900">{trade.symbol}</span>
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-semibold border ${sideConfig.bg} ${sideConfig.color} ${sideConfig.border}`}>
                  <SideIcon className="w-3 h-3 mr-1" />
                  {sideConfig.label}
                </span>
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-semibold border ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border} ${statusConfig.pulse ? 'animate-pulse' : ''}`}>
                  {statusConfig.label}
                </span>
              </div>
              <p className="text-sm text-slate-600">
                {trade.quantity} @ ${trade.entry_price.toFixed(2)}
                {trade.exit_price && ` → $${trade.exit_price.toFixed(2)}`}
              </p>
            </div>
          </div>

          <div className="text-right">
            <div className={`font-semibold ${isProfit ? 'text-success-600' : 'text-error-600'}`}>
              {isProfit ? '+' : ''}{formatCurrency(totalPnl)}
            </div>
            <div className={`text-sm ${isProfit ? 'text-success-600' : 'text-error-600'}`}>
              {isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6 hover:shadow-medium transition-all duration-300 group">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-4">
          <SymbolLogo symbol={trade.symbol} className="w-12 h-12" />
          <div>
            <div className="flex items-center space-x-3 mb-2">
              <h3 className="text-lg font-bold text-slate-900">{trade.symbol}</h3>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${sideConfig.bg} ${sideConfig.color} ${sideConfig.border}`}>
                <SideIcon className="w-4 h-4 mr-2" />
                {sideConfig.label} Position
              </span>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border} ${statusConfig.pulse ? 'animate-pulse' : ''}`}>
                {statusConfig.label}
              </span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-slate-600">
              <span>Trade #{trade.id.slice(0, 8)}</span>
              <span>•</span>
              <span>{formatTime(trade.entry_time)}</span>
              {trade.strategy_name && (
                <>
                  <span>•</span>
                  <span className="flex items-center">
                    <Brain className="w-3 h-3 mr-1" />
                    {trade.strategy_name}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* P&L Badge */}
        <div className={`text-right p-3 rounded-xl border ${isProfit ? 'bg-success-50 border-success-200' : 'bg-error-50 border-error-200'}`}>
          <div className={`text-xl font-bold ${isProfit ? 'text-success-700' : 'text-error-700'}`}>
            {isProfit ? '+' : ''}{formatCurrency(totalPnl)}
          </div>
          <div className={`text-sm ${isProfit ? 'text-success-600' : 'text-error-600'} flex items-center justify-end`}>
            {isProfit ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
            {isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%
          </div>
        </div>
      </div>

      {/* Trade Details Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Quantity</p>
          <p className="text-lg font-bold text-slate-900">{trade.quantity}</p>
        </div>

        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Entry Price</p>
          <p className="text-lg font-bold text-slate-900">${trade.entry_price.toFixed(2)}</p>
        </div>

        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">
            {trade.status === 'open' ? 'Current Price' : 'Exit Price'}
          </p>
          <p className="text-lg font-bold text-slate-900">
            ${(trade.exit_price || trade.current_price || 0).toFixed(2)}
          </p>
        </div>

        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Duration</p>
          <p className="text-lg font-bold text-slate-900">{formatDuration(trade.duration)}</p>
        </div>
      </div>

      {/* Additional Info */}
      <div className="space-y-3">
        {/* Trade Value */}
        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-slate-500" />
            <span className="text-sm font-medium text-slate-700">Trade Value</span>
          </div>
          <span className="font-semibold text-slate-900">
            ${(trade.quantity * trade.entry_price).toLocaleString()}
          </span>
        </div>

        {/* Fees */}
        {(trade.fees || trade.commission) && (
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <div className="flex items-center space-x-2">
              <Percent className="w-4 h-4 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">Fees & Commission</span>
            </div>
            <span className="font-semibold text-slate-900">
              ${((trade.fees || 0) + (trade.commission || 0)).toFixed(2)}
            </span>
          </div>
        )}

        {/* Tags */}
        {trade.tags && trade.tags.length > 0 && (
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
            <div className="flex items-center space-x-2">
              <Target className="w-4 h-4 text-slate-500" />
              <span className="text-sm font-medium text-slate-700">Tags</span>
            </div>
            <div className="flex flex-wrap gap-1">
              {trade.tags.map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 text-xs bg-primary-100 text-primary-700 rounded-lg"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100 mt-4">
        <div className="text-sm text-slate-600">
          {trade.status === 'open' ? (
            <span className="flex items-center">
              <Activity className="w-4 h-4 mr-1 text-primary-500" />
              Position active since {formatTime(trade.entry_time)}
            </span>
          ) : (
            <span>
              Closed on {trade.exit_time ? formatTime(trade.exit_time) : 'Unknown'}
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => onViewDetails?.(trade)}
            className="btn-ghost text-sm"
          >
            <Eye className="w-4 h-4 mr-1" />
            Details
          </button>
          
          {trade.status === 'open' && onClose && (
            <button
              onClick={() => onClose(trade.id)}
              className="btn-secondary text-sm"
            >
              Close Position
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TradeCard;
