import React from 'react';
import {
  Activity, Clock, CheckCircle, Target
} from 'lucide-react';

interface SignalStatsProps {
  stats: {
    total: number;
    pending: number;
    executed: number;
    failed: number;
    averageConfidence: number;
    successRate: number;
    todayCount: number;
    topStrategy: string;
  };
  loading?: boolean;
}

const SignalStats: React.FC<SignalStatsProps> = ({ stats, loading = false }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4 animate-pulse">
            <div className="flex items-center justify-between mb-3">
              <div className="h-4 bg-slate-200 rounded w-16"></div>
              <div className="h-8 w-8 bg-slate-200 rounded-lg"></div>
            </div>
            <div className="h-6 bg-slate-200 rounded w-12 mb-1"></div>
            <div className="h-3 bg-slate-200 rounded w-20"></div>
          </div>
        ))}
      </div>
    );
  }

  const statCards = [
    {
      title: 'Total Signals',
      value: stats.total.toString(),
      subtitle: `${stats.todayCount} today`,
      icon: Activity,
      color: 'text-primary-600',
      bg: 'bg-primary-50'
    },
    {
      title: 'Pending',
      value: stats.pending.toString(),
      subtitle: 'Awaiting execution',
      icon: Clock,
      color: 'text-warning-600',
      bg: 'bg-warning-50'
    },
    {
      title: 'Success Rate',
      value: `${stats.successRate.toFixed(1)}%`,
      subtitle: `${stats.executed} executed`,
      icon: CheckCircle,
      color: 'text-success-600',
      bg: 'bg-success-50'
    },
    {
      title: 'Avg Confidence',
      value: `${stats.averageConfidence.toFixed(0)}%`,
      subtitle: 'Signal quality',
      icon: Target,
      color: 'text-indigo-600',
      bg: 'bg-indigo-50'
    }
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {statCards.map((stat, index) => {
        const Icon = stat.icon;
        
        return (
          <div key={index} className="card p-4 hover:shadow-medium transition-all duration-300 group">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
                {stat.title}
              </h4>
              <div className={`p-2 rounded-lg ${stat.bg} ${stat.color} group-hover:scale-110 transition-transform duration-200`}>
                <Icon className="w-4 h-4" />
              </div>
            </div>
            
            <div>
              <p className="text-xl font-bold text-slate-900 mb-1">
                {stat.value}
              </p>
              <p className="text-xs text-slate-500">
                {stat.subtitle}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default SignalStats;
