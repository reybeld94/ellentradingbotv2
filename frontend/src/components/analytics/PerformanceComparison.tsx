import React, { useState } from 'react';
import { BarChart3, TrendingUp, TrendingDown } from 'lucide-react';

interface BenchmarkData {
  name: string;
  symbol: string;
  value: number;
  change: number;
  color: string;
}

interface PerformanceData {
  period: string;
  portfolio: number;
  benchmarks: BenchmarkData[];
}

interface PerformanceComparisonProps {
  data: PerformanceData[];
  loading?: boolean;
  selectedPeriod?: string;
  onPeriodChange?: (period: string) => void;
}

const PerformanceComparison: React.FC<PerformanceComparisonProps> = ({
  data,
  loading = false,
  selectedPeriod = '1M',
  onPeriodChange
}) => {
  const [hoveredBar, setHoveredBar] = useState<string | null>(null);

  const periods = ['1W', '1M', '3M', '6M', '1Y', 'ALL'];

  const currentData = data.find(d => d.period === selectedPeriod) || data[0];

  if (!currentData) return null;

  const allValues = [
    { name: 'Portfolio', value: currentData.portfolio, color: '#0ea5e9' },
    ...currentData.benchmarks.map(b => ({ name: b.name, value: b.value, color: b.color }))
  ];

  const maxValue = Math.max(...allValues.map(v => Math.abs(v.value)));
  const minValue = Math.min(...allValues.map(v => v.value));

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 bg-slate-200 rounded w-48 animate-pulse"></div>
          <div className="h-8 bg-slate-200 rounded w-40 animate-pulse"></div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="flex items-center space-x-4 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-16"></div>
              <div className="flex-1 h-8 bg-slate-200 rounded"></div>
              <div className="h-4 bg-slate-200 rounded w-12"></div>
            </div>
          ))}
        </div>
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
            Performance Comparison
          </h3>
          <p className="text-sm text-slate-600">
            Portfolio vs benchmarks for {selectedPeriod}
          </p>
        </div>

        {/* Period Selector */}
        <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
          {periods.map((period) => (
            <button
              key={period}
              onClick={() => onPeriodChange?.(period)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                selectedPeriod === period
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {period}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="space-y-4">
        {allValues.map((item, index) => {
          const isPositive = item.value >= 0;
          const barWidth = maxValue > 0 ? Math.abs(item.value) / maxValue * 100 : 0;
          const isHovered = hoveredBar === item.name;

          return (
            <div
              key={item.name}
              className="group cursor-pointer"
              onMouseEnter={() => setHoveredBar(item.name)}
              onMouseLeave={() => setHoveredBar(null)}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className={`text-sm font-medium transition-colors duration-200 ${
                    isHovered ? 'text-slate-900' : 'text-slate-700'
                  }`}>
                    {item.name}
                  </span>
                  {index === 0 && (
                    <span className="px-2 py-1 text-xs bg-primary-100 text-primary-700 rounded-full">
                      You
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-semibold ${
                    isPositive ? 'text-success-600' : 'text-error-600'
                  }`}>
                    {isPositive ? '+' : ''}{item.value.toFixed(2)}%
                  </span>
                  {isPositive ? (
                    <TrendingUp className="w-4 h-4 text-success-600" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-error-600" />
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative w-full h-6 bg-slate-100 rounded-lg overflow-hidden">
                {/* Zero line */}
                {minValue < 0 && (
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-slate-300"
                    style={{
                      left: `${(Math.abs(minValue) / (maxValue - minValue)) * 100}%`
                    }}
                  />
                )}

                {/* Bar */}
                <div
                  className={`absolute top-0 bottom-0 rounded-lg transition-all duration-500 ${
                    isHovered ? 'opacity-80' : ''
                  }`}
                  style={{
                    backgroundColor: item.color,
                    width: `${barWidth}%`,
                    left: isPositive ? `${minValue < 0 ? (Math.abs(minValue) / (maxValue - minValue)) * 100 : 0}%` : `${(Math.abs(minValue) - Math.abs(item.value)) / (maxValue - minValue) * 100}%`
                  }}
                />

                {/* Value label */}
                <div className="absolute inset-0 flex items-center justify-end pr-3">
                  <span className="text-xs font-medium text-white drop-shadow">
                    {isPositive ? '+' : ''}{item.value.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-6 border-t border-slate-200">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <p className="text-xs font-medium text-slate-500 mb-1">Outperformance</p>
            <p className={`text-lg font-bold ${
              currentData.portfolio > (currentData.benchmarks[0]?.value || 0)
                ? 'text-success-600'
                : 'text-error-600'
            }`}>
              {currentData.portfolio > (currentData.benchmarks[0]?.value || 0) ? '+' : ''}
              {(currentData.portfolio - (currentData.benchmarks[0]?.value || 0)).toFixed(2)}%
            </p>
          </div>

          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <p className="text-xs font-medium text-slate-500 mb-1">Best Benchmark</p>
            <p className="text-lg font-bold text-primary-600">
              {currentData.benchmarks.reduce((best, current) =>
                current.value > best.value ? current : best,
                currentData.benchmarks[0]
              )?.symbol || 'N/A'}
            </p>
          </div>

          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <p className="text-xs font-medium text-slate-500 mb-1">Ranking</p>
            <p className="text-lg font-bold text-indigo-600">
              {allValues
                .sort((a, b) => b.value - a.value)
                .findIndex(item => item.name === 'Portfolio') + 1}/{allValues.length}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceComparison;

