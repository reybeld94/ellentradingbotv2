import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  X,
  Eye,
  MoreHorizontal,
  Search,
  RefreshCw
} from 'lucide-react';

interface Signal {
  id: number;
  symbol: string;
  action: 'BUY' | 'SELL';
  status: 'pending' | 'executed' | 'rejected';
  confidence: number;
  quantity: number;
  strategy_id: string;
  timestamp: string;
  reason: string;
  price: number;
  target: number;
  stopLoss?: number;
  error_message?: string;
}

interface ProfessionalSignalsPageProps {
  signals?: Signal[];
  onApprove?: (signalId: number) => void;
  onReject?: (signalId: number) => void;
  onViewDetails?: (signal: Signal) => void;
  onRefresh?: () => void;
}

const ProfessionalSignalsPage: React.FC<ProfessionalSignalsPageProps> = ({
  signals = [],
  onApprove,
  onReject,
  onViewDetails,
  onRefresh
}) => {
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  const filteredSignals = signals
    .filter(signal => {
      const matchesFilter = filter === 'all' || signal.status === filter;
      const matchesSearch = signal.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           signal.strategy_id.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    })
    .sort((a, b) => {
      const aVal = a[sortBy as keyof Signal];
      const bVal = b[sortBy as keyof Signal];
      const direction = sortOrder === 'asc' ? 1 : -1;

      if (sortBy === 'timestamp') {
        return direction * (new Date(bVal as string).getTime() - new Date(aVal as string).getTime());
      }
      return direction * ((aVal as number) > (bVal as number) ? 1 : -1);
    });

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

    if (diffInMinutes < 60) {
      return `${diffInMinutes}m ago`;
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)}h ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getStatusBadge = (status: string) => {
    const configs: Record<string, { label: string; bg: string; text: string; border: string; icon: any; }> = {
      pending: { label: 'Pending', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200', icon: Clock },
      executed: { label: 'Executed', bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', icon: CheckCircle },
      rejected: { label: 'Rejected', bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', icon: X }
    };
    return configs[status] || configs.pending;
  };

  const getActionBadge = (action: string) => {
    return action === 'BUY'
      ? { label: 'BUY', bg: 'bg-emerald-600', text: 'text-white', icon: TrendingUp }
      : { label: 'SELL', bg: 'bg-red-600', text: 'text-white', icon: TrendingDown };
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-emerald-600 bg-emerald-50';
    if (confidence >= 80) return 'text-blue-600 bg-blue-50';
    if (confidence >= 70) return 'text-amber-600 bg-amber-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Trading Signals</h1>
              <p className="text-gray-600">Monitor and manage algorithmic trading signals</p>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={onRefresh}
                className="flex items-center space-x-2 bg-white border border-gray-200 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <RefreshCw className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-700">Refresh</span>
              </button>
              <div className="flex items-center space-x-2 bg-emerald-50 border border-emerald-200 px-3 py-2 rounded-lg">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-emerald-700 font-medium">Live</span>
              </div>
            </div>
          </div>

          {/* Filters */}
          <div className="flex flex-col md:flex-row gap-4 mb-6">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search by symbol or strategy..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div className="flex space-x-2">
              {['all', 'pending', 'executed', 'rejected'].map((status) => (
                <button
                  key={status}
                  onClick={() => setFilter(status)}
                  className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors capitalize ${
                    filter === status
                      ? 'bg-blue-600 text-white'
                      : 'bg-white border border-gray-200 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Signals List */}
        <div className="space-y-4">
          {filteredSignals.map((signal) => {
            const StatusIcon = getStatusBadge(signal.status).icon;
            const ActionIcon = getActionBadge(signal.action).icon;
            const statusConfig = getStatusBadge(signal.status);
            const actionConfig = getActionBadge(signal.action);

            return (
              <div key={signal.id} className="bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow">
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    {/* Left Section */}
                    <div className="flex items-start space-x-4">
                      <div className="flex-shrink-0">
                        <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                          <span className="text-sm font-bold text-gray-700">{signal.symbol}</span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-3 mb-2">
                          <h3 className="text-lg font-semibold text-gray-900">{signal.symbol}</h3>
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${actionConfig.bg} ${actionConfig.text}`}>
                            <ActionIcon className="w-3 h-3 mr-1" />
                            {actionConfig.label}
                          </span>
                          <span className={`inline-flex items-center px-2 py-1 rounded border text-xs font-medium ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}>
                            <StatusIcon className="w-3 h-3 mr-1" />
                            {statusConfig.label}
                          </span>
                        </div>
                        <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                          <span>Strategy: {signal.strategy_id}</span>
                          <span>•</span>
                          <span>{formatTime(signal.timestamp)}</span>
                          <span>•</span>
                          <span>Qty: {signal.quantity}</span>
                        </div>
                        <p className="text-sm text-gray-700 max-w-2xl">{signal.reason}</p>
                        {signal.error_message && (
                          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                            {signal.error_message}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right Section */}
                    <div className="flex items-start space-x-6 text-right">
                      {/* Price Info */}
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Current Price</p>
                        <p className="text-lg font-semibold text-gray-900">${signal.price}</p>
                        <p className="text-xs text-gray-500 mt-1">
                          Target: <span className="font-medium">${signal.target}</span>
                        </p>
                        {signal.stopLoss && (
                          <p className="text-xs text-gray-500">
                            Stop: <span className="font-medium">${signal.stopLoss}</span>
                          </p>
                        )}
                      </div>

                      {/* Confidence */}
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Confidence</p>
                        <div className={`inline-flex items-center px-2 py-1 rounded text-sm font-semibold ${getConfidenceColor(signal.confidence)}`}>
                          {signal.confidence}%
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center space-x-2">
                        {signal.status === 'pending' && (
                          <>
                            <button
                              onClick={() => onApprove?.(signal.id)}
                              className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                              title="Approve Signal"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => onReject?.(signal.id)}
                              className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              title="Reject Signal"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => onViewDetails?.(signal)}
                          className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button className="p-2 text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
                          <MoreHorizontal className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Empty State */}
        {filteredSignals.length === 0 && (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Search className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No signals found</h3>
            <p className="text-gray-500">Try adjusting your filters or search criteria</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfessionalSignalsPage;
