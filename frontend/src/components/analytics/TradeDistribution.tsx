import React, { useState, useEffect } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  PieChart,
  Pie,
  Legend,
} from 'recharts';
import { BarChart3, PieChart as PieChartIcon } from 'lucide-react';
import api from '../../services/api';

interface TradeDistributionData {
  win_distribution: Array<{
    range: string;
    count: number;
    percentage: number;
  }>;
  loss_distribution: Array<{
    range: string;
    count: number;
    percentage: number;
  }>;
  total_winners: number;
  total_losers: number;
  avg_winner: number;
  avg_loser: number;
}

interface TradeDistributionProps {
  timeframe?: string;
  portfolioId?: number;
}

const TradeDistribution: React.FC<TradeDistributionProps> = ({
  timeframe = '3M',
  portfolioId,
}) => {
  const [distribution, setDistribution] = useState<TradeDistributionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewType, setViewType] = useState<'bar' | 'pie'>('bar');

  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;

    const fetchTradeDistribution = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await api.analytics.getTradeAnalytics(
          timeframe,
          portfolioId,
          controller.signal
        );
        if (!isMounted) return;
        const data = await response.json();
        setDistribution(data.trade_distribution);
      } catch (err) {
        if (!isMounted) return;
        console.error('Error fetching trade distribution:', err);
        setError('Error loading trade distribution data');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchTradeDistribution();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [timeframe, portfolioId]);

  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(2)}%`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !distribution) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <span className="text-red-700">{error || 'No data available'}</span>
      </div>
    );
  }

  const combinedData: Array<{ range: string; winners: number; losers: number; winPercent: number; lossPercent: number }> = [];
  const maxWinLength = Math.max(
    distribution.win_distribution.length,
    distribution.loss_distribution.length,
  );

  for (let i = 0; i < maxWinLength; i++) {
    const winData = distribution.win_distribution[i];
    const lossData = distribution.loss_distribution[i];

    combinedData.push({
      range: winData?.range || lossData?.range || `Range ${i + 1}`,
      winners: winData?.count || 0,
      losers: -(lossData?.count || 0),
      winPercent: winData?.percentage || 0,
      lossPercent: lossData?.percentage || 0,
    });
  }

  const pieData = [
    {
      name: 'Winning Trades',
      value: distribution.total_winners,
      color: '#10b981',
    },
    {
      name: 'Losing Trades',
      value: distribution.total_losers,
      color: '#ef4444',
    },
  ];

  const COLORS = ['#10b981', '#ef4444'];

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Trade Distribution</h3>
          <p className="text-sm text-gray-600">
            Distribution of winning and losing trades by P&L range
          </p>
        </div>

        <div className="flex bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setViewType('bar')}
            className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewType === 'bar'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            Bar Chart
          </button>
          <button
            onClick={() => setViewType('pie')}
            className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
              viewType === 'pie'
                ? 'bg-white text-gray-900 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <PieChartIcon className="h-4 w-4 mr-2" />
            Pie Chart
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-2xl font-bold text-green-600">
            {distribution.total_winners}
          </p>
          <p className="text-sm text-gray-600">Winners</p>
        </div>
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <p className="text-2xl font-bold text-red-600">
            {distribution.total_losers}
          </p>
          <p className="text-sm text-gray-600">Losers</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-xl font-bold text-green-600">
            {formatPercentage(distribution.avg_winner)}
          </p>
          <p className="text-sm text-gray-600">Avg Winner Return (%)</p>
        </div>
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <p className="text-xl font-bold text-red-600">
            {formatPercentage(distribution.avg_loser)}
          </p>
          <p className="text-sm text-gray-600">Avg Loser Return (%)</p>
        </div>
      </div>

      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          {viewType === 'bar' ? (
            <BarChart data={combinedData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="range"
                tick={{ fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                formatter={(value: any, name: string) => {
                  const absValue = Math.abs(value as number);
                  const label = name === 'winners' ? 'Winners' : 'Losers';
                  return [absValue, label];
                }}
              />
              <Legend />
              <Bar dataKey="winners" fill="#10b981" name="Winners" radius={[2, 2, 0, 0]} />
              <Bar dataKey="losers" fill="#ef4444" name="Losers" radius={[0, 0, 2, 2]} />
            </BarChart>
          ) : (
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent = 0 }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TradeDistribution;

