import React from 'react';
import { Grid } from 'lucide-react';

interface CorrelationMatrixProps {
  assets: string[];
  matrix: number[][]; // values between -1 and 1
  loading?: boolean;
}

const getColor = (value: number) => {
  const intensity = Math.abs(value);
  const opacity = intensity;
  if (value > 0) {
    return `rgba(34,197,94,${opacity})`; // green
  }
  return `rgba(239,68,68,${opacity})`; // red
};

const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ assets, matrix, loading = false }) => {
  if (loading) {
    return (
      <div className="card p-6">
        <div className="h-6 bg-slate-200 rounded w-48 mb-4 animate-pulse"></div>
        <div className="space-y-2">
          {Array.from({ length: assets.length }).map((_, i) => (
            <div key={i} className="h-6 bg-slate-200 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6 overflow-x-auto">
      <h3 className="text-lg font-semibold text-slate-900 mb-4 flex items-center">
        <Grid className="w-5 h-5 mr-2 text-primary-600" />
        Correlation Matrix
      </h3>
      <table className="min-w-full text-xs text-center">
        <thead>
          <tr>
            <th className="p-2"></th>
            {assets.map(asset => (
              <th key={asset} className="p-2 font-medium text-slate-600">{asset}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={assets[i]}> 
              <th className="p-2 font-medium text-slate-600 text-left">{assets[i]}</th>
              {row.map((val, j) => (
                <td key={j} className="p-1">
                  <div
                    className="w-8 h-8 flex items-center justify-center rounded"
                    style={{ backgroundColor: getColor(val) }}
                  >
                    {i === j ? '-' : val.toFixed(2)}
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default CorrelationMatrix;

