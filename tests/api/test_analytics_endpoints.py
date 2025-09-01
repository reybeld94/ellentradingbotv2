import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trades import Trade
from app.core.auth import get_current_verified_user
from app.services import portfolio_service

client = TestClient(app)


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user(db_session):
    user = User(email="test@example.com", username="test", password_hash="x", is_verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db_session, test_user):
    portfolio = Portfolio(
        name="test_portfolio",
        api_key_encrypted="key",
        secret_key_encrypted="secret",
        base_url="http://example.com",
        broker="alpaca",
        is_active=True,
        user_id=test_user.id,
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


@pytest.fixture
def auth_headers(db_session, test_user, test_portfolio, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_verified_user] = override_user
    monkeypatch.setattr(portfolio_service, "get_active", lambda db, user: test_portfolio)

    yield {"Authorization": "Bearer test"}

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers_no_portfolio(db_session, test_user, monkeypatch):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_verified_user] = override_user
    monkeypatch.setattr(portfolio_service, "get_active", lambda db, user: None)

    yield {"Authorization": "Bearer test"}

    app.dependency_overrides.clear()


def test_get_performance_metrics_success(db_session, test_user, test_portfolio, auth_headers):
    """Test obtener métricas de performance exitosamente"""

    trades_data = [
        {"pnl": 100.0, "quantity": 10, "entry_price": 50.0, "status": "closed"},
        {"pnl": -20.0, "quantity": 5, "entry_price": 40.0, "status": "closed"},
        {"pnl": 75.0, "quantity": 15, "entry_price": 30.0, "status": "closed"},
    ]

    for data in trades_data:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            action="buy",
            **data,
        )
        db_session.add(trade)
    db_session.commit()

    response = client.get("/api/v1/analytics/performance?timeframe=1M", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    expected_fields = [
        "total_pnl",
        "total_pnl_percentage",
        "sharpe_ratio",
        "max_drawdown",
        "win_rate",
        "avg_hold_time",
        "profit_factor",
        "total_trades",
        "winning_trades",
        "losing_trades",
        "timeframe",
    ]
    for field in expected_fields:
        assert field in data

    assert data["total_pnl"] == 155.0
    assert data["total_trades"] == 3
    assert data["winning_trades"] == 2
    assert data["losing_trades"] == 1
    assert data["timeframe"] == "1M"


def test_get_analytics_summary_success(auth_headers):
    """Test obtener resumen de analytics"""
    response = client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "timeframes" in data
    assert "all_time" in data
    assert "portfolio_id" in data
    assert "portfolio_name" in data
    for tf in ["1d", "1w", "1m", "3m"]:
        assert tf in data["timeframes"]


def test_performance_metrics_no_portfolio(auth_headers_no_portfolio):
    """Test cuando no hay portfolio activo"""
    response = client.get("/api/v1/analytics/performance", headers=auth_headers_no_portfolio)
    assert response.status_code == 400
    assert "No active portfolio found" in response.json()["detail"]
