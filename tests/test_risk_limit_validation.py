import os
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "secret")

from app.main import app
from app.database import Base, get_db
from app.core.auth import get_current_verified_user
from app.services.risk_service import RiskService
import app.services.risk_service as risk_service_module
from app.services import portfolio_service
from app.models.user import User

client = TestClient(app)


class DummyDB:
    def commit(self):
        pass

    def refresh(self, obj):
        pass


def _make_risk_limit():
    return SimpleNamespace(
        max_daily_drawdown=0.02,
        max_weekly_drawdown=0.05,
        max_account_drawdown=0.10,
        max_position_size=0.05,
        max_symbol_exposure=0.10,
        max_sector_exposure=0.25,
        max_total_exposure=0.95,
        max_orders_per_hour=10,
        max_orders_per_day=50,
        max_open_positions=10,
        trading_start_time="09:30:00",
        trading_end_time="15:30:00",
        allow_extended_hours=False,
        min_price=1.0,
        max_price=500.0,
        min_volume=100000,
        max_spread_percent=0.02,
        block_earnings_days=True,
        block_fomc_days=True,
        block_news_sentiment_negative=False,
    )


def test_update_risk_limits_boundary_values(monkeypatch):
    service = RiskService(db_session=DummyDB())
    risk_limit = _make_risk_limit()
    monkeypatch.setattr(service, "get_or_create_risk_limits", lambda u, p: risk_limit)

    updated = service.update_risk_limits(1, 1, {
        "max_daily_drawdown": 0.0,
        "max_position_size": 1.0,
    })

    assert updated.max_daily_drawdown == 0.0
    assert updated.max_position_size == 1.0


def test_update_risk_limits_invalid_values(monkeypatch):
    service = RiskService(db_session=DummyDB())
    risk_limit = _make_risk_limit()
    monkeypatch.setattr(service, "get_or_create_risk_limits", lambda u, p: risk_limit)

    with pytest.raises(ValueError):
        service.update_risk_limits(1, 1, {"max_daily_drawdown": -0.01})

    with pytest.raises(ValueError):
        service.update_risk_limits(1, 1, {"max_daily_drawdown": 1.1})


@pytest.fixture
def auth_headers(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    def override_user():
        return User(id=1, email="test@example.com", username="test", password_hash="x", is_verified=True)

    def override_get_active(db_session, user):
        return SimpleNamespace(id=1)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_verified_user] = override_user
    monkeypatch.setattr(portfolio_service, "get_active", override_get_active)

    yield {"Authorization": "Bearer test"}

    db.close()
    app.dependency_overrides.clear()


def test_update_risk_limits_api_boundary(auth_headers, monkeypatch):
    def fake_update(self, user_id, portfolio_id, updates):
        return SimpleNamespace(
            max_daily_drawdown=updates.get("max_daily_drawdown", 0.02),
            max_orders_per_hour=10,
            max_orders_per_day=50,
            max_open_positions=5,
        )

    monkeypatch.setattr(risk_service_module.RiskService, "update_risk_limits", fake_update)

    response = client.put(
        "/api/v1/risk/limits",
        json={"max_daily_drawdown": 0.0},
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.json()["limits"]["max_daily_drawdown"] == 0.0


def test_update_risk_limits_api_invalid(auth_headers, monkeypatch):
    def raise_value_error(self, user_id, portfolio_id, updates):
        raise ValueError("max_daily_drawdown must be between 0.0 and 1.0")

    monkeypatch.setattr(risk_service_module.RiskService, "update_risk_limits", raise_value_error)

    response = client.put(
        "/api/v1/risk/limits",
        json={"max_daily_drawdown": -0.1},
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "max_daily_drawdown" in response.json()["detail"]

