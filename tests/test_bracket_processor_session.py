import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.signal import Signal
from app.models.order import Order
from app.core.types import OrderStatus
from app.execution.bracket_order_processor import BracketOrderProcessor


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.mark.asyncio
async def test_bracket_processor_uses_same_session(db_session):
    user = User(id=1, email="test@example.com", username="user", password_hash="pwd")
    db_session.add(user)
    signal = Signal(id=1, symbol="AAPL", action="buy", strategy_id="strat", user_id=user.id)
    db_session.add(signal)
    db_session.commit()

    parent_order = Order(
        client_order_id="PARENT",
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        order_type="market",
        status=OrderStatus.FILLED,
        is_bracket_parent=True,
        signal_id=signal.id,
        user_id=user.id,
    )
    db_session.add(parent_order)
    db_session.commit()

    child_order = Order(
        client_order_id="CHILD",
        symbol="AAPL",
        side="sell",
        quantity=Decimal("10"),
        order_type="limit",
        limit_price=Decimal("200"),
        status=OrderStatus.PENDING_PARENT,
        parent_order_id=parent_order.id,
        signal_id=signal.id,
        user_id=user.id,
    )
    db_session.add(child_order)
    db_session.commit()

    processor = BracketOrderProcessor(db_session)
    child_id = child_order.id
    parent_id = parent_order.id

    async def fake_execute_single_order(self, **_):
        parent = self.db.query(Order).filter(Order.id == parent_id).one()
        parent.notes = "updated"
        return {"status": "success", "broker_order_id": "SIM-TEST"}

    processor.executor.execute_single_order = fake_execute_single_order.__get__(processor.executor, type(processor.executor))

    await processor.activate_bracket_orders(parent_order.id)

    parent_ref = db_session.query(Order).filter(Order.id == parent_id).one()
    child_ref = db_session.query(Order).filter(Order.id == child_id).one()

    assert parent_ref.notes == "updated"
    assert child_ref.status == OrderStatus.SENT
