import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export interface EquityPoint {
  timestamp: string;
  equity: number;
}

const EquityCurveChart: React.FC<{ data: EquityPoint[] }> = ({ data }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4">Equity Curve</h3>
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={(ts) => new Date(ts).toLocaleDateString()}
        />
        <YAxis />
        <Tooltip labelFormatter={(ts) => new Date(ts).toLocaleString()} />
        <Line type="monotone" dataKey="equity" stroke="#4f46e5" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  </div>
);

export default EquityCurveChart;
