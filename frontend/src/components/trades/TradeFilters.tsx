import React from 'react';
import {
  Search, TrendingUp, TrendingDown,
  CheckCircle, Activity, X, SlidersHorizontal, Brain
} from 'lucide-react';

interface FilterOptions {
  search: string;
  status: string[];
  side: string[];
  dateRange: string;
  strategy: string[];
  minPnL: string;
  maxPnL: string;
  profitableOnly: boolean;
  minDuration: string;
  maxDuration: string;
}

interface TradeFiltersProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  strategies: Array<{ id: string; name: string }>;
  onReset: () => void;
}

const TradeFilters: React.FC<TradeFiltersProps> = ({
  filters,
  onFiltersChange,
  strategies,
  onReset
}) => {
  const statusOptions = [
    { value: 'open', label: 'Open', icon: Activity, color: 'text-primary-600' },
    { value: 'closed', label: 'Closed', icon: CheckCircle, color: 'text-slate-600' }
  ];

  const sideOptions = [
    { value: 'buy', label: 'Long', icon: TrendingUp, color: 'text-success-600' },
    { value: 'sell', label: 'Short', icon: TrendingDown, color: 'text-error-600' }
  ];

  const dateRangeOptions = [
    { value: 'today', label: 'Today' },
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 3 months' },
    { value: '1y', label: 'Last year' },
    { value: 'all', label: 'All time' }
  ];

  const updateFilter = (key: keyof FilterOptions, value: string | boolean | string[]) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const toggleArrayFilter = (key: 'status' | 'side' | 'strategy', value: string) => {
    const currentArray = filters[key] as string[];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    updateFilter(key, newArray);
  };

  const hasActiveFilters = () => {
    return (
      filters.search !== '' ||
      filters.status.length > 0 ||
      filters.side.length > 0 ||
      filters.strategy.length > 0 ||
      filters.dateRange !== '30d' ||
      filters.minPnL !== '' ||
      filters.maxPnL !== '' ||
      filters.profitableOnly ||
      filters.minDuration !== '' ||
      filters.maxDuration !== ''
    );
  };

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center">
          <SlidersHorizontal className="w-5 h-5 mr-2 text-primary-600" />
          Trade Filters
        </h3>
        {hasActiveFilters() && (
          <button
            onClick={onReset}
            className="text-sm text-error-600 hover:text-error-700 font-medium flex items-center"
          >
            <X className="w-4 h-4 mr-1" />
            Reset All
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
        <input
          type="text"
          placeholder="Search by symbol, trade ID, or strategy..."
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          className="input-field pl-10"
        />
      </div>

      {/* Quick Filters */}
      <div>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={filters.profitableOnly}
            onChange={(e) => updateFilter('profitableOnly', e.target.checked)}
            className="rounded border-slate-300 text-success-600 focus:ring-success-500"
          />
          <span className="text-sm font-medium text-slate-700">Profitable trades only</span>
        </label>
      </div>

      {/* Status Filter */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">Trade Status</label>
        <div className="grid grid-cols-2 gap-2">
          {statusOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = filters.status.includes(option.value);
            
            return (
              <button
                key={option.value}
                onClick={() => toggleArrayFilter('status', option.value)}
                className={`flex items-center justify-center p-3 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? 'bg-primary-50 border-primary-200 text-primary-700'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'
                }`}
              >
                <Icon className={`w-4 h-4 mr-2 ${isSelected ? 'text-primary-600' : option.color}`} />
                <span className="text-sm font-medium">{option.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Side Filter */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">Position Type</label>
        <div className="grid grid-cols-2 gap-2">
          {sideOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = filters.side.includes(option.value);
            
            return (
              <button
                key={option.value}
                onClick={() => toggleArrayFilter('side', option.value)}
                className={`flex items-center justify-center p-3 rounded-xl border transition-all duration-200 ${
                  isSelected
                    ? 'bg-primary-50 border-primary-200 text-primary-700'
                    : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50 hover:border-slate-300'
                }`}
              >
                <Icon className={`w-4 h-4 mr-2 ${isSelected ? 'text-primary-600' : option.color}`} />
                <span className="text-sm font-medium">{option.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* P&L Range */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">P&L Range</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            placeholder="Min P&L $"
            value={filters.minPnL}
            onChange={(e) => updateFilter('minPnL', e.target.value)}
            className="input-field text-sm"
          />
          <input
            type="number"
            placeholder="Max P&L $"
            value={filters.maxPnL}
            onChange={(e) => updateFilter('maxPnL', e.target.value)}
            className="input-field text-sm"
          />
        </div>
      </div>

      {/* Duration Range */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">Hold Duration (minutes)</label>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="number"
            placeholder="Min duration"
            value={filters.minDuration}
            onChange={(e) => updateFilter('minDuration', e.target.value)}
            className="input-field text-sm"
          />
          <input
            type="number"
            placeholder="Max duration"
            value={filters.maxDuration}
            onChange={(e) => updateFilter('maxDuration', e.target.value)}
            className="input-field text-sm"
          />
        </div>
      </div>

      {/* Date Range */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">Date Range</label>
        <select
          value={filters.dateRange}
          onChange={(e) => updateFilter('dateRange', e.target.value)}
          className="input-field"
        >
          {dateRangeOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Strategy Filter */}
      {strategies.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-3">Trading Strategies</label>
          <div className="space-y-2 max-h-40 overflow-y-auto">
            {strategies.map((strategy) => {
              const isSelected = filters.strategy.includes(strategy.id);
              
              return (
                <label
                  key={strategy.id}
                  className="flex items-center space-x-3 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleArrayFilter('strategy', strategy.id)}
                    className="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                  />
                  <Brain className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-700 flex-1">
                    {strategy.name}
                  </span>
                </label>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default TradeFilters;
