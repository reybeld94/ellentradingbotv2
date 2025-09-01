import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  change?: {
    value: string;
    type: 'positive' | 'negative' | 'neutral';
    period: string;
  };
  icon: LucideIcon;
  trend?: number[];
  loading?: boolean;
  format?: 'currency' | 'percentage' | 'number';
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  icon: Icon,
  trend,
  loading = false
}) => {
  const getChangeColor = (type: 'positive' | 'negative' | 'neutral') => {
    switch (type) {
      case 'positive':
        return 'text-success-600 bg-success-50 border-success-200';
      case 'negative':
        return 'text-error-600 bg-error-50 border-error-200';
      case 'neutral':
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="card p-6 animate-pulse">
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 bg-slate-200 rounded w-24"></div>
          <div className="h-10 w-10 bg-slate-200 rounded-xl"></div>
        </div>
        <div className="h-8 bg-slate-200 rounded w-32 mb-2"></div>
        <div className="h-4 bg-slate-200 rounded w-20"></div>
      </div>
    );
  }

  return (
    <div className="card p-6 hover:shadow-medium transition-all duration-300 group">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
          {title}
        </h3>
        <div className="p-3 rounded-xl bg-primary-50 text-primary-600 group-hover:bg-primary-100 transition-colors">
          <Icon className="h-5 w-5" />
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-2xl font-bold text-slate-900">
          {value}
        </p>

        {change && (
          <div className="flex items-center space-x-2">
            <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold border ${getChangeColor(change.type)}`}>
              {change.value}
            </span>
            <span className="text-xs text-slate-500">{change.period}</span>
          </div>
        )}

        {trend && trend.length > 0 && (
          <div className="mt-4">
            <div className="flex items-end space-x-1 h-8">
              {trend.map((value, index) => (
                <div
                  key={index}
                  className="bg-primary-200 rounded-sm flex-1 transition-all duration-300 hover:bg-primary-300"
                  style={{ height: `${Math.max(4, (value / Math.max(...trend)) * 100)}%` }}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MetricCard;

