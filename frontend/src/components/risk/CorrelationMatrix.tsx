import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Grid, BarChart3 } from 'lucide-react';

interface CorrelationData {
  symbol1: string;
  symbol2: string;
  correlation: number;
  pValue: number;
  significance: 'high' | 'medium' | 'low';
}

interface CorrelationMatrixProps {
  symbols: string[];
  correlations: CorrelationData[];
  loading?: boolean;
  timeframe?: '1W' | '1M' | '3M' | '6M' | '1Y';
  onTimeframeChange?: (timeframe: '1W' | '1M' | '3M' | '6M' | '1Y') => void;
}

const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({
  symbols,
  correlations,
  loading = false,
  timeframe = '3M',
  onTimeframeChange
}) => {
  const [hoveredCell, setHoveredCell] = useState<{symbol1: string, symbol2: string} | null>(null);
  const [selectedCell, setSelectedCell] = useState<{symbol1: string, symbol2: string} | null>(null);

  const getCorrelation = (symbol1: string, symbol2: string) => {
    if (symbol1 === symbol2) return 1;
    const correlation = correlations.find(
      c => (c.symbol1 === symbol1 && c.symbol2 === symbol2) ||
           (c.symbol1 === symbol2 && c.symbol2 === symbol1)
    );
    return correlation ? correlation.correlation : 0;
  };

  const getCorrelationData = (symbol1: string, symbol2: string) => {
    return correlations.find(
      c => (c.symbol1 === symbol1 && c.symbol2 === symbol2) ||
           (c.symbol1 === symbol2 && c.symbol2 === symbol1)
    );
  };

  const getCorrelationColor = (correlation: number) => {
    const absCorr = Math.abs(correlation);
    const intensity = Math.floor(absCorr * 10) / 10;
    if (correlation > 0) {
      if (intensity < 0.3) return 'bg-red-100 text-red-800';
      if (intensity < 0.6) return 'bg-red-200 text-red-900';
      if (intensity < 0.8) return 'bg-red-400 text-white';
      return 'bg-red-600 text-white';
    } else if (correlation < 0) {
      if (intensity < 0.3) return 'bg-blue-100 text-blue-800';
      if (intensity < 0.6) return 'bg-blue-200 text-blue-900';
      if (intensity < 0.8) return 'bg-blue-400 text-white';
      return 'bg-blue-600 text-white';
    } else {
      return 'bg-slate-100 text-slate-800';
    }
  };

  const getCorrelationLevel = (correlation: number) => {
    const absCorr = Math.abs(correlation);
    if (absCorr < 0.3) return 'Low';
    if (absCorr < 0.7) return 'Medium';
    return 'High';
  };

  const timeframes = [
    { key: '1W', label: '1W' },
    { key: '1M', label: '1M' },
    { key: '3M', label: '3M' },
    { key: '6M', label: '6M' },
    { key: '1Y', label: '1Y' },
  ] as const;

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 bg-slate-200 rounded w-40 animate-pulse"></div>
          <div className="h-8 bg-slate-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-6 gap-1 animate-pulse">
          {Array.from({ length: 36 }).map((_, i) => (
            <div key={i} className="aspect-square bg-slate-200 rounded"></div>
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
            <Grid className="w-5 h-5 mr-2 text-primary-600" />
            Correlation Matrix
          </h3>
          <p className="text-sm text-slate-600">
            Asset correlation analysis for {timeframe}
          </p>
        </div>
        
        {/* Timeframe Selector */}
        <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
          {timeframes.map((tf) => (
            <button
              key={tf.key}
              onClick={() => onTimeframeChange?.(tf.key)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 ${
                timeframe === tf.key
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {tf.label}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-6">
        {/* Matrix Grid */}
        <div className="overflow-x-auto">
          <div className="inline-block min-w-full">
            {/* Header Row */}
            <div className="flex">
              <div className="w-16 h-12"></div>
              {symbols.map(symbol => (
                <div key={symbol} className="w-16 h-12 flex items-center justify-center">
                  <span className="text-xs font-semibold text-slate-700 transform -rotate-45">
                    {symbol}
                  </span>
                </div>
              ))}
            </div>
            
            {/* Matrix Rows */}
            {symbols.map((rowSymbol) => (
              <div key={rowSymbol} className="flex">
                {/* Row Header */}
                <div className="w-16 h-16 flex items-center justify-center">
                  <span className="text-xs font-semibold text-slate-700">
                    {rowSymbol}
                  </span>
                </div>
                
                {/* Correlation Cells */}
                {symbols.map((colSymbol) => {
                  const correlation = getCorrelation(rowSymbol, colSymbol);
                  const colorClass = getCorrelationColor(correlation);
                  const isHovered = hoveredCell?.symbol1 === rowSymbol && hoveredCell?.symbol2 === colSymbol;
                  const isSelected = selectedCell?.symbol1 === rowSymbol && selectedCell?.symbol2 === colSymbol;
                  const isDiagonal = rowSymbol === colSymbol;
                  
                  return (
                    <div
                      key={`${rowSymbol}-${colSymbol}`}
                      className={`w-16 h-16 flex items-center justify-center cursor-pointer transition-all duration-200 border border-slate-200 ${colorClass} ${
                        (isHovered || isSelected) ? 'scale-110 z-10 shadow-lg rounded-lg' : ''
                      } ${isDiagonal ? 'border-slate-400' : ''}`}
                      onMouseEnter={() => setHoveredCell({ symbol1: rowSymbol, symbol2: colSymbol })}
                      onMouseLeave={() => setHoveredCell(null)}
                      onClick={() => setSelectedCell(
                        selectedCell?.symbol1 === rowSymbol && selectedCell?.symbol2 === colSymbol 
                          ? null 
                          : { symbol1: rowSymbol, symbol2: colSymbol }
                      )}
                    >
                      <span className="text-xs font-bold">
                        {isDiagonal ? '1.00' : correlation.toFixed(2)}
                      </span>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-slate-700">Correlation:</span>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-blue-600 rounded"></div>
              <span className="text-xs text-slate-600">-1.0 (Perfect Negative)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-slate-100 rounded border"></div>
              <span className="text-xs text-slate-600">0.0 (No Correlation)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 bg-red-600 rounded"></div>
              <span className="text-xs text-slate-600">+1.0 (Perfect Positive)</span>
            </div>
          </div>
        </div>

        {/* Correlation Insights */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Highest Positive Correlation */}
          {(() => {
            const highestPositive = correlations
              .filter(c => c.correlation > 0)
              .sort((a, b) => b.correlation - a.correlation)[0];
            
            return (
              <div className="p-4 bg-red-50 rounded-xl border border-red-200">
                <div className="flex items-center mb-2">
                  <TrendingUp className="w-4 h-4 text-red-600 mr-2" />
                  <span className="text-sm font-semibold text-red-700">Highest Positive</span>
                </div>
                {highestPositive ? (
                  <div>
                    <p className="font-medium text-slate-900">
                      {highestPositive.symbol1} - {highestPositive.symbol2}
                    </p>
                    <p className="text-2xl font-bold text-red-600 mb-1">
                      {highestPositive.correlation.toFixed(3)}
                    </p>
                    <p className="text-xs text-slate-600">
                      {getCorrelationLevel(highestPositive.correlation)} correlation
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No positive correlations</p>
                )}
              </div>
            );
          })()}

          {/* Highest Negative Correlation */}
          {(() => {
            const highestNegative = correlations
              .filter(c => c.correlation < 0)
              .sort((a, b) => a.correlation - b.correlation)[0];
            
            return (
              <div className="p-4 bg-blue-50 rounded-xl border border-blue-200">
                <div className="flex items-center mb-2">
                  <TrendingDown className="w-4 h-4 text-blue-600 mr-2" />
                  <span className="text-sm font-semibold text-blue-700">Highest Negative</span>
                </div>
                {highestNegative ? (
                  <div>
                    <p className="font-medium text-slate-900">
                      {highestNegative.symbol1} - {highestNegative.symbol2}
                    </p>
                    <p className="text-2xl font-bold text-blue-600 mb-1">
                      {highestNegative.correlation.toFixed(3)}
                    </p>
                    <p className="text-xs text-slate-600">
                      {getCorrelationLevel(highestNegative.correlation)} correlation
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No negative correlations</p>
                )}
              </div>
            );
          })()}

          {/* Average Correlation */}
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
            <div className="flex items-center mb-2">
              <BarChart3 className="w-4 h-4 text-slate-600 mr-2" />
              <span className="text-sm font-semibold text-slate-700">Average Correlation</span>
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900 mb-1">
                {correlations.length > 0 
                  ? (correlations.reduce((sum, c) => sum + Math.abs(c.correlation), 0) / correlations.length).toFixed(3)
                  : '0.000'
                }
              </p>
              <p className="text-xs text-slate-600">
                Absolute average across all pairs
              </p>
            </div>
          </div>
        </div>

        {/* Selected Cell Details */}
        {selectedCell && (
          <div className="p-4 bg-primary-50 rounded-xl border border-primary-200">
            {(() => {
              const corrData = getCorrelationData(selectedCell.symbol1, selectedCell.symbol2);
              const correlation = getCorrelation(selectedCell.symbol1, selectedCell.symbol2);
              
              return (
                <div>
                  <h4 className="font-semibold text-primary-900 mb-3">
                    {selectedCell.symbol1} - {selectedCell.symbol2} Correlation
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-primary-600">Correlation</p>
                      <p className="text-lg font-bold text-primary-900">
                        {correlation.toFixed(3)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-primary-600">Strength</p>
                      <p className="text-lg font-bold text-primary-900">
                        {getCorrelationLevel(correlation)}
                      </p>
                    </div>
                    {corrData && (
                      <>
                        <div>
                          <p className="text-xs text-primary-600">P-Value</p>
                          <p className="text-lg font-bold text-primary-900">
                            {corrData.pValue.toFixed(4)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-primary-600">Significance</p>
                          <p className="text-lg font-bold text-primary-900 capitalize">
                            {corrData.significance}
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
};

export default CorrelationMatrix;

