import React, { useState, useEffect } from 'react';
import { Shield, RefreshCw, Download, Settings } from 'lucide-react';
import RiskMetrics from '../components/risk/RiskMetrics';
import ExposureChart from '../components/risk/ExposureChart';
import RiskAlerts from '../components/risk/RiskAlerts';
import CorrelationMatrix from '../components/risk/CorrelationMatrix';

interface RiskData {
  metrics: {
    portfolioVaR: number;
    portfolioCVaR: number;
    positionLimit: number;
    usedPositions: number;
    marginUtilization: number;
    leverageRatio: number;
    correlationRisk: number;
    concentrationRisk: number;
    liquidityRisk: number;
    marketRisk: number;
    riskScore: number;
    riskLevel: 'low' | 'medium' | 'high' | 'critical';
  };
  exposures: Array<{ symbol: string; exposure: number; limit: number }>;
  alerts: Array<{ id: string; message: string; severity: 'low' | 'medium' | 'high' | 'critical'; timestamp: string }>;
  correlation: { assets: string[]; matrix: number[][] };
}

const RiskDashboard: React.FC = () => {
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchRiskData = async () => {
    try {
      setLoading(true);
      // Mock data
      const mock: RiskData = {
        metrics: {
          portfolioVaR: 5.6,
          portfolioCVaR: 8.2,
          positionLimit: 20,
          usedPositions: 12,
          marginUtilization: 54.3,
          leverageRatio: 1.4,
          correlationRisk: 32.5,
          concentrationRisk: 18.7,
          liquidityRisk: 14.2,
          marketRisk: 22.1,
          riskScore: 62,
          riskLevel: 'medium'
        },
        exposures: [
          { symbol: 'AAPL', exposure: 25000, limit: 30000 },
          { symbol: 'TSLA', exposure: 20000, limit: 15000 },
          { symbol: 'MSFT', exposure: 12000, limit: 20000 },
          { symbol: 'NVDA', exposure: 8000, limit: 10000 }
        ],
        alerts: [
          { id: '1', message: 'TSLA exposure exceeds limit', severity: 'high', timestamp: new Date().toISOString() },
          { id: '2', message: 'Portfolio VaR approaching threshold', severity: 'medium', timestamp: new Date().toISOString() }
        ],
        correlation: {
          assets: ['AAPL', 'TSLA', 'MSFT', 'NVDA'],
          matrix: [
            [1, 0.6, 0.8, 0.7],
            [0.6, 1, 0.5, 0.4],
            [0.8, 0.5, 1, 0.6],
            [0.7, 0.4, 0.6, 1]
          ]
        }
      };
      setData(mock);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
    const interval = setInterval(fetchRiskData, 300000);
    return () => clearInterval(interval);
  }, []);

  const exportData = () => {
    console.log('Exporting risk data...');
  };

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Risk Dashboard</h2>
          <p className="text-slate-600">Assessing portfolio risk...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Risk Dashboard</h1>
            <p className="text-slate-600 mt-1">Real-time risk analysis and alerts</p>
          </div>
          <div className="flex items-center space-x-3">
            <button onClick={exportData} className="btn-ghost">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
            <button onClick={fetchRiskData} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button className="btn-ghost">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </button>
          </div>
        </div>

        {data && (
          <div className="space-y-6">
            <RiskMetrics metrics={data.metrics} loading={loading} />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ExposureChart data={data.exposures} loading={loading} />
              <CorrelationMatrix assets={data.correlation.assets} matrix={data.correlation.matrix} loading={loading} />
            </div>
            <RiskAlerts alerts={data.alerts} loading={loading} />
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskDashboard;

