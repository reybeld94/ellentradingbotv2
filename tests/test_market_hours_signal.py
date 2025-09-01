import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.user import User
from app.models.signal import Signal
from app.execution.order_executor import OrderExecutor
from app.services.exit_rules_service import ExitRulesService

import sys
import types

dummy_testing = types.ModuleType("app.execution.testing")
dummy_testing.ExecutionTester = object
sys.modules.setdefault("app.execution.testing", dummy_testing)

from app.signals.processor import WebhookProcessor


@pytest.mark.asyncio
async def test_signal_fails_when_market_closed(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    # Create minimal user and signal
    user = User(email="test@example.com", username="user", password_hash="x")
    db.add(user)
    db.commit()
    db.refresh(user)

    signal = Signal(
        symbol="AAPL",
        action="buy",
        strategy_id="strat",
        user_id=user.id,
        portfolio_id=1,
    )
    db.add(signal)
    db.commit()
    db.refresh(signal)

    processor = WebhookProcessor(db)

    # Mock exit rules retrieval to return something truthy
    monkeypatch.setattr(
        ExitRulesService,
        "get_exit_rules",
        lambda self, strategy_id, user_id: {"dummy": True},
        raising=False,
    )

    # Simulate market closed
    async def fake_market_hours(self, symbol):
        return {"is_open": False, "status": "closed"}

    monkeypatch.setattr(OrderExecutor, "get_market_hours", fake_market_hours)

    result = await processor._create_automatic_bracket_orders(signal, user.id, 1)

    assert result["status"] == "failed"
    assert signal.status == "bracket_failed"

    db.close()
