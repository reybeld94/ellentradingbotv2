import asyncio
import json
import os

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

import importlib
from app import integrations

stream_module = importlib.import_module(integrations.broker_stream.__module__)
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

    client_attr = 'kraken_client' if hasattr(stream_module, 'kraken_client') else 'alpaca_client'
    monkeypatch.setattr(getattr(stream_module, client_attr), 'get_account', lambda: DummyAccount())
    monkeypatch.setattr(
        stream_module.position_manager,
        'get_portfolio_summary',
        lambda *a, **k: {'total_positions': 1}
    )
    stream_cls = type(integrations.broker_stream)
    stream_instance = stream_cls()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(stream_instance._handle_trade_update({}))
    assert messages and messages[0]['event'] == 'account_update'
