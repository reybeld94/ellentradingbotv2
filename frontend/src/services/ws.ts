export interface WSHandlers {
  onSignal?: (data: any) => void;
  onOrder?: (data: any) => void;
  onTrade?: (data: any) => void;
  onAccountUpdate?: (data: any) => void;
}

export const connectWebSocket = (handlers: WSHandlers) => {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const ws = new WebSocket(`${protocol}://${window.location.host}/ws/updates`);
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      switch (msg.event) {
        case 'new_signal':
          handlers.onSignal?.(msg.payload);
          break;
        case 'order_update':
          handlers.onOrder?.(msg.payload);
          break;
        case 'trade_update':
          handlers.onTrade?.(msg.payload);
          break;
        case 'account_update':
          handlers.onAccountUpdate?.(msg.payload);
          break;
        default:
          break;
      }
    } catch (err) {
      console.error('WS message error', err);
    }
  };
  return ws;
};
