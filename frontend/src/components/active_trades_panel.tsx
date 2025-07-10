import { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Clock,
  DollarSign,
  Eye,
  EyeOff,
} from 'lucide-react';

interface Trade {
  id: number;
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

type Side = 'LONG' | 'SHORT';

interface ProcessedTrade {
  id: number;
  symbol: string;
  side: Side;
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  exchange: string;
}

interface ActiveTradesPanelProps {
  trades?: Trade[];
}

const ActiveTradesPanel = ({ trades = [] }: ActiveTradesPanelProps) => {
  const [showPnL, setShowPnL] = useState(true);

  const processedTrades: ProcessedTrade[] = trades.map((t) => {
    const pnl = t.pnl ?? 0;
    const currentPrice = t.entry_price + pnl / t.quantity;
    const pnlPercent = t.quantity ? (pnl / (t.entry_price * t.quantity)) * 100 : 0;
    const side: Side = t.action.toLowerCase() === 'buy' ? 'LONG' : 'SHORT';
    return {
      id: t.id,
      symbol: t.symbol,
      side,
      size: t.quantity,
      entryPrice: t.entry_price,
      currentPrice,
      pnl,
      pnlPercent,
      openTime: new Date(t.opened_at).toLocaleTimeString(),
      exchange: 'Alpaca',
    };
  });

  const totalPnL = processedTrades.reduce((sum, trade) => sum + trade.pnl, 0);
  const profitableTrades = processedTrades.filter(trade => trade.pnl > 0).length;

  const getSideColor = (side: Side) => {
    return side === 'LONG' ? 'text-green-600' : 'text-red-600';
  };

  const getSideBg = (side: Side) => {
    return side === 'LONG' ? 'bg-green-100' : 'bg-red-100';
  };

  const getPnLColor = (pnl: number) => {
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getExchangeColor = (exchange: string) => {
    return exchange === 'Alpaca' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800';
  };

  const formatPrice = (price: number) => {
    return price > 1000 ? price.toLocaleString() : price.toFixed(2);
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-6 h-fit">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-800">Trades Activos</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowPnL(!showPnL)}
            className="p-1 hover:bg-gray-100 rounded"
            title={showPnL ? "Ocultar P&L" : "Mostrar P&L"}
          >
            {showPnL ? <Eye className="w-4 h-4 text-gray-500" /> : <EyeOff className="w-4 h-4 text-gray-500" />}
          </button>
        </div>
      </div>

      {/* Resumen */}
      <div className="grid grid-cols-2 gap-3 mb-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-center">
          <div className="text-sm text-gray-600">Total</div>
          <div className="text-lg font-bold text-gray-800">{processedTrades.length}</div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600">P&L Total</div>
          <div className={`text-lg font-bold ${getPnLColor(totalPnL)}`}>
            {showPnL ? `$${totalPnL.toFixed(2)}` : '***'}
          </div>
        </div>
      </div>

      {/* Lista de Trades */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {processedTrades.length === 0 ? (
          <div className="text-center py-8">
            <Activity className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No active trades</p>
          </div>
        ) : (
          processedTrades.map((trade) => (
            <div key={trade.id} className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors">
            {/* Primera fila: Symbol, Side, Exchange */}
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="font-bold text-gray-800">{trade.symbol}</span>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSideBg(trade.side)} ${getSideColor(trade.side)}`}>
                  {trade.side}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${getExchangeColor(trade.exchange)}`}>
                  {trade.exchange}
                </span>
              </div>
            </div>

            {/* Segunda fila: Tamaño y Hora */}
            <div className="flex items-center justify-between mb-2 text-sm text-gray-600">
              <span>Tamaño: {trade.size}</span>
              <div className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                <span>{trade.openTime}</span>
              </div>
            </div>

            {/* Tercera fila: Precios */}
            <div className="grid grid-cols-2 gap-2 text-xs mb-2">
              <div>
                <span className="text-gray-500">Entrada: </span>
                <span className="font-medium">${formatPrice(trade.entryPrice)}</span>
              </div>
              <div>
                <span className="text-gray-500">Actual: </span>
                <span className="font-medium">${formatPrice(trade.currentPrice)}</span>
              </div>
            </div>

            {/* Cuarta fila: P&L */}
            {showPnL && (
              <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                <div className="flex items-center gap-1">
                  <DollarSign className="w-3 h-3 text-gray-400" />
                  <span className={`font-bold text-sm ${getPnLColor(trade.pnl)}`}>
                    ${trade.pnl.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  {trade.pnl >= 0 ? (
                    <TrendingUp className="w-3 h-3 text-green-600" />
                  ) : (
                    <TrendingDown className="w-3 h-3 text-red-600" />
                  )}
                  <span className={`text-sm font-medium ${getPnLColor(trade.pnl)}`}>
                    {trade.pnlPercent >= 0 ? '+' : ''}{trade.pnlPercent.toFixed(2)}%
                  </span>
                </div>
              </div>
            )}
            </div>
          ))
        )}
      </div>

      {/* Footer con estadísticas */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex justify-between text-xs text-gray-600">
          <span>{profitableTrades}/{processedTrades.length} rentables</span>
          <span>Última actualización: hace 2m</span>
        </div>
      </div>
    </div>
  );
};

export default ActiveTradesPanel;