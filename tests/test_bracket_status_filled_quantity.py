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


def test_get_bracket_status_uses_filled_quantity(db_session):
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
        filled_quantity=Decimal("5"),
        signal_id=signal.id,
        user_id=user.id,
    )
    db_session.add(parent_order)
    db_session.commit()

    processor = BracketOrderProcessor(db_session)
    status = processor.get_bracket_status(parent_order.id)

    assert status["parent_order"]["filled_quantity"] == Decimal("5")
    assert "filled_qty" not in status["parent_order"]
