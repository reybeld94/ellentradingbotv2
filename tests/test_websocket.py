import asyncio
import json
import sys
import types
from fastapi.testclient import TestClient

# Stub alpaca modules for testing without the actual package
sys.modules.setdefault('alpaca', types.ModuleType('alpaca'))
sys.modules.setdefault('alpaca.trading', types.ModuleType('alpaca.trading'))
sys.modules.setdefault('alpaca.trading.client', types.ModuleType('alpaca.trading.client'))
sys.modules.setdefault('alpaca.trading.requests', types.ModuleType('alpaca.trading.requests'))
sys.modules.setdefault('alpaca.trading.enums', types.ModuleType('alpaca.trading.enums'))
sys.modules.setdefault('alpaca.data', types.ModuleType('alpaca.data'))
sys.modules.setdefault('alpaca.data.historical', types.ModuleType('alpaca.data.historical'))
sys.modules.setdefault('alpaca.data.requests', types.ModuleType('alpaca.data.requests'))

# Provide dummy classes used during import
class Dummy:
    def __init__(self, *args, **kwargs):
        pass

sys.modules['alpaca.trading.client'].TradingClient = Dummy
sys.modules['alpaca.trading.requests'].MarketOrderRequest = Dummy
sys.modules['alpaca.trading.requests'].GetOrdersRequest = Dummy
sys.modules['alpaca.trading.enums'].OrderSide = Dummy
sys.modules['alpaca.trading.enums'].TimeInForce = Dummy
sys.modules['alpaca.trading.enums'].AssetClass = Dummy
sys.modules['alpaca.data.historical'].CryptoHistoricalDataClient = Dummy
sys.modules['alpaca.data.historical'].StockHistoricalDataClient = Dummy
sys.modules['alpaca.data.requests'].CryptoLatestQuoteRequest = Dummy
sys.modules['alpaca.data.requests'].StockLatestQuoteRequest = Dummy

from app.main import app
from app.websockets import ws_manager

client = TestClient(app)

def test_websocket_broadcast():
    with client.websocket_connect("/ws/updates") as websocket:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(ws_manager.broadcast(json.dumps({"event": "test"})))
        data = websocket.receive_text()
        assert "\"event\": \"test\"" in data
