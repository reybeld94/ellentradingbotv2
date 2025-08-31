import React, { useState, useEffect } from 'react';
import { Settings, TrendingDown, TrendingUp, RotateCcw, Save, Plus, Trash2, Calculator } from 'lucide-react';

interface ExitRules {
  strategy_id: string;
  stop_loss_pct: number;
  take_profit_pct: number;
  trailing_stop_pct: number;
  use_trailing: boolean;
  risk_reward_ratio: number;
  created_at: string;
  updated_at: string;
}

interface PriceCalculation {
  entry_price: number;
  stop_loss_price: number;
  take_profit_price: number;
  strategy_id: string;
  rules: any;
}

const ExitRulesManager: React.FC = () => {
  const [exitRules, setExitRules] = useState<ExitRules[]>([]);
  const [selectedStrategy, setSelectedStrategy] = useState<string>('');
  const [editingRules, setEditingRules] = useState<Partial<ExitRules> | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCalculator, setShowCalculator] = useState(false);
  const [calculatorPrice, setCalculatorPrice] = useState<string>('100');
  const [calculationResult, setCalculationResult] = useState<PriceCalculation | null>(null);

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    loadAllExitRules();
  }, []);

  const loadAllExitRules = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/v1/exit-rules`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setExitRules(data);
      } else {
        console.error('Failed to load exit rules');
      }
    } catch (error) {
      console.error('Error loading exit rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveExitRules = async (strategyId: string, rules: Partial<ExitRules>) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const method = exitRules.some(r => r.strategy_id === strategyId) ? 'PUT' : 'POST';
      const url = `${API_BASE}/api/v1/exit-rules/${strategyId}`;

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(rules),
      });

      if (response.ok) {
        await loadAllExitRules();
        setEditingRules(null);
        setSelectedStrategy('');
      } else {
        const error = await response.json();
        console.error('Failed to save exit rules:', error);
        alert(`Error: ${error.detail || 'Failed to save rules'}`);
      }
    } catch (error) {
      console.error('Error saving exit rules:', error);
      alert('Error saving rules');
    } finally {
      setLoading(false);
    }
  };

  const deleteExitRules = async (strategyId: string) => {
    if (!confirm(`Delete exit rules for ${strategyId}?`)) return;

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/v1/exit-rules/${strategyId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        await loadAllExitRules();
      } else {
        console.error('Failed to delete exit rules');
      }
    } catch (error) {
      console.error('Error deleting exit rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const calculateExitPrices = async (strategyId: string, entryPrice: number) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE}/api/v1/exit-rules/${strategyId}/calculate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entry_price: entryPrice,
          side: 'buy'
        }),
      });

      if (response.ok) {
        const result = await response.json();
        setCalculationResult(result);
      } else {
        console.error('Failed to calculate exit prices');
      }
    } catch (error) {
      console.error('Error calculating exit prices:', error);
    }
  };

  const startEditing = (strategyId: string) => {
    const existing = exitRules.find(r => r.strategy_id === strategyId);
    if (existing) {
      setEditingRules({ ...existing });
    } else {
      setEditingRules({
        strategy_id: strategyId,
        stop_loss_pct: 0.02,
        take_profit_pct: 0.04,
        trailing_stop_pct: 0.015,
        use_trailing: true,
        risk_reward_ratio: 2.0,
      });
    }
    setSelectedStrategy(strategyId);
  };

  const handleInputChange = (field: keyof ExitRules, value: any) => {
    if (!editingRules) return;
    setEditingRules({
      ...editingRules,
      [field]: value,
    });
  };

  const formatPercent = (decimal: number) => `${(decimal * 100).toFixed(1)}%`;

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Settings className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-800">Exit Rules Manager</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCalculator(!showCalculator)}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
          >
            <Calculator className="w-4 h-4" />
            Calculator
          </button>
          <button
            onClick={loadAllExitRules}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
          >
            <RotateCcw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Calculator Panel */}
      {showCalculator && (
        <div className="mb-6 p-4 bg-green-50 rounded-lg border border-green-200">
          <h3 className="text-lg font-semibold mb-3 text-green-800">Exit Price Calculator</h3>
          <div className="flex items-center gap-4 mb-4">
            <select
              value={selectedStrategy}
              onChange={(e) => setSelectedStrategy(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="">Select Strategy</option>
              {exitRules.map(rule => (
                <option key={rule.strategy_id} value={rule.strategy_id}>
                  {rule.strategy_id}
                </option>
              ))}
            </select>
            <input
              type="number"
              value={calculatorPrice}
              onChange={(e) => setCalculatorPrice(e.target.value)}
              placeholder="Entry Price"
              className="px-3 py-2 border border-gray-300 rounded-lg w-32"
              step="0.01"
            />
            <button
              onClick={() => selectedStrategy && calculateExitPrices(selectedStrategy, parseFloat(calculatorPrice))}
              disabled={!selectedStrategy || !calculatorPrice}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
            >
              Calculate
            </button>
          </div>

          {calculationResult && (
            <div className="grid grid-cols-3 gap-4 p-4 bg-white rounded border">
              <div className="text-center">
                <div className="text-sm text-gray-600">Entry Price</div>
                <div className="text-xl font-bold text-gray-800">${calculationResult.entry_price}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-red-600">Stop Loss</div>
                <div className="text-xl font-bold text-red-600">${calculationResult.stop_loss_price}</div>
              </div>
              <div className="text-center">
                <div className="text-sm text-green-600">Take Profit</div>
                <div className="text-xl font-bold text-green-600">${calculationResult.take_profit_price}</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* New Strategy Form */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-center gap-4">
          <input
            type="text"
            placeholder="Strategy ID (e.g., momentum_v1)"
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg flex-1"
          />
          <button
            onClick={() => selectedStrategy && startEditing(selectedStrategy)}
            disabled={!selectedStrategy || loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Plus className="w-4 h-4" />
            Configure Rules
          </button>
        </div>
      </div>

      {/* Editing Form */}
      {editingRules && (
        <div className="mb-6 p-6 bg-gray-50 rounded-lg border-2 border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">
              Configuring: {editingRules.strategy_id}
            </h3>
            <button
              onClick={() => {
                setEditingRules(null);
                setSelectedStrategy('');
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              Cancel
            </button>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stop Loss Percentage
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={(editingRules.stop_loss_pct || 0) * 100}
                  onChange={(e) => handleInputChange('stop_loss_pct', parseFloat(e.target.value) / 100)}
                  className="px-3 py-2 border border-gray-300 rounded-lg w-20"
                  step="0.1"
                  min="0.1"
                  max="50"
                />
                <span className="text-gray-600">%</span>
                <TrendingDown className="w-4 h-4 text-red-500" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Take Profit Percentage
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={(editingRules.take_profit_pct || 0) * 100}
                  onChange={(e) => handleInputChange('take_profit_pct', parseFloat(e.target.value) / 100)}
                  className="px-3 py-2 border border-gray-300 rounded-lg w-20"
                  step="0.1"
                  min="0.1"
                  max="100"
                />
                <span className="text-gray-600">%</span>
                <TrendingUp className="w-4 h-4 text-green-500" />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Trailing Stop Percentage
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={(editingRules.trailing_stop_pct || 0) * 100}
                  onChange={(e) => handleInputChange('trailing_stop_pct', parseFloat(e.target.value) / 100)}
                  className="px-3 py-2 border border-gray-300 rounded-lg w-20"
                  step="0.1"
                  min="0.1"
                  max="50"
                />
                <span className="text-gray-600">%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Risk/Reward Ratio
              </label>
              <input
                type="number"
                value={editingRules.risk_reward_ratio || 0}
                onChange={(e) => handleInputChange('risk_reward_ratio', parseFloat(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg w-20"
                step="0.1"
                min="0.5"
                max="10"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={editingRules.use_trailing || false}
                onChange={(e) => handleInputChange('use_trailing', e.target.checked)}
                className="rounded"
              />
              <span className="text-sm font-medium text-gray-700">Enable Trailing Stop</span>
            </label>
          </div>

          <div className="mt-6 flex justify-end">
            <button
              onClick={() => editingRules && saveExitRules(editingRules.strategy_id!, editingRules)}
              disabled={loading}
              className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              Save Rules
            </button>
          </div>
        </div>
      )}

      {/* Rules List */}
      <div className="overflow-x-auto">
        <table className="w-full border border-gray-200 rounded-lg">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Strategy</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Stop Loss</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Take Profit</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Trailing</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">R:R Ratio</th>
              <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Actions</th>
            </tr>
          </thead>
          <tbody>
            {exitRules.map((rule) => (
              <tr key={rule.strategy_id} className="border-t border-gray-200 hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{rule.strategy_id}</td>
                <td className="px-4 py-3 text-center text-red-600">{formatPercent(rule.stop_loss_pct)}</td>
                <td className="px-4 py-3 text-center text-green-600">{formatPercent(rule.take_profit_pct)}</td>
                <td className="px-4 py-3 text-center">
                  {rule.use_trailing ? (
                    <span className="text-blue-600">{formatPercent(rule.trailing_stop_pct)}</span>
                  ) : (
                    <span className="text-gray-400">Disabled</span>
                  )}
                </td>
                <td className="px-4 py-3 text-center text-gray-600">1:{rule.risk_reward_ratio}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex justify-center gap-2">
                    <button
                      onClick={() => startEditing(rule.strategy_id)}
                      className="text-blue-600 hover:text-blue-800"
                      title="Edit"
                    >
                      <Settings className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => deleteExitRules(rule.strategy_id)}
                      className="text-red-600 hover:text-red-800"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {exitRules.length === 0 && !loading && (
          <div className="text-center py-8 text-gray-500">
            No exit rules configured. Create your first strategy rules above.
          </div>
        )}

        {loading && (
          <div className="text-center py-8 text-gray-500">
            Loading...
          </div>
        )}
      </div>
    </div>
  );
};

export default ExitRulesManager;
