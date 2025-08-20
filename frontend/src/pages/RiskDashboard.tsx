import React, { useEffect, useState } from 'react';
import { AlertTriangle, DollarSign, PieChart, Target, RefreshCw, Calculator } from 'lucide-react';
import SymbolLogo from '../components/SymbolLogo';
import api from '../services/api';

interface RiskStatus {
  account_info: {
    buying_power: number;
    portfolio_value: number;
    cash_percentage: number;
  };
  allocation_info: {
    available_capital: number;
    open_positions: number;
    reserved_slots: number;
    capital_per_position: number;
    next_position_percentage: number;
  };
  current_positions: Array<{
    symbol: string;
    quantity: number;
    market_value: number;
    unrealized_pl: number;
    percentage: number;
  }>;
  risk_metrics: {
    position_count: number;
    capital_utilization: number;
    largest_position_pct: number;
    concentration_risk: string;
  };
  next_positions_simulation: Array<{
    symbol: string;
    current_price: number;
    would_buy_qty: number;
    would_invest_usd: number;
    minimum_required: number;
    can_enter: boolean;
    percentage_of_portfolio: number;
  }>;
  debug_info?: unknown;
}

const RiskDashboard: React.FC = () => {
  const [riskStatus, setRiskStatus] = useState<RiskStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Debug info display component
  const DebugInfo: React.FC<{ debugInfo: unknown }> = ({ debugInfo }) => {
    const [showDebug, setShowDebug] = useState(false);

    if (!debugInfo) return null;

    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
        <button
          onClick={() => setShowDebug(!showDebug)}
          className="text-yellow-800 font-medium mb-2 flex items-center"
        >
          🐛 Debug Info {showDebug ? '▼' : '▶'}
        </button>
        {showDebug && (
          <div className="text-xs overflow-auto max-h-96">
            <pre className="whitespace-pre-wrap text-yellow-800">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}
      </div>
    );
  };

  const fetchRiskStatus = async () => {
    try {
      const response = await api.risk.getStatus();
      if (!response.ok) throw new Error('Failed to fetch risk status');
      const data = await response.json();
      setRiskStatus(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading risk status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskStatus();
    const interval = setInterval(fetchRiskStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
        <div className="flex flex-col items-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-2" />
          <p className="text-gray-600">Loading risk dashboard...</p>
        </div>
      </div>
    );
  }

  if (!riskStatus) {
    return (
      <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Failed to load risk data</p>
          <button
            onClick={fetchRiskStatus}
            className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const { account_info, allocation_info, current_positions, risk_metrics, next_positions_simulation } = riskStatus;

  return (
    <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Risk Management</h1>
          <p className="text-gray-600 mt-2">
            Monitor portfolio allocation and risk metrics
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-sm text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </div>
          <button
            onClick={fetchRiskStatus}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Debug info without interrupting dashboard */}
      {riskStatus.debug_info && <DebugInfo debugInfo={riskStatus.debug_info} />}

      {/* Top Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Available Capital</p>
              <p className="text-2xl font-bold text-green-600">
                ${account_info.buying_power.toLocaleString()}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Open Positions</p>
              <p className="text-2xl font-bold text-blue-600">
                {allocation_info.open_positions}
              </p>
            </div>
            <Target className="h-8 w-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Next Position Size</p>
              <p className="text-2xl font-bold text-purple-600">
                ${allocation_info.capital_per_position.toLocaleString()}
              </p>
              <p className="text-xs text-gray-500">
                {allocation_info.next_position_percentage.toFixed(1)}% of capital
              </p>
            </div>
            <Calculator className="h-8 w-8 text-purple-600" />
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Risk Level</p>
              <p
                className={`text-2xl font-bold ${
                  risk_metrics.concentration_risk === 'High'
                    ? 'text-red-600'
                    : risk_metrics.concentration_risk === 'Medium'
                    ? 'text-yellow-600'
                    : 'text-green-600'
                }`}
              >
                {risk_metrics.concentration_risk}
              </p>
            </div>
            <AlertTriangle
              className={`h-8 w-8 ${
                risk_metrics.concentration_risk === 'High'
                  ? 'text-red-600'
                  : risk_metrics.concentration_risk === 'Medium'
                  ? 'text-yellow-600'
                  : 'text-green-600'
              }`}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Current Positions */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <PieChart className="h-5 w-5 mr-2" />
            Current Positions
          </h3>

          {current_positions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No open positions</p>
          ) : (
            <div className="space-y-3">
              {current_positions.map((position) => (
                <div
                  key={position.symbol}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center">
                    <SymbolLogo symbol={position.symbol} className="mr-3" />
                    <div>
                      <p className="font-medium">{position.symbol}</p>
                      <p className="text-sm text-gray-600">
                        {position.quantity} units • {position.percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">
                      ${position.market_value.toLocaleString()}
                    </p>
                    <p
                      className={`text-sm ${
                        position.unrealized_pl >= 0 ? 'text-green-600' : 'text-red-600'
                      }`}
                    >
                      {position.unrealized_pl >= 0 ? '+' : ''}
                      ${position.unrealized_pl.toFixed(2)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Next Positions Simulation */}
        <div className="bg-white p-6 rounded-xl shadow">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <Calculator className="h-5 w-5 mr-2" />
            Next Signal Simulation
          </h3>

          <div className="space-y-3">
            {next_positions_simulation.map((sim) => (
              <div
                key={sim.symbol}
                className={`p-3 rounded-lg border-2 ${
                  sim.can_enter ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <SymbolLogo symbol={sim.symbol} className="mr-3" />
                    <div>
                      <p className="font-medium">{sim.symbol}</p>
                      <p className="text-sm text-gray-600">
                        @ ${sim.current_price.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    {sim.can_enter ? (
                      <>
                        <p className="font-medium text-green-600">
                          ${sim.would_invest_usd.toFixed(0)}
                        </p>
                        <p className="text-sm text-gray-600">
                          {sim.would_buy_qty.toFixed(6)} units
                        </p>
                      </>
                    ) : (
                      <p className="text-sm text-red-600">Insufficient capital</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Smart Allocation Info */}
      <div className="mt-8 bg-white p-6 rounded-xl shadow">
        <h3 className="text-lg font-semibold mb-4">Smart Allocation Formula</h3>
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-center text-lg font-mono">
            Capital per Position = ${allocation_info.available_capital.toLocaleString()} ÷
            ({allocation_info.open_positions} positions + {allocation_info.reserved_slots} reserved) =
            <span className="font-bold text-blue-600"> ${allocation_info.capital_per_position.toLocaleString()}</span>
          </p>
          <p className="text-center text-sm text-gray-600 mt-2">
            Reserved slots ensure capital availability for future opportunities
          </p>
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;
