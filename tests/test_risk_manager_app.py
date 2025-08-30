import pytest
from types import SimpleNamespace
from datetime import datetime

from app.risk.manager import RiskManager, RiskViolation
from app.core.types import NormalizedSignal, SignalAction
import app.risk.manager as manager_module


def _make_signal(qty):
    return NormalizedSignal(
        symbol="AAPL",
        action=SignalAction.BUY,
        strategy_id="strat",
        quantity=qty,
        raw_payload={},
        idempotency_key="id1",
        fired_at=datetime.utcnow(),
    )


class DummyBroker:
    def __init__(self, price=100.0):
        self.price = price

    def get_account(self):
        return SimpleNamespace(buying_power=10000.0, portfolio_value=10000.0)

    def get_latest_trade(self, symbol):
        assert symbol == "AAPL"
        return SimpleNamespace(price=self.price)


def test_quantity_exceeds_limit(monkeypatch):
    rm = RiskManager(db_session=None)
    monkeypatch.setattr(manager_module, "broker_client", DummyBroker(price=100.0))
    signal = _make_signal(200)
    risk_limits = SimpleNamespace(max_position_size=0.05)
    with pytest.raises(RiskViolation):
        rm._calculate_position_size(signal, 1, 1, risk_limits)


def test_quantity_within_limit(monkeypatch):
    rm = RiskManager(db_session=None)
    monkeypatch.setattr(manager_module, "broker_client", DummyBroker(price=100.0))
    signal = _make_signal(4)
    risk_limits = SimpleNamespace(max_position_size=0.05)
    qty = rm._calculate_position_size(signal, 1, 1, risk_limits)
    assert qty == 4

