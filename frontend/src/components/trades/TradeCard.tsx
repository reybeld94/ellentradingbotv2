import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Brain,
  ArrowUpRight,
  ArrowDownRight,
  Eye
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
  onClose
}) => {
  const isProfit = (trade.realized_pnl || trade.unrealized_pnl || 0) >= 0;
  const totalPnl = trade.realized_pnl || trade.unrealized_pnl || 0;
  const pnlPercent = trade.pnl_percent || ((totalPnl / (trade.entry_price * trade.quantity)) * 100) || 0;
  
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getSideConfig = (side: 'buy' | 'sell') => {
    return side === 'buy'
      ? {
          color: 'text-green-700',
          bg: 'bg-green-100',
          border: 'border-green-200',
          icon: TrendingUp,
          label: 'LONG'
        }
      : {
          color: 'text-red-700',
          bg: 'bg-red-100',
          border: 'border-red-200',
          icon: TrendingDown,
          label: 'SHORT'
        };
  };

  const sideConfig = getSideConfig(trade.side);

  return (
    <div className="bg-white border border-slate-200 rounded-lg hover:shadow-md transition-all duration-200 group">
      <div className="p-4">
        <div className="flex items-center justify-between">
          {/* Left Section: Symbol + Basic Info */}
          <div className="flex items-center space-x-4 flex-1">
            <div className="flex items-center space-x-3">
              <SymbolLogo symbol={trade.symbol} className="w-10 h-10 flex-shrink-0" />
              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <h3 className="text-lg font-bold text-slate-900">{trade.symbol}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${sideConfig.bg} ${sideConfig.color}`}>
                    {sideConfig.label}
                  </span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    trade.status === 'open' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {trade.status.toUpperCase()}
                  </span>
                </div>
                <div className="text-sm text-slate-500">
                  #{trade.id.slice(0, 8)} • {formatTime(trade.entry_time)}
                </div>
              </div>
            </div>
          </div>

          {/* Center Section: Trade Details */}
          <div className="hidden md:flex items-center space-x-8 flex-1 justify-center">
            <div className="text-center">
              <div className="text-xs text-slate-500 mb-1">Quantity</div>
              <div className="text-sm font-semibold text-slate-900">{trade.quantity}</div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-slate-500 mb-1">Entry Price</div>
              <div className="text-sm font-semibold text-slate-900">${trade.entry_price.toFixed(2)}</div>
            </div>

            {trade.exit_price && (
              <div className="text-center">
                <div className="text-xs text-slate-500 mb-1">Exit Price</div>
                <div className="text-sm font-semibold text-slate-900">${trade.exit_price.toFixed(2)}</div>
              </div>
            )}

            {trade.strategy_name && (
              <div className="text-center">
                <div className="text-xs text-slate-500 mb-1">Strategy</div>
                <div className="text-sm font-semibold text-slate-700 flex items-center">
                  <Brain className="w-3 h-3 mr-1" />
                  {trade.strategy_name}
                </div>
              </div>
            )}
          </div>

          {/* Right Section: PnL + Actions */}
          <div className="flex items-center space-x-4">
            {/* PnL */}
            <div className="text-right">
              <div className={`text-lg font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                {isProfit ? '+' : ''}{formatCurrency(totalPnl)}
              </div>
              <div className={`text-sm flex items-center justify-end ${isProfit ? 'text-green-500' : 'text-red-500'}`}>
                {isProfit ? <ArrowUpRight className="w-3 h-3 mr-1" /> : <ArrowDownRight className="w-3 h-3 mr-1" />}
                {isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => onViewDetails?.(trade)}
                className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
                title="View Details"
              >
                <Eye className="w-4 h-4" />
              </button>
              
              {trade.status === 'open' && onClose && (
                <button
                  onClick={() => onClose(trade.id)}
                  className="px-3 py-1.5 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors border border-red-200"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Details - Only show on smaller screens */}
        <div className="md:hidden mt-3 pt-3 border-t border-slate-100">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-xs text-slate-500">Quantity</div>
              <div className="text-sm font-semibold">{trade.quantity}</div>
            </div>
            <div>
              <div className="text-xs text-slate-500">Entry</div>
              <div className="text-sm font-semibold">${trade.entry_price.toFixed(2)}</div>
            </div>
            {trade.exit_price ? (
              <div>
                <div className="text-xs text-slate-500">Exit</div>
                <div className="text-sm font-semibold">${trade.exit_price.toFixed(2)}</div>
              </div>
            ) : (
              <div>
                <div className="text-xs text-slate-500">Status</div>
                <div className="text-sm font-semibold text-blue-600">Active</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradeCard;

