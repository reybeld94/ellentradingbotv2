import os
os.environ.setdefault('SECRET_KEY', 'secret')

from app.integrations.alpaca.client import AlpacaClient


def test_submit_order_uses_extended_hours_outside_regular(monkeypatch):
    client = AlpacaClient()

    class DummyTrading:
        def submit_order(self, order):
            self.order = order
            return type("O", (), {"id": "1", "status": "accepted"})()

    dummy = DummyTrading()
    monkeypatch.setattr(client, "_trading", dummy)
    monkeypatch.setattr(
        "app.integrations.alpaca.client._in_regular_trading_hours", lambda: False
    )

    client.submit_order("AAPL", 1, "buy")
    assert dummy.order.extended_hours is True


def test_get_position(monkeypatch):
    client = AlpacaClient()

    class DummyPos:
        def __init__(self, symbol, qty):
            self.symbol = symbol
            self.qty = qty

    class DummyTrading:
        def get_open_position(self, symbol):
            assert symbol == "AAPL"
            return DummyPos(symbol, "3.5")

    monkeypatch.setattr(client, "_trading", DummyTrading())

    pos = client.get_position("AAPL")
    assert pos is not None
    assert pos.qty == 3.5

