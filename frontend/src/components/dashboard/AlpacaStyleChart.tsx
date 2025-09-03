import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';
import { api } from '../../services/api';

interface PortfolioDataPoint {
  timestamp: string;
  portfolio_value: number;
}

interface PortfolioPerformanceData {
  current_value: number;
  change_amount: number;
  change_percent: number;
  initial_value: number;
  timeframe: string;
  last_updated: string;
  historical_data: PortfolioDataPoint[];
}

interface AlpacaStyleChartProps {
  loading?: boolean;
}

const AlpacaStyleChart: React.FC<AlpacaStyleChartProps> = ({
  loading = false
}) => {
  const [data, setData] = useState<PortfolioPerformanceData | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<
    '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'
  >('1D');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const timeframes: Array<{ key: typeof selectedTimeframe; label: string }> = [
    { key: '1D', label: '1D' },
    { key: '1W', label: '1W' },
    { key: '1M', label: '1M' },
    { key: '3M', label: '3M' },
    { key: '1Y', label: '1Y' },
    { key: 'ALL', label: 'All' }
  ];

  const fetchData = async (
    timeframe: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL'
  ) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.trading.getPortfolioPerformance(timeframe);
      if (response.ok) {
        const portfolioData = await response.json();
        setData(portfolioData);
      } else {
        throw new Error('Failed to fetch portfolio data');
      }
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('Error fetching portfolio performance:', err);
      setError('Failed to load portfolio data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData(selectedTimeframe);
  }, [selectedTimeframe]);

  useEffect(() => {
    if (selectedTimeframe === '1D') {
      const interval = setInterval(() => {
        fetchData('1D');
      }, 30000);
      return () => clearInterval(interval);
    }
  }, [selectedTimeframe]);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(value);
  };

  const formatTimestamp = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();

    if (isToday && selectedTimeframe === '1D') {
      return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    }

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTooltip = (value: any, name: string, props: any) => {
    if (name === 'portfolio_value') {
      const timestamp = new Date(props.payload.timestamp);
      return [
        formatCurrency(value),
        timestamp.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
          hour12: true
        })
      ];
    }
    return [value, name];
  };

  if (loading || isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="h-4 bg-gray-200 rounded w-32 mb-2"></div>
              <div className="h-8 bg-gray-200 rounded w-48 mb-1"></div>
              <div className="h-4 bg-gray-200 rounded w-40"></div>
            </div>
            <div className="flex space-x-2">
              {timeframes.map((tf) => (
                <div key={tf.key} className="h-8 w-10 bg-gray-200 rounded"></div>
              ))}
            </div>
          </div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="text-center text-red-600">{error || 'No data available'}</div>
      </div>
    );
  }

  const isPositive = data.change_amount >= 0;
  const chartColor = isPositive ? '#10B981' : '#EF4444';
  const lastUpdated = new Date(data.last_updated);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-sm font-medium text-gray-600 mb-2">
            Your portfolio
          </h3>
          <div className="flex items-center space-x-2">
            <span className="text-3xl font-bold text-gray-900">
              {formatCurrency(data.current_value)}
            </span>
            <span
              className={`text-lg font-medium ${
                isPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {isPositive ? '+' : ''}
              {data.change_percent}%
            </span>
          </div>
          <div className="text-sm text-gray-500 mt-1">
            {lastUpdated.toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
              hour12: true,
              timeZoneName: 'short'
            })}
          </div>
        </div>
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {timeframes.map((tf) => (
            <button
              key={tf.key}
              onClick={() => setSelectedTimeframe(tf.key)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                selectedTimeframe === tf.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64 -mx-2">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.historical_data}>
            <XAxis
              dataKey="timestamp"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 12, fill: '#6B7280' }}
              tickFormatter={formatTimestamp}
              interval="preserveStartEnd"
            />
            <YAxis hide domain={['dataMin - 10', 'dataMax + 10']} />
            <Tooltip
              formatter={formatTooltip}
              labelFormatter={() => ''}
              contentStyle={{
                backgroundColor: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
            />
            <Line
              type="monotone"
              dataKey="portfolio_value"
              stroke={chartColor}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, stroke: chartColor, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AlpacaStyleChart;

