import React from 'react';
import {
  TrendingUp, TrendingDown, Clock, CheckCircle, XCircle,
  Brain, Target, MoreVertical, Play, X, Eye
} from 'lucide-react';
import SymbolLogo from '../SymbolLogo';

interface Signal {
  id: number;
  symbol: string;
  action: 'BUY' | 'SELL';
  price: number;
  confidence: number;
  strategy_id: string;
  strategy_name?: string;
  created_at: string;
  status: 'pending' | 'processed' | 'error' | 'cancelled';
  quantity?: number;
  target_price?: number;
  stop_loss?: number;
  reasoning?: string;
  market_conditions?: string;
}

interface SignalCardProps {
  signal: Signal;
  onExecute?: (signalId: number) => void;
  onCancel?: (signalId: number) => void;
  onViewDetails?: (signal: Signal) => void;
  compact?: boolean;
}

const SignalCard: React.FC<SignalCardProps> = ({
  signal,
  onExecute,
  onCancel,
  onViewDetails,
  compact = false
}) => {
  const getStatusConfig = (status: Signal['status']) => {
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
      case 'processed':
        return {
          icon: CheckCircle,
          color: 'text-success-600',
          bg: 'bg-success-50',
          border: 'border-success-200',
          label: 'Executed',
          pulse: false
        };
      case 'error':
        return {
          icon: XCircle,
          color: 'text-error-600',
          bg: 'bg-error-50',
          border: 'border-error-200',
          label: 'Failed',
          pulse: false
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
    }
  };

  const getActionConfig = (action: 'BUY' | 'SELL') => {
    return action === 'BUY'
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-success-600 bg-success-100 border-success-200';
    if (confidence >= 60) return 'text-warning-600 bg-warning-100 border-warning-200';
    return 'text-error-600 bg-error-100 border-error-200';
  };

  const formatTime = (dateString: string) => {
    const now = new Date();
    const signalTime = new Date(dateString);
    const diffMs = now.getTime() - signalTime.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return signalTime.toLocaleDateString();
  };

  const statusConfig = getStatusConfig(signal.status);
  const actionConfig = getActionConfig(signal.action);
  const StatusIcon = statusConfig.icon;
  const ActionIcon = actionConfig.icon;

  if (compact) {
    return (
      <div className="card p-4 hover:shadow-medium transition-all duration-300 group">
        <div className="flex items-center space-x-4">
          {/* Symbol & Action */}
          <div className="flex items-center space-x-3">
            <SymbolLogo symbol={signal.symbol} className="w-8 h-8" />
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-semibold text-slate-900">{signal.symbol}</span>
                <span className={`inline-flex items-center px-2 py-1 rounded-lg text-xs font-semibold border ${actionConfig.bg} ${actionConfig.color} ${actionConfig.border}`}>
                  <ActionIcon className="w-3 h-3 mr-1" />
                  {signal.action}
                </span>
              </div>
              <p className="text-sm text-slate-600">${signal.price.toFixed(2)}</p>
            </div>
          </div>

          {/* Status & Confidence */}
          <div className="flex items-center space-x-2 ml-auto">
            <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold border ${getConfidenceColor(signal.confidence)}`}>
              {signal.confidence}%
            </span>
            <div className={`p-2 rounded-lg ${statusConfig.bg} ${statusConfig.border} border`}>
              <StatusIcon className={`w-4 h-4 ${statusConfig.color} ${statusConfig.pulse ? 'animate-pulse' : ''}`} />
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
          <SymbolLogo symbol={signal.symbol} className="w-12 h-12" />
          <div>
            <div className="flex items-center space-x-3 mb-1">
              <h3 className="text-lg font-bold text-slate-900">{signal.symbol}</h3>
              <span className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${actionConfig.bg} ${actionConfig.color} ${actionConfig.border}`}>
                <ActionIcon className="w-4 h-4 mr-2" />
                {signal.action} Signal
              </span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-slate-600">
              <span>${signal.price.toFixed(2)}</span>
              {signal.strategy_name && (
                <>
                  <span>•</span>
                  <span className="flex items-center">
                    <Brain className="w-3 h-3 mr-1" />
                    {signal.strategy_name}
                  </span>
                </>
              )}
              <span>•</span>
              <span>{formatTime(signal.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Status & Actions */}
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

      {/* Metrics Grid */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center p-3 bg-slate-50 rounded-xl">
          <p className="text-xs font-medium text-slate-500 mb-1">Confidence</p>
          <div className="flex items-center justify-center space-x-1">
            <div className={`w-2 h-2 rounded-full ${getConfidenceColor(signal.confidence).includes('success') ? 'bg-success-500' : getConfidenceColor(signal.confidence).includes('warning') ? 'bg-warning-500' : 'bg-error-500'}`}></div>
            <span className="text-lg font-bold text-slate-900">{signal.confidence}%</span>
          </div>
        </div>

        {signal.target_price && (
          <div className="text-center p-3 bg-slate-50 rounded-xl">
            <p className="text-xs font-medium text-slate-500 mb-1">Target</p>
            <p className="text-lg font-bold text-slate-900">${signal.target_price.toFixed(2)}</p>
          </div>
        )}

        {signal.quantity && (
          <div className="text-center p-3 bg-slate-50 rounded-xl">
            <p className="text-xs font-medium text-slate-500 mb-1">Quantity</p>
            <p className="text-lg font-bold text-slate-900">{signal.quantity}</p>
          </div>
        )}
      </div>

      {/* Reasoning */}
      {signal.reasoning && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-slate-700 mb-2 flex items-center">
            <Target className="w-4 h-4 mr-1" />
            Signal Reasoning
          </h4>
          <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl">
            {signal.reasoning}
          </p>
        </div>
      )}

      {/* Action Buttons */}
      {signal.status === 'pending' && (
        <div className="flex items-center space-x-3 pt-4 border-t border-slate-100">
          <button
            onClick={() => onExecute?.(signal.id)}
            className="btn-primary flex-1"
          >
            <Play className="w-4 h-4 mr-2" />
            Execute Signal
          </button>
          <button
            onClick={() => onViewDetails?.(signal)}
            className="btn-secondary"
          >
            <Eye className="w-4 h-4 mr-2" />
            Details
          </button>
          <button
            onClick={() => onCancel?.(signal.id)}
            className="btn-ghost text-error-600 hover:bg-error-50"
          >
            <X className="w-4 h-4 mr-2" />
            Cancel
          </button>
        </div>
      )}

      {signal.status !== 'pending' && (
        <div className="flex justify-center pt-4 border-t border-slate-100">
          <button
            onClick={() => onViewDetails?.(signal)}
            className="btn-ghost"
          >
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </button>
        </div>
      )}
    </div>
  );
};

export default SignalCard;
