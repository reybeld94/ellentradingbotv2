import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "secret")

from fastapi import FastAPI

from app.api.v1 import trades
from app.database import Base, get_db
from app.core.auth import get_current_verified_user
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trades import Trade
from app.core.types import TradeStatus
from app.services.order_executor import OrderExecutor

app = FastAPI()
app.include_router(trades.router, prefix="/api/v1")

client = TestClient(app)

@pytest.fixture
def setup_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    user = User(email="a@b.c", username="u", password_hash="x", is_verified=True, position_limit=10)
    db.add(user)
    db.commit()
    db.refresh(user)

    portfolio = Portfolio(name="p", api_key_encrypted="k", secret_key_encrypted="s", base_url="https://paper-api.alpaca.markets", is_active=True, user_id=user.id)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)

    trade = Trade(user_id=user.id, portfolio_id=portfolio.id, symbol="AAPL", action="buy", quantity=1, entry_price=100.0, status=TradeStatus.OPEN, opened_at=datetime.utcnow(), strategy_id="s")
    db.add(trade)
    db.commit()
    db.refresh(trade)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_verified_user] = lambda: user

    yield client, db, trade, user

    db.close()
    app.dependency_overrides.clear()


def test_close_trade_executes_signal(setup_db, monkeypatch):
    client, db, trade, user = setup_db
    called = {}

    def fake_execute(self, signal, u):
        called["signal"] = signal
        called["user"] = u

    monkeypatch.setattr(OrderExecutor, "execute_signal", fake_execute)

    response = client.post(f"/api/v1/trades/{trade.id}/close", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    assert called["signal"].symbol == trade.symbol

    db.refresh(trade)
    assert trade.status == TradeStatus.CLOSED


def test_close_trade_failure_keeps_open(setup_db, monkeypatch):
    client, db, trade, user = setup_db
    called = {"called": False}

    def fake_execute(self, signal, u):
        called["called"] = True
        raise Exception("boom")

    monkeypatch.setattr(OrderExecutor, "execute_signal", fake_execute)

    response = client.post(f"/api/v1/trades/{trade.id}/close", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    assert called["called"] is True

    db.refresh(trade)
    assert trade.status == TradeStatus.OPEN
