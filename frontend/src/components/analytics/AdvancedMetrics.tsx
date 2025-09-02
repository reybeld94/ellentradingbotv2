import React from 'react';
import {
  Target, TrendingUp, Shield, Activity,
  BarChart3, Zap, AlertTriangle, Award
} from 'lucide-react';

interface AdvancedMetricsProps {
  metrics: {
    sharpeRatio: number;
    sortinoRatio: number;
    calmarRatio: number;
    maxDrawdown: number;
    volatility: number;
    beta: number;
    alpha: number;
    winRate: number;
    profitFactor: number;
    payoffRatio: number;
    averageWin: number;
    averageLoss: number;
    largestWin: number;
    largestLoss: number;
    consecutiveWins: number;
    consecutiveLosses: number;
    recoveryFactor: number;
    ulcerIndex: number;
  };
  loading?: boolean;
}

const AdvancedMetrics: React.FC<AdvancedMetricsProps> = ({ metrics, loading = false }) => {
  const getRiskLevel = (value: number, thresholds: number[], reverse = false) => {
    const levels = reverse
      ? ['text-success-600 bg-success-50', 'text-warning-600 bg-warning-50', 'text-error-600 bg-error-50']
      : ['text-error-600 bg-error-50', 'text-warning-600 bg-warning-50', 'text-success-600 bg-success-50'];

    if (reverse) {
      if (value <= thresholds[0]) return levels[2];
      if (value <= thresholds[1]) return levels[1];
      return levels[0];
    } else {
      if (value <= thresholds[0]) return levels[0];
      if (value <= thresholds[1]) return levels[1];
      return levels[2];
    }
  };

  const getScoreIcon = (score: number) => {
    if (score >= 80) return { icon: Award, color: 'text-success-600' };
    if (score >= 60) return { icon: Target, color: 'text-warning-600' };
    return { icon: AlertTriangle, color: 'text-error-600' };
  };

  const calculateOverallScore = () => {
    const weights = {
      sharpeRatio: 0.2,
      winRate: 0.15,
      profitFactor: 0.15,
      maxDrawdown: 0.15,
      volatility: 0.1,
      recoveryFactor: 0.1,
      alpha: 0.15
    };

    let score = 0;

    score += Math.min(100, Math.max(0, (metrics.sharpeRatio + 2) * 25)) * weights.sharpeRatio;
    score += metrics.winRate * weights.winRate;
    score += Math.min(100, Math.max(0, (metrics.profitFactor - 1) * 50)) * weights.profitFactor;
    score += Math.max(0, 100 - metrics.maxDrawdown * 2) * weights.maxDrawdown;
    score += Math.max(0, 100 - metrics.volatility) * weights.volatility;
    score += Math.min(100, metrics.recoveryFactor * 20) * weights.recoveryFactor;
    score += Math.min(100, Math.max(0, (metrics.alpha + 10) * 5)) * weights.alpha;

    return Math.round(score);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="h-4 bg-slate-200 rounded w-24"></div>
              <div className="h-8 w-8 bg-slate-200 rounded-lg"></div>
            </div>
            <div className="h-8 bg-slate-200 rounded w-16 mb-2"></div>
            <div className="h-3 bg-slate-200 rounded w-32"></div>
          </div>
        ))}
      </div>
    );
  }

  const overallScore = calculateOverallScore();
  const scoreConfig = getScoreIcon(overallScore);
  const ScoreIcon = scoreConfig.icon;

  const metricCards = [
    {
      title: 'Overall Score',
      value: `${overallScore}/100`,
      description: 'Composite performance rating',
      icon: ScoreIcon,
      color: scoreConfig.color,
      bg: overallScore >= 80 ? 'bg-success-50' : overallScore >= 60 ? 'bg-warning-50' : 'bg-error-50'
    },
    {
      title: 'Sharpe Ratio',
      value: metrics.sharpeRatio.toFixed(2),
      description: 'Risk-adjusted returns',
      icon: TrendingUp,
      color: getRiskLevel(metrics.sharpeRatio, [0.5, 1.0]).split(' ')[0],
      bg: getRiskLevel(metrics.sharpeRatio, [0.5, 1.0]).split(' ')[1]
    },
    {
      title: 'Sortino Ratio',
      value: metrics.sortinoRatio.toFixed(2),
      description: 'Downside risk-adjusted returns',
      icon: Shield,
      color: getRiskLevel(metrics.sortinoRatio, [0.5, 1.0]).split(' ')[0],
      bg: getRiskLevel(metrics.sortinoRatio, [0.5, 1.0]).split(' ')[1]
    },
    {
      title: 'Max Drawdown',
      value: `${metrics.maxDrawdown.toFixed(1)}%`,
      description: 'Largest peak-to-trough loss',
      icon: AlertTriangle,
      color: getRiskLevel(metrics.maxDrawdown, [10, 20], true).split(' ')[0],
      bg: getRiskLevel(metrics.maxDrawdown, [10, 20], true).split(' ')[1]
    },
    {
      title: 'Profit Factor',
      value: metrics.profitFactor.toFixed(2),
      description: 'Gross profit / gross loss',
      icon: Target,
      color: getRiskLevel(metrics.profitFactor, [1.2, 2.0]).split(' ')[0],
      bg: getRiskLevel(metrics.profitFactor, [1.2, 2.0]).split(' ')[1]
    },
    {
      title: 'Volatility',
      value: `${metrics.volatility.toFixed(1)}%`,
      description: 'Return standard deviation',
      icon: Activity,
      color: getRiskLevel(metrics.volatility, [15, 25], true).split(' ')[0],
      bg: getRiskLevel(metrics.volatility, [15, 25], true).split(' ')[1]
    },
    {
      title: 'Beta',
      value: metrics.beta.toFixed(2),
      description: 'Market correlation',
      icon: BarChart3,
      color: 'text-primary-600',
      bg: 'bg-primary-50'
    },
    {
      title: 'Alpha',
      value: `${metrics.alpha.toFixed(1)}%`,
      description: 'Excess return vs market',
      icon: Zap,
      color: metrics.alpha >= 0 ? 'text-success-600' : 'text-error-600',
      bg: metrics.alpha >= 0 ? 'bg-success-50' : 'bg-error-50'
    },
    {
      title: 'Recovery Factor',
      value: metrics.recoveryFactor.toFixed(2),
      description: 'Net profit / max drawdown',
      icon: TrendingUp,
      color: getRiskLevel(metrics.recoveryFactor, [2, 5]).split(' ')[0],
      bg: getRiskLevel(metrics.recoveryFactor, [2, 5]).split(' ')[1]
    }
  ];

  return (
    <div className="space-y-6">
      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {metricCards.map((metric, index) => {
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
                <p className={`text-2xl font-bold mb-2 ${metric.color}`}>
                  {metric.value}
                </p>
                <p className="text-xs text-slate-500">
                  {metric.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Win/Loss Analysis */}
        <div className="card p-6">
          <h4 className="text-lg font-semibold text-slate-900 mb-4">Win/Loss Analysis</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Win Rate</span>
              <span className="font-semibold text-slate-900">{metrics.winRate.toFixed(1)}%</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Average Win</span>
              <span className="font-semibold text-success-600">
                +${metrics.averageWin.toLocaleString()}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Average Loss</span>
              <span className="font-semibold text-error-600">
                -${metrics.averageLoss.toLocaleString()}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Payoff Ratio</span>
              <span className={`font-semibold ${
                metrics.payoffRatio >= 1 ? 'text-success-600' : 'text-error-600'
              }`}>
                {metrics.payoffRatio.toFixed(2)}
              </span>
            </div>

            <div className="pt-3 border-t border-slate-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-600">Largest Win</span>
                <span className="font-semibold text-success-600">
                  +${metrics.largestWin.toLocaleString()}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Largest Loss</span>
                <span className="font-semibold text-error-600">
                  -${metrics.largestLoss.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Risk Metrics */}
        <div className="card p-6">
          <h4 className="text-lg font-semibold text-slate-900 mb-4">Risk Assessment</h4>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Calmar Ratio</span>
              <span className="font-semibold text-slate-900">{metrics.calmarRatio.toFixed(2)}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Ulcer Index</span>
              <span className="font-semibold text-slate-900">{metrics.ulcerIndex.toFixed(2)}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Consecutive Wins</span>
              <span className="font-semibold text-success-600">{metrics.consecutiveWins}</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Consecutive Losses</span>
              <span className="font-semibold text-error-600">{metrics.consecutiveLosses}</span>
            </div>

            <div className="pt-3 border-t border-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600">Risk Level</span>
                <span className={`px-3 py-1 text-xs font-semibold rounded-full ${
                  overallScore >= 80
                    ? 'bg-success-100 text-success-700'
                    : overallScore >= 60
                    ? 'bg-warning-100 text-warning-700'
                    : 'bg-error-100 text-error-700'
                }`}>
                  {overallScore >= 80 ? 'Low' : overallScore >= 60 ? 'Medium' : 'High'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedMetrics;

