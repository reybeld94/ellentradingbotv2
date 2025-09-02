import React from 'react';
import {
  X, TrendingUp, TrendingDown, Brain, Target,
  Clock, Zap, BarChart3, AlertTriangle
} from 'lucide-react';

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
  risk_score?: number;
  expected_return?: number;
}

interface SignalModalProps {
  signal: Signal | null;
  isOpen: boolean;
  onClose: () => void;
  onExecute?: (signalId: number) => void;
  onCancel?: (signalId: number) => void;
}

const SignalModal: React.FC<SignalModalProps> = ({
  signal,
  isOpen,
  onClose,
  onExecute,
  onCancel
}) => {
  if (!isOpen || !signal) return null;

  const ActionIcon = signal.action === 'BUY' ? TrendingUp : TrendingDown;
  const actionColor = signal.action === 'BUY' ? 'text-success-600' : 'text-error-600';
  const actionBg = signal.action === 'BUY' ? 'bg-success-50' : 'bg-error-50';

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-slate-500 bg-opacity-75 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="inline-block w-full max-w-2xl my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-strong rounded-2xl">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-slate-200">
            <div className="flex items-center space-x-4">
              <div className={`p-3 rounded-xl ${actionBg}`}>
                <ActionIcon className={`w-6 h-6 ${actionColor}`} />
              </div>
              <div>
                <h3 className="text-xl font-bold text-slate-900">
                  {signal.action} {signal.symbol}
                </h3>
                <p className="text-sm text-slate-600">
                  Signal #{signal.id} • {new Date(signal.created_at).toLocaleString()}
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
          <div className="p-6 space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 bg-slate-50 rounded-xl">
                <p className="text-xs font-medium text-slate-500 mb-1">Price</p>
                <p className="text-lg font-bold text-slate-900">${signal.price.toFixed(2)}</p>
              </div>
              <div className="text-center p-4 bg-slate-50 rounded-xl">
                <p className="text-xs font-medium text-slate-500 mb-1">Confidence</p>
                <p className="text-lg font-bold text-primary-600">{signal.confidence}%</p>
              </div>
              {signal.target_price && (
                <div className="text-center p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs font-medium text-slate-500 mb-1">Target</p>
                  <p className="text-lg font-bold text-success-600">${signal.target_price.toFixed(2)}</p>
                </div>
              )}
              {signal.stop_loss && (
                <div className="text-center p-4 bg-slate-50 rounded-xl">
                  <p className="text-xs font-medium text-slate-500 mb-1">Stop Loss</p>
                  <p className="text-lg font-bold text-error-600">${signal.stop_loss.toFixed(2)}</p>
                </div>
              )}
            </div>

            {/* Strategy Information */}
            {signal.strategy_name && (
              <div className="p-4 bg-primary-50 rounded-xl border border-primary-100">
                <h4 className="flex items-center text-sm font-semibold text-primary-900 mb-2">
                  <Brain className="w-4 h-4 mr-2" />
                  Strategy: {signal.strategy_name}
                </h4>
                <p className="text-sm text-primary-700">
                  Strategy ID: {signal.strategy_id}
                </p>
              </div>
            )}

            {/* Signal Reasoning */}
            {signal.reasoning && (
              <div>
                <h4 className="flex items-center text-sm font-semibold text-slate-900 mb-3">
                  <Target className="w-4 h-4 mr-2 text-primary-600" />
                  Signal Analysis
                </h4>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {signal.reasoning}
                  </p>
                </div>
              </div>
            )}

            {/* Market Conditions */}
            {signal.market_conditions && (
              <div>
                <h4 className="flex items-center text-sm font-semibold text-slate-900 mb-3">
                  <BarChart3 className="w-4 h-4 mr-2 text-primary-600" />
                  Market Conditions
                </h4>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <p className="text-sm text-slate-700 leading-relaxed">
                    {signal.market_conditions}
                  </p>
                </div>
              </div>
            )}

            {/* Risk Assessment */}
            {(signal.risk_score || signal.expected_return) && (
              <div>
                <h4 className="flex items-center text-sm font-semibold text-slate-900 mb-3">
                  <AlertTriangle className="w-4 h-4 mr-2 text-warning-600" />
                  Risk Assessment
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  {signal.risk_score && (
                    <div className="p-4 bg-warning-50 rounded-xl border border-warning-100">
                      <p className="text-xs font-medium text-warning-600 mb-1">Risk Score</p>
                      <p className="text-lg font-bold text-warning-700">{signal.risk_score}/10</p>
                    </div>
                  )}
                  {signal.expected_return && (
                    <div className="p-4 bg-success-50 rounded-xl border border-success-100">
                      <p className="text-xs font-medium text-success-600 mb-1">Expected Return</p>
                      <p className="text-lg font-bold text-success-700">+{signal.expected_return.toFixed(1)}%</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Trade Details */}
            {signal.quantity && (
              <div>
                <h4 className="flex items-center text-sm font-semibold text-slate-900 mb-3">
                  <Zap className="w-4 h-4 mr-2 text-primary-600" />
                  Trade Details
                </h4>
                <div className="p-4 bg-slate-50 rounded-xl">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-slate-500">Quantity:</span>
                      <span className="ml-2 font-semibold text-slate-900">{signal.quantity} shares</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Total Value:</span>
                      <span className="ml-2 font-semibold text-slate-900">
                        ${(signal.quantity * signal.price).toLocaleString()}
                      </span>
                    </div>
                    {signal.target_price && (
                      <div>
                        <span className="text-slate-500">Potential Profit:</span>
                        <span className="ml-2 font-semibold text-success-600">
                          +${((signal.target_price - signal.price) * signal.quantity).toLocaleString()}
                        </span>
                      </div>
                    )}
                    {signal.stop_loss && (
                      <div>
                        <span className="text-slate-500">Max Loss:</span>
                        <span className="ml-2 font-semibold text-error-600">
                          -${((signal.price - signal.stop_loss) * signal.quantity).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between p-6 bg-slate-50 border-t border-slate-200">
            <div className="flex items-center space-x-2 text-sm text-slate-600">
              <Clock className="w-4 h-4" />
              <span>Created {new Date(signal.created_at).toLocaleString()}</span>
            </div>
            
            <div className="flex items-center space-x-3">
              {signal.status === 'pending' && (
                <>
                  <button
                    onClick={() => onCancel?.(signal.id)}
                    className="btn-ghost text-error-600 hover:bg-error-50"
                  >
                    Cancel Signal
                  </button>
                  <button
                    onClick={() => {
                      onExecute?.(signal.id);
                      onClose();
                    }}
                    className="btn-primary"
                  >
                    <Zap className="w-4 h-4 mr-2" />
                    Execute Now
                  </button>
                </>
              )}
              {signal.status !== 'pending' && (
                <button onClick={onClose} className="btn-secondary">
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SignalModal;
