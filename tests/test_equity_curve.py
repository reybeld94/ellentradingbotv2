from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.database import Base
from app.models.trades import Trade
from app.services.trade_service import TradeService


def _setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_equity_curve_filters_by_strategy():
    db = _setup_db()
    now = datetime.utcnow()
    trades = [
        Trade(strategy_id="A", symbol="AAPL", action="buy", quantity=1, entry_price=100,
              status="closed", closed_at=now, pnl=10, user_id=1, portfolio_id=1),
        Trade(strategy_id="B", symbol="AAPL", action="buy", quantity=1, entry_price=100,
              status="closed", closed_at=now, pnl=5, user_id=1, portfolio_id=1),
    ]
    db.add_all(trades)
    db.commit()

    service = TradeService(db)
    curve = service.get_equity_curve(1, 1, strategy_id="A")
    assert len(curve) == 1
    assert curve[0]["strategy_id"] == "A"
    db.close()
