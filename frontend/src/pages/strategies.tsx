import React, { useEffect, useState } from 'react';
import { RefreshCw } from 'lucide-react';
import api from '../services/api';
import EquityCurveChart, { EquityPoint } from '../components/EquityCurveChart';

interface Strategy {
  id: number;
  name: string;
  description?: string;
  is_active?: boolean;
}

interface StrategyMetrics {
  strategy_id: string;
  total_pl: number;
  win_rate: number;
  profit_factor: number;
  drawdown: number;
}

const StrategiesPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', description: '' });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [metricsStrategy, setMetricsStrategy] = useState<Strategy | null>(null);
  const [metrics, setMetrics] = useState<StrategyMetrics | null>(null);
  const [metricsLoading, setMetricsLoading] = useState(false);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [equityLoading, setEquityLoading] = useState(false);
  const [equityError, setEquityError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'metrics' | 'settings'>(
    'analysis'
  );

  const loadStrategies = async () => {
    try {
      const res = await api.strategies.list();
      if (!res.ok) throw new Error('Failed to load strategies');
      const data = await res.json();
      const list = Array.isArray(data) ? data : [];
      setStrategies(list);
      if (list.length > 0) {
        setSelectedStrategy((prev) => prev ?? list[0]);
      } else {
        setSelectedStrategy(null);
      }
    } catch (e) {
      console.error('Error loading strategies:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStrategies();
  }, []);

  useEffect(() => {
    if (selectedStrategy) {
      fetchEquityCurve(String(selectedStrategy.id));
    } else {
      setEquityCurve([]);
    }
  }, [selectedStrategy]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingId) {
        const res = await api.strategies.update(editingId, form);
        if (!res.ok) throw new Error('Failed to update strategy');
      } else {
        const res = await api.strategies.create(form);
        if (!res.ok) throw new Error('Failed to create strategy');
      }
      setForm({ name: '', description: '' });
      setEditingId(null);
      loadStrategies();
    } catch (e) {
      console.error('Error saving strategy:', e);
    }
  };

  const handleEdit = (strategy: Strategy) => {
    setForm({ name: strategy.name, description: strategy.description || '' });
    setEditingId(strategy.id);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this strategy?')) return;
    try {
      const res = await api.strategies.delete(id);
      if (!res.ok) throw new Error('Failed to delete strategy');
      loadStrategies();
    } catch (e) {
      console.error('Error deleting strategy:', e);
    }
  };

  const viewMetrics = async (strategy: Strategy) => {
    setMetricsStrategy(strategy);
    setMetrics(null);
    setMetricsLoading(true);
    try {
      const res = await api.strategies.metrics(strategy.id);
      if (!res.ok) throw new Error('Failed to load metrics');
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      console.error('Error loading metrics:', e);
    } finally {
      setMetricsLoading(false);
    }
  };

  const fetchEquityCurve = async (strategyId: string) => {
    setEquityLoading(true);
    setEquityError(null);
    try {
      const res = await api.trading.getEquityCurve();
      if (!res.ok) throw new Error('Failed to load equity curve');
      const data = await res.json();
      const list = Array.isArray(data) ? data : [];
      const filtered = list.filter((p: any) => String(p.strategy_id) === String(strategyId));
      setEquityCurve(filtered);
    } catch (e) {
      console.error('Error loading equity curve:', e);
      setEquityError('Failed to load equity curve');
      setEquityCurve([]);
    } finally {
      setEquityLoading(false);
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Strategies</h1>

      <form onSubmit={handleSubmit} className="bg-white p-4 rounded-xl shadow mb-8 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            type="text"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full border border-gray-300 rounded-lg p-2"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            className="w-full border border-gray-300 rounded-lg p-2"
          />
        </div>
        <div className="flex space-x-2">
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-lg">
            {editingId ? 'Update' : 'Create'}
          </button>
          {editingId && (
            <button
              type="button"
              onClick={() => {
                setEditingId(null);
                setForm({ name: '', description: '' });
              }}
              className="bg-gray-200 px-4 py-2 rounded-lg"
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {strategies.length > 0 && (
        <>
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">Select Strategy</label>
            <select
              value={selectedStrategy?.id ?? strategies[0].id}
              onChange={(e) => {
                const id = Number(e.target.value);
                const strat = strategies.find((s) => s.id === id) || null;
                setSelectedStrategy(strat);
              }}
              className="w-full border border-gray-300 rounded-lg p-2"
            >
              {strategies.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.is_active === false ? '🔴' : '🟢'} {s.name}
                </option>
              ))}
            </select>
          </div>
          {selectedStrategy && (
            <div className="bg-white p-4 rounded-xl shadow mb-8">
              <h2 className="text-lg font-semibold">Dashboard for "{selectedStrategy.name}"</h2>
              <p className="mb-4">Description: {selectedStrategy.description || '--'}</p>
              <div className="flex space-x-2 mb-4 overflow-x-auto">
                <button
                  onClick={() => setActiveTab('analysis')}
                  className={`px-4 py-2 rounded-lg whitespace-nowrap ${
                    activeTab === 'analysis'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  Analysis
                </button>
                <button
                  onClick={() => setActiveTab('metrics')}
                  className={`px-4 py-2 rounded-lg whitespace-nowrap ${
                    activeTab === 'metrics'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  Metrics
                </button>
                <button
                  onClick={() => setActiveTab('settings')}
                  className={`px-4 py-2 rounded-lg whitespace-nowrap ${
                    activeTab === 'settings'
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  Settings
                </button>
              </div>
              <div>
                {activeTab === 'analysis' && (
                  <>
                    {equityLoading ? (
                      <div className="flex flex-col items-center py-8">
                        <RefreshCw className="h-6 w-6 animate-spin text-blue-600 mb-2" />
                        <p className="text-gray-600">Loading equity curve...</p>
                      </div>
                    ) : equityError ? (
                      <p className="text-red-600">{equityError}</p>
                    ) : equityCurve.length === 0 ? (
                      <p>No trades available for this strategy</p>
                    ) : (
                      <EquityCurveChart data={equityCurve} />
                    )}
                  </>
                )}
                {activeTab === 'metrics' && (
                  <p>Metrics will be available here</p>
                )}
                {activeTab === 'settings' && (
                  <p>Strategy settings will be available here</p>
                )}
              </div>
            </div>
          )}
        </>
      )}

      {loading ? (
        <p>Loading strategies...</p>
      ) : strategies.length === 0 ? (
        <p>No strategies found.</p>
      ) : (
        <div className="overflow-x-auto border rounded-xl bg-white shadow-sm">
          <table className="min-w-full text-sm text-left text-gray-600">
            <thead className="bg-gray-100 text-gray-700 text-xs uppercase">
              <tr>
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Description</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {strategies.map((s) => (
                <tr key={s.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">{s.name}</td>
                  <td className="px-4 py-2">{s.description || '--'}</td>
                  <td className="px-4 py-2 space-x-2">
                    <button onClick={() => handleEdit(s)} className="text-blue-600 hover:underline">
                      Edit
                    </button>
                    <button onClick={() => handleDelete(s.id)} className="text-red-600 hover:underline">
                      Delete
                    </button>
                    <button onClick={() => viewMetrics(s)} className="text-indigo-600 hover:underline">
                      Metrics
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {metricsStrategy && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-6 rounded-xl w-96 shadow-lg">
            <h3 className="text-lg font-semibold mb-4">Metrics for {metricsStrategy.name}</h3>
            {metricsLoading ? (
              <p>Loading metrics...</p>
            ) : metrics ? (
              <ul className="space-y-2 text-sm text-gray-700">
                <li>Total P/L: {metrics.total_pl.toFixed(2)}</li>
                <li>Win Rate: {(metrics.win_rate * 100).toFixed(2)}%</li>
                <li>Profit Factor: {metrics.profit_factor.toFixed(2)}</li>
                <li>Drawdown: {metrics.drawdown.toFixed(2)}</li>
              </ul>
            ) : (
              <p>No metrics available.</p>
            )}
            <button
              onClick={() => { setMetricsStrategy(null); setMetrics(null); }}
              className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default StrategiesPage;
