import React, { useState } from 'react';
import {
  AlertTriangle, Shield, Clock, CheckCircle, XCircle,
  Bell, Settings, X, Eye, EyeOff, Activity, TrendingUp,
  BarChart3, Target, Globe
} from 'lucide-react';

interface RiskAlert {
  id: string;
  type: 'warning' | 'critical' | 'info';
  category: 'exposure' | 'correlation' | 'volatility' | 'margin' | 'position' | 'market';
  title: string;
  description: string;
  timestamp: string;
  isRead: boolean;
  isAcknowledged: boolean;
  affectedPositions?: string[];
  recommendedAction?: string;
  severity: number; // 1-10 scale
}

interface RiskAlertsProps {
  alerts: RiskAlert[];
  onMarkAsRead: (alertId: string) => void;
  onAcknowledge: (alertId: string) => void;
  onDismiss: (alertId: string) => void;
  loading?: boolean;
}

const RiskAlerts: React.FC<RiskAlertsProps> = ({
  alerts,
  onMarkAsRead,
  onAcknowledge,
  onDismiss,
  loading = false
}) => {
  const [showOnlyUnread, setShowOnlyUnread] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<RiskAlert | null>(null);

  const getAlertConfig = (type: RiskAlert['type']) => {
    switch (type) {
      case 'critical':
        return {
          icon: XCircle,
          bg: 'bg-error-50',
          border: 'border-error-200',
          text: 'text-error-700',
          iconColor: 'text-error-500'
        };
      case 'warning':
        return {
          icon: AlertTriangle,
          bg: 'bg-warning-50',
          border: 'border-warning-200',
          text: 'text-warning-700',
          iconColor: 'text-warning-500'
        };
      case 'info':
        return {
          icon: Shield,
          bg: 'bg-primary-50',
          border: 'border-primary-200',
          text: 'text-primary-700',
          iconColor: 'text-primary-500'
        };
    }
  };

  const getCategoryIcon = (category: RiskAlert['category']) => {
    const icons = {
      exposure: Shield,
      correlation: Activity,
      volatility: TrendingUp,
      margin: BarChart3,
      position: Target,
      market: Globe
    };
    return icons[category] || Shield;
  };

  const formatTime = (timestamp: string) => {
    const now = new Date();
    const alertTime = new Date(timestamp);
    const diffMs = now.getTime() - alertTime.getTime();
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return alertTime.toLocaleDateString();
  };

  const filteredAlerts = alerts.filter(alert => {
    if (showOnlyUnread && alert.isRead) return false;
    if (selectedCategory !== 'all' && alert.category !== selectedCategory) return false;
    return true;
  });

  const unreadCount = alerts.filter(alert => !alert.isRead).length;
  const criticalCount = alerts.filter(alert => alert.type === 'critical').length;

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 bg-slate-200 rounded w-32 animate-pulse"></div>
          <div className="h-8 bg-slate-200 rounded w-24 animate-pulse"></div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="p-4 border border-slate-200 rounded-xl animate-pulse">
              <div className="flex items-start space-x-3">
                <div className="w-10 h-10 bg-slate-200 rounded-lg"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-slate-200 rounded w-3/4"></div>
                  <div className="h-3 bg-slate-200 rounded w-1/2"></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1 flex items-center">
            <Bell className="w-5 h-5 mr-2 text-primary-600" />
            Risk Alerts
            {unreadCount > 0 && (
              <span className="ml-2 bg-error-100 text-error-700 text-xs font-semibold px-2 py-1 rounded-full">
                {unreadCount} new
              </span>
            )}
          </h3>
          <p className="text-sm text-slate-600">
            {criticalCount > 0 && (
              <span className="text-error-600 font-medium">
                {criticalCount} critical alert{criticalCount > 1 ? 's' : ''} require attention
              </span>
            )}
            {criticalCount === 0 && 'All systems operating normally'}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowOnlyUnread(!showOnlyUnread)}
            className={`btn-ghost text-sm ${showOnlyUnread ? 'bg-primary-50 text-primary-700' : ''}`}
          >
            {showOnlyUnread ? <Eye className="w-4 h-4 mr-1" /> : <EyeOff className="w-4 h-4 mr-1" />}
            {showOnlyUnread ? 'Show All' : 'Unread Only'}
          </button>
          
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white"
          >
            <option value="all">All Categories</option>
            <option value="exposure">Exposure</option>
            <option value="correlation">Correlation</option>
            <option value="volatility">Volatility</option>
            <option value="margin">Margin</option>
            <option value="position">Position</option>
            <option value="market">Market</option>
          </select>
        </div>
      </div>

      {/* Alerts List */}
      <div className="space-y-3 max-h-96 overflow-y-auto scrollbar-hide">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="h-8 w-8 text-success-600" />
            </div>
            <h4 className="text-lg font-semibold text-slate-900 mb-2">No Active Alerts</h4>
            <p className="text-slate-600">
              {showOnlyUnread 
                ? "You're all caught up! No unread alerts."
                : "All risk parameters are within acceptable limits."
              }
            </p>
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const config = getAlertConfig(alert.type);
            const Icon = config.icon;
            const CategoryIcon = getCategoryIcon(alert.category);
            
            return (
              <div
                key={alert.id}
                className={`relative p-4 rounded-xl border-2 transition-all duration-200 cursor-pointer hover:shadow-sm ${
                  config.border
                } ${config.bg} ${
                  !alert.isRead ? 'border-l-4 border-l-primary-500' : ''
                }`}
                onClick={() => setSelectedAlert(alert)}
              >
                <div className="flex items-start space-x-3">
                  {/* Alert Icon */}
                  <div className="flex-shrink-0">
                    <Icon className={`w-6 h-6 ${config.iconColor}`} />
                  </div>
                  
                  {/* Alert Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className={`font-semibold ${config.text}`}>
                        {alert.title}
                      </h4>
                      <div className="flex items-center space-x-2 ml-4">
                        <CategoryIcon className="w-4 h-4 text-slate-400" />
                        <span className="text-xs text-slate-500 uppercase tracking-wide">
                          {alert.category}
                        </span>
                      </div>
                    </div>
                    
                    <p className="text-sm text-slate-600 mb-3 line-clamp-2">
                      {alert.description}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <span className="text-xs text-slate-500">
                          {formatTime(alert.timestamp)}
                        </span>
                        
                        {alert.affectedPositions && alert.affectedPositions.length > 0 && (
                          <div className="flex items-center space-x-1">
                            <span className="text-xs text-slate-500">Affects:</span>
                            {alert.affectedPositions.slice(0, 3).map((symbol) => (
                              <span
                                key={symbol}
                                className="text-xs bg-slate-200 text-slate-700 px-2 py-1 rounded"
                              >
                                {symbol}
                              </span>
                            ))}
                            {alert.affectedPositions.length > 3 && (
                              <span className="text-xs text-slate-500">
                                +{alert.affectedPositions.length - 3} more
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      
                      {/* Severity Indicator */}
                      <div className="flex items-center space-x-1">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <div
                            key={i}
                            className={`w-1 h-4 rounded ${
                              i < Math.ceil(alert.severity / 2) 
                                ? alert.severity > 7 ? 'bg-error-500' : alert.severity > 4 ? 'bg-warning-500' : 'bg-success-500'
                                : 'bg-slate-200'
                            }`}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  {/* Action Buttons */}
                  <div className="flex items-center space-x-1">
                    {!alert.isRead && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onMarkAsRead(alert.id);
                        }}
                        className="p-1 rounded text-slate-400 hover:text-slate-600 transition-colors"
                        title="Mark as read"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    )}
                    
                    {!alert.isAcknowledged && alert.type !== 'info' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onAcknowledge(alert.id);
                        }}
                        className="p-1 rounded text-slate-400 hover:text-slate-600 transition-colors"
                        title="Acknowledge"
                      >
                        <CheckCircle className="w-4 h-4" />
                      </button>
                    )}
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDismiss(alert.id);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-error-600 transition-colors"
                      title="Dismiss"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Recommended Action */}
                {alert.recommendedAction && (
                  <div className="mt-3 pt-3 border-t border-slate-200">
                    <div className="flex items-start space-x-2">
                      <Settings className="w-4 h-4 text-slate-400 mt-0.5" />
                      <div>
                        <p className="text-xs font-medium text-slate-700 mb-1">Recommended Action:</p>
                        <p className="text-xs text-slate-600">{alert.recommendedAction}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
            <div
              className="fixed inset-0 transition-opacity bg-slate-500 bg-opacity-75"
              onClick={() => setSelectedAlert(null)}
            />
            
            <div className="inline-block w-full max-w-md my-8 overflow-hidden text-left align-middle transition-all transform bg-white shadow-xl rounded-2xl">
              <div className="p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-slate-900">Alert Details</h3>
                  <button
                    onClick={() => setSelectedAlert(null)}
                    className="p-1 rounded text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-1">{selectedAlert.title}</h4>
                    <p className="text-sm text-slate-600">{selectedAlert.description}</p>
                  </div>
                  
                  {selectedAlert.affectedPositions && (
                    <div>
                      <h5 className="text-sm font-medium text-slate-700 mb-2">Affected Positions:</h5>
                      <div className="flex flex-wrap gap-1">
                        {selectedAlert.affectedPositions.map(symbol => (
                          <span key={symbol} className="text-xs bg-slate-100 text-slate-700 px-2 py-1 rounded">
                            {symbol}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedAlert.recommendedAction && (
                    <div>
                      <h5 className="text-sm font-medium text-slate-700 mb-2">Recommended Action:</h5>
                      <p className="text-sm text-slate-600">{selectedAlert.recommendedAction}</p>
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                    <span className="text-xs text-slate-500">
                      {formatTime(selectedAlert.timestamp)}
                    </span>
                    <div className="flex items-center space-x-2">
                      {!selectedAlert.isAcknowledged && selectedAlert.type !== 'info' && (
                        <button
                          onClick={() => {
                            onAcknowledge(selectedAlert.id);
                            setSelectedAlert(null);
                          }}
                          className="btn-primary text-sm"
                        >
                          Acknowledge
                        </button>
                      )}
                      <button
                        onClick={() => {
                          onDismiss(selectedAlert.id);
                          setSelectedAlert(null);
                        }}
                        className="btn-secondary text-sm"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RiskAlerts;

