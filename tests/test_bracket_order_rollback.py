import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.signal import Signal
from app.models.order import Order
from app.execution.order_manager import OrderManager
from app.services.exit_rules_service import ExitRulesService


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


def test_exit_order_failure_rolls_back_main_order(db_session, monkeypatch):
    # Create required user and signal
    user = User(id=1, email="test@example.com", username="user", password_hash="pwd")
    db_session.add(user)
    signal = Signal(id=1, symbol="AAPL", action="buy", strategy_id="strat", user_id=user.id)
    db_session.add(signal)
    db_session.commit()

    om = OrderManager(db_session)

    # Mock current price and exit rule calculation
    monkeypatch.setattr(om, "_get_current_price", lambda symbol: 100.0)

    def fake_calc(self, strategy_id, user_id, price, action):
        return {
            "entry_price": Decimal("100"),
            "stop_loss_price": Decimal("95"),
            "take_profit_price": Decimal("105"),
        }

    monkeypatch.setattr(ExitRulesService, "calculate_exit_prices", fake_calc)

    # Force failure when creating the take profit order
    original_add = db_session.add

    def failing_add(obj):
        if isinstance(obj, Order) and getattr(obj, "client_order_id", "").startswith("TP_"):
            raise Exception("failure creating exits")
        return original_add(obj)

    monkeypatch.setattr(db_session, "add", failing_add)

    result = om.create_bracket_order_from_signal(signal, user_id=user.id, portfolio_id=None)

    assert result["status"] == "error"
    # No orders should be persisted due to rollback
    assert db_session.query(Order).count() == 0
