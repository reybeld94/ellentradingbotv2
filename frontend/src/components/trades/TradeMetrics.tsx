import React from 'react';
import {
  TrendingUp, TrendingDown, Target, Activity,
  DollarSign, BarChart3
} from 'lucide-react';

interface TradeMetricsProps {
  metrics: {
    totalTrades: number;
    openTrades: number;
    closedTrades: number;
    winningTrades: number;
    losingTrades: number;
    totalPnL: number;
    winRate: number;
    avgWin: number;
    avgLoss: number;
    bestTrade: number;
    worstTrade: number;
    avgHoldTime: number;
    profitFactor: number;
    sharpeRatio: number;
    maxDrawdown: number;
    totalVolume: number;
  };
  loading?: boolean;
}

const TradeMetrics: React.FC<TradeMetricsProps> = ({ metrics, loading = false }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(Math.abs(value));
  };

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const formatDuration = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}d`;
    if (hours > 0) return `${hours}h`;
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
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

  const metricCards = [
    {
      title: 'Total P&L',
      value: `${metrics.totalPnL >= 0 ? '+' : ''}${formatCurrency(metrics.totalPnL)}`,
      subtitle: `${metrics.totalTrades} trades`,
      icon: DollarSign,
      color: metrics.totalPnL >= 0 ? 'text-success-600' : 'text-error-600',
      bg: metrics.totalPnL >= 0 ? 'bg-success-50' : 'bg-error-50'
    },
    {
      title: 'Win Rate',
      value: formatPercent(metrics.winRate),
      subtitle: `${metrics.winningTrades}W / ${metrics.losingTrades}L`,
      icon: Target,
      color: metrics.winRate >= 50 ? 'text-success-600' : 'text-error-600',
      bg: metrics.winRate >= 50 ? 'bg-success-50' : 'bg-error-50'
    },
    {
      title: 'Open Positions',
      value: metrics.openTrades.toString(),
      subtitle: `${metrics.closedTrades} closed`,
      icon: Activity,
      color: 'text-primary-600',
      bg: 'bg-primary-50'
    },
    {
      title: 'Avg Win',
      value: formatCurrency(metrics.avgWin),
      subtitle: 'Per winning trade',
      icon: TrendingUp,
      color: 'text-success-600',
      bg: 'bg-success-50'
    },
    {
      title: 'Avg Loss',
      value: formatCurrency(metrics.avgLoss),
      subtitle: 'Per losing trade',
      icon: TrendingDown,
      color: 'text-error-600',
      bg: 'bg-error-50'
    },
    {
      title: 'Best Trade',
      value: `+${formatCurrency(metrics.bestTrade)}`,
      subtitle: formatDuration(metrics.avgHoldTime),
      icon: BarChart3,
      color: 'text-success-600',
      bg: 'bg-success-50'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Main Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {metricCards.map((metric, index) => {
          const Icon = metric.icon;
          
          return (
            <div key={index} className="card p-4 hover:shadow-medium transition-all duration-300 group">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
                  {metric.title}
                </h4>
                <div className={`p-2 rounded-lg ${metric.bg} ${metric.color} group-hover:scale-110 transition-transform duration-200`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              
              <div>
                <p className={`text-xl font-bold mb-1 ${metric.color}`}>
                  {metric.value}
                </p>
                <p className="text-xs text-slate-500">
                  {metric.subtitle}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Advanced Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <h4 className="text-sm font-medium text-slate-600 mb-2">Profit Factor</h4>
          <p className="text-2xl font-bold text-primary-600">{metrics.profitFactor.toFixed(2)}</p>
          <p className="text-xs text-slate-500">Gross profit / gross loss</p>
        </div>

        <div className="card p-4">
          <h4 className="text-sm font-medium text-slate-600 mb-2">Sharpe Ratio</h4>
          <p className="text-2xl font-bold text-indigo-600">{metrics.sharpeRatio.toFixed(2)}</p>
          <p className="text-xs text-slate-500">Risk-adjusted returns</p>
        </div>

        <div className="card p-4">
          <h4 className="text-sm font-medium text-slate-600 mb-2">Max Drawdown</h4>
          <p className="text-2xl font-bold text-error-600">-{formatPercent(metrics.maxDrawdown)}</p>
          <p className="text-xs text-slate-500">Largest peak-to-trough loss</p>
        </div>

        <div className="card p-4">
          <h4 className="text-sm font-medium text-slate-600 mb-2">Total Volume</h4>
          <p className="text-2xl font-bold text-slate-900">{formatCurrency(metrics.totalVolume)}</p>
          <p className="text-xs text-slate-500">Cumulative trade value</p>
        </div>
      </div>
    </div>
  );
};

export default TradeMetrics;
