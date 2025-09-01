import pytest
from datetime import datetime, timedelta
import statistics
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analytics.portfolio_analytics import PortfolioAnalytics
from app.database import Base
from app.models.user import User
from app.models.portfolio import Portfolio
from app.models.trades import Trade


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


@pytest.fixture
def test_user(db_session):
    user = User(email="test@example.com", username="testuser", password_hash="test", is_verified=True)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_portfolio(db_session, test_user):
    portfolio = Portfolio(
        name="test_portfolio",
        api_key_encrypted="key",
        secret_key_encrypted="secret",
        base_url="http://example.com",
        broker="alpaca",
        is_active=True,
        user_id=test_user.id,
    )
    db_session.add(portfolio)
    db_session.commit()
    db_session.refresh(portfolio)
    return portfolio


def test_calculate_win_rate(db_session, test_user, test_portfolio):
    """Test cálculo de win rate"""
    analytics = PortfolioAnalytics(db_session)

    trades_data = [
        {"pnl": 100.0, "status": "closed"},
        {"pnl": 50.0, "status": "closed"},
        {"pnl": -30.0, "status": "closed"},
    ]

    for trade_data in trades_data:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            quantity=10,
            entry_price=100.0,
            **trade_data,
        )
        db_session.add(trade)

    db_session.commit()

    base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    win_rate = analytics._calculate_win_rate(base_query)

    assert win_rate == 66.67


def test_profit_factor_calculation(db_session, test_user, test_portfolio):
    """Test cálculo de profit factor"""
    analytics = PortfolioAnalytics(db_session)

    trades_data = [
        {"pnl": 100.0},
        {"pnl": 50.0},
        {"pnl": -50.0},
    ]

    for trade_data in trades_data:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            status="closed",
            **trade_data,
        )
        db_session.add(trade)

    db_session.commit()

    base_query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    pf = analytics._calculate_profit_factor(base_query)

    assert pf == 3.0


def test_sharpe_ratio_calculation(db_session, test_user, test_portfolio):
    """Test cálculo de Sharpe Ratio con retornos en decimales"""
    analytics = PortfolioAnalytics(db_session)

    pnls = [10.0, -5.0, 15.0, -7.0, 5.0]
    for pnl in pnls:
        trade = Trade(
            user_id=test_user.id,
            portfolio_id=test_portfolio.id,
            symbol="AAPL",
            pnl=pnl,
            quantity=1,
            entry_price=100.0,
            status="closed",
            opened_at=datetime.utcnow(),
        )
        db_session.add(trade)

    db_session.commit()

    query = db_session.query(Trade).filter(Trade.user_id == test_user.id)
    sharpe = analytics._calculate_sharpe_ratio(query)

    returns = [p / 100.0 for p in pnls]
    avg_return = statistics.mean(returns)
    std_return = statistics.stdev(returns)
    risk_free_rate = 0.0055 / 252
    expected_sharpe = round((avg_return - risk_free_rate) / std_return, 4)

    assert sharpe == expected_sharpe

