import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.signal import Signal
from app.models.order import Order
from app.core.types import OrderStatus
from app.services.bracket_reconciliation_service import BracketReconciliationService


@pytest.mark.asyncio
async def test_reconcile_updates_child_status():
    engine = create_engine("sqlite://")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    user = User(email="test@example.com", username="test", password_hash="x")
    db.add(user)
    db.flush()

    signal = Signal(symbol="AAPL", action="buy", strategy_id="s", user_id=user.id)
    db.add(signal)
    db.flush()

    parent = Order(
        client_order_id="parent1",
        symbol="AAPL",
        side="buy",
        quantity=1,
        order_type="market",
        status=OrderStatus.FILLED,
        signal_id=signal.id,
        user_id=user.id,
        is_bracket_parent=True,
    )
    db.add(parent)
    db.flush()

    child = Order(
        client_order_id="child1",
        symbol="AAPL",
        side="sell",
        quantity=1,
        order_type="limit",
        status=OrderStatus.SENT,
        broker_order_id="brk1",
        parent_order_id=parent.id,
        updated_at=datetime.utcnow() - timedelta(minutes=20),
        signal_id=signal.id,
        user_id=user.id,
    )
    db.add(child)
    db.commit()

    service = BracketReconciliationService()
    service.db = db

    class FakeExecutor:
        async def _get_order_status_from_broker(self, broker_order_id):
            return "filled"

    service.executor = FakeExecutor()

    class DummyProcessor:
        async def handle_child_order_fill(self, order_id):
            pass

    service.bracket_processor = DummyProcessor()

    result = await service._reconcile_inconsistent_children()

    db.refresh(child)
    assert result["fixed"] == 1
    assert child.status == OrderStatus.FILLED

    db.close()
