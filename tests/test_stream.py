import asyncio
import json
import sys
import types
import os

# Stub alpaca modules for testing
sys.modules.setdefault('alpaca', types.ModuleType('alpaca'))
sys.modules.setdefault('alpaca.trading', types.ModuleType('alpaca.trading'))
sys.modules.setdefault('alpaca.trading.client', types.ModuleType('alpaca.trading.client'))
sys.modules.setdefault('alpaca.trading.requests', types.ModuleType('alpaca.trading.requests'))
sys.modules.setdefault('alpaca.trading.enums', types.ModuleType('alpaca.trading.enums'))
sys.modules.setdefault('alpaca.trading.stream', types.ModuleType('alpaca.trading.stream'))
sys.modules.setdefault('alpaca.data', types.ModuleType('alpaca.data'))
sys.modules.setdefault('alpaca.data.live', types.ModuleType('alpaca.data.live'))
sys.modules.setdefault('alpaca.data.historical', types.ModuleType('alpaca.data.historical'))
sys.modules.setdefault('alpaca.data.requests', types.ModuleType('alpaca.data.requests'))

os.environ.setdefault('ALPACA_API_KEY', 'key')
os.environ.setdefault('ALPACA_SECRET_KEY', 'secret')
os.environ.setdefault('SECRET_KEY', 'secret')

class DummyStream:
    def __init__(self, *a, **kw):
        self.handler = None
    def subscribe_trade_updates(self, handler):
        self.handler = handler
    async def _run_forever(self):
        await asyncio.sleep(0)

class DummyDataStream:
    def __init__(self, *a, **kw):
        pass
    def subscribe_trades(self, *a, **kw):
        pass
    async def _run_forever(self):
        await asyncio.sleep(0)

sys.modules['alpaca.trading.stream'].TradingStream = DummyStream
sys.modules['alpaca.data.live'].StockDataStream = DummyDataStream
sys.modules['alpaca.data.live'].CryptoDataStream = DummyDataStream
sys.modules['alpaca.data.historical'].CryptoHistoricalDataClient = DummyDataStream
sys.modules['alpaca.data.historical'].StockHistoricalDataClient = DummyDataStream
sys.modules['alpaca.data.requests'].CryptoLatestQuoteRequest = lambda *a, **k: None
sys.modules['alpaca.data.requests'].StockLatestQuoteRequest = lambda *a, **k: None
sys.modules['alpaca.trading.client'].TradingClient = lambda *a, **k: None
sys.modules['alpaca.trading.requests'].MarketOrderRequest = lambda *a, **k: None
sys.modules['alpaca.trading.requests'].GetOrdersRequest = lambda *a, **k: None
sys.modules['alpaca.trading.enums'].OrderSide = types.SimpleNamespace(BUY=1, SELL=2)
sys.modules['alpaca.trading.enums'].TimeInForce = types.SimpleNamespace(DAY=1, GTC=2)
sys.modules['alpaca.trading.enums'].AssetClass = types.SimpleNamespace(CRYPTO=1, US_EQUITY=2)

from app.integrations.alpaca import stream as stream_module
from app.websockets import ws_manager

class DummyAccount:
    cash = 100.0
    portfolio_value = 200.0
    buying_power = 150.0

def test_trade_update_triggers_broadcast(monkeypatch):
    messages = []
    async def fake_broadcast(msg: str):
        messages.append(json.loads(msg))
    monkeypatch.setattr(ws_manager, 'broadcast', fake_broadcast)
    monkeypatch.setattr(stream_module.alpaca_client, 'get_account', lambda: DummyAccount())
    monkeypatch.setattr(
        stream_module.position_manager,
        'get_portfolio_summary',
        lambda *a, **k: {'total_positions': 1}
    )
    alpaca_stream = stream_module.AlpacaStream()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(alpaca_stream._handle_trade_update({}))
    assert messages and messages[0]['event'] == 'account_update'
