import React from 'react';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  MoreVertical,
  X,
  Eye,
  Target,
} from 'lucide-react';
import SymbolLogo from '../SymbolLogo';

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
}

interface SignalCardProps {
  signal: Signal;
  onApprove?: (signalId: number) => void;
  onReject?: (signalId: number) => void;
  onViewDetails?: (signal: Signal) => void;
  compact?: boolean;
}

const SignalCard: React.FC<SignalCardProps> = ({
  signal,
  onApprove,
  onReject,
  onViewDetails,
  compact = false,
}) => {
  const getStatusConfig = (status: SignalStatus) => {
    switch (status) {
      case 'pending':
        return {
          icon: Clock,
          color: 'text-warning-600',
          bg: 'bg-warning-50',
          border: 'border-warning-200',
          label: 'Pending',
          pulse: true,
        };
      case 'validated':
        return {
          icon: CheckCircle,
          color: 'text-blue-600',
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          label: 'Validated',
          pulse: false,
        };
      case 'executed':
        return {
          icon: CheckCircle,
          color: 'text-success-600',
          bg: 'bg-success-50',
          border: 'border-success-200',
          label: 'Executed',
          pulse: false,
        };
      case 'bracket_created':
        return {
          icon: CheckCircle,
          color: 'text-indigo-600',
          bg: 'bg-indigo-50',
          border: 'border-indigo-200',
          label: 'Bracket Created',
          pulse: false,
        };
      case 'bracket_failed':
        return {
          icon: XCircle,
          color: 'text-error-600',
          bg: 'bg-error-50',
          border: 'border-error-200',
          label: 'Bracket Failed',
          pulse: false,
        };
      case 'error':
        return {
          icon: XCircle,
          color: 'text-error-600',
          bg: 'bg-error-50',
          border: 'border-error-200',
          label: 'Error',
          pulse: false,
        };
      case 'rejected':
        return {
          icon: X,
          color: 'text-slate-500',
          bg: 'bg-slate-50',
          border: 'border-slate-200',
          label: 'Rejected',
          pulse: false,
        };
      default:
        return {
          icon: Clock,
          color: 'text-slate-600',
          bg: 'bg-slate-50',
          border: 'border-slate-200',
          label: status,
          pulse: false,
        };
    }
  };

  const getActionConfig = (action: 'buy' | 'sell') =>
    action === 'buy'
      ? {
          color: 'text-success-700',
          bg: 'bg-success-100',
          border: 'border-success-200',
          icon: TrendingUp,
        }
      : {
          color: 'text-error-700',
          bg: 'bg-error-100',
          border: 'border-error-200',
          icon: TrendingDown,
        };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80)
      return 'text-success-600 bg-success-100 border-success-200';
    if (confidence >= 60)
      return 'text-warning-600 bg-warning-100 border-warning-200';
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
  const confidence = signal.confidence ?? 0;

  if (compact) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg hover:shadow-md transition-all duration-200 group">
        <div className="p-4">
          <div className="flex items-center justify-between">
            {/* Left Section: Symbol */}
            <div className="flex items-center space-x-3 flex-1">
              <SymbolLogo
                symbol={signal.symbol}
                className="w-10 h-10 flex-shrink-0"
              />
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-lg font-bold text-slate-900">
                    {signal.symbol}
                  </span>
                  <span
                    className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold border ${actionConfig.bg} ${actionConfig.color} ${actionConfig.border}`}
                  >
                    <ActionIcon className="w-3 h-3 mr-1" />
                    {signal.action.toUpperCase()}
                  </span>
                </div>
              </div>
            </div>

            {/* Center Section: Details */}
            <div className="hidden md:flex items-center space-x-6 flex-1 justify-center text-sm text-slate-600">
              <div>{signal.strategy_id}</div>
              <span>•</span>
              <div>{formatTime(signal.timestamp)}</div>
              {signal.quantity !== undefined && (
                <>
                  <span>•</span>
                  <div>Qty {signal.quantity}</div>
                </>
              )}
              {signal.confidence !== undefined && (
                <>
                  <span>•</span>
                  <div
                    className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getConfidenceColor(confidence)}`}
                  >
                    {confidence}%
                  </div>
                </>
              )}
            </div>

            {/* Right Section: Status & Actions */}
            <div className="flex items-center space-x-2">
              <span
                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold border ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border}`}
              >
                <StatusIcon
                  className={`w-3 h-3 mr-1 ${statusConfig.pulse ? 'animate-pulse' : ''}`}
                />
                {statusConfig.label}
              </span>
              <button
                onClick={() => onViewDetails?.(signal)}
                className="p-1 rounded-full text-slate-500 hover:bg-slate-100"
              >
                <Eye className="w-4 h-4" />
              </button>
              {signal.status === 'pending' && (
                <>
                  <button
                    onClick={() => onApprove?.(signal.id)}
                    className="p-1 rounded-full text-success-600 hover:bg-success-50"
                  >
                    <CheckCircle className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => onReject?.(signal.id)}
                    className="p-1 rounded-full text-error-600 hover:bg-error-50"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Mobile Details */}
          <div className="md:hidden mt-3 pt-3 border-t border-slate-100 text-sm text-slate-600">
            <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-2">
              <div>{signal.strategy_id}</div>
              <span>•</span>
              <div>{formatTime(signal.timestamp)}</div>
              {signal.quantity !== undefined && (
                <>
                  <span>•</span>
                  <div>Qty {signal.quantity}</div>
                </>
              )}
              {signal.confidence !== undefined && (
                <>
                  <span>•</span>
                  <div
                    className={`px-2 py-0.5 rounded-full text-xs font-semibold border ${getConfidenceColor(confidence)}`}
                  >
                    {confidence}%
                  </div>
                </>
              )}
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
              <h3 className="text-lg font-bold text-slate-900">
                {signal.symbol}
              </h3>
              <span
                className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${actionConfig.bg} ${actionConfig.color} ${actionConfig.border}`}
              >
                <ActionIcon className="w-4 h-4 mr-2" />
                {signal.action.toUpperCase()}
              </span>
            </div>
            <div className="flex items-center space-x-4 text-sm text-slate-600">
              <span>Strategy: {signal.strategy_id}</span>
              <span>•</span>
              <span>{formatTime(signal.timestamp)}</span>
            </div>
          </div>
        </div>

        {/* Status */}
        <div className="flex items-center space-x-3">
          <span
            className={`inline-flex items-center px-3 py-1.5 rounded-xl text-sm font-semibold border ${statusConfig.bg} ${statusConfig.color} ${statusConfig.border}`}
          >
            <StatusIcon
              className={`w-4 h-4 mr-2 ${statusConfig.pulse ? 'animate-pulse' : ''}`}
            />
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
        {signal.confidence !== undefined && (
          <div className="text-center p-3 bg-slate-50 rounded-xl">
            <p className="text-xs font-medium text-slate-500 mb-1">
              Confidence
            </p>
            <div className="flex items-center justify-center space-x-1">
              <div
                className={`w-2 h-2 rounded-full ${getConfidenceColor(confidence).includes('success')
                  ? 'bg-success-500'
                  : getConfidenceColor(confidence).includes('warning')
                    ? 'bg-warning-500'
                    : 'bg-error-500'
                }`}
              />
              <span className="text-lg font-bold text-slate-900">
                {confidence}%
              </span>
            </div>
          </div>
        )}

        {signal.quantity !== undefined && (
          <div className="text-center p-3 bg-slate-50 rounded-xl">
            <p className="text-xs font-medium text-slate-500 mb-1">Quantity</p>
            <p className="text-lg font-bold text-slate-900">
              {signal.quantity}
            </p>
          </div>
        )}
      </div>

      {/* Reason */}
      {signal.reason && (
        <div className="mb-4">
          <h4 className="text-sm font-medium text-slate-700 mb-2 flex items-center">
            <Target className="w-4 h-4 mr-1" />
            Reason
          </h4>
          <p className="text-sm text-slate-600 bg-slate-50 p-3 rounded-xl">
            {signal.reason}
          </p>
        </div>
      )}

      {signal.error_message && (
        <div className="mb-4 text-sm text-error-600 bg-error-50 border border-error-200 p-3 rounded-xl">
          {signal.error_message}
        </div>
      )}

      {/* Action Buttons */}
      {signal.status === 'pending' && (
        <div className="flex items-center space-x-3 pt-4 border-t border-slate-100">
          <button
            onClick={() => onApprove?.(signal.id)}
            className="btn-primary flex-1"
          >
            <CheckCircle className="w-4 h-4 mr-2" />
            Approve
          </button>
          <button
            onClick={() => onViewDetails?.(signal)}
            className="btn-secondary"
          >
            <Eye className="w-4 h-4 mr-2" />
            Details
          </button>
          <button
            onClick={() => onReject?.(signal.id)}
            className="btn-ghost text-error-600 hover:bg-error-50"
          >
            <X className="w-4 h-4 mr-2" />
            Reject
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

