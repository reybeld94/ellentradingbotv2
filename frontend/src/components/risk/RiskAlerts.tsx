import React from 'react';
import { AlertTriangle, CheckCircle2, Bell, Clock } from 'lucide-react';

interface AlertItem {
  id: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
}

interface RiskAlertsProps {
  alerts: AlertItem[];
  loading?: boolean;
}

const severityStyles: Record<AlertItem['severity'], { bg: string; text: string; icon: React.ReactNode }> = {
  low: { bg: 'bg-success-50', text: 'text-success-700', icon: <CheckCircle2 className="w-4 h-4" /> },
  medium: { bg: 'bg-warning-50', text: 'text-warning-700', icon: <Bell className="w-4 h-4" /> },
  high: { bg: 'bg-error-50', text: 'text-error-700', icon: <AlertTriangle className="w-4 h-4" /> },
  critical: { bg: 'bg-error-100', text: 'text-error-800', icon: <AlertTriangle className="w-4 h-4" /> },
};

const RiskAlerts: React.FC<RiskAlertsProps> = ({ alerts, loading = false }) => {
  if (loading) {
    return (
      <div className="card p-6">
        <div className="h-6 bg-slate-200 rounded w-40 mb-4 animate-pulse"></div>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center space-x-3 py-2 border-b border-slate-200 last:border-0">
            <div className="w-4 h-4 bg-slate-200 rounded-full animate-pulse"></div>
            <div className="flex-1 h-4 bg-slate-200 rounded animate-pulse"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
        <AlertTriangle className="w-5 h-5 mr-2 text-error-600" />
        Risk Alerts
      </h3>
      <div className="divide-y divide-slate-200">
        {alerts.map(alert => {
          const style = severityStyles[alert.severity];
          return (
            <div key={alert.id} className="flex items-start py-3">
              <div className={`p-2 rounded-full mr-3 ${style.bg} ${style.text}`}>{style.icon}</div>
              <div className="flex-1">
                <p className="text-sm font-medium text-slate-900">{alert.message}</p>
                <p className="text-xs text-slate-500 flex items-center mt-1">
                  <Clock className="w-3 h-3 mr-1" />
                  {new Date(alert.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          );
        })}
        {alerts.length === 0 && (
          <p className="text-sm text-slate-500 py-4 text-center">No active risk alerts</p>
        )}
      </div>
    </div>
  );
};

export default RiskAlerts;

