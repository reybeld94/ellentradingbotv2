import math
import os
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault('SECRET_KEY', 'secret')

from app.database import Base
from app.models.trades import Trade
from app.services.trade_service import TradeService


def _setup_trades(pnls):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    now = datetime.utcnow()
    for pnl in pnls:
        trade = Trade(
            strategy_id="s",
            symbol="AAPL",
            action="buy",
            quantity=1,
            entry_price=100,
            exit_price=100 + pnl,
            status="closed",
            pnl=pnl,
            opened_at=now,
            closed_at=now,
        )
        session.add(trade)
    session.commit()
    return session


def test_metrics_basic():
    session = _setup_trades([10, -5, 15, -7, 5])
    svc = TradeService(session)
    sharpe = svc.calculate_sharpe_ratio("s", risk_free_rate=0.0)
    sortino = svc.calculate_sortino_ratio("s", risk_free_rate=0.0)
    wl = svc.calculate_avg_win_loss("s")
    expectancy = svc.calculate_expectancy("s")

    returns = [p / 100 for p in [10, -5, 15, -7, 5]]
    mean_ret = sum(returns) / len(returns)
    std_dev = math.sqrt(sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1))
    neg_returns = [r for r in returns if r < 0]
    neg_std = math.sqrt(sum((r - sum(neg_returns) / len(neg_returns)) ** 2 for r in neg_returns) / (len(neg_returns) - 1))
    assert math.isclose(sharpe, (mean_ret) / std_dev, rel_tol=1e-6)
    assert math.isclose(sortino, (mean_ret) / neg_std, rel_tol=1e-6)
    assert wl == {'avg_win': 10, 'avg_loss': 6, 'win_loss_ratio': 10/6}
    assert math.isclose(expectancy, 3.6, rel_tol=1e-6)
    session.close()


def test_metrics_edge_cases():
    session = _setup_trades([])
    svc = TradeService(session)
    assert svc.calculate_sharpe_ratio("s") == 0.0
    assert svc.calculate_sortino_ratio("s") == 0.0
    assert svc.calculate_avg_win_loss("s") == {'avg_win': 0.0, 'avg_loss': 0.0, 'win_loss_ratio': 0.0}
    assert svc.calculate_expectancy("s") == 0.0
    session.close()

    session = _setup_trades([5, 15])
    svc = TradeService(session)
    assert svc.calculate_sharpe_ratio("s", risk_free_rate=0.0) > 0.0
    assert svc.calculate_sortino_ratio("s", risk_free_rate=0.0) == 0.0
    wl = svc.calculate_avg_win_loss("s")
    assert wl == {'avg_win': 10, 'avg_loss': 0.0, 'win_loss_ratio': 0.0}
    assert math.isclose(svc.calculate_expectancy("s"), 10.0, rel_tol=1e-6)
    session.close()

    session = _setup_trades([-5, -15])
    svc = TradeService(session)
    assert svc.calculate_sharpe_ratio("s", risk_free_rate=0.0) < 0.0
    assert svc.calculate_sortino_ratio("s", risk_free_rate=0.0) < 0.0
    wl = svc.calculate_avg_win_loss("s")
    assert wl == {'avg_win': 0.0, 'avg_loss': 10.0, 'win_loss_ratio': 0.0}
    assert math.isclose(svc.calculate_expectancy("s"), -10.0, rel_tol=1e-6)
    session.close()
