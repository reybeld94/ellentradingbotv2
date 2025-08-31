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
def client_and_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield client

    db.close()
    app.dependency_overrides.clear()


def get_headers():
    return {"Authorization": "Bearer test"}


def user_factory(user_id: int) -> User:
    return User(id=user_id, email=f"user{user_id}@example.com", username=f"user{user_id}", password_hash="x", is_verified=True)


def test_create_exit_rules(client_and_db):
    client = client_and_db

    app.dependency_overrides[get_current_verified_user] = lambda: user_factory(1)

    payload = {
        "strategy_id": "test_strategy",
        "stop_loss_pct": 0.03,
        "take_profit_pct": 0.06,
        "trailing_stop_pct": 0.02,
        "use_trailing": True,
        "risk_reward_ratio": 2.0,
    }

    response = client.post("/api/v1/exit-rules/test_strategy", json=payload, headers=get_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "test_strategy"
    assert data["stop_loss_pct"] == 0.03


def test_calculate_exit_prices(client_and_db):
    client = client_and_db
    app.dependency_overrides[get_current_verified_user] = lambda: user_factory(1)

    response = client.post(
        "/api/v1/exit-rules/test_strategy/calculate",
        json={"entry_price": 100.0, "side": "buy"},
        headers=get_headers(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["entry_price"] == 100.0
    assert "stop_loss_price" in data
    assert "take_profit_price" in data


def test_authorization_get_and_update(client_and_db):
    client = client_and_db

    # Owner creates rules
    app.dependency_overrides[get_current_verified_user] = lambda: user_factory(1)
    client.post(
        "/api/v1/exit-rules/test_strategy",
        json={
            "strategy_id": "test_strategy",
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.06,
            "trailing_stop_pct": 0.02,
            "use_trailing": True,
            "risk_reward_ratio": 2.0,
        },
        headers=get_headers(),
    )

    # Owner can retrieve
    response = client.get("/api/v1/exit-rules/test_strategy", headers=get_headers())
    assert response.status_code == 200

    # Another user cannot retrieve or update
    app.dependency_overrides[get_current_verified_user] = lambda: user_factory(2)
    response = client.get("/api/v1/exit-rules/test_strategy", headers=get_headers())
    assert response.status_code == 403 or response.status_code == 404

    response = client.put(
        "/api/v1/exit-rules/test_strategy",
        json={"stop_loss_pct": 0.05},
        headers=get_headers(),
    )
    assert response.status_code == 403 or response.status_code == 404
