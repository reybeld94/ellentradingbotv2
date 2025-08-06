import types
import pytest

from app.services import portfolio_service as ps


class DummyQuery:
    def __init__(self, portfolio):
        self.portfolio = portfolio

    def filter_by(self, **kwargs):
        # ignore filters for simplicity
        return self

    def first(self):
        return self.portfolio


class DummyDB:
    def __init__(self, portfolio):
        self.portfolio = portfolio

    def query(self, model):
        return DummyQuery(self.portfolio)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


def test_update_active_portfolio_refreshes_credentials(monkeypatch):
    portfolio = types.SimpleNamespace(
        id=1,
        user_id=1,
        name="paper",
        api_key_encrypted="old",
        secret_key_encrypted="old",
        base_url="https://paper-api.alpaca.markets",
        broker="alpaca",
        is_paper=True,
        is_active=True,
    )
    db = DummyDB(portfolio)
    user = types.SimpleNamespace(id=1)

    called = {"update": False, "refresh": False, "refresh_client": False}

    def fake_update(self, p):
        called["update"] = True

    def fake_refresh():
        called["refresh"] = True

    def fake_refresh_client():
        called["refresh_client"] = True

    monkeypatch.setattr(ps.settings.__class__, "update_from_portfolio", fake_update)
    monkeypatch.setattr(ps.alpaca_client, "refresh", fake_refresh)
    monkeypatch.setattr(ps, "refresh_broker_client", fake_refresh_client)

    ps.update_portfolio(db, user, 1, api_key="new", secret_key="newsecret")

    assert called["update"]
    assert called["refresh"]
    assert called["refresh_client"]
