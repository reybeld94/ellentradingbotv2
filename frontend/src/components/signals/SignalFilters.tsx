import React from 'react';
import {
  Search, TrendingUp, TrendingDown,
  Clock, CheckCircle, XCircle, X, SlidersHorizontal,
  AlertCircle, Target
} from 'lucide-react';

interface FilterOptions {
  search: string;
  status: string[];
  action: string[];
  confidence: [number, number];
  dateRange: string;
  strategy: string[];
}

interface SignalFiltersProps {
  filters: FilterOptions;
  onFiltersChange: (filters: FilterOptions) => void;
  strategies: Array<{ id: string; name: string }>;
  onReset: () => void;
}

const SignalFilters: React.FC<SignalFiltersProps> = ({
  filters,
  onFiltersChange,
  strategies,
  onReset
}) => {
  const statusOptions = [
    { value: 'pending', label: 'Pending', icon: Clock, color: 'text-warning-600' },
    { value: 'validated', label: 'Validated', icon: CheckCircle, color: 'text-blue-600' },
    { value: 'executed', label: 'Executed', icon: CheckCircle, color: 'text-success-600' },
    { value: 'bracket_created', label: 'Bracket Created', icon: Target, color: 'text-indigo-600' },
    { value: 'bracket_failed', label: 'Bracket Failed', icon: XCircle, color: 'text-error-600' },
    { value: 'error', label: 'Error', icon: AlertCircle, color: 'text-error-600' },
    { value: 'rejected', label: 'Rejected', icon: X, color: 'text-slate-500' },
  ];

  const actionOptions = [
    { value: 'buy', label: 'Buy', icon: TrendingUp, color: 'text-success-600' },
    { value: 'sell', label: 'Sell', icon: TrendingDown, color: 'text-error-600' },
  ];

  const dateRangeOptions = [
    { value: 'today', label: 'Today' },
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 3 months' },
    { value: 'custom', label: 'Custom range' }
  ];

  const updateFilter = <K extends keyof FilterOptions>(key: K, value: FilterOptions[K]) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const toggleArrayFilter = (key: 'status' | 'action' | 'strategy', value: string) => {
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
      filters.action.length > 0 ||
      filters.strategy.length > 0 ||
      filters.dateRange !== '30d' ||
      filters.confidence[0] !== 0 ||
      filters.confidence[1] !== 100
    );
  };

  return (
    <div className="card p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-900 flex items-center">
          <SlidersHorizontal className="w-5 h-5 mr-2 text-primary-600" />
          Filters
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
          placeholder="Search by symbol or strategy..."
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          className="input-field pl-10"
        />
      </div>

      {/* Status Filter */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">Status</label>
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

      {/* Action Filter */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">Action Type</label>
        <div className="grid grid-cols-2 gap-2">
          {actionOptions.map((option) => {
            const Icon = option.icon;
            const isSelected = filters.action.includes(option.value);
            
            return (
              <button
                key={option.value}
                onClick={() => toggleArrayFilter('action', option.value)}
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

      {/* Confidence Range */}
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-3">
          Confidence Range: {filters.confidence[0]}% - {filters.confidence[1]}%
        </label>
        <div className="space-y-3">
          <input
            type="range"
            min="0"
            max="100"
            value={filters.confidence[0]}
            onChange={(e) => updateFilter('confidence', [parseInt(e.target.value), filters.confidence[1]])}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
          />
          <input
            type="range"
            min="0"
            max="100"
            value={filters.confidence[1]}
            onChange={(e) => updateFilter('confidence', [filters.confidence[0], parseInt(e.target.value)])}
            className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
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
          <label className="block text-sm font-medium text-slate-700 mb-3">Strategies</label>
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

export default SignalFilters;
