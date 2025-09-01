import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.user import User
from app.models.signal import Signal
from app.models.order import Order
from app.signals.processor import WebhookProcessor
from app.services.exit_rules_service import ExitRulesService
from app.execution.order_executor import OrderExecutor
from app.execution.order_manager import OrderManager


@pytest.mark.asyncio
async def test_bracket_creation_failure_does_not_persist_orders(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

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

    monkeypatch.setattr(
        ExitRulesService,
        "get_exit_rules",
        lambda self, strategy_id, user_id: {"dummy": True},
        raising=False,
    )

    async def open_market(self, symbol):
        return {"is_open": True}

    monkeypatch.setattr(OrderExecutor, "get_market_hours", open_market)

    def failing_bracket(self, signal, user_id, portfolio_id, commit=True):
        order = Order(
            client_order_id="test",
            symbol=signal.symbol,
            side="buy",
            quantity=1,
            order_type="market",
            status="new",
            signal_id=signal.id,
            user_id=user_id,
            portfolio_id=portfolio_id,
        )
        db.add(order)
        db.flush()
        raise Exception("boom")

    monkeypatch.setattr(OrderManager, "create_bracket_order_from_signal", failing_bracket)

    result = await processor._create_automatic_bracket_orders(signal, user.id, 1)

    assert result["status"] == "error"
    assert db.query(Order).count() == 0

    db.close()
