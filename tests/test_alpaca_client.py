import os
import time
import pytest
from decimal import Decimal

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

    class DummyMarketOrder:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setattr(
        "alpaca.trading.requests.MarketOrderRequest", DummyMarketOrder
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
    assert pos.qty == Decimal("3.5")


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


def test_submit_order_timeout(monkeypatch):
    client = AlpacaClient()

    class DummyTrading:
        def submit_order(self, order):
            time.sleep(0.2)

    monkeypatch.setattr(client, "_trading", DummyTrading())
    monkeypatch.setattr(
        "alpaca.trading.requests.MarketOrderRequest",
        lambda **kw: type("O", (), kw),
    )
    with pytest.raises(TimeoutError):
        client.submit_order("AAPL", 1, "buy", timeout=0.1)


def test_get_latest_trade_timeout(monkeypatch):
    client = AlpacaClient()

    class DummyData:
        def get_stock_latest_trade(self, req):
            time.sleep(0.2)
            return {"AAPL": type("T", (), {"price": 1.0})()}

    monkeypatch.setattr(client, "_stock_data", DummyData())
    monkeypatch.setattr(client, "is_crypto_symbol", lambda s: False)

    with pytest.raises(TimeoutError):
        client.get_latest_trade("AAPL", timeout=0.1)


def test_submit_order_decimal_precision(monkeypatch):
    client = AlpacaClient()

    class DummyTrading:
        def submit_order(self, order):
            self.order = order
            return type("O", (), {"id": "1", "status": "accepted"})()

    class DummyLimitOrder:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    monkeypatch.setattr(client, "_trading", DummyTrading())
    monkeypatch.setattr(
        "alpaca.trading.requests.LimitOrderRequest", DummyLimitOrder
    )

    qty = Decimal("0.0001")
    price = Decimal("123.456789")
    client.submit_order("AAPL", qty, "buy", order_type="limit", price=price)

    assert client._trading.order.qty == str(qty)
    assert client._trading.order.limit_price == str(price)

