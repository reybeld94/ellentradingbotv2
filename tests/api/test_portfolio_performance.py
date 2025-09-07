import sys
import types
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi import APIRouter

# Provide lightweight modules to satisfy imports during app startup
order_processor_module = types.ModuleType("app.execution.order_processor")


class _DummyOrderProcessor:
    def __init__(self, db):
        pass

    def process_pending_orders(self):
        return {}

    def process_single_order(self, order_id):
        return {"success": True, "order_id": order_id, "client_order_id": "x"}


order_processor_module.OrderProcessor = _DummyOrderProcessor
sys.modules.setdefault("app.execution.order_processor", order_processor_module)

execution_api_module = types.ModuleType("app.api.v1.execution")
execution_api_module.router = APIRouter()
sys.modules.setdefault("app.api.v1.execution", execution_api_module)

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.portfolio import Portfolio
from app.core.auth import get_current_verified_user
from app.services import portfolio_service
import app.api.v1.portfolio_performance as portfolio_performance_module

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


def test_portfolio_performance_success(auth_headers, monkeypatch):
    class FakeClient:
        def __init__(self, portfolio):
            self._trading = SimpleNamespace(
                get_portfolio_history=lambda req: SimpleNamespace(
                    equity=[1000.0, 1100.0],
                    timestamp=[datetime.now().timestamp(), datetime.now().timestamp() + 60],
                )
            )

    monkeypatch.setattr(
        portfolio_performance_module, "AlpacaClient", FakeClient  # type: ignore
    )

    response = client.get(
        "/api/v1/portfolio/performance?timeframe=1D", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["initial_value"] == 1000.0
    assert data["current_value"] == 1100.0
    assert len(data["historical_data"]) == 2


def test_portfolio_performance_no_data(auth_headers, monkeypatch):
    class EmptyClient:
        def __init__(self, portfolio):
            self._trading = SimpleNamespace(
                get_portfolio_history=lambda req: SimpleNamespace(equity=[], timestamp=[])
            )

    monkeypatch.setattr(
        portfolio_performance_module, "AlpacaClient", EmptyClient  # type: ignore
    )

    response = client.get(
        "/api/v1/portfolio/performance?timeframe=1D", headers=auth_headers
    )
    assert response.status_code == 404
    assert "No portfolio history data available" in response.json()["detail"]


def test_portfolio_performance_no_portfolio(auth_headers_no_portfolio):
    response = client.get(
        "/api/v1/portfolio/performance?timeframe=1D",
        headers=auth_headers_no_portfolio,
    )
    assert response.status_code == 400
    assert "No active portfolio found" in response.json()["detail"]
