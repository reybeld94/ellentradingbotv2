import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { vi, describe, test, expect, beforeEach } from 'vitest';
import EquityCurve from '../EquityCurve';
import TradeDistribution from '../TradeDistribution';
import MonthlyHeatmap from '../MonthlyHeatmap';
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
      getEquityCurve: vi.fn(),
      getTradeAnalytics: vi.fn(),
      getMonthlyPerformance: vi.fn(),
    },
  },
}));

const mockEquityCurveData = {
  equity_curve: [
    { date: '2024-01-01T00:00:00', equity: 10000, drawdown: 0, trade_id: 1, symbol: 'AAPL', pnl: 100 },
    { date: '2024-01-02T00:00:00', equity: 10150, drawdown: 0, trade_id: 2, symbol: 'TSLA', pnl: 150 },
    { date: '2024-01-03T00:00:00', equity: 10100, drawdown: -3.3, trade_id: 3, symbol: 'MSFT', pnl: -50 },
  ],
  drawdown_periods: [
    {
      start_date: '2024-01-03T00:00:00',
      end_date: '2024-01-04T00:00:00',
      max_drawdown: -8.5,
      duration_days: 1,
    },
  ],
};

const mockTradeDistribution = {
  trade_distribution: {
    win_distribution: [
      { range: '$0 - $50', count: 5, percentage: 25 },
      { range: '$50 - $100', count: 8, percentage: 40 },
      { range: '$100 - $200', count: 7, percentage: 35 },
    ],
    loss_distribution: [
      { range: '$-50 - $0', count: 3, percentage: 30 },
      { range: '$-100 - $-50', count: 4, percentage: 40 },
      { range: '$-200 - $-100', count: 3, percentage: 30 },
    ],
    total_winners: 20,
    total_losers: 10,
    avg_winner: 75.5,
    avg_loser: -65.2,
  },
};

const mockMonthlyData = {
  monthly_returns: [
    { month: '2024-01', pnl: 1500, trades: 25, win_rate: 68 },
    { month: '2024-02', pnl: -500, trades: 18, win_rate: 44 },
    { month: '2024-03', pnl: 2200, trades: 32, win_rate: 72 },
  ],
};

describe('Advanced Analytics Charts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('EquityCurve', () => {
    test('renders equity curve correctly', async () => {
      (api.analytics.getEquityCurve as any).mockResolvedValue(mockEquityCurveData);

      render(<EquityCurve timeframe="1M" />);

      await waitFor(() => {
        expect(screen.getByText('Equity Curve')).toBeInTheDocument();
      });

      expect(screen.getByText('Current Equity')).toBeInTheDocument();
      expect(screen.getByText('Total Trades')).toBeInTheDocument();
      expect(screen.getByText('Max Drawdown')).toBeInTheDocument();
    });

    test('shows drawdown periods warning', async () => {
      (api.analytics.getEquityCurve as any).mockResolvedValue(mockEquityCurveData);

      render(<EquityCurve timeframe="1M" />);

      await waitFor(() => {
        expect(screen.getByText(/Significant Drawdown Period/)).toBeInTheDocument();
      });
    });
  });

  describe('TradeDistribution', () => {
    test('renders trade distribution correctly', async () => {
      (api.analytics.getTradeAnalytics as any).mockResolvedValue(mockTradeDistribution);

      render(<TradeDistribution timeframe="3M" />);

      await waitFor(() => {
        expect(screen.getByText('Trade Distribution')).toBeInTheDocument();
      });

      expect(screen.getByText('20')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });

    test('toggles between bar and pie chart views', async () => {
      (api.analytics.getTradeAnalytics as any).mockResolvedValue(mockTradeDistribution);

      render(<TradeDistribution timeframe="3M" />);

      await waitFor(() => {
        expect(screen.getByText('Bar Chart')).toBeInTheDocument();
        expect(screen.getByText('Pie Chart')).toBeInTheDocument();
      });
    });
  });

  describe('MonthlyHeatmap', () => {
    test('renders monthly heatmap correctly', async () => {
      (api.analytics.getMonthlyPerformance as any).mockResolvedValue(mockMonthlyData);

      render(<MonthlyHeatmap />);

      await waitFor(() => {
        expect(screen.getByText('Monthly Performance Heatmap')).toBeInTheDocument();
      });

      expect(screen.getByText('Total P&L')).toBeInTheDocument();
      expect(screen.getByText('Positive Months')).toBeInTheDocument();
    });
  });
});

