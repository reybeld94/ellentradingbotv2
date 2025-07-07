import os
import types
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault('SECRET_KEY', 'secret')

from app.database import Base
from app.models.trades import Trade
from app.models.strategy_position import StrategyPosition
from app.models.signal import Signal
from app.services.trade_service import TradeService
from app.services.strategy_position_manager import StrategyPositionManager
from app.services.order_executor import OrderExecutor



def _setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_refresh_does_not_close_open_trades(monkeypatch):
    db = _setup_db()
    trade = Trade(
        strategy_id="s",
        symbol="AAPL",
        action="buy",
        quantity=1,
        entry_price=100,
        status="open",
        user_id=1,
        portfolio_id=1,
    )
    db.add(trade)
    db.commit()

    service = TradeService(db)

    class DummyBroker:
        def list_orders(self, *a, **k):
            return []
        def is_crypto_symbol(self, s):
            return False
        def get_latest_quote(self, s):
            return types.SimpleNamespace(ask_price=105)
        def get_latest_crypto_quote(self, s):
            return types.SimpleNamespace(ap=105)
        def get_position(self, s):
            return None

    monkeypatch.setattr(service, "broker", DummyBroker())

    service.refresh_user_trades(1, 1)
    refreshed = db.query(Trade).first()
    assert refreshed.status == "open"
    assert refreshed.pnl == 5
    db.close()

def test_execute_sell_closes_trades(monkeypatch):
    db = _setup_db()

    # existing position and open trades
    position = StrategyPosition(
        strategy_id="s",
        symbol="AAPL",
        quantity=2,
        avg_price=100,
        total_invested=200,
    )
    db.add(position)
    trade1 = Trade(
        strategy_id="s",
        symbol="AAPL",
        action="buy",
        quantity=1,
        entry_price=100,
        status="open",
        user_id=1,
        portfolio_id=1,
    )
    trade2 = Trade(
        strategy_id="s",
        symbol="AAPL",
        action="buy",
        quantity=1,
        entry_price=110,
        status="open",
        user_id=1,
        portfolio_id=1,
    )
    db.add_all([trade1, trade2])
    db.commit()

    oe = OrderExecutor()

    class DummyBroker:
        def is_crypto_symbol(self, s):
            return False
        def get_latest_quote(self, s):
            return types.SimpleNamespace(ask_price=120)
        def submit_order(self, **kwargs):
            return types.SimpleNamespace(id="1")
    monkeypatch.setattr(oe, "broker", DummyBroker())
    monkeypatch.setattr(asyncio, "create_task", lambda coro: None)
    from app.websockets import manager as ws_manager
    monkeypatch.setattr(ws_manager, "ws_manager", ws_manager.ws_manager)
    monkeypatch.setattr(ws_manager.ws_manager, "broadcast", lambda *a, **k: None)

    spm = StrategyPositionManager(db)
    signal = Signal(
        symbol="AAPL",
        action="sell",
        strategy_id="s",
        quantity=2,
        user_id=1,
        portfolio_id=1,
    )
    oe._execute_sell_signal(signal, spm, "AAPL", db)

    trades = db.query(Trade).order_by(Trade.entry_price).all()
    assert all(t.status == "closed" for t in trades)
    assert trades[0].pnl == 20  # 120 - 100
    assert trades[1].pnl == 10  # 120 - 110
    db.close()
