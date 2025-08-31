import pytest
from types import SimpleNamespace

from app.services.position_manager import PositionManager
from app.models.signal import Signal


def test_validate_buy_signal_insufficient_buying_power(monkeypatch):
    pm = PositionManager()

    class DummyBroker:
        def get_positions(self):
            return []

        def get_position(self, symbol):
            return None

        def get_account(self):
            return SimpleNamespace(buying_power=50)

        def get_latest_quote(self, symbol):
            return SimpleNamespace(ask_price=20)

        def get_latest_crypto_quote(self, symbol):
            return SimpleNamespace(ask_price=20)

        def get_latest_trade(self, symbol):
            return SimpleNamespace(price=15)

    dummy = DummyBroker()
    monkeypatch.setattr(PositionManager, "broker", property(lambda self: dummy))

    signal = Signal(symbol="AAPL", action="buy", strategy_id="s")

    with pytest.raises(ValueError):
        pm.validate_buy_signal(signal, calculated_quantity=3)


def test_validate_buy_signal_margin_account(monkeypatch):
    pm = PositionManager()

    class DummyBroker:
        def get_positions(self):
            return []

        def get_position(self, symbol):
            return None

        def get_account(self):
            return SimpleNamespace(cash=0, buying_power=1000)

        def get_latest_quote(self, symbol):
            return SimpleNamespace(ask_price=20)

        def get_latest_crypto_quote(self, symbol):
            return SimpleNamespace(ask_price=20)

        def get_latest_trade(self, symbol):
            return SimpleNamespace(price=15)

    dummy = DummyBroker()
    monkeypatch.setattr(PositionManager, "broker", property(lambda self: dummy))

    signal = Signal(symbol="AAPL", action="buy", strategy_id="s")

    assert pm.validate_buy_signal(signal, calculated_quantity=3)

