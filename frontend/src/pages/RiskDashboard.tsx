import React, { useState, useEffect } from 'react';
import {
  Shield, Activity, BarChart3,
  RefreshCw, Download, Settings, Bell
} from 'lucide-react';
import RiskMetrics from '../components/risk/RiskMetrics';
import ExposureChart from '../components/risk/ExposureChart';
import RiskAlerts from '../components/risk/RiskAlerts';
import CorrelationMatrix from '../components/risk/CorrelationMatrix';
import { api } from '../services/api';

interface RiskDashboardData {
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
  exposure: Array<{
    category: string;
    exposure: number;
    limit: number;
    utilizationPercent: number;
    riskLevel: 'low' | 'medium' | 'high';
    positions: Array<{
      symbol: string;
      value: number;
      percentage: number;
      riskContribution: number;
    }>;
  }>;
  alerts: Array<{
    id: string;
    type: 'warning' | 'critical' | 'info';
    category: 'exposure' | 'correlation' | 'volatility' | 'margin' | 'position' | 'market';
    title: string;
    description: string;
    timestamp: string;
    isRead: boolean;
    isAcknowledged: boolean;
    affectedPositions?: string[];
    recommendedAction?: string;
    severity: number;
  }>;
  correlations: {
    symbols: string[];
    data: Array<{
      symbol1: string;
      symbol2: string;
      correlation: number;
      pValue: number;
      significance: 'high' | 'medium' | 'low';
    }>;
  };
}

