import React from 'react';
import {
  Clock, CheckCircle, XCircle,
  AlertTriangle, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import SymbolLogo from '../SymbolLogo';

interface ActivityItem {
  id: string;
  type: 'trade' | 'signal' | 'order' | 'alert';
  symbol: string;
  action: 'BUY' | 'SELL';
  status: 'success' | 'pending' | 'error' | 'warning';
  amount?: number;
  price?: number;
  quantity?: number;
  timestamp: string;
  description: string;
}

interface RecentActivityProps {
  activities: ActivityItem[];
  loading?: boolean;
}

const RecentActivity: React.FC<RecentActivityProps> = ({
  activities,
  loading = false
}) => {
  const getStatusIcon = (status: ActivityItem['status']) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-success-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-warning-600" />;
      case 'error':
        return <XCircle className="h-4 w-4 text-error-600" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-warning-600" />;
    }
  };

  const getStatusBg = (status: ActivityItem['status']) => {
    switch (status) {
      case 'success':
        return 'bg-success-50 border-success-200';
      case 'pending':
        return 'bg-warning-50 border-warning-200';
      case 'error':
        return 'bg-error-50 border-error-200';
      case 'warning':
        return 'bg-warning-50 border-warning-200';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center space-x-4 animate-pulse">
              <div className="w-10 h-10 bg-slate-200 rounded-xl"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                <div className="h-3 bg-slate-200 rounded w-1/2"></div>
              </div>
              <div className="h-4 bg-slate-200 rounded w-16"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-900">Recent Activity</h3>
        <button className="text-sm text-primary-600 hover:text-primary-700 font-medium">
          View All
        </button>
      </div>

      <div className="space-y-4">
        {activities.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Clock className="h-8 w-8 text-slate-400" />
            </div>
            <p className="text-slate-500">No recent activity</p>
          </div>
        ) : (
          activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-center space-x-4 p-3 rounded-xl hover:bg-slate-50 transition-colors duration-200 group"
            >
              {/* Status & Symbol */}
              <div className="relative">
                <div className="w-10 h-10 flex items-center justify-center">
                  <SymbolLogo symbol={activity.symbol} className="w-8 h-8" />
                </div>
                <div className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-2 border-white flex items-center justify-center ${getStatusBg(activity.status)}`}>
                  {getStatusIcon(activity.status)}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-slate-900">{activity.symbol}</span>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    activity.action === 'BUY' 
                      ? 'bg-success-100 text-success-800' 
                      : 'bg-error-100 text-error-800'
                  }`}>
                    {activity.action === 'BUY' ? (
                      <ArrowUpRight className="h-3 w-3 mr-1" />
                    ) : (
                      <ArrowDownRight className="h-3 w-3 mr-1" />
                    )}
                    {activity.action}
                  </span>
                </div>
                <p className="text-sm text-slate-600 truncate">{activity.description}</p>
                {activity.quantity && activity.price && (
                  <p className="text-xs text-slate-500">
                    {activity.quantity} shares @ ${activity.price.toFixed(2)}
                  </p>
                )}
              </div>

              {/* Amount & Time */}
              <div className="text-right">
                {activity.amount && (
                  <p className={`font-semibold text-sm ${
                    activity.action === 'BUY' ? 'text-error-600' : 'text-success-600'
                  }`}>
                    {activity.action === 'BUY' ? '-' : '+'}{formatAmount(activity.amount)}
                  </p>
                )}
                <p className="text-xs text-slate-500">{formatTime(activity.timestamp)}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default RecentActivity;

