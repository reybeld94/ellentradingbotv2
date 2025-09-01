import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Clock,
  BarChart3,
  PieChart,
  AlertTriangle,
  Trophy,
  Shield,
  Calendar,
} from 'lucide-react';
import api from '../../services/api';
import EquityCurve from './EquityCurve';
import TradeDistribution from './TradeDistribution';
import MonthlyHeatmap from './MonthlyHeatmap';
import RiskDashboard from './RiskDashboard';

interface PerformanceMetrics {
  total_pnl: number;
  total_pnl_percentage: number;
  sharpe_ratio: number;
  max_drawdown: number;
  win_rate: number;
  avg_hold_time: string;
  profit_factor: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  largest_win: number;
  largest_loss: number;
  avg_win: number;
  avg_loss: number;
  timeframe: string;
  start_date: string;
  end_date: string;
}

interface AnalyticsSummary {
  timeframes: {
    [key: string]: {
      total_pnl: number;
      total_pnl_percentage: number;
      win_rate: number;
      total_trades: number;
      sharpe_ratio: number;
    };
  };
  all_time: {
    total_pnl: number;
    max_drawdown: number;
    profit_factor: number;
    largest_win: number;
    largest_loss: number;
    avg_hold_time: string;
  };
  portfolio_id: number;
  portfolio_name: string;
}

