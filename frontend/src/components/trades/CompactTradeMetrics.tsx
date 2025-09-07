import React from 'react';

interface TradeStats {
  totalPnL: number;
  winRate: number;
  avgWin: number;
  avgLoss: number;
  bestTrade: number;
  profitFactor: number;
  sharpeRatio: number;
  maxDrawdown: number;
}

interface CompactTradeMetricsProps {
  stats: TradeStats;
}

const CompactTradeMetrics: React.FC<CompactTradeMetricsProps> = ({ stats }) => (
  <div className="card p-4 mb-4">
    <h3 className="text-base font-semibold text-slate-900 mb-3">Metrics</h3>
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Total P&L</span>
        <span className={`font-semibold ${stats.totalPnL >= 0 ? 'text-success-600' : 'text-error-600'}`}>
          {stats.totalPnL >= 0 ? '+' : ''}${Math.abs(stats.totalPnL).toFixed(2)}
        </span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Win Rate</span>
        <span className="font-semibold text-slate-900">{stats.winRate.toFixed(1)}%</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Avg Win</span>
        <span className="font-semibold text-success-600">${stats.avgWin.toFixed(2)}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Avg Loss</span>
        <span className="font-semibold text-error-600">${Math.abs(stats.avgLoss).toFixed(2)}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Best Trade</span>
        <span className="font-semibold text-success-600">+${stats.bestTrade.toFixed(2)}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Profit Factor</span>
        <span className={`font-semibold ${stats.profitFactor >= 1 ? 'text-success-600' : 'text-error-600'}`}>
          {stats.profitFactor.toFixed(2)}
        </span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Sharpe Ratio</span>
        <span className="font-semibold text-slate-900">{stats.sharpeRatio.toFixed(2)}</span>
      </div>
      <div className="flex justify-between items-center">
        <span className="text-sm text-slate-600">Max Drawdown</span>
        <span className="font-semibold text-error-600">-{Math.abs(stats.maxDrawdown).toFixed(2)}%</span>
      </div>
    </div>
  </div>
);

export default CompactTradeMetrics;
