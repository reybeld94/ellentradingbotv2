import types
import pytest

from app.execution import order_manager
from app.models.signal import Signal


def test_calculate_position_size_fractionable(monkeypatch):
    class DummyOE:
        def __init__(self):
            self.broker = types.SimpleNamespace(is_asset_fractionable=lambda s: True)
        def map_symbol(self, symbol):
            return symbol
        def _get_market_price(self, symbol):
            return 50
        def is_crypto(self, symbol):
            return False
    monkeypatch.setattr(order_manager, "OrderExecutor", DummyOE)
    om = order_manager.OrderManager(db=None)
    signal = Signal(symbol="AAPL", action="buy", strategy_id="s")
    qty = om.calculate_position_size(signal, available_capital=1000, max_position_pct=0.1)
    assert qty == 2.0


def test_calculate_position_size_non_fractionable_insufficient_capital(monkeypatch):
    class DummyOE:
        def __init__(self):
            self.broker = types.SimpleNamespace(is_asset_fractionable=lambda s: False)
        def map_symbol(self, symbol):
            return symbol
        def _get_market_price(self, symbol):
            return 100
        def is_crypto(self, symbol):
            return False
    monkeypatch.setattr(order_manager, "OrderExecutor", DummyOE)
    om = order_manager.OrderManager(db=None)
    signal = Signal(symbol="AAPL", action="buy", strategy_id="s")
    with pytest.raises(ValueError):
        om.calculate_position_size(signal, available_capital=50, max_position_pct=0.1)


def test_calculate_position_size_uses_signal_quantity():
    om = order_manager.OrderManager(db=None)
    signal = Signal(symbol="AAPL", action="buy", strategy_id="s", quantity=5)
    qty = om.calculate_position_size(signal, available_capital=1000, max_position_pct=0.1)
    assert qty == 5.0