const PortfolioAnalytics: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('1M');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'equity' | 'distribution' | 'monthly' | 'risk'>('overview');

  const timeframeOptions = [
    { value: '1D', label: '1 Day' },
    { value: '1W', label: '1 Week' },
    { value: '1M', label: '1 Month' },
    { value: '3M', label: '3 Months' },
    { value: '6M', label: '6 Months' },
    { value: '1Y', label: '1 Year' },
    { value: 'ALL', label: 'All Time' }
  ];

  useEffect(() => {
    fetchAnalyticsData();
  }, [selectedTimeframe]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [metricsResponse, summaryResponse] = await Promise.all([
        api.analytics.getPerformanceMetrics(selectedTimeframe),
        api.analytics.getSummary()
      ]);

      setMetrics(metricsResponse);
      setSummary(summaryResponse);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Error loading analytics data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (percentage: number): string => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
  };

  const getPnlColor = (pnl: number): string => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const MetricCard: React.FC<{
    title: string;
    value: string | number;
    subtitle?: string;
    icon: React.ElementType;
    colorClass?: string;
    trend?: 'up' | 'down' | 'neutral';
  }> = ({ title, value, subtitle, icon: Icon, colorClass = 'text-blue-600', trend }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Icon className={`h-8 w-8 ${colorClass}`} />
          <div>
            <h3 className="text-sm font-medium text-gray-500">{title}</h3>
            <p className={`text-2xl font-bold ${colorClass}`}>{value}</p>
            {subtitle && (
              <p className="text-sm text-gray-400">{subtitle}</p>
            )}
          </div>
        </div>
        {trend && (
          <div className="flex items-center">
            {trend === 'up' && <TrendingUp className="h-5 w-5 text-green-500" />}
            {trend === 'down' && <TrendingDown className="h-5 w-5 text-red-500" />}
          </div>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
        <button
          onClick={fetchAnalyticsData}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!metrics || !summary) {
    return (
      <div className="text-center text-gray-500 py-8">
        No analytics data available
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Portfolio Analytics</h1>
          <p className="text-gray-600">
            Performance analysis for {summary.portfolio_name}
          </p>
        </div>

        {/* Timeframe Selector */}
        <div className="flex space-x-2">
          {timeframeOptions.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedTimeframe(option.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedTimeframe === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg mb-6">
        {[ 
          { key: 'overview', label: 'Overview', icon: BarChart3 },
          { key: 'equity', label: 'Equity Curve', icon: TrendingUp },
          { key: 'distribution', label: 'Trade Distribution', icon: PieChart },
          { key: 'monthly', label: 'Monthly Performance', icon: Calendar },
          { key: 'risk', label: 'Risk Dashboard', icon: Shield },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <Icon className="h-4 w-4 mr-2" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Content based on active tab */}
      {activeTab === 'overview' && (
        <>
          {/* Main Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <MetricCard
              title="Total P&L"
              value={formatCurrency(metrics.total_pnl)}
              subtitle={formatPercentage(metrics.total_pnl_percentage)}
              icon={DollarSign}
              colorClass={getPnlColor(metrics.total_pnl)}
              trend={metrics.total_pnl > 0 ? 'up' : metrics.total_pnl < 0 ? 'down' : 'neutral'}
            />

            <MetricCard
              title="Win Rate"
              value={formatPercentage(metrics.win_rate)}
              subtitle={`${metrics.winning_trades}/${metrics.total_trades} trades`}
              icon={Target}
              colorClass={metrics.win_rate >= 50 ? 'text-green-600' : 'text-red-600'}
            />

            <MetricCard
              title="Profit Factor"
              value={metrics.profit_factor.toFixed(2)}
              subtitle={metrics.profit_factor > 1 ? 'Profitable' : 'Unprofitable'}
              icon={Trophy}
              colorClass={metrics.profit_factor > 1 ? 'text-green-600' : 'text-red-600'}
            />

            <MetricCard
              title="Max Drawdown"
              value={formatPercentage(metrics.max_drawdown)}
              icon={Shield}
              colorClass={Math.abs(metrics.max_drawdown) < 10 ? 'text-green-600' : 'text-red-600'}
            />
          </div>

          {/* Advanced Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <MetricCard
              title="Sharpe Ratio"
              value={metrics.sharpe_ratio.toFixed(3)}
              subtitle={
                metrics.sharpe_ratio > 1
                  ? 'Excellent'
                  : metrics.sharpe_ratio > 0.5
                  ? 'Good'
                  : 'Poor'
              }
              icon={BarChart3}
              colorClass={
                metrics.sharpe_ratio > 1 ? 'text-green-600' : 'text-yellow-600'
              }
            />

            <MetricCard
              title="Avg Hold Time"
              value={metrics.avg_hold_time}
              icon={Clock}
              colorClass="text-purple-600"
            />

            <MetricCard
              title="Total Trades"
              value={metrics.total_trades}
              subtitle={`${selectedTimeframe} period`}
              icon={PieChart}
              colorClass="text-blue-600"
            />
          </div>

          {/* Trade Summary */}
          <div className="bg-white p-6 rounded-lg shadow-sm border mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Trade Summary</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(metrics.largest_win)}
                </p>
                <p className="text-sm text-gray-500">Largest Win</p>
              </div>

              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(metrics.largest_loss)}
                </p>
                <p className="text-sm text-gray-500">Largest Loss</p>
              </div>

              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(metrics.avg_win)}
                </p>
                <p className="text-sm text-gray-500">Avg Win</p>
              </div>

              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(metrics.avg_loss)}
                </p>
                <p className="text-sm text-gray-500">Avg Loss</p>
              </div>
            </div>
          </div>

          {/* Performance Comparison */}
          <div className="bg-white p-6 rounded-lg shadow-sm border">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Comparison</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-4 font-medium text-gray-700">
                      Period
                    </th>
                    <th className="text-right py-2 px-4 font-medium text-gray-700">
                      P&L
                    </th>
                    <th className="text-right py-2 px-4 font-medium text-gray-700">
                      P&L %
                    </th>
                    <th className="text-right py-2 px-4 font-medium text-gray-700">
                      Win Rate
                    </th>
                    <th className="text-right py-2 px-4 font-medium text-gray-700">
                      Trades
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(summary.timeframes).map(([period, data]) => (
                    <tr key={period} className="border-b">
                      <td className="py-2 px-4 font-medium capitalize">
                        {period
                          .replace('d', ' day')
                          .replace('w', ' week')
                          .replace('m', ' month')}
                      </td>
                      <td
                        className={`py-2 px-4 text-right font-medium ${getPnlColor(
                          data.total_pnl,
                        )}`}
                      >
                        {formatCurrency(data.total_pnl)}
                      </td>
                      <td
                        className={`py-2 px-4 text-right ${getPnlColor(
                          data.total_pnl_percentage,
                        )}`}
                      >
                        {formatPercentage(data.total_pnl_percentage)}
                      </td>
                      <td className="py-2 px-4 text-right">
                        {formatPercentage(data.win_rate)}
                      </td>
                      <td className="py-2 px-4 text-right">
                        {data.total_trades}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {activeTab === 'equity' && (
        <EquityCurve
          timeframe={selectedTimeframe}
          portfolioId={summary?.portfolio_id}
          height={500}
        />
      )}

      {activeTab === 'distribution' && (
        <TradeDistribution
          timeframe={selectedTimeframe}
          portfolioId={summary?.portfolio_id}
        />
      )}

      {activeTab === 'monthly' && (
        <MonthlyHeatmap portfolioId={summary?.portfolio_id} />
      )}

      {activeTab === 'risk' && (
        <RiskDashboard timeframe={selectedTimeframe} portfolioId={summary?.portfolio_id} />
      )}
    </div>
  );
};

export default PortfolioAnalytics;

