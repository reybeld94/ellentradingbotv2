import React, { useState, useEffect } from 'react';
import {
  BarChart3, PieChart, TrendingUp, Shield,
  Download, RefreshCw, Settings,
  Target
} from 'lucide-react';
import PortfolioAllocation from '../components/analytics/PortfolioAllocation';
import PerformanceComparison from '../components/analytics/PerformanceComparison';
import HeatMap from '../components/analytics/HeatMap';
import AdvancedMetrics from '../components/analytics/AdvancedMetrics';

interface AnalyticsData {
  allocation: Array<{
    symbol: string;
    value: number;
    percentage: number;
    change24h: number;
    shares: number;
    avgPrice: number;
    currentPrice: number;
    sector?: string;
  }>;
  performance: Array<{
    period: string;
    portfolio: number;
    benchmarks: Array<{
      name: string;
      symbol: string;
      value: number;
      change: number;
      color: string;
    }>;
  }>;
  heatmap: Array<{
    date: string;
    value: number;
    trades: number;
    pnl: number;
  }>;
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
  totalValue: number;
}

const Analytics: React.FC = () => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'allocation' | 'performance' | 'risk'>('overview');
  const [timeframe, setTimeframe] = useState('1M');

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);

      // Mock data - replace with real API calls
      const mockData: AnalyticsData = {
        allocation: [
          {
            symbol: 'AAPL',
            value: 45000,
            percentage: 30.5,
            change24h: 2.1,
            shares: 300,
            avgPrice: 145.50,
            currentPrice: 150.00,
            sector: 'Technology'
          },
          {
            symbol: 'GOOGL',
            value: 32000,
            percentage: 21.7,
            change24h: -0.8,
            shares: 120,
            avgPrice: 265.00,
            currentPrice: 267.50,
            sector: 'Technology'
          },
          {
            symbol: 'TSLA',
            value: 28000,
            percentage: 19.0,
            change24h: 4.2,
            shares: 140,
            avgPrice: 195.00,
            currentPrice: 200.00,
            sector: 'Automotive'
          },
          {
            symbol: 'MSFT',
            value: 25000,
            percentage: 16.9,
            change24h: 1.5,
            shares: 75,
            avgPrice: 330.00,
            currentPrice: 333.33,
            sector: 'Technology'
          },
          {
            symbol: 'NVDA',
            value: 18000,
            percentage: 12.2,
            change24h: 3.8,
            shares: 60,
            avgPrice: 295.00,
            currentPrice: 300.00,
            sector: 'Technology'
          }
        ],
        performance: [
          {
            period: '1W',
            portfolio: 2.3,
            benchmarks: [
              { name: 'S&P 500', symbol: 'SPY', value: 1.8, change: 1.8, color: '#8b5cf6' },
              { name: 'NASDAQ', symbol: 'QQQ', value: 2.1, change: 2.1, color: '#06b6d4' },
              { name: 'Russell 2000', symbol: 'IWM', value: 0.9, change: 0.9, color: '#f59e0b' }
            ]
          },
          {
            period: '1M',
            portfolio: 8.7,
            benchmarks: [
              { name: 'S&P 500', symbol: 'SPY', value: 5.2, change: 5.2, color: '#8b5cf6' },
              { name: 'NASDAQ', symbol: 'QQQ', value: 7.1, change: 7.1, color: '#06b6d4' },
              { name: 'Russell 2000', symbol: 'IWM', value: 3.4, change: 3.4, color: '#f59e0b' }
            ]
          },
          {
            period: '3M',
            portfolio: 15.2,
            benchmarks: [
              { name: 'S&P 500', symbol: 'SPY', value: 12.1, change: 12.1, color: '#8b5cf6' },
              { name: 'NASDAQ', symbol: 'QQQ', value: 14.8, change: 14.8, color: '#06b6d4' },
              { name: 'Russell 2000', symbol: 'IWM', value: 8.7, change: 8.7, color: '#f59e0b' }
            ]
          }
        ],
        heatmap: Array.from({ length: 365 }, (_, i) => ({
          date: new Date(Date.now() - (365 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          value: Math.random() * 100,
          trades: Math.floor(Math.random() * 10),
          pnl: (Math.random() - 0.5) * 2000
        })),
        metrics: {
          sharpeRatio: 1.45,
          sortinoRatio: 1.78,
          calmarRatio: 0.95,
          maxDrawdown: 12.3,
          volatility: 18.7,
          beta: 1.12,
          alpha: 3.2,
          winRate: 67.5,
          profitFactor: 1.85,
          payoffRatio: 1.4,
          averageWin: 1250,
          averageLoss: 890,
          largestWin: 8500,
          largestLoss: 3200,
          consecutiveWins: 7,
          consecutiveLosses: 3,
          recoveryFactor: 2.8,
          ulcerIndex: 8.1
        },
        totalValue: 148000
      };

      setData(mockData);
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyticsData();

    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAnalyticsData, 300000);
    return () => clearInterval(interval);
  }, []);

  const exportData = () => {
    console.log('Exporting analytics data...');
  };

  const tabs = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'allocation', label: 'Allocation', icon: PieChart },
    { key: 'performance', label: 'Performance', icon: TrendingUp },
    { key: 'risk', label: 'Risk Analysis', icon: Shield }
  ];

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <BarChart3 className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Analytics</h2>
          <p className="text-slate-600">Analyzing your portfolio performance...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Portfolio Analytics</h1>
            <p className="text-slate-600 mt-1">
              Comprehensive analysis and performance insights
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <button onClick={exportData} className="btn-ghost">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>

            <button onClick={fetchAnalyticsData} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>

            <button className="btn-ghost">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="card p-2">
          <div className="flex items-center space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  onClick={() => setSelectedTab(tab.key as any)}
                  className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    selectedTab === tab.key
                      ? 'bg-primary-100 text-primary-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        {selectedTab === 'overview' && data && (
          <div className="space-y-6">
            {/* Quick Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="card p-6 text-center">
                <div className="p-3 bg-primary-100 rounded-xl w-fit mx-auto mb-4">
                  <BarChart3 className="w-6 h-6 text-primary-600" />
                </div>
                <p className="text-2xl font-bold text-slate-900 mb-1">
                  ${data.totalValue.toLocaleString()}
                </p>
                <p className="text-sm text-slate-600">Total Portfolio Value</p>
              </div>

              <div className="card p-6 text-center">
                <div className="p-3 bg-success-100 rounded-xl w-fit mx-auto mb-4">
                  <TrendingUp className="w-6 h-6 text-success-600" />
                </div>
                <p className="text-2xl font-bold text-success-600 mb-1">
                  {data.metrics.sharpeRatio.toFixed(2)}
                </p>
                <p className="text-sm text-slate-600">Sharpe Ratio</p>
              </div>

              <div className="card p-6 text-center">
                <div className="p-3 bg-warning-100 rounded-xl w-fit mx-auto mb-4">
                  <Target className="w-6 h-6 text-warning-600" />
                </div>
                <p className="text-2xl font-bold text-warning-600 mb-1">
                  {data.metrics.winRate.toFixed(1)}%
                </p>
                <p className="text-sm text-slate-600">Win Rate</p>
              </div>

              <div className="card p-6 text-center">
                <div className="p-3 bg-error-100 rounded-xl w-fit mx-auto mb-4">
                  <Shield className="w-6 h-6 text-error-600" />
                </div>
                <p className="text-2xl font-bold text-error-600 mb-1">
                  {data.metrics.maxDrawdown.toFixed(1)}%
                </p>
                <p className="text-sm text-slate-600">Max Drawdown</p>
              </div>
            </div>

            {/* Main Overview Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <PortfolioAllocation
                data={data.allocation}
                totalValue={data.totalValue}
                loading={loading}
              />

              <PerformanceComparison
                data={data.performance}
                loading={loading}
                selectedPeriod={timeframe}
                onPeriodChange={setTimeframe}
              />
            </div>

            {/* Heatmap */}
            <HeatMap
              data={data.heatmap}
              loading={loading}
              title="Trading Activity Heatmap"
            />
          </div>
        )}

        {selectedTab === 'allocation' && data && (
          <div className="space-y-6">
            <PortfolioAllocation
              data={data.allocation}
              totalValue={data.totalValue}
              loading={loading}
              viewType="pie"
            />

            {/* Sector Breakdown */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Sector Allocation</h3>
              {(() => {
                const sectorData = data.allocation.reduce((acc, item) => {
                  const sector = item.sector || 'Other';
                  if (!acc[sector]) {
                    acc[sector] = { value: 0, percentage: 0 };
                  }
                  acc[sector].value += item.value;
                  acc[sector].percentage += item.percentage;
                  return acc;
                }, {} as Record<string, { value: number; percentage: number }>);

                return (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(sectorData).map(([sector, data]) => (
                      <div key={sector} className="text-center p-4 bg-slate-50 rounded-xl">
                        <p className="text-lg font-bold text-slate-900 mb-1">
                          {data.percentage.toFixed(1)}%
                        </p>
                        <p className="text-sm text-slate-600">{sector}</p>
                        <p className="text-xs text-slate-500">
                          ${data.value.toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {selectedTab === 'performance' && data && (
          <div className="space-y-6">
            <PerformanceComparison
              data={data.performance}
              loading={loading}
              selectedPeriod={timeframe}
              onPeriodChange={setTimeframe}
            />

            {/* Performance Timeline */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Performance Timeline</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data.performance.map((period) => (
                  <div key={period.period} className="text-center p-4 bg-slate-50 rounded-xl">
                    <p className="text-xs font-medium text-slate-500 mb-1">{period.period}</p>
                    <p className={`text-xl font-bold mb-2 ${
                      period.portfolio >= 0 ? 'text-success-600' : 'text-error-600'
                    }`}>
                      {period.portfolio >= 0 ? '+' : ''}{period.portfolio.toFixed(1)}%
                    </p>
                    <div className="text-xs text-slate-600">
                      vs {period.benchmarks[0]?.symbol}:{' '}
                      <span className={period.portfolio > period.benchmarks[0]?.value ? 'text-success-600' : 'text-error-600'}>
                        {period.portfolio > period.benchmarks[0]?.value ? '+' : ''}
                        {(period.portfolio - (period.benchmarks[0]?.value || 0)).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'risk' && data && (
          <div className="space-y-6">
            <AdvancedMetrics metrics={data.metrics} loading={loading} />
          </div>
        )}
      </div>
    </div>
  );
};

export default Analytics;

