import React, { useState } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface ChartDataPoint {
  date: string;
  value: number;
  pnl?: number;
}

interface PortfolioChartProps {
  data: ChartDataPoint[];
  loading?: boolean;
  timeframe?: '1D' | '1W' | '1M' | '3M' | '1Y';
  onTimeframeChange?: (timeframe: '1D' | '1W' | '1M' | '3M' | '1Y') => void;
}

const PortfolioChart: React.FC<PortfolioChartProps> = ({
  data,
  loading = false,
  timeframe = '1D',
  onTimeframeChange
}) => {
  const [selectedPeriod, setSelectedPeriod] = useState(timeframe);

  const timeframes = [
    { key: '1D', label: '1D' },
    { key: '1W', label: '1W' },
    { key: '1M', label: '1M' },
    { key: '3M', label: '3M' },
    { key: '1Y', label: '1Y' },
  ] as const;

  const currentValue = data.length > 0 ? data[data.length - 1].value : 0;
  const previousValue = data.length > 1 ? data[0].value : currentValue;
  const change = currentValue - previousValue;
  const changePercent = previousValue !== 0 ? ((change / previousValue) * 100) : 0;
  const isPositive = change >= 0;

  // Generate SVG path for the chart
  const generatePath = () => {
    if (data.length === 0) return '';
    
    const width = 400;
    const height = 120;
    const padding = 20;
    
    const minValue = Math.min(...data.map(d => d.value));
    const maxValue = Math.max(...data.map(d => d.value));
    const valueRange = maxValue - minValue || 1;
    
    const points = data.map((point, index) => {
      const x = padding + ((width - 2 * padding) * index) / (data.length - 1);
      const y = height - padding - ((point.value - minValue) / valueRange) * (height - 2 * padding);
      return `${x},${y}`;
    });
    
    return `M ${points.join(' L ')}`;
  };

  const generateGradientPath = () => {
    const path = generatePath();
    if (!path) return '';
    
    const width = 400;
    const height = 120;
    return `${path} L ${width - 20},${height - 20} L 20,${height - 20} Z`;
  };

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="space-y-2">
            <div className="h-4 bg-slate-200 rounded w-32 animate-pulse"></div>
            <div className="h-8 bg-slate-200 rounded w-48 animate-pulse"></div>
          </div>
          <div className="h-10 bg-slate-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="h-32 bg-slate-200 rounded animate-pulse"></div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            Portfolio Performance
          </h3>
          <div className="flex items-center space-x-3">
            <span className="text-2xl font-bold text-slate-900">
              ${currentValue.toLocaleString('en-US', { minimumFractionDigits: 2 })}
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
                {isPositive ? '+' : ''}${change.toFixed(2)} ({changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
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

      {/* Chart */}
      <div className="relative h-32 w-full">
        <svg
          width="100%"
          height="100%"
          viewBox="0 0 400 120"
          className="overflow-visible"
        >
          <defs>
            <linearGradient
              id="portfolioGradient"
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
          
          {/* Gradient Fill */}
          <path
            d={generateGradientPath()}
            fill="url(#portfolioGradient)"
            className="transition-all duration-1000"
          />
          
          {/* Main Line */}
          <path
            d={generatePath()}
            stroke={isPositive ? '#22c55e' : '#ef4444'}
            strokeWidth="2"
            fill="none"
            className="transition-all duration-1000"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Data Points */}
          {data.map((point, index) => {
            const width = 400;
            const height = 120;
            const padding = 20;
            const minValue = Math.min(...data.map(d => d.value));
            const maxValue = Math.max(...data.map(d => d.value));
            const valueRange = maxValue - minValue || 1;
            
            const x = padding + ((width - 2 * padding) * index) / (data.length - 1);
            const y = height - padding - ((point.value - minValue) / valueRange) * (height - 2 * padding);
            
            return (
              <circle
                key={index}
                cx={x}
                cy={y}
                r="3"
                fill={isPositive ? '#22c55e' : '#ef4444'}
                className="opacity-0 hover:opacity-100 transition-opacity duration-200"
              />
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default PortfolioChart;

