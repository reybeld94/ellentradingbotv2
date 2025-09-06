import React, { useState, useEffect } from 'react';
import { Calendar, TrendingUp, TrendingDown } from 'lucide-react';
import api from '../../services/api';

interface MonthlyReturn {
  month: string;
  pnl: number;
  trades: number;
  win_rate: number;
}

interface MonthlyHeatmapProps {
  portfolioId?: number;
}

const MonthlyHeatmap: React.FC<MonthlyHeatmapProps> = ({ portfolioId }) => {
  const [monthlyData, setMonthlyData] = useState<MonthlyReturn[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    let isMounted = true;

    const fetchMonthlyData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await api.analytics.getMonthlyPerformance(portfolioId, controller.signal);
        if (!isMounted) return;
        const data = await response.json();
        setMonthlyData(data.monthly_returns || []);
      } catch (err) {
        if (!isMounted) return;
        console.error('Error fetching monthly data:', err);
        setError('Error loading monthly performance data');
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchMonthlyData();

    return () => {
      isMounted = false;
      controller.abort();
    };
  }, [portfolioId]);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const greenLevels = ['bg-green-100', 'bg-green-200', 'bg-green-300', 'bg-green-400', 'bg-green-500'];
  const redLevels = ['bg-red-100', 'bg-red-200', 'bg-red-300', 'bg-red-400', 'bg-red-500'];

  const getColorIntensity = (pnl: number, maxAbsPnl: number): string => {
    if (pnl === 0) return 'bg-gray-100';

    const intensity = Math.abs(pnl) / maxAbsPnl;
    const level = Math.min(Math.floor(intensity * 5) + 1, 5);

    return pnl > 0 ? greenLevels[level - 1] : redLevels[level - 1];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !monthlyData || monthlyData.length === 0) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border">
        <div className="text-center text-gray-500 py-8">
          {error || 'No monthly performance data available'}
        </div>
      </div>
    );
  }

  const totalPnl = monthlyData.reduce((sum, month) => sum + month.pnl, 0);
  const avgMonthlyReturn = totalPnl / monthlyData.length;
  const positiveMonths = monthlyData.filter((m) => m.pnl > 0).length;
  const winRate = (positiveMonths / monthlyData.length) * 100;
  const maxAbsPnl = Math.max(...monthlyData.map((m) => Math.abs(m.pnl)));

  const yearMonthData: { [year: string]: { [month: string]: MonthlyReturn } } = {};
  monthlyData.forEach((data) => {
    const [year, month] = data.month.split('-');
    if (!yearMonthData[year]) {
      yearMonthData[year] = {};
    }
    yearMonthData[year][month] = data;
  });

  const months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

  return (
    <div className="bg-white p-6 rounded-lg shadow-sm border">
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center">
            <Calendar className="h-5 w-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-900">Monthly Performance Heatmap</h3>
          </div>
          <p className="text-sm text-gray-600 mt-1">Monthly P&L performance overview</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <p className="text-xl font-bold text-blue-600">{formatCurrency(totalPnl)}</p>
          <p className="text-sm text-gray-600">Total P&L</p>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <p className="text-xl font-bold text-green-600">{formatCurrency(avgMonthlyReturn)}</p>
          <p className="text-sm text-gray-600">Avg Monthly</p>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <p className="text-xl font-bold text-purple-600">{positiveMonths}</p>
          <p className="text-sm text-gray-600">Positive Months</p>
        </div>
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <p className="text-xl font-bold text-gray-600">{winRate.toFixed(1)}%</p>
          <p className="text-sm text-gray-600">Monthly Win Rate</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <div className="min-w-full">
          <div className="flex mb-2">
            <div className="w-16"></div>
            {monthNames.map((month) => (
              <div key={month} className="w-20 text-center text-sm font-medium text-gray-600">
                {month}
              </div>
            ))}
          </div>

          {Object.keys(yearMonthData)
            .sort()
            .map((year) => (
              <div key={year} className="flex items-center mb-2">
                <div className="w-16 text-sm font-medium text-gray-700 text-right pr-3">
                  {year}
                </div>
                {months.map((month) => {
                  const monthData = yearMonthData[year][month];
                  const colorClass = monthData
                    ? getColorIntensity(monthData.pnl, maxAbsPnl)
                    : 'bg-gray-100';

                  return (
                    <div
                      key={month}
                      className={`w-20 h-16 mr-1 rounded-lg border border-gray-200 ${colorClass} flex flex-col items-center justify-center cursor-pointer hover:ring-2 hover:ring-blue-300 transition-all duration-200 ${
                        monthData ? 'hover:shadow-md' : ''
                      }`}
                      title={
                        monthData
                          ? `${year}-${month}: ${formatCurrency(monthData.pnl)} (${monthData.trades} trades, ${monthData.win_rate}% WR)`
                          : `${year}-${month}: No data`
                      }
                    >
                      {monthData && (
                        <>
                          <div className="flex items-center">
                            {monthData.pnl >= 0 ? (
                              <TrendingUp className="h-3 w-3 text-green-700" />
                            ) : (
                              <TrendingDown className="h-3 w-3 text-red-700" />
                            )}
                          </div>
                          <div
                            className={`text-xs font-medium mt-1 ${
                              monthData.pnl >= 0 ? 'text-green-800' : 'text-red-800'
                            }`}
                          >
                            {Math.abs(monthData.pnl) >= 1000
                              ? `${(monthData.pnl / 1000).toFixed(1)}k`
                              : monthData.pnl.toFixed(0)}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
        </div>
      </div>

      <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">Hover over cells for detailed information</div>
        <div className="flex items-center space-x-2">
          <span className="text-xs text-gray-500">Loss</span>
          <div className="flex space-x-1">
            <div className="w-3 h-3 bg-red-500 rounded"></div>
            <div className="w-3 h-3 bg-red-400 rounded"></div>
            <div className="w-3 h-3 bg-red-300 rounded"></div>
            <div className="w-3 h-3 bg-red-200 rounded"></div>
            <div className="w-3 h-3 bg-red-100 rounded"></div>
            <div className="w-3 h-3 bg-gray-100 rounded border"></div>
            <div className="w-3 h-3 bg-green-100 rounded"></div>
            <div className="w-3 h-3 bg-green-200 rounded"></div>
            <div className="w-3 h-3 bg-green-300 rounded"></div>
            <div className="w-3 h-3 bg-green-400 rounded"></div>
            <div className="w-3 h-3 bg-green-500 rounded"></div>
          </div>
          <span className="text-xs text-gray-500">Profit</span>
        </div>
      </div>
    </div>
  );
};

export default MonthlyHeatmap;

