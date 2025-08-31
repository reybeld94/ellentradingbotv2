import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "secret")

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.schemas.webhook import TradingViewWebhook
from app.signals.processor import WebhookProcessor
from app.utils.rate_limiter import RateLimiter, get_rate_limiter

import fakeredis
import fakeredis.aioredis


@pytest.fixture
def client_and_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # create required objects
    user = User(email="reybel@example.com", username="reybel", password_hash="x", is_verified=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    portfolio = Portfolio(
        name="p",
        api_key_encrypted="k",
        secret_key_encrypted="s",
        base_url="https://paper-api.alpaca.markets",
        is_active=True,
        user_id=user.id,
    )
    db.add(portfolio)
    strategy = Strategy(name="s")
    db.add(strategy)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Override rate limiter with fakeredis using a shared server
    server = fakeredis.FakeServer()

    async def override_get_rate_limiter():
        redis_instance = fakeredis.aioredis.FakeRedis(server=server)
        return RateLimiter(redis_instance, limit=2, window=60)

    app.dependency_overrides[get_rate_limiter] = override_get_rate_limiter

    client = TestClient(app)
    yield client
    db.close()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_processor_blocks_invalid_data(client_and_db):
    """Ensure processor rejects invalid symbol or quantity."""
    db = next(app.dependency_overrides[get_db]())
    processor = WebhookProcessor(db)
    user = db.query(User).first()

    data = TradingViewWebhook(symbol="BAD$", action="buy", strategy_id="s", quantity=-5)
    result = await processor.process_tradingview_webhook(data, user)
    assert result["status"] == "validation_failed"
    assert any("Invalid" in err for err in result["errors"])


def test_rate_limiter_blocks_high_frequency(client_and_db, monkeypatch):
    """Ensure rate limiter blocks excessive requests."""
    client = client_and_db

    async def fake_process(self, data, user):
        return {"status": "accepted", "signal_id": 1}

    monkeypatch.setattr(WebhookProcessor, "process_tradingview_webhook", fake_process)

    payload = {
        "symbol": "AAPL",
        "action": "buy",
        "strategy_id": "s",
        "quantity": 1,
    }
    url = "/api/v1/webhook-public?api_key=ELLENTRADING0408"

    # First two requests succeed
    assert client.post(url, json=payload).status_code == 200
    assert client.post(url, json=payload).status_code == 200
    # Third request is rate limited
    response = client.post(url, json=payload)
    assert response.status_code == 429
    assert response.json()["detail"] == "Too many requests"
