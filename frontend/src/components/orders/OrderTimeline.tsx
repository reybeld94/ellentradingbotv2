import React from 'react';
import {
  Clock, CheckCircle, XCircle, AlertTriangle,
  Play, Activity
} from 'lucide-react';

interface TimelineEvent {
  id: string;
  type: 'created' | 'submitted' | 'partially_filled' | 'filled' | 'canceled' | 'rejected' | 'modified';
  timestamp: string;
  description: string;
  details?: string;
  quantity?: number;
  price?: number;
}

interface OrderTimelineProps {
  events: TimelineEvent[];
  loading?: boolean;
}

const OrderTimeline: React.FC<OrderTimelineProps> = ({ events, loading = false }) => {
  const getEventConfig = (type: TimelineEvent['type']) => {
    switch (type) {
      case 'created':
        return { icon: Play, color: 'text-primary-600', bg: 'bg-primary-100', border: 'border-primary-200' };
      case 'submitted':
        return { icon: Clock, color: 'text-warning-600', bg: 'bg-warning-100', border: 'border-warning-200' };
      case 'partially_filled':
        return { icon: Activity, color: 'text-indigo-600', bg: 'bg-indigo-100', border: 'border-indigo-200' };
      case 'filled':
        return { icon: CheckCircle, color: 'text-success-600', bg: 'bg-success-100', border: 'border-success-200' };
      case 'canceled':
        return { icon: XCircle, color: 'text-slate-500', bg: 'bg-slate-100', border: 'border-slate-200' };
      case 'rejected':
        return { icon: XCircle, color: 'text-error-600', bg: 'bg-error-100', border: 'border-error-200' };
      case 'modified':
        return { icon: AlertTriangle, color: 'text-warning-600', bg: 'bg-warning-100', border: 'border-warning-200' };
      default:
        return { icon: Clock, color: 'text-slate-500', bg: 'bg-slate-100', border: 'border-slate-200' };
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-slate-900 mb-4">Order Timeline</h3>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-start space-x-4 animate-pulse">
              <div className="w-10 h-10 bg-slate-200 rounded-full"></div>
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                <div className="h-3 bg-slate-200 rounded w-1/2"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-6">Order Timeline</h3>
      
      {events.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Clock className="h-8 w-8 text-slate-400" />
          </div>
          <p className="text-slate-500">No timeline events available</p>
        </div>
      ) : (
        <div className="space-y-6">
          {events.map((event, index) => {
            const config = getEventConfig(event.type);
            const Icon = config.icon;
            const isLast = index === events.length - 1;

            return (
              <div key={event.id} className="relative">
                {/* Timeline Line */}
                {!isLast && (
                  <div className="absolute left-5 top-12 w-0.5 h-16 bg-slate-200"></div>
                )}

                {/* Event */}
                <div className="flex items-start space-x-4">
                  {/* Icon */}
                  <div className={`flex-shrink-0 w-10 h-10 rounded-full border-2 ${config.bg} ${config.border} flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${config.color}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="text-sm font-semibold text-slate-900 mb-1">
                          {event.description}
                        </h4>
                        <p className="text-xs text-slate-500 mb-2">
                          {formatTime(event.timestamp)}
                        </p>
                        {event.details && (
                          <p className="text-sm text-slate-600 mb-2">
                            {event.details}
                          </p>
                        )}
                        {(event.quantity || event.price) && (
                          <div className="flex items-center space-x-4 text-xs text-slate-500">
                            {event.quantity && (
                              <span>Qty: {event.quantity}</span>
                            )}
                            {event.price && (
                              <span>Price: ${event.price.toFixed(2)}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default OrderTimeline;

