import React, { useState, useEffect } from 'react';
import ProfessionalSignalsPage from '../components/signals/ProfessionalSignalsPage';
import SignalModal from '../components/signals/SignalModal';

export type SignalStatus =
  | 'pending'
  | 'validated'
  | 'rejected'
  | 'executed'
  | 'bracket_created'
  | 'bracket_failed'
  | 'error';

interface RawSignal {
  id: number;
  symbol: string;
  action: 'buy' | 'sell';
  strategy_id: string;
  status: SignalStatus;
  timestamp: string;
  quantity?: number;
  confidence?: number;
  reason?: string;
  error_message?: string;
  price?: number;
  target?: number;
  stopLoss?: number;
}

interface NormalizedSignal {
  id: number;
  symbol: string;
  action: 'BUY' | 'SELL';
  status: 'pending' | 'executed' | 'rejected';
  confidence: number;
  quantity: number;
  strategy_id: string;
  timestamp: string;
  reason: string;
  price: number;
  target: number;
  stopLoss?: number;
  error_message?: string;
}

const SignalsPage: React.FC = () => {
  const [signals, setSignals] = useState<RawSignal[]>([]);
  const [selectedSignal, setSelectedSignal] = useState<RawSignal | null>(null);

  const getAuthToken = () => localStorage.getItem('token');

  const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
    const token = getAuthToken();
    if (!token) throw new Error('No authentication token available');

    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    };

    const response = await fetch(url, { ...options, headers });
    if (response.status === 401) {
      localStorage.removeItem('token');
      window.location.reload();
      throw new Error('Authentication failed');
    }
    if (!response.ok) throw new Error(`API Error: ${response.status}`);
    return response;
  };

  const fetchSignals = async () => {
    try {
      const response = await authenticatedFetch('/api/v1/signals');
      const data = await response.json();
      setSignals(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Error fetching signals:', error);
      setSignals([]);
    }
  };

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(fetchSignals, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (signalId: number) => {
    try {
      await authenticatedFetch(`/api/v1/signals/${signalId}/approve`, {
        method: 'POST',
      });
      fetchSignals();
    } catch (error) {
      console.error('Error approving signal:', error);
    }
  };

  const handleReject = async (signalId: number) => {
    try {
      await authenticatedFetch(`/api/v1/signals/${signalId}/reject`, {
        method: 'POST',
      });
      fetchSignals();
    } catch (error) {
      console.error('Error rejecting signal:', error);
    }
  };

  const handleViewDetails = (signal: NormalizedSignal) => {
    const raw = signals.find(s => s.id === signal.id);
    if (raw) setSelectedSignal(raw);
  };

  const normalizeStatus = (status: SignalStatus): 'pending' | 'executed' | 'rejected' => {
    switch (status) {
      case 'executed':
      case 'bracket_created':
        return 'executed';
      case 'rejected':
      case 'bracket_failed':
      case 'error':
        return 'rejected';
      default:
        return 'pending';
    }
  };

  const normalizedSignals: NormalizedSignal[] = signals.map(s => ({
    id: s.id,
    symbol: s.symbol,
    action: s.action.toUpperCase() === 'SELL' ? 'SELL' : 'BUY',
    status: normalizeStatus(s.status),
    confidence: s.confidence ?? 0,
    quantity: s.quantity ?? 0,
    strategy_id: s.strategy_id,
    timestamp: s.timestamp,
    reason: s.reason ?? '',
    price: s.price ?? 0,
    target: s.target ?? 0,
    stopLoss: s.stopLoss,
    error_message: s.error_message,
  }));

  return (
    <>
      <ProfessionalSignalsPage
        signals={normalizedSignals}
        onApprove={handleApprove}
        onReject={handleReject}
        onViewDetails={handleViewDetails}
        onRefresh={fetchSignals}
      />
      <SignalModal
        signal={selectedSignal}
        isOpen={selectedSignal !== null}
        onClose={() => setSelectedSignal(null)}
        onApprove={handleApprove}
        onReject={handleReject}
      />
    </>
  );
};

export default SignalsPage;
