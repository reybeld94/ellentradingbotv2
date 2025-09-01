import pytest

from app.execution.order_manager import OrderManager, PriceUnavailableError
from app.models.signal import Signal


def test_create_bracket_order_aborts_on_price_error(monkeypatch):
    om = OrderManager(db=None)

    def fake_get_current_price(symbol):
        raise PriceUnavailableError("no price")

    called = {"flag": False}

    def fake_create_order_from_signal(signal, user_id, portfolio_id, **kwargs):
        called["flag"] = True
        return None

    monkeypatch.setattr(om, "_get_current_price", fake_get_current_price)
    monkeypatch.setattr(om, "create_order_from_signal", fake_create_order_from_signal)

    signal = Signal(symbol="AAPL", action="buy", strategy_id="s")

    result = om.create_bracket_order_from_signal(signal, user_id=1, portfolio_id=1)

    assert result["status"] == "error"
    assert "price" in result["message"].lower()
    assert called["flag"] is False


def test_create_bracket_order_aborts_on_zero_price(monkeypatch):
    om = OrderManager(db=None)

    class DummyTrade:
        price = 0

    def fake_get_latest_trade(symbol):
        return DummyTrade()

    called = {"flag": False}

    def fake_create_order_from_signal(signal, user_id, portfolio_id, **kwargs):
        called["flag"] = True
        return None

    monkeypatch.setattr(
        "app.integrations.broker_client.get_latest_trade",
        fake_get_latest_trade,
    )
    monkeypatch.setattr(om, "create_order_from_signal", fake_create_order_from_signal)

    signal = Signal(symbol="AAPL", action="buy", strategy_id="s")

    result = om.create_bracket_order_from_signal(signal, user_id=1, portfolio_id=1)

    assert result["status"] == "error"
    assert "price" in result["message"].lower()
    assert called["flag"] is False
