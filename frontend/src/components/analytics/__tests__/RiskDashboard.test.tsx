import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { vi, describe, test, expect, beforeEach } from 'vitest';
import RiskDashboard from '../RiskDashboard';
import api from '../../../services/api';

class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserver;

vi.mock('../../../services/api', () => ({
  default: {
    analytics: {
      getRiskDashboard: vi.fn(),
    },
  },
}));

const mockRiskDashboardData = {
  risk_metrics: {
    total_return: 2500,
    volatility: 150.75,
    sharpe_ratio: 1.234,
    sortino_ratio: 1.678,
    calmar_ratio: 2.145,
    max_drawdown: -12.5,
    var_95: -85.5,
    expected_shortfall_95: -125.75,
    risk_score: {
      score: 45.2,
      level: 'Moderate',
      color: 'yellow',
      components: { drawdown: 25.0, volatility: 35.8, sortino: 15.2 },
    },
  },
  var_analysis: {
    var_levels: {
      var_99: { value: -150.0, confidence: '99%' },
      var_95: { value: -85.5, confidence: '95%' },
      var_90: { value: -65.25, confidence: '90%' },
    },
    expected_shortfall: {
      value: -125.75,
      interpretation: 'Average loss in worst 5% of cases: $126',
    },
  },
  position_sizing: {
    position_analysis: [
      { category: 'Small (<$1K)', trades: 15, total_pnl: 450, avg_pnl: 30, percentage_of_trades: 50 },
      { category: 'Medium ($1K-$5K)', trades: 10, total_pnl: 800, avg_pnl: 80, percentage_of_trades: 33.3 },
      { category: 'Large ($5K-$10K)', trades: 5, total_pnl: 1250, avg_pnl: 250, percentage_of_trades: 16.7 },
    ],
    concentration_metrics: {
      avg_position_size: 2500,
      max_position_size: 8500,
      concentration_ratio: 3.4,
      top_20_percent_concentration: 65.2,
    },
  },
  time_based_risk: {
    hourly_analysis: [
      { hour: '09:00', trades: 5, avg_pnl: 45.5, volatility: 25.2 },
      { hour: '10:00', trades: 8, avg_pnl: -12.25, volatility: 35.8 },
      { hour: '11:00', trades: 7, avg_pnl: 78.9, volatility: 18.5 },
    ],
    daily_analysis: [
      { day: 'Monday', trades: 8, avg_pnl: 65.25, volatility: 45.2 },
      { day: 'Tuesday', trades: 10, avg_pnl: -25.5, volatility: 52.1 },
      { day: 'Wednesday', trades: 12, avg_pnl: 88.75, volatility: 38.9 },
    ],
  },
  correlation_analysis: {
    correlations: [
      { pair: 'AAPL/MSFT', correlation: 0.654, strength: 'Moderate', common_days: 15 },
      { pair: 'TSLA/NVDA', correlation: -0.234, strength: 'Weak', common_days: 12 },
    ],
    diversification_score: 78.5,
    analysis_summary: 'Analyzed 2 symbol pairs from 4 most active symbols',
  },
  risk_limits_status: {
    status: 'Active',
    configured_limits: {
      max_daily_drawdown: 5.0,
      max_weekly_drawdown: 10.0,
      max_position_size: 10000,
    },
    current_usage: {
      daily_pnl: -125.5,
      daily_drawdown_used: 35.2,
    },
  },
};

describe('RiskDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.analytics.getRiskDashboard as any).mockResolvedValue(mockRiskDashboardData);
  });

  test('renders risk dashboard correctly', async () => {
    render(<RiskDashboard timeframe="3M" />);

    await waitFor(() => {
      expect(screen.getByText('Risk Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('45.2')).toBeInTheDocument();
    expect(screen.getByText('Moderate Risk')).toBeInTheDocument();
    expect(screen.getByText('Max Drawdown')).toBeInTheDocument();
    expect(screen.getByText('Volatility')).toBeInTheDocument();
    expect(screen.getByText('VaR (95%)')).toBeInTheDocument();
  });

  test('shows high risk alert when appropriate', async () => {
    const highRiskData = { ...mockRiskDashboardData, risk_metrics: { ...mockRiskDashboardData.risk_metrics, risk_score: { ...mockRiskDashboardData.risk_metrics.risk_score, level: 'Very High' } } };
    (api.analytics.getRiskDashboard as any).mockResolvedValue(highRiskData);

    render(<RiskDashboard timeframe="3M" />);

    await waitFor(() => {
      expect(screen.getByText('High Risk Alert')).toBeInTheDocument();
    });
  });

  test('navigates between different sections', async () => {
    render(<RiskDashboard timeframe="3M" />);

    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });

    expect(screen.getByText('Value at Risk')).toBeInTheDocument();
    expect(screen.getByText('Position Sizing')).toBeInTheDocument();
    expect(screen.getByText('Time Analysis')).toBeInTheDocument();
    expect(screen.getByText('Correlations')).toBeInTheDocument();
  });

  test('displays VaR analysis when selected', async () => {
    render(<RiskDashboard timeframe="3M" />);

    await waitFor(() => {
      expect(screen.getByText('Risk Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('99% VaR')).toBeInTheDocument();
    expect(screen.getByText('95% VaR')).toBeInTheDocument();
  });

  test('handles loading state', () => {
    (api.analytics.getRiskDashboard as any).mockImplementation(() => new Promise(() => {}));
    render(<RiskDashboard />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  test('handles error state', async () => {
    (api.analytics.getRiskDashboard as any).mockRejectedValue(new Error('API Error'));
    render(<RiskDashboard />);
    await waitFor(() => {
      expect(screen.getByText('Error loading risk dashboard data')).toBeInTheDocument();
    });
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });
});

