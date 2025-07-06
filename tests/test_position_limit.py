import types
import pytest
import os

os.environ.setdefault('SECRET_KEY', 'secret')
os.environ.setdefault('ALPACA_API_KEY', 'key')
os.environ.setdefault('ALPACA_SECRET_KEY', 'secret')

from app.services.order_executor import OrderExecutor
from app.models.signal import Signal
from app.models.user import User

class DummyPM:
    def __init__(self, open_positions):
        self.open_positions = open_positions
    def count_open_positions(self):
        return self.open_positions
    def get_position_quantity(self, symbol):
        return 0

class DummyBroker:
    def get_account(self):
        return types.SimpleNamespace(cash="1000")


def test_order_blocked_when_limit_exceeded(monkeypatch):
    oe = OrderExecutor()
    monkeypatch.setattr(oe, 'broker', DummyBroker())
    oe.position_manager = DummyPM(open_positions=2)

    user = User(id=1, email="a@b.c", username="u", position_limit=2)
    signal = Signal(symbol="AAPL", action="buy", strategy_id="s", quantity=1)
    with pytest.raises(ValueError):
        oe.execute_signal(signal, user)
