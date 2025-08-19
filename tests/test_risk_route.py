import asyncio
from types import SimpleNamespace
import pytest

from app.api.v1 import risk


def test_market_value_calculation(monkeypatch):
    monkeypatch.setattr(risk.position_manager, "get_current_positions", lambda: {"AAPL": 5, "USD": 25.31})
    monkeypatch.setattr(risk.risk_manager, "get_allocation_info", lambda buying_power: {})
    monkeypatch.setattr(risk.risk_manager, "calculate_optimal_position_size", lambda **k: 0)
    monkeypatch.setattr(risk.risk_manager, "get_symbol_minimum", lambda s: 0)

    class DummyBroker:
        def get_account(self):
            return SimpleNamespace(buying_power=1000.0, portfolio_value=1000.0)

        def get_latest_quote(self, symbol):
            assert symbol == "AAPL"
            return SimpleNamespace(ask_price=180.0)

    from app import integrations
    monkeypatch.setattr(integrations, "broker_client", DummyBroker())

    res = asyncio.get_event_loop().run_until_complete(risk.get_risk_status(current_user=None))
    positions = {p["symbol"]: p for p in res["current_positions"]}
    assert positions["AAPL"]["market_value"] == pytest.approx(5 * 180.0)
    assert positions["USD"]["market_value"] == pytest.approx(25.31)
