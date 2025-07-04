import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface Trade {
  id: number;
  strategy_id: string;
  symbol: string;
  action: string;
  quantity: number;
  entry_price: number;
  exit_price: number | null;
  status: string;
  opened_at: string;
  closed_at: string | null;
  pnl: number | null;
}

const TradesPage: React.FC = () => {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await api.trading.getTrades();
        if (!response.ok) {
          throw new Error('Failed to fetch trades');
        }
        const data = await response.json();
        setTrades(data);
      } catch (error) {
        console.error('Error loading trades:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrades();
    const interval = window.setInterval(fetchTrades, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Trades</h1>

      {loading ? (
        <p>Loading trades...</p>
      ) : trades.length === 0 ? (
        <p>No trades found.</p>
      ) : (
        <div className="overflow-x-auto border rounded-xl bg-white shadow-sm">
          <table className="min-w-full text-sm text-left text-gray-600">
            <thead className="bg-gray-100 text-gray-700 text-xs uppercase">
              <tr>
                <th className="px-4 py-3">Strategy</th>
                <th className="px-4 py-3">Symbol</th>
                <th className="px-4 py-3">Action</th>
                <th className="px-4 py-3">Qty</th>
                <th className="px-4 py-3">Entry</th>
                <th className="px-4 py-3">Exit</th>
                <th className="px-4 py-3">PnL</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Opened</th>
                <th className="px-4 py-3">Closed</th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr key={trade.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2">{trade.strategy_id}</td>
                  <td className="px-4 py-2">{trade.symbol}</td>
                  <td className="px-4 py-2">{trade.action.toUpperCase()}</td>
                  <td className="px-4 py-2">{trade.quantity}</td>
                  <td className="px-4 py-2">${trade.entry_price.toFixed(2)}</td>
                  <td className="px-4 py-2">
                    {trade.exit_price !== null ? `$${trade.exit_price.toFixed(2)}` : '--'}
                  </td>
                  <td className={`px-4 py-2 ${trade.pnl !== null ? (trade.pnl >= 0 ? 'text-green-600' : 'text-red-500') : ''}`}>
                    {trade.pnl !== null ? `$${trade.pnl.toFixed(2)}` : '--'}
                  </td>
                  <td className="px-4 py-2 capitalize">{trade.status}</td>
                  <td className="px-4 py-2">{new Date(trade.opened_at).toLocaleString()}</td>
                  <td className="px-4 py-2">
                    {trade.closed_at ? new Date(trade.closed_at).toLocaleString() : '--'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default TradesPage;
