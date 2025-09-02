import React, { useState } from 'react';
import { PieChart, BarChart3, TrendingUp, TrendingDown } from 'lucide-react';
import SymbolLogo from '../SymbolLogo';

interface AllocationData {
  symbol: string;
  value: number;
  percentage: number;
  change24h: number;
  shares: number;
  avgPrice: number;
  currentPrice: number;
  sector?: string;
}

interface PortfolioAllocationProps {
  data: AllocationData[];
  totalValue: number;
  loading?: boolean;
  viewType?: 'pie' | 'bar';
  onViewTypeChange?: (type: 'pie' | 'bar') => void;
}

const PortfolioAllocation: React.FC<PortfolioAllocationProps> = ({
  data,
  totalValue,
  loading = false,
  viewType = 'pie',
  onViewTypeChange
}) => {
  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);

  // Generate colors for pie chart
  const generateColor = (index: number, total: number) => {
    const hue = (index * 360) / total;
    return `hsl(${hue}, 70%, 60%)`;
  };

  // Calculate pie chart paths
  const generatePieSlices = () => {
    if (data.length === 0) return [];

    let cumulativePercentage = 0;
    const radius = 80;
    const centerX = 100;
    const centerY = 100;

    return data.map((item, index) => {
      const startAngle = (cumulativePercentage * 360) / 100;
      const endAngle = ((cumulativePercentage + item.percentage) * 360) / 100;

      const startAngleRad = (startAngle * Math.PI) / 180;
      const endAngleRad = (endAngle * Math.PI) / 180;

      const largeArcFlag = item.percentage > 50 ? 1 : 0;

      const x1 = centerX + radius * Math.cos(startAngleRad);
      const y1 = centerY + radius * Math.sin(startAngleRad);
      const x2 = centerX + radius * Math.cos(endAngleRad);
      const y2 = centerY + radius * Math.sin(endAngleRad);

      const pathData = [
        `M ${centerX} ${centerY}`,
        `L ${x1} ${y1}`,
        `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
        'Z'
      ].join(' ');

      cumulativePercentage += item.percentage;

      return {
        ...item,
        path: pathData,
        color: generateColor(index, data.length),
        isSelected: selectedSegment === item.symbol
      };
    });
  };

  const pieSlices = generatePieSlices();

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 bg-slate-200 rounded w-48 animate-pulse"></div>
          <div className="h-8 bg-slate-200 rounded w-20 animate-pulse"></div>
        </div>
        <div className="flex items-center justify-center h-64 bg-slate-100 rounded-xl animate-pulse">
          <PieChart className="w-16 h-16 text-slate-300" />
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
            <PieChart className="w-5 h-5 mr-2 text-primary-600" />
            Portfolio Allocation
          </h3>
          <p className="text-sm text-slate-600">
            Total Value: {formatCurrency(totalValue)}
          </p>
        </div>

        <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => onViewTypeChange?.('pie')}
            className={`p-2 rounded-md transition-all duration-200 ${
              viewType === 'pie'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <PieChart className="w-4 h-4" />
          </button>
          <button
            onClick={() => onViewTypeChange?.('bar')}
            className={`p-2 rounded-md transition-all duration-200 ${
              viewType === 'bar'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <div className="flex items-center justify-center">
          {viewType === 'pie' ? (
            <div className="relative">
              <svg width="200" height="200" viewBox="0 0 200 200">
                {pieSlices.map((slice) => (
                  <path
                    key={slice.symbol}
                    d={slice.path}
                    fill={slice.color}
                    stroke="white"
                    strokeWidth="2"
                    className={`cursor-pointer transition-all duration-200 ${
                      slice.isSelected ? 'opacity-80 transform scale-105' : 'hover:opacity-80'
                    }`}
                    onClick={() => setSelectedSegment(
                      selectedSegment === slice.symbol ? null : slice.symbol
                    )}
                  />
                ))}
                {/* Center circle */}
                <circle
                  cx="100"
                  cy="100"
                  r="30"
                  fill="white"
                  stroke="#e2e8f0"
                  strokeWidth="2"
                />
                <text
                  x="100"
                  y="105"
                  textAnchor="middle"
                  className="text-sm font-semibold fill-slate-900"
                >
                  {data.length}
                </text>
                <text
                  x="100"
                  y="120"
                  textAnchor="middle"
                  className="text-xs fill-slate-500"
                >
                  positions
                </text>
              </svg>
            </div>
          ) : (
            <div className="w-full space-y-2">
              {data.slice(0, 8).map((item, index) => (
                <div key={item.symbol} className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2 w-20">
                    <SymbolLogo symbol={item.symbol} className="w-5 h-5" />
                    <span className="text-sm font-medium text-slate-900">{item.symbol}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-600">{item.percentage.toFixed(1)}%</span>
                      <span className="text-xs font-medium text-slate-900">
                        {formatCurrency(item.value)}
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className="h-2 rounded-full transition-all duration-500"
                        style={{
                          width: `${item.percentage}%`,
                          backgroundColor: generateColor(index, data.length)
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Legend & Details */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-slate-700 mb-3">
            Holdings ({data.length})
          </h4>
          <div className="space-y-3 max-h-64 overflow-y-auto scrollbar-hide">
            {data.map((item, index) => {
              const isProfit = item.change24h >= 0;

              return (
                <div
                  key={item.symbol}
                  className={`flex items-center justify-between p-3 rounded-lg border transition-all duration-200 cursor-pointer ${
                    selectedSegment === item.symbol
                      ? 'border-primary-200 bg-primary-50'
                      : 'border-slate-200 bg-slate-50 hover:border-slate-300'
                  }`}
                  onClick={() => setSelectedSegment(
                    selectedSegment === item.symbol ? null : item.symbol
                  )}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: generateColor(index, data.length) }}
                    />
                    <div>
                      <div className="flex items-center space-x-2">
                        <SymbolLogo symbol={item.symbol} className="w-5 h-5" />
                        <span className="font-medium text-slate-900">{item.symbol}</span>
                      </div>
                      <p className="text-xs text-slate-600">
                        {item.shares} shares @ ${item.avgPrice.toFixed(2)}
                      </p>
                    </div>
                  </div>

                  <div className="text-right">
                    <p className="font-semibold text-slate-900">{item.percentage.toFixed(1)}%</p>
                    <div className={`flex items-center text-xs ${
                      isProfit ? 'text-success-600' : 'text-error-600'
                    }`}>
                      {isProfit ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
                      {isProfit ? '+' : ''}{item.change24h.toFixed(2)}%
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Item Details */}
      {selectedSegment && (
        <div className="mt-6 pt-6 border-t border-slate-200">
          {(() => {
            const selected = data.find(item => item.symbol === selectedSegment);
            if (!selected) return null;

            const isProfit = selected.change24h >= 0;
            const unrealizedPnL = (selected.currentPrice - selected.avgPrice) * selected.shares;

            return (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs font-medium text-slate-500 mb-1">Market Value</p>
                  <p className="text-lg font-bold text-slate-900">{formatCurrency(selected.value)}</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs font-medium text-slate-500 mb-1">Current Price</p>
                  <p className="text-lg font-bold text-slate-900">${selected.currentPrice.toFixed(2)}</p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs font-medium text-slate-500 mb-1">Unrealized P&L</p>
                  <p className={`text-lg font-bold ${unrealizedPnL >= 0 ? 'text-success-600' : 'text-error-600'}`}>
                    {unrealizedPnL >= 0 ? '+' : ''}{formatCurrency(unrealizedPnL)}
                  </p>
                </div>
                <div className="text-center p-3 bg-slate-50 rounded-lg">
                  <p className="text-xs font-medium text-slate-500 mb-1">24h Change</p>
                  <p className={`text-lg font-bold ${isProfit ? 'text-success-600' : 'text-error-600'}`}>
                    {isProfit ? '+' : ''}{selected.change24h.toFixed(2)}%
                  </p>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default PortfolioAllocation;

