import React from 'react';
import { BarChart3, AlertTriangle } from 'lucide-react';

interface ExposureItem {
  symbol: string;
  exposure: number;
  limit: number;
}

interface ExposureChartProps {
  data: ExposureItem[];
  loading?: boolean;
}

const ExposureChart: React.FC<ExposureChartProps> = ({ data, loading = false }) => {
  const maxExposure = Math.max(...data.map(d => Math.max(d.exposure, d.limit)), 1);

  if (loading) {
    return (
      <div className="card p-6">
        <div className="h-6 bg-slate-200 rounded w-48 mb-4 animate-pulse"></div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex items-center space-x-3 mb-3">
            <div className="w-16 h-4 bg-slate-200 rounded animate-pulse"></div>
            <div className="flex-1 h-4 bg-slate-200 rounded animate-pulse"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
        <BarChart3 className="w-5 h-5 mr-2 text-primary-600" />
        Exposure by Asset
      </h3>
      <div className="space-y-3">
        {data.map(item => {
          const pct = (item.exposure / maxExposure) * 100;
          const limitPct = (item.limit / maxExposure) * 100;
          const over = item.exposure > item.limit;
          return (
            <div key={item.symbol} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-slate-700">{item.symbol}</span>
                <span className={`font-semibold ${over ? 'text-error-600' : 'text-slate-900'}`}>${item.exposure.toLocaleString()}</span>
              </div>
              <div className="relative w-full bg-slate-200 h-3 rounded-full">
                <div
                  className={`absolute left-0 top-0 h-3 rounded-full ${over ? 'bg-error-500' : 'bg-primary-500'}`}
                  style={{ width: `${pct}%` }}
                />
                <div
                  className="absolute top-0 h-3 rounded-full bg-slate-400 opacity-50"
                  style={{ left: `${limitPct}%`, width: '2px' }}
                />
              </div>
              {over && (
                <div className="text-xs text-error-600 flex items-center">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  Over exposure limit
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ExposureChart;

