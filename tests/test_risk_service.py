import pytest
from types import SimpleNamespace
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.risk_service import RiskService
import app.services.risk_service as risk_service_module


class DummyBroker:
    def __init__(self, portfolio_value):
        self._portfolio_value = portfolio_value

    def get_account(self):
        return SimpleNamespace(portfolio_value=self._portfolio_value)


class FakeQuery:
    def __init__(self, entities, db):
        self.entities = entities
        self.db = db

    def filter(self, condition):
        from app.models.signal import Signal

        if any(ent is Signal for ent in self.entities):
            for clause in condition.clauses:
                left = getattr(clause, "left", None)
                if getattr(left, "key", None) == "timestamp":
                    self.db.captured_one_hour_ago = clause.right.value
        return self

    def count(self):
        return 0

    def scalar(self):
        return 0


class FakeDB:
    def __init__(self):
        self.captured_one_hour_ago = None

    def query(self, *entities):
        return FakeQuery(entities, self)


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


@pytest.mark.parametrize(
    "now, expected",
    [
        (
            datetime(2024, 1, 2, 0, 30, tzinfo=ZoneInfo("America/New_York")),
            datetime(2024, 1, 1, 23, 30, tzinfo=ZoneInfo("America/New_York")),
        ),
        (
            datetime(2024, 3, 10, 3, 30, tzinfo=ZoneInfo("America/New_York")),
            datetime(2024, 3, 10, 2, 30, tzinfo=ZoneInfo("America/New_York")),
        ),
    ],
)
def test_get_risk_summary_last_hour_handles_day_change_and_dst(monkeypatch, now, expected):
    db = FakeDB()
    service = RiskService(db_session=db)

    risk_limit = SimpleNamespace(
        max_daily_drawdown=0,
        max_orders_per_hour=1000,
        max_orders_per_day=1000,
        max_open_positions=1000,
        trading_start_time=None,
        trading_end_time=None,
        allow_extended_hours=False,
    )

    monkeypatch.setattr(risk_service_module, "now_eastern", lambda: now)
    monkeypatch.setattr(service, "get_or_create_risk_limits", lambda u, p: risk_limit)

    service.get_risk_summary(user_id=1, portfolio_id=1)

    assert db.captured_one_hour_ago == expected
