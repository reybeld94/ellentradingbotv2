import React from 'react';
import {
  Shield, AlertTriangle, TrendingDown, Activity,
  Target, BarChart3, Zap
} from 'lucide-react';

interface RiskMetricsProps {
  metrics: {
    portfolioVaR: number;
    portfolioCVaR: number;
    positionLimit: number;
    usedPositions: number;
    marginUtilization: number;
    leverageRatio: number;
    correlationRisk: number;
    concentrationRisk: number;
    liquidityRisk: number;
    marketRisk: number;
    riskScore: number;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
  };
  loading?: boolean;
}

const RiskMetrics: React.FC<RiskMetricsProps> = ({ metrics, loading = false }) => {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'low':
        return { bg: 'bg-success-50', text: 'text-success-700', border: 'border-success-200' };
      case 'medium':
        return { bg: 'bg-warning-50', text: 'text-warning-700', border: 'border-warning-200' };
      case 'high':
        return { bg: 'bg-error-50', text: 'text-error-700', border: 'border-error-200' };
      case 'critical':
        return { bg: 'bg-error-100', text: 'text-error-800', border: 'border-error-300' };
      default:
        return { bg: 'bg-slate-50', text: 'text-slate-700', border: 'border-slate-200' };
    }
  };

  const getUtilizationColor = (percentage: number) => {
    if (percentage <= 50) return 'text-success-600 bg-success-100';
    if (percentage <= 75) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const riskColors = getRiskColor(metrics.riskLevel);

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="h-4 bg-slate-200 rounded w-20"></div>
              <div className="h-8 w-8 bg-slate-200 rounded-lg"></div>
            </div>
            <div className="h-8 bg-slate-200 rounded w-16 mb-2"></div>
            <div className="h-3 bg-slate-200 rounded w-24"></div>
          </div>
        ))}
      </div>
    );
  }

  const riskMetricCards = [
    {
      title: 'Risk Score',
      value: `${metrics.riskScore}/100`,
      subtitle: `${metrics.riskLevel.toUpperCase()} RISK`,
      icon: Shield,
      color: riskColors.text,
      bg: riskColors.bg,
      border: riskColors.border
    },
    {
      title: 'Portfolio VaR',
      value: `${metrics.portfolioVaR.toFixed(1)}%`,
      subtitle: '95% confidence, 1-day',
      icon: TrendingDown,
      color: 'text-error-600',
      bg: 'bg-error-50'
    },
    {
      title: 'CVaR (ES)',
      value: `${metrics.portfolioCVaR.toFixed(1)}%`,
      subtitle: 'Expected shortfall',
      icon: AlertTriangle,
      color: 'text-error-600',
      bg: 'bg-error-50'
    },
    {
      title: 'Position Usage',
      value: `${metrics.usedPositions}/${metrics.positionLimit}`,
      subtitle: `${((metrics.usedPositions/metrics.positionLimit)*100).toFixed(0)}% utilized`,
      icon: Target,
      color: getUtilizationColor((metrics.usedPositions/metrics.positionLimit)*100).split(' ')[0],
      bg: getUtilizationColor((metrics.usedPositions/metrics.positionLimit)*100).split(' ')[1]
    },
    {
      title: 'Margin Usage',
      value: `${metrics.marginUtilization.toFixed(1)}%`,
      subtitle: 'Of available margin',
      icon: BarChart3,
      color: getUtilizationColor(metrics.marginUtilization).split(' ')[0],
      bg: getUtilizationColor(metrics.marginUtilization).split(' ')[1]
    },
    {
      title: 'Leverage',
      value: `${metrics.leverageRatio.toFixed(2)}x`,
      subtitle: 'Portfolio leverage',
      icon: Zap,
      color: metrics.leverageRatio > 2 ? 'text-error-600' : metrics.leverageRatio > 1.5 ? 'text-warning-600' : 'text-success-600',
      bg: metrics.leverageRatio > 2 ? 'bg-error-50' : metrics.leverageRatio > 1.5 ? 'bg-warning-50' : 'bg-success-50'
    },
    {
      title: 'Correlation Risk',
      value: `${metrics.correlationRisk.toFixed(1)}%`,
      subtitle: 'Portfolio correlation',
      icon: Activity,
      color: 'text-primary-600',
      bg: 'bg-primary-50'
    },
    {
      title: 'Concentration',
      value: `${metrics.concentrationRisk.toFixed(1)}%`,
      subtitle: 'Largest position weight',
      icon: Target,
      color: metrics.concentrationRisk > 25 ? 'text-error-600' : metrics.concentrationRisk > 15 ? 'text-warning-600' : 'text-success-600',
      bg: metrics.concentrationRisk > 25 ? 'bg-error-50' : metrics.concentrationRisk > 15 ? 'bg-warning-50' : 'bg-success-50'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Risk Overview */}
      <div className={`card p-6 border-2 ${riskColors.border} ${riskColors.bg}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-slate-900">Overall Risk Assessment</h3>
          <Shield className={`w-8 h-8 ${riskColors.text}`} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className={`text-3xl font-bold ${riskColors.text} mb-1`}>
              {metrics.riskScore}
            </p>
            <p className="text-sm text-slate-600">Risk Score</p>
          </div>

          <div className="text-center">
            <p className={`text-2xl font-bold ${riskColors.text} mb-1`}>
              {metrics.riskLevel.toUpperCase()}
            </p>
            <p className="text-sm text-slate-600">Risk Level</p>
          </div>

          <div className="text-center">
            <p className="text-2xl font-bold text-slate-900 mb-1">
              {metrics.marketRisk.toFixed(1)}%
            </p>
            <p className="text-sm text-slate-600">Market Risk</p>
          </div>

          <div className="text-center">
            <p className="text-2xl font-bold text-slate-900 mb-1">
              {metrics.liquidityRisk.toFixed(1)}%
            </p>
            <p className="text-sm text-slate-600">Liquidity Risk</p>
          </div>
        </div>
      </div>

      {/* Detailed Risk Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {riskMetricCards.map((metric, index) => {
          const Icon = metric.icon;

          return (
            <div key={index} className="card p-6 hover:shadow-medium transition-all duration-300 group">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">
                  {metric.title}
                </h4>
                <div className={`p-3 rounded-xl ${metric.bg} group-hover:scale-110 transition-transform duration-200`}>
                  <Icon className={`w-5 h-5 ${metric.color}`} />
                </div>
              </div>

              <div>
                <p className={`text-2xl font-bold mb-1 ${metric.color}`}>
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

      {/* Risk Utilization Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card p-6">
          <h4 className="text-lg font-semibold text-slate-900 mb-4">Position Utilization</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Open Positions</span>
              <span className="text-sm font-semibold text-slate-900">
                {metrics.usedPositions} of {metrics.positionLimit}
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  (metrics.usedPositions/metrics.positionLimit)*100 > 80
                    ? 'bg-error-500'
                    : (metrics.usedPositions/metrics.positionLimit)*100 > 60
                    ? 'bg-warning-500'
                    : 'bg-success-500'
                }`}
                style={{ width: `${(metrics.usedPositions/metrics.positionLimit)*100}%` }}
              />
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h4 className="text-lg font-semibold text-slate-900 mb-4">Margin Utilization</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-600">Used Margin</span>
              <span className="text-sm font-semibold text-slate-900">
                {metrics.marginUtilization.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-500 ${
                  metrics.marginUtilization > 80
                    ? 'bg-error-500'
                    : metrics.marginUtilization > 60
                    ? 'bg-warning-500'
                    : 'bg-success-500'
                }`}
                style={{ width: `${metrics.marginUtilization}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskMetrics;

