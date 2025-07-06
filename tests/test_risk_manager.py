import math
from datetime import datetime
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault('SECRET_KEY', 'secret')

from app.database import Base
from app.models.trades import Trade
from app.services.risk_manager import RiskManager


def _setup_session(wins: int, losses: int):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    now = datetime.utcnow()
    for _ in range(wins):
        trade = Trade(
            strategy_id="s",
            symbol="AAPL",
            action="buy",
            quantity=1,
            entry_price=100,
            exit_price=110,
            status="closed",
            pnl=10,
            opened_at=now,
            closed_at=now,
        )
        session.add(trade)
    for _ in range(losses):
        trade = Trade(
            strategy_id="s",
            symbol="AAPL",
            action="buy",
            quantity=1,
            entry_price=100,
            exit_price=90,
            status="closed",
            pnl=-10,
            opened_at=now,
            closed_at=now,
        )
        session.add(trade)
    session.commit()
    return session, sessionmaker(bind=engine)


def test_risk_manager_default_percentage():
    session, factory = _setup_session(5, 5)
    rm = RiskManager(session_factory=factory)
    qty = rm.calculate_optimal_position_size(price=100, buying_power=1000)
    assert math.isclose(qty, 1.4, rel_tol=1e-6)
    session.close()


def test_risk_manager_with_monte_carlo():
    # 33 wins, 27 losses -> win rate 55%, R=1 -> kelly ~= 0.10
    session, factory = _setup_session(33, 27)
    rm = RiskManager(session_factory=factory)
    qty = rm.calculate_optimal_position_size(price=100, buying_power=1000)
    assert math.isclose(qty, 1.0, rel_tol=1e-6)
    session.close()

