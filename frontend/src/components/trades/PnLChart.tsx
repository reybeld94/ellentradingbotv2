import React, { useState } from 'react';
import { TrendingUp, TrendingDown, BarChart3 } from 'lucide-react';

interface ChartDataPoint {
  date: string;
  cumulativePnL: number;
  dailyPnL: number;
  tradeCount: number;
}

interface PnLChartProps {
  data: ChartDataPoint[];
  loading?: boolean;
  timeframe?: '1W' | '1M' | '3M' | '6M' | '1Y';
  onTimeframeChange?: (timeframe: '1W' | '1M' | '3M' | '6M' | '1Y') => void;
}

const PnLChart: React.FC<PnLChartProps> = ({
  data,
  loading = false,
  timeframe = '1M',
  onTimeframeChange
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState(timeframe);
  const [showCumulative, setShowCumulative] = useState(true);

  const timeframes = [
    { key: '1W', label: '1W' },
    { key: '1M', label: '1M' },
    { key: '3M', label: '3M' },
    { key: '6M', label: '6M' },
    { key: '1Y', label: '1Y' },
  ] as const;

  const currentPnL = data.length > 0 ? data[data.length - 1].cumulativePnL : 0;
  const previousPnL = data.length > 1 ? data[0].cumulativePnL : 0;
  const change = currentPnL - previousPnL;
  const changePercent = previousPnL !== 0 ? ((change / Math.abs(previousPnL)) * 100) : 0;
  const isPositive = change >= 0;

  const totalTrades = data.reduce((sum, point) => sum + point.tradeCount, 0);
  const avgDailyPnL = data.length > 0 ? data.reduce((sum, point) => sum + point.dailyPnL, 0) / data.length : 0;

  // Generate SVG path for the chart
  const generatePath = () => {
    if (data.length === 0) return '';
    
    const width = 600;
    const height = 200;
    const padding = 40;
    
    const values = data.map(d => showCumulative ? d.cumulativePnL : d.dailyPnL);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = maxValue - minValue || 1;
    
    const points = data.map((point, index) => {
      const x = padding + ((width - 2 * padding) * index) / (data.length - 1);
      const value = showCumulative ? point.cumulativePnL : point.dailyPnL;
      const y = height - padding - ((value - minValue) / valueRange) * (height - 2 * padding);
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  };

  const generateGradientPath = () => {
    const path = generatePath();
    if (!path) return '';
    
    const width = 600;
    const height = 200;
    return `${path} L ${width - 40},${height - 40} L 40,${height - 40} Z`;
  };

  const generateZeroLine = () => {
    if (data.length === 0) return '';
    
    const width = 600;
    const height = 200;
    const padding = 40;
    
    const values = data.map(d => showCumulative ? d.cumulativePnL : d.dailyPnL);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = maxValue - minValue || 1;
    
    const zeroY = height - padding - ((0 - minValue) / valueRange) * (height - 2 * padding);
    return `M ${padding},${zeroY} L ${width - padding},${zeroY}`;
  };

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="space-y-2">
            <div className="h-4 bg-slate-200 rounded w-32 animate-pulse"></div>
            <div className="h-8 bg-slate-200 rounded w-48 animate-pulse"></div>
          </div>
          <div className="h-10 bg-slate-200 rounded w-40 animate-pulse"></div>
        </div>
        <div className="h-48 bg-slate-200 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-primary-600" />
            P&L Performance
          </h3>
          <div className="flex items-center space-x-4">
            <span className="text-2xl font-bold text-slate-900">
              ${Math.abs(currentPnL).toLocaleString('en-US', { minimumFractionDigits: 2 })}
            </span>
            <div className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg text-sm font-semibold
              ${isPositive 
                ? 'bg-success-50 text-success-700 border border-success-200' 
                : 'bg-error-50 text-error-700 border border-error-200'
              }`}>
              {isPositive ? (
                <TrendingUp className="h-4 w-4" />
              ) : (
                <TrendingDown className="h-4 w-4" />
              )}
              <span>
                {isPositive ? '+' : ''}${Math.abs(change).toFixed(2)} ({changePercent.toFixed(1)}%)
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-4 text-sm text-slate-600 mt-2">
            <span>{totalTrades} trades</span>
            <span>•</span>
            <span>Avg daily: ${avgDailyPnL.toFixed(2)}</span>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          {/* Chart Type Toggle */}
          <div className="flex items-center space-x-1 bg-slate-100 rounded-xl p-1">
            <button
              onClick={() => setShowCumulative(true)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${
                showCumulative
                  ? 'bg-white text-primary-700 shadow-soft'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Cumulative
            </button>
            <button
              onClick={() => setShowCumulative(false)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${
                !showCumulative
                  ? 'bg-white text-primary-700 shadow-soft'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Daily
            </button>
          </div>

          {/* Timeframe Selector */}
          <div className="flex items-center space-x-1 bg-slate-100 rounded-xl p-1">
            {timeframes.map((tf) => (
              <button
                key={tf.key}
                onClick={() => {
                  setSelectedPeriod(tf.key);
                  onTimeframeChange?.(tf.key);
                }}
                className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all duration-200 ${
                  selectedPeriod === tf.key
                    ? 'bg-white text-primary-700 shadow-soft'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="relative h-48 w-full">
        {data.length === 0 ? (
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="text-center">
              <BarChart3 className="w-12 h-12 mx-auto mb-2 text-slate-300" />
              <p>No trading data available</p>
            </div>
          </div>
        ) : (
          <svg
            width="100%"
            height="100%"
            viewBox="0 0 600 200"
            className="overflow-visible"
          >
            <defs>
              <linearGradient
                id="pnlGradient"
                x1="0%"
                y1="0%"
                x2="0%"
                y2="100%"
              >
                <stop
                  offset="0%"
                  stopColor={isPositive ? '#22c55e' : '#ef4444'}
                  stopOpacity="0.2"
                />
                <stop
                  offset="100%"
                  stopColor={isPositive ? '#22c55e' : '#ef4444'}
                  stopOpacity="0"
                />
              </linearGradient>
            </defs>
            
            {/* Zero line */}
            <path
              d={generateZeroLine()}
              stroke="#e2e8f0"
              strokeWidth="1"
              strokeDasharray="4,4"
              fill="none"
            />
            
            {/* Gradient Fill */}
            <path
              d={generateGradientPath()}
              fill="url(#pnlGradient)"
              className="transition-all duration-1000"
            />
            
            {/* Main Line */}
            <path
              d={generatePath()}
              stroke={isPositive ? '#22c55e' : '#ef4444'}
              strokeWidth="3"
              fill="none"
              className="transition-all duration-1000"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            
            {/* Data Points */}
            {data.map((point, index) => {
              const width = 600;
              const height = 200;
              const padding = 40;
              const values = data.map(d => showCumulative ? d.cumulativePnL : d.dailyPnL);
              const minValue = Math.min(...values);
              const maxValue = Math.max(...values);
              const valueRange = maxValue - minValue || 1;
              
              const x = padding + ((width - 2 * padding) * index) / (data.length - 1);
              const value = showCumulative ? point.cumulativePnL : point.dailyPnL;
              const y = height - padding - ((value - minValue) / valueRange) * (height - 2 * padding);
              
              return (
                <circle
                  key={index}
                  cx={x}
                  cy={y}
                  r="4"
                  fill={isPositive ? '#22c55e' : '#ef4444'}
                  className="opacity-0 hover:opacity-100 transition-opacity duration-200 cursor-pointer"
                  title={`${point.date}: $${value.toFixed(2)}`}
                />
              );
            })}
          </svg>
        )}
      </div>
    </div>
  );
};

export default PnLChart;
