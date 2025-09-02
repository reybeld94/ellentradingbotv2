import React, { useState } from 'react';
import { BarChart3, PieChart } from 'lucide-react';

interface ExposureData {
  category: string;
  exposure: number;
  limit: number;
  utilizationPercent: number;
  riskLevel: 'low' | 'medium' | 'high';
  positions: Array<{
    symbol: string;
    value: number;
    percentage: number;
    riskContribution: number;
  }>;
}

interface ExposureChartProps {
  data: ExposureData[];
  loading?: boolean;
  chartType?: 'bar' | 'pie';
  onChartTypeChange?: (type: 'bar' | 'pie') => void;
}

const ExposureChart: React.FC<ExposureChartProps> = ({
  data,
  loading = false,
  chartType = 'bar',
  onChartTypeChange
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const getRiskColor = (level: 'low' | 'medium' | 'high') => {
    switch (level) {
      case 'low':
        return { bg: 'bg-success-100', text: 'text-success-600', bar: 'bg-success-500' };
      case 'medium':
        return { bg: 'bg-warning-100', text: 'text-warning-600', bar: 'bg-warning-500' };
      case 'high':
        return { bg: 'bg-error-100', text: 'text-error-600', bar: 'bg-error-500' };
    }
  };

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
          <div className="h-6 bg-slate-200 rounded w-40 animate-pulse"></div>
          <div className="h-8 bg-slate-200 rounded w-20 animate-pulse"></div>
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="animate-pulse">
              <div className="flex justify-between mb-2">
                <div className="h-4 bg-slate-200 rounded w-20"></div>
                <div className="h-4 bg-slate-200 rounded w-16"></div>
              </div>
              <div className="h-6 bg-slate-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const totalExposure = data.reduce((sum, item) => sum + item.exposure, 0);
  const maxLimit = Math.max(...data.map(item => item.limit));

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-primary-600" />
            Risk Exposure by Category
          </h3>
          <p className="text-sm text-slate-600">
            Current exposure vs limits across risk categories
          </p>
        </div>
        
        <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
          <button
            onClick={() => onChartTypeChange?.('bar')}
            className={`p-2 rounded-md transition-all duration-200 ${
              chartType === 'bar'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
          </button>
          <button
            onClick={() => onChartTypeChange?.('pie')}
            className={`p-2 rounded-md transition-all duration-200 ${
              chartType === 'pie'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <PieChart className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <div>
          {chartType === 'bar' ? (
            <div className="space-y-6">
              {data.map((category) => {
                const riskConfig = getRiskColor(category.riskLevel);
                const utilizationWidth = (category.exposure / category.limit) * 100;
                const limitWidth = (category.limit / maxLimit) * 100;
                
                return (
                  <div
                    key={category.category}
                    className="cursor-pointer"
                    onClick={() => setSelectedCategory(
                      selectedCategory === category.category ? null : category.category
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-700">
                        {category.category}
                      </span>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-slate-500">
                          {formatCurrency(category.exposure)} / {formatCurrency(category.limit)}
                        </span>
                        <span className={`px-2 py-1 text-xs font-semibold rounded-full ${riskConfig.bg} ${riskConfig.text}`}>
                          {category.utilizationPercent.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    
                    <div className="relative">
                      {/* Limit background */}
                      <div 
                        className="h-8 bg-slate-100 rounded-lg"
                        style={{ width: `${limitWidth}%` }}
                      />
                      {/* Current exposure */}
                      <div
                        className={`absolute top-0 h-8 rounded-lg transition-all duration-500 ${riskConfig.bar} ${
                          selectedCategory === category.category ? 'opacity-80' : 'hover:opacity-90'
                        }`}
                        style={{ width: `${(utilizationWidth / 100) * limitWidth}%` }}
                      />
                      {/* Warning threshold line */}
                      <div
                        className="absolute top-0 bottom-0 w-0.5 bg-warning-500"
                        style={{ left: `${0.8 * limitWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <svg width="280" height="280" viewBox="0 0 280 280">
                {(() => {
                  let cumulativePercentage = 0;
                  const radius = 100;
                  const centerX = 140;
                  const centerY = 140;
                  
                  return data.map((category) => {
                    const percentage = (category.exposure / totalExposure) * 100;
                    const startAngle = (cumulativePercentage * 360) / 100;
                    const endAngle = ((cumulativePercentage + percentage) * 360) / 100;
                    
                    const startAngleRad = (startAngle * Math.PI) / 180;
                    const endAngleRad = (endAngle * Math.PI) / 180;
                    
                    const largeArcFlag = percentage > 50 ? 1 : 0;
                    
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

                    cumulativePercentage += percentage;
                    
                    const riskConfig = getRiskColor(category.riskLevel);
                    const color = riskConfig.bar.includes('success') ? '#22c55e' : 
                                  riskConfig.bar.includes('warning') ? '#f59e0b' : '#ef4444';

                    return (
                      <path
                        key={category.category}
                        d={pathData}
                        fill={color}
                        stroke="white"
                        strokeWidth="2"
                        className={`cursor-pointer transition-all duration-200 ${
                          selectedCategory === category.category ? 'opacity-80' : 'hover:opacity-80'
                        }`}
                        onClick={() => setSelectedCategory(
                          selectedCategory === category.category ? null : category.category
                        )}
                      />
                    );
                  });
                })()}
                
                {/* Center circle */}
                <circle cx="140" cy="140" r="40" fill="white" stroke="#e2e8f0" strokeWidth="2" />
                <text x="140" y="135" textAnchor="middle" className="text-sm font-semibold fill-slate-900">
                  Risk
                </text>
                <text x="140" y="150" textAnchor="middle" className="text-xs fill-slate-500">
                  Exposure
                </text>
              </svg>
            </div>
          )}
        </div>

        {/* Categories List */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-slate-700 mb-4">Exposure Categories</h4>
          <div className="space-y-3 max-h-80 overflow-y-auto scrollbar-hide">
            {data.map((category) => {
              const riskConfig = getRiskColor(category.riskLevel);
              const isSelected = selectedCategory === category.category;
              
              return (
                <div
                  key={category.category}
                  className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                    isSelected
                      ? 'border-primary-200 bg-primary-50'
                      : 'border-slate-200 bg-slate-50 hover:border-slate-300'
                  }`}
                  onClick={() => setSelectedCategory(isSelected ? null : category.category)}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h5 className="font-medium text-slate-900">{category.category}</h5>
                    <span className={`px-2.5 py-1 text-xs font-semibold rounded-lg ${riskConfig.bg} ${riskConfig.text}`}>
                      {category.riskLevel.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-slate-500">Exposure</p>
                      <p className="font-semibold text-slate-900">{formatCurrency(category.exposure)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Limit</p>
                      <p className="font-semibold text-slate-900">{formatCurrency(category.limit)}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Utilization</p>
                      <p className={`font-semibold ${riskConfig.text}`}>
                        {category.utilizationPercent.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-slate-500">Positions</p>
                      <p className="font-semibold text-slate-900">{category.positions.length}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Selected Category Details */}
      {selectedCategory && (
        <div className="mt-6 pt-6 border-t border-slate-200">
          {(() => {
            const selected = data.find(cat => cat.category === selectedCategory);
            if (!selected) return null;
            
            return (
              <div>
                <h4 className="text-lg font-semibold text-slate-900 mb-4">
                  {selected.category} - Position Details
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {selected.positions.map((position) => (
                    <div key={position.symbol} className="p-4 bg-slate-50 rounded-xl">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-semibold text-slate-900">{position.symbol}</span>
                        <span className="text-sm text-slate-600">{position.percentage.toFixed(1)}%</span>
                      </div>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Value:</span>
                          <span className="text-slate-900">{formatCurrency(position.value)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Risk Contribution:</span>
                          <span className="text-slate-900">{position.riskContribution.toFixed(2)}%</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default ExposureChart;

