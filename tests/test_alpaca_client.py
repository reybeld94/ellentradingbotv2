import os
os.environ.setdefault('SECRET_KEY', 'secret')

from app.integrations.alpaca.client import AlpacaClient


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

