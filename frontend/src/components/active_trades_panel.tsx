import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Activity, Clock, DollarSign, MoreVertical, Eye, EyeOff } from 'lucide-react';

const ActiveTradesPanel = ({ trades = [] }) => {
  const [showPnL, setShowPnL] = useState(true);
  const [expandedTrade, setExpandedTrade] = useState(null);

  // Datos de ejemplo si no se proporcionan trades
  const defaultTrades = [
    {
      id: 1,
      symbol: 'AAPL',
      side: 'LONG',
      size: 100,
      entryPrice: 178.50,
      currentPrice: 180.25,
      pnl: 175.00,
      pnlPercent: 0.98,
      openTime: '10:30',
      exchange: 'Alpaca'
    },
    {
      id: 2,
      symbol: 'TSLA',
      side: 'SHORT',
      size: 50,
      entryPrice: 248.80,
      currentPrice: 245.20,
      pnl: 180.00,
      pnlPercent: 1.45,
      openTime: '11:15',
      exchange: 'Alpaca'
    },
    {
      id: 3,
      symbol: 'NVDA',
      side: 'LONG',
      size: 25,
      entryPrice: 485.20,
      currentPrice: 492.80,
      pnl: 190.00,
      pnlPercent: 1.56,
      openTime: '12:45',
      exchange: 'Kraken'
    },
    {
      id: 4,
      symbol: 'BTC/USD',
      side: 'LONG',
      size: 0.5,
      entryPrice: 43250.00,
      currentPrice: 43680.00,
      pnl: 215.00,
      pnlPercent: 0.99,
      openTime: '09:20',
      exchange: 'Kraken'
    }
  ];

  const activeTrades = trades.length > 0 ? trades : defaultTrades;
  const totalPnL = activeTrades.reduce((sum, trade) => sum + trade.pnl, 0);
  const profitableTrades = activeTrades.filter(trade => trade.pnl > 0).length;

  const getSideColor = (side) => {
    return side === 'LONG' ? 'text-green-600' : 'text-red-600';
  };

  const getSideBg = (side) => {
    return side === 'LONG' ? 'bg-green-100' : 'bg-red-100';
  };

  const getPnLColor = (pnl) => {
    return pnl >= 0 ? 'text-green-600' : 'text-red-600';
  };

  const getExchangeColor = (exchange) => {
    return exchange === 'Alpaca' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800';
  };

  const formatPrice = (price) => {
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
          <div className="text-lg font-bold text-gray-800">{activeTrades.length}</div>
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
        {activeTrades.map((trade) => (
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
        ))}
      </div>

      {/* Footer con estadísticas */}
      <div className="mt-4 pt-3 border-t border-gray-200">
        <div className="flex justify-between text-xs text-gray-600">
          <span>{profitableTrades}/{activeTrades.length} rentables</span>
          <span>Última actualización: hace 2m</span>
        </div>
      </div>
    </div>
  );
};

export default ActiveTradesPanel;