import React from 'react';

interface StrategyStat {
  id: string;
  name: string;
  totalPnL: number;
  winRate: number;
  trades: number;
}

interface CompactStrategyPerformanceProps {
  strategyStats: StrategyStat[];
}

const CompactStrategyPerformance: React.FC<CompactStrategyPerformanceProps> = ({ strategyStats }) => {
  if (strategyStats.length === 0) return null;
  return (
    <div className="card p-4">
      <h3 className="text-base font-semibold text-slate-900 mb-3">Performance by Strategy</h3>
      <div className="space-y-2">
        {strategyStats.map((s) => (
          <div key={s.id} className="flex justify-between items-center py-2 px-3 rounded-lg bg-slate-50">
            <div className="flex flex-col">
              <span className="font-medium text-slate-700 text-sm">{s.name}</span>
              <span className="text-xs text-slate-500">Win Rate: {s.winRate.toFixed(1)}% ({s.trades} trades)</span>
            </div>
            <span className={`text-sm font-semibold ${s.totalPnL >= 0 ? 'text-success-600' : 'text-error-600'}`}>
              {s.totalPnL >= 0 ? '+' : ''}${Math.abs(s.totalPnL).toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CompactStrategyPerformance;
