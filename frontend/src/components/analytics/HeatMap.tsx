import React, { useState } from 'react';
import { Calendar, Activity } from 'lucide-react';

interface HeatMapData {
  date: string;
  value: number;
  trades: number;
  pnl: number;
}

interface HeatMapProps {
  data: HeatMapData[];
  loading?: boolean;
  title?: string;
  period?: 'daily' | 'weekly' | 'monthly';
  onPeriodChange?: (period: 'daily' | 'weekly' | 'monthly') => void;
}

const HeatMap: React.FC<HeatMapProps> = ({
  data,
  loading = false,
  title = 'Trading Activity Heatmap',
  period = 'daily',
  onPeriodChange
}) => {
  const [hoveredCell, setHoveredCell] = useState<HeatMapData | null>(null);

  // Get color intensity based on value
  const getColorIntensity = (value: number, max: number, min: number) => {
    if (value === 0) return 'bg-slate-100';

    const normalizedValue = Math.abs(value);
    const normalizedMax = Math.max(Math.abs(max), Math.abs(min));
    const intensity = normalizedValue / normalizedMax;

    if (value > 0) {
      const opacity = Math.max(0.1, intensity);
      return `bg-success-500${opacity > 0.7 ? '' : opacity > 0.4 ? ' bg-opacity-60' : ' bg-opacity-30'}`;
    } else {
      const opacity = Math.max(0.1, intensity);
      return `bg-error-500${opacity > 0.7 ? '' : opacity > 0.4 ? ' bg-opacity-60' : ' bg-opacity-30'}`;
    }
  };

  // Generate calendar grid for daily view
  const generateCalendarGrid = () => {
    if (period !== 'daily') return [];

    const today = new Date();
    const startDate = new Date(today);
    startDate.setDate(today.getDate() - 365);

    const weeks = [];
    const current = new Date(startDate);

    while (current <= today) {
      const week = [] as { date: Date; dateStr: string; data: HeatMapData }[];
      for (let i = 0; i < 7; i++) {
        const dateStr = current.toISOString().split('T')[0];
        const dayData = data.find(d => d.date === dateStr);
        week.push({
          date: new Date(current),
          dateStr,
          data: dayData || { date: dateStr, value: 0, trades: 0, pnl: 0 }
        });
        current.setDate(current.getDate() + 1);
      }
      weeks.push(week);
    }

    return weeks;
  };

  const calendarWeeks = generateCalendarGrid();
  const maxValue = Math.max(...data.map(d => Math.abs(d.value)));
  const minValue = Math.min(...data.map(d => d.value));

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);

  const formatDate = (date: Date) =>
    date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });

  if (loading) {
    return (
      <div className="card p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 bg-slate-200 rounded w-48 animate-pulse"></div>
          <div className="h-8 bg-slate-200 rounded w-32 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-53 gap-1 animate-pulse">
          {Array.from({ length: 365 }).map((_, i) => (
            <div key={i} className="w-3 h-3 bg-slate-200 rounded-sm"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 mb-1 flex items-center">
            <Calendar className="w-5 h-5 mr-2 text-primary-600" />
            {title}
          </h3>
          <p className="text-sm text-slate-600">
            Daily P&L and trading activity over time
          </p>
        </div>

        {/* Period Selector */}
        <div className="flex items-center space-x-1 bg-slate-100 rounded-lg p-1">
          {['daily', 'weekly', 'monthly'].map((p) => (
            <button
              key={p}
              onClick={() => onPeriodChange?.(p as any)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 capitalize ${
                period === p
                  ? 'bg-white text-primary-700 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Calendar Heatmap */}
      <div className="relative">
        {/* Month labels */}
        <div className="flex justify-between mb-2 text-xs text-slate-500">
          {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].map((month) => (
            <span key={month}>{month}</span>
          ))}
        </div>

        {/* Days of week labels */}
        <div className="flex flex-col mr-3 text-xs text-slate-500 absolute left-0 top-8">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="h-3 flex items-center mb-1">
              {day}
            </div>
          ))}
        </div>

        {/* Heatmap Grid */}
        <div className="ml-12 overflow-x-auto">
          <div className="flex space-x-1 min-w-max">
            {calendarWeeks.map((week, weekIndex) => (
              <div key={weekIndex} className="flex flex-col space-y-1">
                {week.map((day, dayIndex) => {
                  const colorClass = getColorIntensity(day.data.pnl, maxValue, minValue);
                  const isToday = day.date.toDateString() === new Date().toDateString();

                  return (
                    <div
                      key={dayIndex}
                      className={`w-3 h-3 rounded-sm cursor-pointer transition-all duration-200 border ${
                        colorClass
                      } ${
                        isToday ? 'ring-2 ring-primary-500' : 'border-slate-200'
                      } ${
                        hoveredCell?.date === day.dateStr ? 'scale-125' : 'hover:scale-110'
                      }`}
                      onMouseEnter={() => setHoveredCell(day.data)}
                      onMouseLeave={() => setHoveredCell(null)}
                      title={`${formatDate(day.date)}: ${formatCurrency(day.data.pnl)} (${day.data.trades} trades)`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-200">
        <div className="text-xs text-slate-500">Less activity</div>
        <div className="flex items-center space-x-1">
          <div className="w-3 h-3 bg-slate-100 rounded-sm"></div>
          <div className="w-3 h-3 bg-success-500 bg-opacity-30 rounded-sm"></div>
          <div className="w-3 h-3 bg-success-500 bg-opacity-60 rounded-sm"></div>
          <div className="w-3 h-3 bg-success-500 rounded-sm"></div>
        </div>
        <div className="text-xs text-slate-500">More activity</div>
      </div>

      {/* Hover Details */}
      {hoveredCell && (
        <div className="mt-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-slate-900">
                {new Date(hoveredCell.date).toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </h4>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <p className="text-xs text-slate-500">P&L</p>
                <p className={`font-semibold ${
                  hoveredCell.pnl >= 0 ? 'text-success-600' : 'text-error-600'
                }`}>
                  {hoveredCell.pnl >= 0 ? '+' : ''}{formatCurrency(hoveredCell.pnl)}
                </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">Trades</p>
                <p className="font-semibold text-slate-900">{hoveredCell.trades}</p>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500">Activity</p>
                <div className="flex items-center">
                  <Activity className="w-4 h-4 text-primary-500 mr-1" />
                  <p className="font-semibold text-primary-600">
                    {hoveredCell.value.toFixed(1)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="text-center p-3 bg-slate-50 rounded-lg">
          <p className="text-xs font-medium text-slate-500 mb-1">Best Day</p>
          <p className="text-lg font-bold text-success-600">
            +{formatCurrency(Math.max(...data.map(d => d.pnl)))}
          </p>
        </div>
        <div className="text-center p-3 bg-slate-50 rounded-lg">
          <p className="text-xs font-medium text-slate-500 mb-1">Worst Day</p>
          <p className="text-lg font-bold text-error-600">
            {formatCurrency(Math.min(...data.map(d => d.pnl)))}
          </p>
        </div>
        <div className="text-center p-3 bg-slate-50 rounded-lg">
          <p className="text-xs font-medium text-slate-500 mb-1">Total Trades</p>
          <p className="text-lg font-bold text-slate-900">
            {data.reduce((sum, d) => sum + d.trades, 0)}
          </p>
        </div>
      </div>
    </div>
  );
};

export default HeatMap;

