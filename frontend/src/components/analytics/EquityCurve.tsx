import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle } from 'lucide-react';
import api from '../../services/api';

interface EquityCurveData {
  date: string;
  equity: number;
  drawdown: number;
  trade_id: number;
  symbol: string;
  pnl: number;
}

interface DrawdownPeriod {
  start_date: string;
  end_date: string;
  start_equity: number;
  end_equity: number;
  max_drawdown: number;
  duration_days: number;
}

interface EquityCurveProps {
  timeframe?: string;
  portfolioId?: number;
  height?: number;
}

const EquityCurve: React.FC<EquityCurveProps> = ({
  timeframe = '3M',
  portfolioId,
  height = 400,
}) => {
  const [data, setData] = useState<EquityCurveData[]>([]);
  const [drawdownPeriods, setDrawdownPeriods] = useState<DrawdownPeriod[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showDrawdown, setShowDrawdown] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;

    const fetchEquityCurveData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await api.analytics.getEquityCurve(timeframe, portfolioId, controller.signal);

        const formattedData = response.equity_curve.map((point: EquityCurveData) => ({
          ...point,
          date: new Date(point.date).toLocaleDateString(),
          equity: Math.round(point.equity * 100) / 100,
          drawdown: Math.round(point.drawdown * 100) / 100,
        }));

        if (!isMounted) return;
        setData(formattedData);
        setDrawdownPeriods(response.drawdown_periods || []);
      } catch (err) {
        if (!isMounted) return;
        console.error('Error fetching equity curve:', err);
        setError('Error loading equity curve data');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchEquityCurveData();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [timeframe, portfolioId]);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatTooltip = (value: any, name: string) => {
    if (name === 'equity') {
      return [formatCurrency(value), 'Equity'];
    }
    if (name === 'drawdown') {
      return [`${value}%`, 'Drawdown'];
    }
    return [value, name];
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length > 0) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-sm">
          <p className="font-medium text-gray-900">{label}</p>
          <p className="text-blue-600">
            <span className="font-medium">Equity:</span> {formatCurrency(data.equity)}
          </p>
          {showDrawdown && (
            <p className="text-red-600">
              <span className="font-medium">Drawdown:</span> {data.drawdown}%
            </p>
          )}
          <p className="text-gray-600 text-sm">
            <span className="font-medium">Trade:</span> {data.symbol} ({formatCurrency(data.pnl)})
          </p>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        No equity curve data available for the selected period
      </div>
    );
  }

  const finalEquity = data[data.length - 1]?.equity || 0;
  const initialEquity = data[0]?.equity || 0;
  const totalReturn = finalEquity - initialEquity;
  const totalReturnPercent =
    initialEquity !== 0 ? (totalReturn / Math.abs(initialEquity)) * 100 : 0;

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Equity Curve</h3>
          <div className="flex items-center space-x-4 mt-2">
            <div className="flex items-center">
              {totalReturn >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span
                className={`text-sm font-medium ${
                  totalReturn >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {formatCurrency(totalReturn)} ({totalReturnPercent >= 0 ? '+' : ''}
                {totalReturnPercent.toFixed(1)}%)
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={showDrawdown}
              onChange={(e) => setShowDrawdown(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Show Drawdown</span>
          </label>
        </div>
      </div>

      {drawdownPeriods.length > 0 && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center mb-2">
            <AlertTriangle className="h-4 w-4 text-red-500 mr-2" />
            <span className="text-sm font-medium text-red-700">
              {drawdownPeriods.length} Significant Drawdown Period
              {drawdownPeriods.length > 1 ? 's' : ''}
            </span>
          </div>
          <div className="text-xs text-red-600 space-y-1">
            {drawdownPeriods.slice(0, 3).map((period, index) => (
              <div key={index}>
                {new Date(period.start_date).toLocaleDateString()} -{' '}
                {period.end_date
                  ? new Date(period.end_date).toLocaleDateString()
                  : 'Ongoing'}: <span className="font-medium">
                  {period.max_drawdown.toFixed(1)}%
                </span>{' '}
                ({period.duration_days} days)
              </div>
            ))}
            {drawdownPeriods.length > 3 && (
              <div className="text-gray-500">+{drawdownPeriods.length - 3} more periods</div>
            )}
          </div>
        </div>
      )}

      <div style={{ height: height }}>
        <ResponsiveContainer width="100%" height="100%">
          {showDrawdown ? (
            <div className="relative w-full h-full">
              <ResponsiveContainer width="100%" height="70%">
                <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 12 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis tick={{ fontSize: 12 }} tickFormatter={formatCurrency} />
                  <Tooltip content={<CustomTooltip />} formatter={formatTooltip} />
                  <Line
                    type="monotone"
                    dataKey="equity"
                    stroke="#2563eb"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, stroke: '#2563eb', strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>

              <ResponsiveContainer width="100%" height="30%">
                <AreaChart data={data} margin={{ top: 0, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10 }}
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    tick={{ fontSize: 10 }}
                    domain={['dataMin', 0]}
                    tickFormatter={(value) => `${value}%`}
                  />
                  <Tooltip
                    formatter={(value: any) => [`${value}%`, 'Drawdown']}
                    labelStyle={{ fontSize: '12px' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="drawdown"
                    stroke="#dc2626"
                    fill="#dc2626"
                    fillOpacity={0.2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} interval="preserveStartEnd" />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={formatCurrency} />
              <Tooltip content={<CustomTooltip />} formatter={formatTooltip} />
              <Legend />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#2563eb"
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, stroke: '#2563eb', strokeWidth: 2 }}
                name="Portfolio Equity"
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <p className="text-2xl font-bold text-blue-600">
            {formatCurrency(finalEquity)}
          </p>
          <p className="text-sm text-gray-500">Current Equity</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-green-600">
            {data.length > 0 ? data.length : 0}
          </p>
          <p className="text-sm text-gray-500">Total Trades</p>
        </div>
        <div className="text-center">
          <p className="text-2xl font-bold text-red-600">
            {Math.min(...data.map((d) => d.drawdown)).toFixed(1)}%
          </p>
          <p className="text-sm text-gray-500">Max Drawdown</p>
        </div>
      </div>
    </div>
  );
};

export default EquityCurve;

