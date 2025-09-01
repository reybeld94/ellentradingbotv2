import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { vi, describe, test, expect, beforeEach } from 'vitest';
class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserver;
import PortfolioAnalytics from '../PortfolioAnalytics';
import api from '../../../services/api';

// Mock API
vi.mock('../../../services/api', () => ({
  default: {
    analytics: {
      getPerformanceMetrics: vi.fn(),
      getSummary: vi.fn(),
    },
  },
}));

const mockMetrics = {
  total_pnl: 1500.00,
  total_pnl_percentage: 15.5,
  sharpe_ratio: 1.25,
  max_drawdown: -8.5,
  win_rate: 65.0,
  avg_hold_time: "2h 30m",
  profit_factor: 1.8,
  total_trades: 20,
  winning_trades: 13,
  losing_trades: 7,
  largest_win: 350.0,
  largest_loss: -120.0,
  avg_win: 85.5,
  avg_loss: -45.2,
  timeframe: "1M",
  start_date: "2024-01-01T00:00:00",
  end_date: "2024-02-01T00:00:00"
};

const mockSummary = {
  timeframes: {
    "1d": { total_pnl: 50, total_pnl_percentage: 0.5, win_rate: 60, total_trades: 3, sharpe_ratio: 0.8 },
    "1w": { total_pnl: 200, total_pnl_percentage: 2.1, win_rate: 70, total_trades: 8, sharpe_ratio: 1.1 },
    "1m": { total_pnl: 1500, total_pnl_percentage: 15.5, win_rate: 65, total_trades: 20, sharpe_ratio: 1.25 },
    "3m": { total_pnl: 3200, total_pnl_percentage: 32.1, win_rate: 68, total_trades: 45, sharpe_ratio: 1.4 }
  },
  all_time: {
    total_pnl: 5500,
    max_drawdown: -12.3,
    profit_factor: 2.1,
    largest_win: 850,
    largest_loss: -200,
    avg_hold_time: "3h 15m"
  },
  portfolio_id: 1,
  portfolio_name: "Main Portfolio"
};

describe('PortfolioAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.analytics.getPerformanceMetrics as any).mockResolvedValue(mockMetrics);
    (api.analytics.getSummary as any).mockResolvedValue(mockSummary);
  });

  test('renders analytics data correctly', async () => {
    render(<PortfolioAnalytics />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText('Loading')).not.toBeInTheDocument();
    });

    // Check main metrics
    expect(screen.getAllByText('$1,500.00')[0]).toBeInTheDocument();
    expect(screen.getAllByText('+15.50%')[0]).toBeInTheDocument();
    expect(screen.getAllByText('+65.00%')[0]).toBeInTheDocument();
    expect(screen.getByText('1.80')).toBeInTheDocument();
  });

  test('handles timeframe selection', async () => {
    render(<PortfolioAnalytics />);

    await waitFor(() => {
      expect(screen.getByText('1 Week')).toBeInTheDocument();
    });

    const weekButton = screen.getAllByText('1 Week')[0];
    fireEvent.click(weekButton);

    await waitFor(() => {
      expect(api.analytics.getPerformanceMetrics).toHaveBeenCalledWith('1W');
    });
  });
});
