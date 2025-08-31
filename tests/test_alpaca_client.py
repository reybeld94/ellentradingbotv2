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


def test_check_crypto_status_without_client():
    client = AlpacaClient()
    client._trading = None
    assert client.check_crypto_status() is False


def test_check_crypto_status_with_assets(monkeypatch):
    client = AlpacaClient()

    class DummyTrading:
        def get_all_assets(self, status, asset_class):
            assert status == "active"
            assert asset_class == "crypto"
            return [type("A", (), {"symbol": "BTCUSD"})()]

    monkeypatch.setattr(client, "_trading", DummyTrading())
    assert client.check_crypto_status() is True


def test_check_crypto_status_handles_exception(monkeypatch):
    client = AlpacaClient()

    class DummyTrading:
        def get_all_assets(self, status, asset_class):
            raise Exception("fail")

    monkeypatch.setattr(client, "_trading", DummyTrading())
    assert client.check_crypto_status() is False


def test_is_crypto_symbol_uses_api(monkeypatch):
    client = AlpacaClient()

    class DummyTrading:
        def get_asset(self, symbol):
            assert symbol == "BTCUSD"
            return type("A", (), {"asset_class": "crypto"})()

    monkeypatch.setattr(client, "_trading", DummyTrading())
    assert client.is_crypto_symbol("BTCUSD") is True


def test_is_crypto_symbol_fallback():
    client = AlpacaClient()
    client._trading = None
    assert client.is_crypto_symbol("BTC/USD") is True
    assert client.is_crypto_symbol("AAPL") is False

