import React, { useEffect, useState } from 'react';
import {
  RefreshCw,
  Target,
  Plus,
  Settings,
  Edit2,
  Trash2,
  Pause,
  Play,
  X,
} from 'lucide-react';
import api from '../services/api';
import EquityCurveChart, { type EquityPoint } from '../components/EquityCurveChart';

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
  sharpe_ratio: number;
  sortino_ratio: number;
  avg_win: number;
  avg_loss: number;
  win_loss_ratio: number;
  expectancy: number;
}

const StrategiesPage: React.FC = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ name: '', description: '' });
  const [editingId, setEditingId] = useState<number | null>(null);
  const [selectedStrategy, setSelectedStrategy] = useState<Strategy | null>(null);
  const [tabMetrics, setTabMetrics] = useState<StrategyMetrics | null>(null);
  const [tabMetricsLoading, setTabMetricsLoading] = useState(false);
  const [equityCurve, setEquityCurve] = useState<EquityPoint[]>([]);
  const [equityLoading, setEquityLoading] = useState(false);
  const [equityError, setEquityError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'analysis' | 'metrics' | 'settings'>(
    'analysis'
  );
  const [showCreateModal, setShowCreateModal] = useState(false);

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

  useEffect(() => {
    if (activeTab === 'metrics' && selectedStrategy) {
      fetchMetricsForTab(selectedStrategy.id);
    }
  }, [activeTab, selectedStrategy]);

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
      setShowCreateModal(false);
      await loadStrategies();
    } catch (e) {
      console.error('Error saving strategy:', e);
    }
  };

  const handleDelete = async (id: number) => {
    const strategy = strategies.find((s) => s.id === id);
    const confirmed = window.confirm(
      `Are you sure you want to delete "${strategy?.name}"? This action cannot be undone.`
    );
    if (!confirmed) return;
    try {
      const res = await api.strategies.delete(id);
      if (!res.ok) throw new Error('Failed to delete strategy');

      if (selectedStrategy?.id === id) {
        const remaining = strategies.filter((s) => s.id !== id);
        setSelectedStrategy(remaining.length > 0 ? remaining[0] : null);
      }

      await loadStrategies();
    } catch (e) {
      console.error('Error deleting strategy:', e);
    }
  };

  const handleToggleActive = async (id: number) => {
    try {
      const strategy = strategies.find((s) => s.id === id);
      const res = await api.strategies.update(id, {
        ...strategy,
        is_active: !strategy?.is_active,
      });
      if (!res.ok) throw new Error('Failed to toggle strategy');

      setStrategies((prev) =>
        prev.map((s) =>
          s.id === id ? { ...s, is_active: !s.is_active } : s
        )
      );

      if (selectedStrategy?.id === id) {
        setSelectedStrategy((prev) =>
          prev ? { ...prev, is_active: !prev.is_active } : null
        );
      }
    } catch (e) {
      console.error('Error toggling strategy:', e);
    }
  };

  const fetchMetricsForTab = async (strategyId: number) => {
    setTabMetrics(null);
    setTabMetricsLoading(true);
    try {
      const res = await api.strategies.metrics(strategyId);
      if (!res.ok) throw new Error('Failed to load metrics');
      const data = await res.json();
      setTabMetrics(data);
    } catch (e) {
      console.error('Error loading metrics:', e);
    } finally {
      setTabMetricsLoading(false);
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
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Target className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Strategies</h1>
            <p className="text-sm text-gray-500">{strategies.length} strategies configured</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
          >
            <Plus className="h-4 w-4" />
            <span>New Strategy</span>
          </button>

          <button className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100">
            <Settings className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md mx-4 shadow-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                {editingId ? 'Edit Strategy' : 'Create New Strategy'}
              </h3>
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setEditingId(null);
                  setForm({ name: '', description: '' });
                }}
                className="p-1 hover:bg-gray-100 rounded"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
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
              <div className="flex justify-end space-x-2">
                <button
                  type="submit"
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
                >
                  {editingId ? 'Update' : 'Create'}
                </button>
                {editingId && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingId(null);
                      setForm({ name: '', description: '' });
                      setShowCreateModal(false);
                    }}
                    className="bg-gray-200 px-4 py-2 rounded-lg"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex flex-col items-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mb-2" />
          <p className="text-gray-600">Loading strategies...</p>
        </div>
      ) : strategies.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-xl">
          <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No strategies yet</h3>
          <p className="text-gray-500 mb-6">Create your first trading strategy to get started</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            Create Strategy
          </button>
        </div>
      ) : (
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
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Return Metrics */}
                      <div>
                        <h3 className="font-semibold flex items-center gap-1 mb-2">
                          <span>📈</span> Return Metrics
                        </h3>
                        <div className="space-y-2">
                          <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Total accumulated profit or loss">
                            <span>Total P&amp;L:</span>
                            {tabMetricsLoading ? (
                              <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                            ) : (
                              <span className={`${tabMetrics && tabMetrics.total_pl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {tabMetrics ? tabMetrics.total_pl.toLocaleString(undefined, { style: 'currency', currency: 'USD' }) : '--'}
                              </span>
                            )}
                          </div>
                          <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Average expected profit or loss per trade">
                            <span>Expectancy:</span>
                            {tabMetricsLoading ? (
                              <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                            ) : (
                              <span className={`${tabMetrics && tabMetrics.expectancy >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {tabMetrics ? tabMetrics.expectancy.toLocaleString(undefined, { style: 'currency', currency: 'USD' }) : '--'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Risk Metrics */}
                      <div>
                        <h3 className="font-semibold flex items-center gap-1 mb-2">
                          <span>📊</span> Risk Metrics
                        </h3>
                        <div className="space-y-2">
                          <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Largest peak-to-trough decline">
                            <span>Max DD:</span>
                            {tabMetricsLoading ? (
                              <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                            ) : (
                              <span className={`text-red-600`}>
                                {tabMetrics ? tabMetrics.drawdown.toLocaleString(undefined, { style: 'currency', currency: 'USD' }) : '--'}
                              </span>
                            )}
                          </div>
                          <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Return adjusted by volatility">
                            <span>Sharpe:</span>
                            {tabMetricsLoading ? (
                              <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                            ) : (
                              <span className={`${tabMetrics && tabMetrics.sharpe_ratio >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {tabMetrics ? tabMetrics.sharpe_ratio.toFixed(2) : '--'}
                              </span>
                            )}
                          </div>
                          <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Return adjusted by downside risk">
                            <span>Sortino:</span>
                            {tabMetricsLoading ? (
                              <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                            ) : (
                              <span className={`${tabMetrics && tabMetrics.sortino_ratio >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {tabMetrics ? tabMetrics.sortino_ratio.toFixed(2) : '--'}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Trade Metrics */}
                    <div>
                      <h3 className="font-semibold flex items-center gap-1 mb-2">
                        <span>🎯</span> Trade Metrics
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Percentage of winning trades">
                          <span>Win Rate:</span>
                          {tabMetricsLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <span className={`${tabMetrics && tabMetrics.win_rate >= 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                              {tabMetrics ? `${(tabMetrics.win_rate * 100).toFixed(1)}%` : '--'}
                            </span>
                          )}
                        </div>
                        <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Gross profit divided by gross loss">
                          <span>Profit Factor:</span>
                          {tabMetricsLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <span className={`${tabMetrics && tabMetrics.profit_factor >= 1 ? 'text-green-600' : 'text-red-600'}`}>
                              {tabMetrics ? tabMetrics.profit_factor.toFixed(2) : '--'}
                            </span>
                          )}
                        </div>
                        <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Average profit of winning trades">
                          <span>Avg Win:</span>
                          {tabMetricsLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <span className="text-green-600">
                              {tabMetrics ? tabMetrics.avg_win.toLocaleString(undefined, { style: 'currency', currency: 'USD' }) : '--'}
                            </span>
                          )}
                        </div>
                        <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Average loss of losing trades">
                          <span>Avg Loss:</span>
                          {tabMetricsLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <span className="text-red-600">
                              {tabMetrics ? `-${tabMetrics.avg_loss.toLocaleString(undefined, { style: 'currency', currency: 'USD' })}` : '--'}
                            </span>
                          )}
                        </div>
                        <div className="p-4 bg-white rounded-xl shadow flex justify-between" title="Average win to average loss ratio">
                          <span>Win/Loss:</span>
                          {tabMetricsLoading ? (
                            <RefreshCw className="h-4 w-4 animate-spin text-blue-600" />
                          ) : (
                            <span className={`${tabMetrics && tabMetrics.win_loss_ratio >= 1 ? 'text-green-600' : 'text-red-600'}`}>
                              {tabMetrics ? tabMetrics.win_loss_ratio.toFixed(2) : '--'}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                {activeTab === 'settings' && (
                  <p>Strategy settings will be available here</p>
                )}
              </div>

              <div className="mt-6 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h4>
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => {
                      setEditingId(selectedStrategy.id);
                      setForm({
                        name: selectedStrategy.name,
                        description: selectedStrategy.description || '',
                      });
                      setShowCreateModal(true);
                    }}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 bg-white hover:bg-gray-50"
                  >
                    <Edit2 className="h-4 w-4 mr-1" />
                    Edit
                  </button>

                  <button
                    onClick={() => handleToggleActive(selectedStrategy.id)}
                    className={`inline-flex items-center px-3 py-2 border rounded-lg text-sm ${
                      selectedStrategy.is_active
                        ? 'border-orange-300 text-orange-700 bg-orange-50 hover:bg-orange-100'
                        : 'border-green-300 text-green-700 bg-green-50 hover:bg-green-100'
                    }`}
                  >
                    {selectedStrategy.is_active ? (
                      <>
                        <Pause className="h-4 w-4 mr-1" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-1" />
                        Resume
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => handleDelete(selectedStrategy.id)}
                    className="inline-flex items-center px-3 py-2 border border-red-300 rounded-lg text-sm text-red-700 bg-red-50 hover:bg-red-100"
                  >
                    <Trash2 className="h-4 w-4 mr-1" />
                    Delete
                  </button>
                </div>
              </div>

            </div>
          )}
        </>
      )}

    </div>
  );
};

export default StrategiesPage;
