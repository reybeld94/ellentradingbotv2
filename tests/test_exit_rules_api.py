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
from app.core.auth import get_current_verified_user
from app.models.user import User

client = TestClient(app)


@pytest.fixture
def auth_headers():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_verified_user] = override_user

    yield {"Authorization": "Bearer test"}

    db.close()
    app.dependency_overrides.clear()


def test_create_exit_rules(auth_headers):
    payload = {
        "strategy_id": "test_strategy",
        "stop_loss_pct": 0.03,
        "take_profit_pct": 0.06,
        "trailing_stop_pct": 0.02,
        "use_trailing": True,
        "risk_reward_ratio": 2.0
    }

    response = client.post(
        "/api/v1/exit-rules/test_strategy",
        json=payload,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "test_strategy"
    assert data["stop_loss_pct"] == 0.03


def test_calculate_exit_prices(auth_headers):
    response = client.post(
        "/api/v1/exit-rules/test_strategy/calculate",
        json={"entry_price": 100.0, "side": "buy"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["entry_price"] == 100.0
    assert "stop_loss_price" in data
    assert "take_profit_price" in data
