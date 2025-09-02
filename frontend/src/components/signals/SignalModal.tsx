import React from 'react';
import {
  X,
  TrendingUp,
  TrendingDown,
  CheckCircle,
  XCircle,
} from 'lucide-react';

import type { SignalStatus } from './SignalCard';

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

interface SignalModalProps {
  signal: Signal | null;
  isOpen: boolean;
  onClose: () => void;
  onApprove?: (signalId: number) => void;
  onReject?: (signalId: number) => void;
}

const statusLabels: Record<SignalStatus, string> = {
  pending: 'Pending',
  validated: 'Validated',
  rejected: 'Rejected',
  executed: 'Executed',
  bracket_created: 'Bracket Created',
  bracket_failed: 'Bracket Failed',
  error: 'Error',
};

const SignalModal: React.FC<SignalModalProps> = ({
  signal,
  isOpen,
  onClose,
  onApprove,
  onReject,
}) => {
  if (!isOpen || !signal) return null;

  const ActionIcon = signal.action === 'buy' ? TrendingUp : TrendingDown;
  const actionColor = signal.action === 'buy' ? 'text-success-600' : 'text-error-600';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 transition-opacity bg-slate-500 bg-opacity-75 backdrop-blur-sm"
          onClick={onClose}
        />

        <div className="inline-block w-full max-w-lg my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-strong rounded-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-200">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-xl ${signal.action === 'buy' ? 'bg-success-50' : 'bg-error-50'}`}>
                <ActionIcon className={`w-6 h-6 ${actionColor}`} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">
                  {signal.action.toUpperCase()} {signal.symbol}
                </h3>
                <p className="text-sm text-slate-600">
                  Signal #{signal.id} • {new Date(signal.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Status</p>
                <p className="text-sm font-semibold text-slate-900">
                  {statusLabels[signal.status]}
                </p>
              </div>
              {signal.confidence !== undefined && (
                <div>
                  <p className="text-xs font-medium text-slate-500 mb-1">Confidence</p>
                  <p className="text-sm font-semibold text-slate-900">
                    {signal.confidence}%
                  </p>
                </div>
              )}
              {signal.quantity !== undefined && (
                <div>
                  <p className="text-xs font-medium text-slate-500 mb-1">Quantity</p>
                  <p className="text-sm font-semibold text-slate-900">
                    {signal.quantity}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Strategy</p>
                <p className="text-sm font-semibold text-slate-900">
                  {signal.strategy_id}
                </p>
              </div>
            </div>

            {signal.reason && (
              <div>
                <p className="text-xs font-medium text-slate-500 mb-1">Reason</p>
                <p className="text-sm text-slate-700 bg-slate-50 p-3 rounded-xl">
                  {signal.reason}
                </p>
              </div>
            )}

            {signal.error_message && (
              <div className="text-sm text-error-600 bg-error-50 border border-error-200 p-3 rounded-xl">
                {signal.error_message}
              </div>
            )}
          </div>

          {/* Actions */}
          {signal.status === 'pending' && (
            <div className="flex items-center space-x-3 p-6 pt-0">
              <button
                onClick={() => onApprove?.(signal.id)}
                className="btn-primary flex-1"
              >
                <CheckCircle className="w-4 h-4 mr-2" /> Approve
              </button>
              <button
                onClick={() => onReject?.(signal.id)}
                className="btn-ghost text-error-600 hover:bg-error-50"
              >
                <XCircle className="w-4 h-4 mr-2" /> Reject
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SignalModal;

