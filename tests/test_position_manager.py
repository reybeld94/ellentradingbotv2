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


def test_count_open_positions_includes_negative(monkeypatch):
    pm = PositionManager()
    monkeypatch.setattr(
        PositionManager,
        "get_current_positions",
        lambda self: {"AAPL": 1, "TSLA": -2, "MSFT": 0},
    )
    assert pm.count_open_positions() == 2


def test_validate_buy_signal_limit_with_negative_positions(monkeypatch):
    pm = PositionManager()
    positions = {"AAPL": 1, "TSLA": -1}

    monkeypatch.setattr(
        PositionManager, "get_current_positions", lambda self: positions
    )
    monkeypatch.setattr(
        PositionManager,
        "get_position_quantity",
        lambda self, symbol: positions.get(symbol, 0),
    )

    class DummyBroker:
        def get_account(self):
            return SimpleNamespace(buying_power=1000)

        def get_latest_quote(self, symbol):
            return SimpleNamespace(ask_price=10)

        def get_latest_crypto_quote(self, symbol):
            return SimpleNamespace(ask_price=10)

        def get_latest_trade(self, symbol):
            return SimpleNamespace(price=10)

    dummy = DummyBroker()
    monkeypatch.setattr(PositionManager, "broker", property(lambda self: dummy))

    signal = Signal(symbol="MSFT", action="buy", strategy_id="s")
    with pytest.raises(ValueError):
        pm.validate_buy_signal(signal, calculated_quantity=1, limit=2)

