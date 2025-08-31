import pytest
from types import SimpleNamespace

from app.services.risk_service import RiskService
import app.services.risk_service as risk_service_module


class DummyBroker:
    def __init__(self, portfolio_value):
        self._portfolio_value = portfolio_value

    def get_account(self):
        return SimpleNamespace(portfolio_value=self._portfolio_value)


def test_daily_drawdown_uses_dynamic_portfolio_value(monkeypatch):
    service = RiskService(db_session=None)
    limits = SimpleNamespace(
        max_orders_per_hour=100,
        max_orders_per_day=100,
        max_open_positions=10,
        max_daily_drawdown=0.10,
    )

    daily_pnl = -1000
    orders_today = 0
    orders_last_hour = 0
    open_positions = 0

    # Portfolio of 10k should trigger warning (10% DD >= 80% of 10% limit)
    monkeypatch.setattr(risk_service_module, "broker_client", DummyBroker(10000))
    warnings = service._get_risk_warnings(
        limits, daily_pnl, orders_today, orders_last_hour, open_positions
    )
    assert any("High daily drawdown" in w for w in warnings)

    # Portfolio of 20k should not trigger warning (5% DD < 80% of limit)
    monkeypatch.setattr(risk_service_module, "broker_client", DummyBroker(20000))
    warnings = service._get_risk_warnings(
        limits, daily_pnl, orders_today, orders_last_hour, open_positions
    )
    assert all("High daily drawdown" not in w for w in warnings)