const RiskDashboard: React.FC = () => {
  const [data, setData] = useState<RiskDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'overview' | 'exposure' | 'alerts' | 'correlation'>('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchRiskData = async () => {
    try {
      setLoading(true);
      
      // Fetch real risk metrics, exposure, and alerts from API
      const [metricsResponse, exposureResponse, alertsResponse] = await Promise.all([
        api.risk.getMetrics(),
        api.risk.getExposure(),
        api.risk.getAlerts()
      ]);
      
      if (!metricsResponse.ok || !exposureResponse.ok || !alertsResponse.ok) {
        throw new Error('Failed to fetch risk data');
      }
      
      const apiData = await metricsResponse.json();
      const exposureData = await exposureResponse.json();
      const alertsData = await alertsResponse.json();
      
      // Combine real data with dummy data (temporarily)
      const mockData: RiskDashboardData = {
        metrics: {
          // Use real data from API
          portfolioVaR: apiData.metrics.portfolioVaR,
          portfolioCVaR: apiData.metrics.portfolioCVaR,
          positionLimit: apiData.metrics.positionLimit,
          usedPositions: apiData.metrics.usedPositions,
          marginUtilization: apiData.metrics.marginUtilization,
          leverageRatio: apiData.metrics.leverageRatio,
          correlationRisk: apiData.metrics.correlationRisk,
          concentrationRisk: apiData.metrics.concentrationRisk,
          liquidityRisk: apiData.metrics.liquidityRisk,
          marketRisk: apiData.metrics.marketRisk,
          riskScore: apiData.metrics.riskScore,
          riskLevel: apiData.metrics.riskLevel
        },
        // Use real exposure and alerts data from API
        exposure: exposureData.exposure || [],
        alerts: alertsData.alerts || [],
        correlations: {
          symbols: ['AAPL', 'GOOGL', 'MSFT', 'JNJ', 'JPM'],
          data: [
            { symbol1: 'AAPL', symbol2: 'GOOGL', correlation: 0.67, pValue: 0.001, significance: 'high' },
            { symbol1: 'AAPL', symbol2: 'MSFT', correlation: 0.82, pValue: 0.000, significance: 'high' },
            { symbol1: 'AAPL', symbol2: 'JNJ', correlation: 0.23, pValue: 0.087, significance: 'low' },
            { symbol1: 'AAPL', symbol2: 'JPM', correlation: 0.45, pValue: 0.012, significance: 'medium' },
            { symbol1: 'GOOGL', symbol2: 'MSFT', correlation: 0.71, pValue: 0.002, significance: 'high' },
            { symbol1: 'GOOGL', symbol2: 'JNJ', correlation: 0.18, pValue: 0.156, significance: 'low' },
            { symbol1: 'GOOGL', symbol2: 'JPM', correlation: 0.39, pValue: 0.028, significance: 'medium' },
            { symbol1: 'MSFT', symbol2: 'JNJ', correlation: 0.15, pValue: 0.234, significance: 'low' },
            { symbol1: 'MSFT', symbol2: 'JPM', correlation: 0.41, pValue: 0.021, significance: 'medium' },
            { symbol1: 'JNJ', symbol2: 'JPM', correlation: -0.12, pValue: 0.367, significance: 'low' }
          ]
        }
      };
      
      setData(mockData);
    } catch (error) {
      console.error('Error fetching risk data:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRiskData();
    
    // Auto-refresh every 2 minutes if enabled
    let interval: number | null = null;
    if (autoRefresh) {
      interval = window.setInterval(fetchRiskData, 120000);
    }

    return () => {
      if (interval !== null) window.clearInterval(interval);
    };
  }, [autoRefresh]);

  const handleMarkAsRead = async (alertId: string) => {
    if (!data) return;
    
    setData({
      ...data,
      alerts: data.alerts.map(alert =>
        alert.id === alertId ? { ...alert, isRead: true } : alert
      )
    });
  };

  const handleAcknowledge = async (alertId: string) => {
    if (!data) return;
    
    setData({
      ...data,
      alerts: data.alerts.map(alert =>
        alert.id === alertId ? { ...alert, isAcknowledged: true, isRead: true } : alert
      )
    });
  };

  const handleDismiss = async (alertId: string) => {
    if (!data) return;
    
    setData({
      ...data,
      alerts: data.alerts.filter(alert => alert.id !== alertId)
    });
  };

  const exportRiskReport = () => {
    console.log('Exporting risk report...');
  };

  const tabs = [
    { key: 'overview', label: 'Overview', icon: Shield },
    { key: 'exposure', label: 'Exposure', icon: BarChart3 },
    { key: 'alerts', label: 'Alerts', icon: Bell },
    { key: 'correlation', label: 'Correlation', icon: Activity }
  ];

  if (loading && !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-primary-600 to-primary-700 rounded-2xl flex items-center justify-center mb-6 mx-auto animate-pulse">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Loading Risk Dashboard</h2>
          <p className="text-slate-600">Analyzing portfolio risk metrics...</p>
        </div>
      </div>
    );
  }

  const unreadAlertsCount = data?.alerts.filter(alert => !alert.isRead).length || 0;
  const criticalAlertsCount = data?.alerts.filter(alert => alert.type === 'critical').length || 0;

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Risk Management</h1>
            <p className="text-slate-600 mt-1">
              Real-time risk monitoring and portfolio protection
              {criticalAlertsCount > 0 && (
                <span className="ml-2 text-error-600 font-semibold">
                  • {criticalAlertsCount} critical alert{criticalAlertsCount > 1 ? 's' : ''}
                </span>
              )}
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`btn-ghost ${autoRefresh ? 'bg-primary-50 text-primary-700' : ''}`}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${autoRefresh ? 'animate-spin' : ''}`} />
              Auto Refresh
            </button>
            
            <button onClick={exportRiskReport} className="btn-ghost">
              <Download className="w-4 h-4 mr-2" />
              Export Report
            </button>
            
            <button onClick={fetchRiskData} className="btn-secondary">
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            
            <button className="btn-ghost">
              <Settings className="w-4 h-4 mr-2" />
              Risk Settings
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="card p-2">
          <div className="flex items-center space-x-1">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const alertCount = tab.key === 'alerts' ? unreadAlertsCount : 0;
              
              return (
                <button
                  key={tab.key}
                  onClick={() => setSelectedTab(tab.key as any)}
                  className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 relative ${
                    selectedTab === tab.key
                      ? 'bg-primary-100 text-primary-700 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-2" />
                  {tab.label}
                  {alertCount > 0 && (
                    <span className="ml-2 bg-error-500 text-white text-xs font-bold px-2 py-1 rounded-full min-w-[18px] h-[18px] flex items-center justify-center">
                      {alertCount > 9 ? '9+' : alertCount}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        {selectedTab === 'overview' && data && (
          <div className="space-y-6">
            <RiskMetrics metrics={data.metrics} loading={loading} />
            
            {/* Quick Overview Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ExposureChart 
                data={data.exposure} 
                loading={loading}
                chartType="bar"
              />
              
              <RiskAlerts
                alerts={data.alerts.slice(0, 5)}
                onMarkAsRead={handleMarkAsRead}
                onAcknowledge={handleAcknowledge}
                onDismiss={handleDismiss}
                loading={loading}
              />
            </div>
          </div>
        )}

        {selectedTab === 'exposure' && data && (
          <div className="space-y-6">
            <ExposureChart 
              data={data.exposure} 
              loading={loading}
              chartType="bar"
            />
            
            {/* Detailed Exposure Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card p-6">
                <h4 className="text-lg font-semibold text-slate-900 mb-4">Sector Concentration</h4>
                <div className="space-y-3">
                  {data.exposure.map((category) => (
                    <div key={category.category} className="flex items-center justify-between">
                      <span className="text-sm text-slate-600">{category.category}</span>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-semibold text-slate-900">
                          {category.utilizationPercent.toFixed(1)}%
                        </span>
                        <div className={`w-3 h-3 rounded-full ${
                          category.riskLevel === 'high' ? 'bg-error-500' :
                          category.riskLevel === 'medium' ? 'bg-warning-500' : 'bg-success-500'
                        }`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="card p-6">
                <h4 className="text-lg font-semibold text-slate-900 mb-4">Risk Limits</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Position Limit</span>
                    <span className="text-sm font-semibold text-slate-900">
                      {data.metrics.usedPositions}/{data.metrics.positionLimit}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Margin Usage</span>
                    <span className="text-sm font-semibold text-slate-900">
                      {data.metrics.marginUtilization.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Leverage Ratio</span>
                    <span className="text-sm font-semibold text-slate-900">
                      {data.metrics.leverageRatio.toFixed(2)}x
                    </span>
                  </div>
                </div>
              </div>

              <div className="card p-6">
                <h4 className="text-lg font-semibold text-slate-900 mb-4">Risk Metrics</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Portfolio VaR</span>
                    <span className="text-sm font-semibold text-error-600">
                      {data.metrics.portfolioVaR.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">CVaR (ES)</span>
                    <span className="text-sm font-semibold text-error-600">
                      {data.metrics.portfolioCVaR.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-slate-600">Correlation Risk</span>
                    <span className="text-sm font-semibold text-warning-600">
                      {data.metrics.correlationRisk.toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'alerts' && data && (
          <div className="space-y-6">
            <RiskAlerts
              alerts={data.alerts}
              onMarkAsRead={handleMarkAsRead}
              onAcknowledge={handleAcknowledge}
              onDismiss={handleDismiss}
              loading={loading}
            />
          </div>
        )}

        {selectedTab === 'correlation' && data && (
          <div className="space-y-6">
            <CorrelationMatrix
              symbols={data.correlations.symbols}
              correlations={data.correlations.data}
              loading={loading}
              timeframe="3M"
            />
            
            {/* Correlation Insights */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card p-6">
                <h4 className="text-lg font-semibold text-slate-900 mb-4">High Risk Correlations</h4>
                <div className="space-y-3">
                  {data.correlations.data
                    .filter(c => Math.abs(c.correlation) > 0.7)
                    .sort((a, b) => Math.abs(b.correlation) - Math.abs(a.correlation))
                    .slice(0, 5)
                    .map((correlation) => (
                      <div key={`${correlation.symbol1}-${correlation.symbol2}`} 
                           className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div>
                          <span className="font-medium text-slate-900">
                            {correlation.symbol1} - {correlation.symbol2}
                          </span>
                          <p className="text-xs text-slate-500">
                            {correlation.significance} significance
                          </p>
                        </div>
                        <span className={`font-bold ${
                          correlation.correlation > 0 ? 'text-error-600' : 'text-blue-600'
                        }`}>
                          {correlation.correlation.toFixed(3)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>

              <div className="card p-6">
                <h4 className="text-lg font-semibold text-slate-900 mb-4">Diversification Opportunities</h4>
                <div className="space-y-3">
                  {data.correlations.data
                    .filter(c => Math.abs(c.correlation) < 0.3)
                    .sort((a, b) => Math.abs(a.correlation) - Math.abs(b.correlation))
                    .slice(0, 5)
                    .map((correlation) => (
                      <div key={`${correlation.symbol1}-${correlation.symbol2}`} 
                           className="flex items-center justify-between p-3 bg-success-50 rounded-lg">
                        <div>
                          <span className="font-medium text-slate-900">
                            {correlation.symbol1} - {correlation.symbol2}
                          </span>
                          <p className="text-xs text-success-600">
                            Good diversification pair
                          </p>
                        </div>
                        <span className="font-bold text-success-600">
                          {correlation.correlation.toFixed(3)}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Risk Summary Footer */}
        <div className="card p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  data?.metrics.riskLevel === 'low' ? 'bg-success-500' :
                  data?.metrics.riskLevel === 'medium' ? 'bg-warning-500' :
                  data?.metrics.riskLevel === 'high' ? 'bg-error-500' : 'bg-error-600'
                } animate-pulse`}></div>
                <span className="text-sm font-medium text-slate-900 capitalize">
                  {data?.metrics.riskLevel || 'Unknown'} Risk Level
                </span>
              </div>
              
              <div className="text-sm text-slate-600">
                Last updated: {new Date().toLocaleTimeString()}
              </div>
            </div>
            
            <div className="flex items-center space-x-4 text-sm">
              <div>
                <span className="text-slate-500">Portfolio VaR: </span>
                <span className="font-semibold text-error-600">
                  {data?.metrics.portfolioVaR.toFixed(2)}%
                </span>
              </div>
              <div>
                <span className="text-slate-500">Risk Score: </span>
                <span className="font-semibold text-slate-900">
                  {data?.metrics.riskScore}/100
                </span>
              </div>
              <div>
                <span className="text-slate-500">Active Alerts: </span>
                <span className={`font-semibold ${
                  criticalAlertsCount > 0 ? 'text-error-600' : 'text-success-600'
                }`}>
                  {criticalAlertsCount}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;

